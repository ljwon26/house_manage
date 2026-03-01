import os
import io
from datetime import datetime, date
from typing import Optional
from PIL import Image

from fastapi import APIRouter, Depends, Form, Request, status, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.models import Diary
from fastapi import Depends
from app.core.dependencies import login_required

templates = Jinja2Templates(directory="templates")
router = APIRouter()

UPLOAD_FOLDER = "static/diary"

@router.get("/diary", response_class=HTMLResponse,dependencies=[Depends(login_required)] )
def get_diary_page(request: Request, db: Session = Depends(get_db)):
    all_dates_query = db.query(Diary.diary_date).all()
    all_dates = [str(d[0]) for d in all_dates_query]
    
    # 첫 화면: 무한 스크롤을 위해 10개만 로드 (오름차순)
    diaries = db.query(Diary).order_by(Diary.diary_date.asc()).limit(10).all()
    
    return templates.TemplateResponse("diary.html", {
        "request": request,
        "diaries": diaries,
        "all_dates": all_dates
    })

@router.get("/diary/api/list")
def get_diary_list(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    diaries = db.query(Diary).order_by(Diary.diary_date.asc()).offset(skip).limit(limit).all()
    result = [{
        "id": d.id,
        "diary_date": str(d.diary_date),
        "content": d.content,
        "image_url": d.image_url,
        "video_url": d.video_url
    } for d in diaries]
    
    return JSONResponse(content={"diaries": result})

@router.post("/diary/save")
async def save_diary(
    date: date = Form(...),
    text: str = Form(...),
    youtube: Optional[str] = Form(""),
    delete_image: Optional[str] = Form("false"),  # [추가됨] 사진 삭제 신호
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    image_url = None
    
    # 1. 새 파일 업로드 처리
    if file and file.filename:
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        timestamp = datetime.now().strftime("%H%M%S")
        safe_filename = f"{date}_{timestamp}_compressed.jpg"
        file_path = os.path.join(UPLOAD_FOLDER, safe_filename)
        
        content = await file.read()
        try:
            img = Image.open(io.BytesIO(content))
            if img.mode != 'RGB': img = img.convert('RGB')
            img.thumbnail((1200, 1200))
            img.save(file_path, "JPEG", quality=80, optimize=True)
            image_url = f"/static/diary/{safe_filename}"
        except Exception as e:
            with open(file_path, "wb") as buffer: buffer.write(content)
            image_url = f"/static/diary/{safe_filename}"

    # 2. 기존 일기 덮어쓰기 로직
    existing_diary = db.query(Diary).filter(Diary.diary_date == date).first()
    
    if existing_diary:
        existing_diary.content = text
        existing_diary.video_url = youtube
        
        # 사용자가 X 버튼을 눌러 사진을 비운 상태로 수정(저장)한 경우 OR 새 사진을 올린 경우 기존 파일 삭제
        if delete_image == "true" or image_url:
            if existing_diary.image_url:
                old_file_path = existing_diary.image_url.lstrip('/')
                if os.path.exists(old_file_path):
                    try: os.remove(old_file_path)
                    except: pass
            
            # X를 눌러 삭제 처리한 경우 DB에서도 비움
            if delete_image == "true":
                existing_diary.image_url = None

        # 새 사진을 올렸다면 새 경로로 덮어쓰기
        if image_url:
            existing_diary.image_url = image_url
            
    else:
        # 신규 생성
        new_diary = Diary(diary_date=date, content=text, video_url=youtube, image_url=image_url)
        db.add(new_diary)
        
    db.commit()
    return JSONResponse(content={"status": "success"})

@router.post("/diary/delete")
async def delete_diary(diary_id: int = Form(...), db: Session = Depends(get_db)):
    diary = db.query(Diary).filter(Diary.id == diary_id).first()
    if diary:
        if diary.image_url:
            file_path = diary.image_url.lstrip('/')
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
        db.delete(diary)
        db.commit()
        return JSONResponse(content={"status": "success"})
    
    return JSONResponse(content={"status": "error", "message": "일기를 찾을 수 없습니다."}, status_code=404)