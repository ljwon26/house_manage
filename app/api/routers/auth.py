from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
import os

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# 로그인 비밀번호 설정 (환경 변수 또는 기본값)
LOGIN_PASSWORD = os.getenv("LOGIN_PASSWORD", "3152")

@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
def login_submit(request: Request, password: str = Form(...)):
    if password == LOGIN_PASSWORD:
        request.session["logged_in"] = True
        # --- [수정] ---
        # 로그인 후 원래 가려던 페이지가 있으면 거기로, 없으면 대시보드로 보냅니다.
        redirect_url = request.session.pop("redirect_after_login", "/dashboard")
        return RedirectResponse(url=redirect_url, status_code=303)
    else:
        return templates.TemplateResponse("login.html", {"request": request, "error": "비밀번호가 틀렸습니다."})

@router.get("/logout")
def logout(request: Request):
    request.session.pop("logged_in", None)
    return RedirectResponse(url="/login", status_code=303)

def is_logged_in(request: Request):
    return request.session.get("logged_in", False)
