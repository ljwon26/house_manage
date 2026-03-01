import os
import shutil
from uuid import uuid4
from typing import Optional
from fastapi import APIRouter, Depends, Form, Request, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.models import Insurance, FamilyMember
from fastapi import Depends
from app.core.dependencies import login_required # login_required 추가

router = APIRouter()
templates = Jinja2Templates(directory="templates")

UPLOAD_DIR = "static/uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# --- [기존] 조회 페이지 ---
@router.get("/insurance", response_class=HTMLResponse, dependencies=[Depends(login_required)])
def get_insurance_page(request: Request, db: Session = Depends(get_db)):
    # 기본 가족 자동 생성 로직
    default_names = ["재원", "다슬", "딸기"]
    current_members = db.query(FamilyMember).all()
    current_names = [m.name for m in current_members]
    
    is_added = False
    for name in default_names:
        if name not in current_names:
            db.add(FamilyMember(name=name))
            is_added = True
    if is_added:
        db.commit()
        current_members = db.query(FamilyMember).all()

    insurances = db.query(Insurance).all()
    
    return templates.TemplateResponse("insurance.html", {
        "request": request,
        "members": current_members,
        "insurances": insurances
    })

# --- [기존] 추가 로직 ---
@router.post("/insurance/add", response_class=RedirectResponse, dependencies=[Depends(login_required)])
async def add_insurance(
    member_name: str = Form(...),
    insurance_name: str = Form(...),
    company: str = Form(...),
    memo: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    file_path = None
    if file and file.filename:
        extension = file.filename.split(".")[-1]
        new_filename = f"{uuid4()}.{extension}"
        file_location = os.path.join(UPLOAD_DIR, new_filename)
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)
        file_path = f"/static/uploads/{new_filename}"

    member = db.query(FamilyMember).filter(FamilyMember.name == member_name).first()
    member_id = member.id if member else 0
    
    new_ins = Insurance(
        family_member_id=member_id,
        family_member_name=member_name,
        insurance_name=insurance_name,
        company=company,
        memo=memo,
        file_path=file_path
    )
    db.add(new_ins)
    db.commit()
    return RedirectResponse(url="/insurance", status_code=303)

# --- [추가됨] 수정 로직 (Update) ---
@router.post("/insurance/update", response_class=RedirectResponse, dependencies=[Depends(login_required)])
async def update_insurance(
    insurance_id: int = Form(...),
    member_name: str = Form(...),
    insurance_name: str = Form(...),
    company: str = Form(...),
    memo: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    ins = db.query(Insurance).filter(Insurance.id == insurance_id).first()
    if not ins:
        return RedirectResponse(url="/insurance", status_code=303)

    # 텍스트 정보 업데이트
    ins.family_member_name = member_name
    ins.insurance_name = insurance_name
    ins.company = company
    ins.memo = memo

    # 사용자 ID 재매핑
    member = db.query(FamilyMember).filter(FamilyMember.name == member_name).first()
    if member:
        ins.family_member_id = member.id

    # 파일이 새로 업로드된 경우 교체
    if file and file.filename:
        # 1. 기존 파일 삭제 (선택 사항)
        if ins.file_path:
            try:
                old_path = ins.file_path.lstrip("/")
                if os.path.exists(old_path):
                    os.remove(old_path)
            except Exception as e:
                print(f"기존 파일 삭제 실패: {e}")

        # 2. 새 파일 저장
        extension = file.filename.split(".")[-1]
        new_filename = f"{uuid4()}.{extension}"
        file_location = os.path.join(UPLOAD_DIR, new_filename)
        
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)
        
        ins.file_path = f"/static/uploads/{new_filename}"

    db.commit()
    return RedirectResponse(url="/insurance", status_code=303)

# --- [기존] 삭제 로직 ---
@router.post("/insurance/delete", response_class=RedirectResponse, dependencies=[Depends(login_required)])
def delete_insurance(insurance_id: int = Form(...), db: Session = Depends(get_db)):
    ins = db.query(Insurance).filter(Insurance.id == insurance_id).first()
    if ins:
        if ins.file_path:
            try:
                os.remove(ins.file_path.lstrip("/"))
            except:
                pass
        db.delete(ins)
        db.commit()
    return RedirectResponse(url="/insurance", status_code=303)