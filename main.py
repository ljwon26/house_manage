import os
import json
from urllib.parse import urlencode
from datetime import date, timedelta, datetime
from typing import List

from fastapi import FastAPI, Depends, Form, Request, BackgroundTasks, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Date, REAL, Float, func
import aiosmtplib
from email.mime.text import MIMEText
from pydantic import BaseModel
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from starlette.middleware.sessions import SessionMiddleware

# --- 프로젝트 내부 모듈 임포트 ---
# 주의: 이 임포트는 FastAPI 앱과 템플릿 객체가 정의된 후에 와야 합니다.
from app.core.database import SessionLocal, Base, engine, get_db
from app.core.models import Income, Expense, Task
from app.api.routers import auth, expenses, tasks, dashboard, monthly_ledger 
from app.api import assets
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
scheduler = AsyncIOScheduler()
scheduler.start()

# --- 데이터베이스 테이블 생성 ---
# 애플리케이션 시작 시 데이터베이스에 테이블을 생성합니다.
@app.on_event("startup")
def create_db_tables():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created.")

# --- 라우터 포함 ---
# 라우터를 포함하여 각 기능별 엔드포인트를 연결합니다.
app.include_router(auth.router, tags=["Auth"])
app.include_router(expenses.router, tags=["Expenses"])
app.include_router(tasks.router, tags=["Tasks"])
app.include_router(dashboard.router, tags=["Dashboard"])
app.include_router(monthly_ledger.router, tags=["MonthlyLedger"])

# --- 메인 페이지 라우트 ---
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return RedirectResponse(url="/dashboard", status_code=303)

# --- 이메일 전송 기능 ---
async def send_email(subject, recipient, body):
    sender = os.getenv("EMAIL_SENDER")
    if not sender:
        print("EMAIL_SENDER environment variable is not set. Skipping email.")
        return

    password = os.getenv("EMAIL_PASSWORD")
    if not password:
        print("EMAIL_PASSWORD environment variable is not set. Skipping email.")
        return

    message = MIMEText(body)
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = recipient

    try:
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        
        async with aiosmtplib.SMTP(hostname=smtp_server, port=smtp_port, use_tls=True) as smtp:
            await smtp.login(sender, password)
            await smtp.send_message(message)
            print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")
