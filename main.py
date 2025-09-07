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
# ▼▼▼ [수정] main.py에서는 더 이상 이메일 관련 라이브러리가 필요 없으므로 아래 2줄을 삭제해도 됩니다. ▼▼▼
# import aiosmtplib
# from email.mime.text import MIMEText 
from pydantic import BaseModel
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from starlette.middleware.sessions import SessionMiddleware

# --- 프로젝트 내부 모듈 임포트 ---
from app.core.database import SessionLocal, Base, engine, get_db
from app.core.models import Income, Expense, Task
from app.api.routers import auth, expenses, tasks, dashboard, monthly_ledger 
from app.api import assets
# ▼▼▼ [핵심] tasks.py에 있는 send_email 함수를 가져오는 이 부분은 그대로 둡니다. ▼▼▼
from app.api.routers.tasks import send_email


app = FastAPI()

app.include_router(assets.router, tags=["Assets"])
# --- FastAPI 앱 인스턴스 생성 ---


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
def create_db_tables():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created.")

# --- 라우터 포함 ---
app.include_router(auth.router, tags=["Auth"])
app.include_router(expenses.router, tags=["Expenses"])
app.include_router(tasks.router, tags=["Tasks"])
app.include_router(dashboard.router, tags=["Dashboard"])
app.include_router(monthly_ledger.router, tags=["MonthlyLedger"])

# --- 메인 페이지 라우트 ---
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return RedirectResponse(url="/login", status_code=303)

# --- [핵심] 이메일 전송 기능 삭제 ---
# ▼▼▼ 아래 async def send_email(...) 함수 전체를 삭제합니다. ▼▼▼
# async def send_email(subject, recipient, body):
#     sender = os.getenv("EMAIL_SENDER")
#     if not sender:
#         print("EMAIL_SENDER environment variable is not set. Skipping email.")
#         return
#     ... (이하 함수 내용 전체) ...
#     except Exception as e:
#         print(f"Error sending email: {e}")
# ▲▲▲ 여기까지 함수 전체를 삭제해주세요. ▲▲▲


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
    # 테이블 생성
    create_db_tables()
    
    # 스케줄러에 마감일 알림 작업 등록
    scheduler.add_job(send_due_date_reminders, 'cron', hour=9, minute=10)
    
    #print("마감일 알림 스케줄러가 매일 09:10에 실행되도록 설정되었습니다.")