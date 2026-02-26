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

templates = Jinja2Templates(directory="templates")
router = APIRouter()

UPLOAD_FOLDER = "static/diary"

@router.get("/diary", response_class=HTMLResponse)
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
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    image_url = None
    
    # 1. 파일 업로드 및 압축 로직 (Pillow 사용)
    if file and file.filename:
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        timestamp = datetime.now().strftime("%H%M%S")
        
        # 압축할 것이므로 확장자를 .jpg로 고정
        safe_filename = f"{date}_{timestamp}_compressed.jpg"
        file_path = os.path.join(UPLOAD_FOLDER, safe_filename)
        
        content = await file.read()
        
        try:
            # 메모리에서 이미지 열기
            img = Image.open(io.BytesIO(content))
            
            # 투명도가 있는 PNG 등이면 RGB로 변환 (JPEG 저장을 위해)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 해상도를 최대 1200x1200 안으로 비율 유지하며 축소
            img.thumbnail((1200, 1200))
            
            # 품질 80으로 JPEG 압축 저장
            img.save(file_path, "JPEG", quality=80, optimize=True)
            image_url = f"/static/diary/{safe_filename}"
            
        except Exception as e:
            print(f"이미지 압축 에러: {e}")
            # 에러 시 원본 그대로 저장하는 안전장치
            with open(file_path, "wb") as buffer:
                buffer.write(content)
            image_url = f"/static/diary/{safe_filename}"

    # 2. 기존 일기 존재 여부 확인 (Upsert 로직)
    existing_diary = db.query(Diary).filter(Diary.diary_date == date).first()
    
    if existing_diary:
        # 수정(Update) 처리
        existing_diary.content = text
        existing_diary.video_url = youtube
        
        if image_url:
            # 새로 올라온 사진이 있다면, 기존 서버의 옛날 사진은 삭제하여 용량 확보
            if existing_diary.image_url:
                old_file_path = existing_diary.image_url.lstrip('/')
                if os.path.exists(old_file_path):
                    try:
                        os.remove(old_file_path)
                    except:
                        pass
            existing_diary.image_url = image_url
    else:
        # 신규(Insert) 처리
        new_diary = Diary(
            diary_date=date,
            content=text,
            video_url=youtube,
            image_url=image_url
        )
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