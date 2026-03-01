import os
import uuid
from fastapi import APIRouter, Depends, Form, Request, status, Response
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.models import TrustedDevice # 추가된 모델 임포트

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# 일반 로그인 비밀번호와 별개로, '기기를 등록할 때만' 쓰는 초강력 마스터 비밀번호입니다.
DEVICE_SECRET_CODE = os.getenv("DEVICE_SECRET_CODE", "Govldnjsl90!")
LOGIN_PASSWORD = os.getenv("LOGIN_PASSWORD", "3152")

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
def login(
    request: Request,
    response: Response,
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    # 1. [보안 핵심] 기기 인증 토큰 확인
    device_token = request.cookies.get("trusted_device_token")
    if not device_token:
        return templates.TemplateResponse("login.html", {
            "request": request, 
            "error": "등록되지 않은 기기입니다. 하단의 '기기 등록'을 먼저 진행해주세요."
        })

    # 2. 토큰이 DB에 실제로 유효한지 검증 (분실 폰 권한 회수 대비)
    trusted_device = db.query(TrustedDevice).filter(TrustedDevice.token == device_token).first()
    if not trusted_device:
        response = templates.TemplateResponse("login.html", {
            "request": request, 
            "error": "인증이 취소되었거나 유효하지 않은 기기입니다."
        })
        response.delete_cookie("trusted_device_token")
        return response

    # 3. 기존 비밀번호 확인
    if password == LOGIN_PASSWORD:
        request.session["authenticated"] = True
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    else:
        return templates.TemplateResponse("login.html", {"request": request, "error": "비밀번호가 일치하지 않습니다."})

# --- 신규: 기기 등록 API ---
@router.post("/register-device")
def register_device(
    request: Request,
    device_name: str = Form(...),
    secret_code: str = Form(...),
    db: Session = Depends(get_db)
):
    # 마스터 등록 코드 확인
    if secret_code != DEVICE_SECRET_CODE:
        return templates.TemplateResponse("login.html", {"request": request, "error": "기기 등록 마스터 코드가 일치하지 않습니다."})

    # 고유 토큰 생성 및 DB 저장
    new_token = str(uuid.uuid4())
    new_device = TrustedDevice(device_name=device_name, token=new_token)
    db.add(new_device)
    db.commit()

    # 쿠키에 토큰을 심어줍니다 (만료일 10년, HttpOnly로 탈취 방지)
    response = templates.TemplateResponse("login.html", {
        "request": request, 
        "message": f"[{device_name}] 기기가 안전하게 등록되었습니다. 이제 로그인해주세요."
    })
    response.set_cookie(
        key="trusted_device_token",
        value=new_token,
        max_age=60 * 60 * 24 * 365 * 10, 
        httponly=True,  # 자바스크립트로 쿠키를 읽을 수 없게 하여 XSS 해킹 완벽 차단
        samesite="lax"
    )
    return response