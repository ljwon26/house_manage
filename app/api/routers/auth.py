from fastapi import APIRouter, Form, Request, status, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
import os

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# 로그인에 사용할 비밀번호 설정 (환경 변수 또는 직접 설정)
LOGIN_PASSWORD = os.getenv("LOGIN_PASSWORD", "3152")

@router.get("/login", response_class=RedirectResponse)
def login(request: Request):
    if request.session.get("logged_in"):
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def process_login(request: Request, password: str = Form(...)):
    if password == LOGIN_PASSWORD:
        request.session["logged_in"] = True
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    else:
        raise HTTPException(status_code=400, detail="Invalid password")

@router.get("/logout")
async def logout(request: Request):
    request.session.pop("logged_in", None)
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

