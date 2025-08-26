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
        # 로그인 후 원래 가려던 페이지가 있으면 거기로, 없으면 대시보드로 보냅니다.
        redirect_url = request.session.pop("redirect_after_login", "/dashboard")
        return RedirectResponse(url=redirect_url, status_code=303)
    else:
        return templates.TemplateResponse("login.html", {"request": request, "error": "비밀번호가 틀렸습니다."})

@router.get("/logout")
def logout(request: Request):
    # --- [수정] ---
    # 1. 서버 측 세션 정보를 모두 비웁니다.
    request.session.clear()
    
    # 2. 로그인 페이지로 리디렉션 응답을 먼저 생성합니다.
    response = RedirectResponse(url="/login", status_code=303)
    
    # 3. 브라우저에게 세션 쿠키를 삭제하라고 명시적으로 명령합니다.
    response.delete_cookie(key="session")
    
    return response

def is_logged_in(request: Request):
    return request.session.get("logged_in", False)
