import os
from datetime import datetime, date
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request, status, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.models import Diary

templates = Jinja2Templates(directory="templates")
router = APIRouter()

# 파일 저장 기본 경로 설정
UPLOAD_FOLDER = "static/diary"

@router.get("/diary", response_class=HTMLResponse)
def get_diary_page(request: Request, db: Session = Depends(get_db)):
    """
    육아일기 달력 및 내역을 보여주는 메인 페이지
    """
    # 1. 달력에 파란 점을 찍기 위해 '작성된 모든 날짜'만 따로 추출
    all_dates_query = db.query(Diary.diary_date).all()
    all_dates = [str(d[0]) for d in all_dates_query]
    
    # 2. 첫 화면에는 무한 스크롤을 위해 최근 10개(빠른 날짜순)만 먼저 로드
    diaries = db.query(Diary).order_by(Diary.diary_date.asc()).limit(10).all()
    
    return templates.TemplateResponse("diary.html", {
        "request": request,
        "diaries": diaries,
        "all_dates": all_dates # 프론트엔드로 전체 날짜 전달
    })

@router.get("/diary/api/list")
def get_diary_list(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    # skip 변수만큼 건너뛰고 limit 개수만큼 가져옴
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
    """
    새로운 일기를 저장하거나, 기존 일기를 덮어씁니다. (파일 업로드 포함)
    """
    image_url = None
    
    # 1. 파일이 첨부된 경우 로컬 스토리지에 저장
    if file and file.filename:
        os.makedirs(UPLOAD_FOLDER, exist_ok=True) # 폴더가 없으면 생성
        
        # 안전한 파일명 생성 (예: 2026-02-25_143022_photo.jpg)
        timestamp = datetime.now().strftime("%H%M%S")
        safe_filename = f"{date}_{timestamp}_{file.filename.replace(' ', '_')}"
        file_path = os.path.join(UPLOAD_FOLDER, safe_filename)
        
        # 파일 쓰기 (비동기)
        content = await file.read()
        with open(file_path, "wb") as buffer:
            buffer.write(content)
            
        # DB에 저장될 웹 경로
        image_url = f"/static/diary/{safe_filename}"

    # 2. 기존 작성된 일기가 있는지 확인
    existing_diary = db.query(Diary).filter(Diary.diary_date == date).first()
    
    if existing_diary:
        # 이미 해당 날짜에 일기가 있으면 덮어쓰기 (수정)
        existing_diary.content = text
        existing_diary.video_url = youtube
        if image_url: # 새 이미지가 올라왔을 때만 이미지 업데이트
            existing_diary.image_url = image_url
    else:
        # 없으면 새로 생성
        new_diary = Diary(
            diary_date=date,
            title="육아일기", # 기존 DB에 title 필수값이면 기본값 삽입
            content=text,
            video_url=youtube,
            image_url=image_url # 이 필드가 models.py에 추가되어 있어야 합니다!
        )
        db.add(new_diary)
        
    db.commit()
    
    # 프론트엔드 자바스크립트가 성공을 인식할 수 있도록 JSON 응답
    return JSONResponse(content={"status": "success"})


@router.post("/diary/delete")
async def delete_diary(
    diary_id: int = Form(...), 
    db: Session = Depends(get_db)
):
    """
    일기 삭제 및 로컬 서버에 저장된 첨부파일(이미지) 물리적 삭제
    """
    diary = db.query(Diary).filter(Diary.id == diary_id).first()
    
    if diary:
        # 1. 연결된 로컬 이미지 파일이 있는지 확인하고 물리적 삭제 진행
        if diary.image_url:
            # DB에 저장된 image_url 예시: "/static/diary/2026-02-25_143022_photo.jpg"
            # 실제 파이썬이 인식해야 할 로컬 파일 경로로 변환 (맨 앞의 '/' 제거)
            file_path = diary.image_url.lstrip('/')
            
            # 해당 경로에 파일이 실제로 존재하는지 체크 후 삭제
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    print(f"첨부파일 삭제 완료: {file_path}")
                except Exception as e:
                    print(f"파일 삭제 중 오류 발생: {e}")

        # 2. DB에서 일기 데이터 최종 삭제
        db.delete(diary)
        db.commit()
        return JSONResponse(content={"status": "success"})
    
    return JSONResponse(content={"status": "error", "message": "일기를 찾을 수 없습니다."}, status_code=404)