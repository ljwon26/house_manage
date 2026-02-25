import os
import json
import pytz
from urllib.parse import urlencode
from datetime import date, timedelta, datetime
from typing import List
from fastapi import FastAPI, Depends, Form, Request, BackgroundTasks, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Date, REAL, Float, func
from pydantic import BaseModel
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from starlette.middleware.sessions import SessionMiddleware
from app.core.database import SessionLocal, Base, engine, get_db
from app.core.models import Income, Expense, Task
from app.api import assets
from app.api.routers.tasks import send_email
from app.api.routers import auth, expenses, tasks, dashboard, monthly_ledger, insurance, diary
from app.core import models 
from app.core.database import engine, Base

app = FastAPI()

# --- 세션 미들웨어 추가 ---
SECRET_KEY = os.getenv("SECRET_KEY", "a_very_secret_key_that_should_be_changed")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# --- 로그인 비밀번호 설정 ---
LOGIN_PASSWORD = os.getenv("LOGIN_PASSWORD", "3152")

# 정적 파일을 서빙하기 위한 설정입니다.
app.mount("/static", StaticFiles(directory="static"), name="static")

# Jinja2 템플릿 엔진을 설정합니다.
templates = Jinja2Templates(directory="templates")

# 스케줄러 설정
scheduler = AsyncIOScheduler(timezone=pytz.timezone('Asia/Seoul'))
scheduler.start()

# --- 데이터베이스 테이블 생성 ---
print("Creating database tables...")
models.Base.metadata.create_all(bind=engine) 
print("Database tables created.")

# --- 라우터 포함 ---
app.include_router(assets.router, tags=["Assets"])
app.include_router(auth.router, tags=["Auth"])
app.include_router(expenses.router, tags=["Expenses"])
app.include_router(tasks.router, tags=["Tasks"])
app.include_router(dashboard.router, tags=["Dashboard"])
app.include_router(monthly_ledger.router, tags=["MonthlyLedger"])
app.include_router(insurance.router, tags=["Insurance"])
app.include_router(diary.router)

# --- 메인 페이지 라우트 ---
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return RedirectResponse(url="/login", status_code=303)

# --- 마감일 이메일 발송 함수 정의 ---
async def send_due_date_reminders():
    """
    매일 정해진 시간에 실행되어, 마감일이 오늘인 Task에 대해 알림 이메일을 보냅니다.
    """
    db = SessionLocal()
    try:
        today = date.today()
        tasks_due_today = db.query(Task).filter(Task.due_date == today).all()

        if tasks_due_today:
            print(f"오늘 마감인 {len(tasks_due_today)}개의 알림을 발견했습니다. 이메일 발송을 시작합니다...")

        for task in tasks_due_today:
            subject = f"[마감일 알림] {task.item_name}"
            body = f"안녕하세요, 오늘 '{task.item_name}' 항목의 마감일입니다. 잊지 말고 확인해주세요!"
            
            # ▼▼▼ [핵심] 이제 이 함수는 tasks.py의 send_email 함수를 정확히 호출합니다. ▼▼▼
            await send_email(to_email=task.email, subject=subject, body=body)
            
    finally:
        db.close()

# --- 애플리케이션 시작 시 실행될 이벤트 ---
@app.on_event("startup")
def startup_event():
    os.makedirs("static/diary", exist_ok=True)
    # 스케줄러에 마감일 알림 작업 등록
    scheduler.add_job(send_due_date_reminders, 'cron', hour=9, minute=10)
