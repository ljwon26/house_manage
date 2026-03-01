from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# ==========================================
# [설정] 접속 허용 비밀번호 (여기를 원하는 비밀번호로 바꾸세요)
# ==========================================
ACCESS_PASSWORD = "3152" 

@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
def login_submit(request: Request, password: str = Form(...)):
    """
    이메일 입력 없이 비밀번호만 확인하는 로그인 로직
    """
    # 설정한 비밀번호와 일치하는지 확인
    if password == ACCESS_PASSWORD:
        request.session["logged_in"] = True
        request.session["user_email"] = "family"  # 세션 식별자
        
        # ★ 로그인 성공 시 대시보드("/")로 즉시 이동시킵니다.
        # (만약 대시보드 URL이 /dashboard 라면 아래 "/"를 "/dashboard"로 변경하세요)
        return RedirectResponse(url="/dashboard", status_code=303)
    
    # 실패 시 에러 메시지와 함께 다시 로그인 페이지 렌더링
    return templates.TemplateResponse("login.html", {
        "request": request, 
        "error": "비밀번호가 올바르지 않습니다."
    })

@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    # 로그아웃 시 다시 로그인 페이지로 이동
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(key="session")
    return response