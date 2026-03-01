from fastapi import APIRouter, Depends, Form, Request, HTTPException, status, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime, date
from typing import Optional
import aiosmtplib
from email.mime.text import MIMEText
from fastapi import Depends

# 모델과 의존성을 정확한 경로에서 가져옵니다.
from app.core.database import get_db
from app.core.models import Task
from fastapi.templating import Jinja2Templates
from app.core.dependencies import login_required # login_required 추가


router = APIRouter()
templates = Jinja2Templates(directory="templates")

# --- [추가된 부분] main.py의 이메일 전송 설정 및 함수 ---
EMAIL_ADDRESS = "ljwon26@gmail.com"
EMAIL_PASSWORD = "qxxq unfr sfcg eoep" # Gmail 앱 비밀번호

async def send_email(to_email: str, subject: str, body: str):
    subtype = 'html' if '<' in body and '>' in body else 'plain'
    msg = MIMEText(body, _subtype=subtype)
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email

    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587

    try:
        #async with aiosmtplib.SMTP(hostname=SMTP_SERVER, port=SMTP_PORT, use_tls=True) as server:
        async with aiosmtplib.SMTP(hostname=SMTP_SERVER, port=SMTP_PORT, start_tls=True) as server:
            await server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            await server.send_message(msg)
            print(f"이메일 전송 성공: '{subject}' to {to_email}")
    except Exception as e:
        print(f"이메일 전송 실패: {e}")

# ===================================================================
# '알림 등록' 폼 페이지를 보여주는 경로
# ===================================================================
@router.get("/add_task_form", response_class=HTMLResponse, dependencies=[Depends(login_required)])
def show_add_task_form(request: Request):
    """
    add_task.html 템플릿을 렌더링하여 알림 등록 폼을 보여줍니다.
    """
    return templates.TemplateResponse("add_task.html", {"request": request})

# ===================================================================
# ▼▼▼ [수정된 부분] 폼 데이터를 받고 이메일을 발송하도록 수정한 경로 ▼▼▼
# ===================================================================
@router.post("/add_task", response_class=RedirectResponse)
async def add_task(
    background_tasks: BackgroundTasks, # 백그라운드 작업을 위해 추가
    item_name: str = Form(...),
    model_name: Optional[str] = Form(None),
    due_date: date = Form(...),
    email: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    add_task.html 폼에서 받은 데이터로 새 Task를 생성하고,
    백그라운드에서 확인 이메일을 발송합니다.
    """
    new_task = Task(
        item_name=item_name,
        model_name=model_name,
        due_date=due_date,
        email=email
    )
    db.add(new_task)
    db.commit()

    # 이메일 내용 구성
    subject = f"[J&D 하우스 관리] 새 일정 등록 완료: {item_name}"
    html_body = f"""
    <div style="font-family: Arial, sans-serif; background-color: #f4f7f9; padding: 20px; text-align: center;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
            <h1 style="color: #1e3a8a; margin-top: 0; font-size: 28px;">🏠 하우스 관리 알림</h1>
            <p style="font-size: 16px; color: #555;">안녕하세요, '{item_name}' 일정이 성공적으로 등록되었습니다.</p>
            <hr style="border: 0; height: 1px; background-color: #eee; margin: 20px 0;">
            <table style="width: 100%; text-align: left; border-collapse: collapse;">
                <tr>
                    <td style="padding: 10px; font-weight: bold; color: #1e3a8a;">일정 항목</td>
                    <td style="padding: 10px; color: #333;">{item_name}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; font-weight: bold; color: #1e3a8a;">세부 모델</td>
                    <td style="padding: 10px; color: #333;">{model_name if model_name else '없음'}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; font-weight: bold; color: #1e3a8a;">마감일</td>
                    <td style="padding: 10px; color: #ef4444; font-weight: bold;">{due_date}</td>
                </tr>
            </table>
            <p style="font-size: 14px; color: #888; margin-top: 30px;">본 메일은 자동 발송된 메일입니다. 회신하지 마세요.</p>
        </div>
    </div>
    """
    
    # 백그라운드에서 이메일 발송 작업을 실행
    background_tasks.add_task(send_email, to_email=email, subject=subject, body=html_body)

    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

# ===================================================================
# 대시보드에서 알림을 삭제하는 함수
# ===================================================================
@router.post("/delete_task_dashboard", response_class=RedirectResponse, dependencies=[Depends(login_required)])
def delete_task_from_dashboard(
    task_id: int = Form(...),
    db: Session = Depends(get_db)
):
    task_to_delete = db.query(Task).filter(Task.id == task_id).first()
    if not task_to_delete:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task_to_delete)
    db.commit()
    
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)


# 아래는 기존의 다른 task 관련 코드들입니다 (수정 없음).
@router.get("/tasks", response_class=HTMLResponse)
def get_tasks(request: Request, db: Session = Depends(get_db)):
    tasks = db.query(Task).all()
    return templates.TemplateResponse("tasks.html", {"request": request, "tasks": tasks})


@router.post("/complete_task", response_class=RedirectResponse)
def complete_task(task_id: int = Form(...), db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if task:
        db.delete(task)
        db.commit()
    return RedirectResponse(url="/tasks", status_code=303)


@router.get("/edit_task/{task_id}", response_class=HTMLResponse)
def edit_task_form(request: Request, task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return templates.TemplateResponse("edit_task.html", {"request": request, "task": task})


@router.post("/edit_task/{task_id}", response_class=RedirectResponse, dependencies=[Depends(login_required)])
def update_task(
    task_id: int,
    title: str = Form(...),
    due_date: str = Form(...),
    db: Session = Depends(get_db)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.title = title
    task.due_date = datetime.strptime(due_date, "%Y-%m-%d").date()
    db.commit()
    return RedirectResponse(url="/tasks", status_code=303)
