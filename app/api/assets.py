from fastapi import APIRouter, Depends, Form, Request, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from datetime import date

from app.core.database import get_db
from app.core.dependencies import login_required
from app.core.models import Assets # DB 모델 import
from .schemas import AssetCreate
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/add_asset", response_class=HTMLResponse)
def add_asset_form(request: Request, ):
    return templates.TemplateResponse("add_asset.html", {"request": request, "today": date.today().isoformat()})

@router.post("/add_asset", response_class=RedirectResponse)
def create_asset(
    date: date = Form(...),
    category: str = Form(...),
    item: str = Form(...),
    amount: float = Form(...),
    notes: str | None = Form(None),
    db: Session = Depends(get_db)
):
    new_asset = Assets(
        date=date,
        category=category,
        item=item,
        amount=amount,
        notes=notes
    )
    db.add(new_asset)
    db.commit()
    return RedirectResponse(url="/", status_code=303)

@router.get("/edit_asset/{asset_id}", response_class=HTMLResponse)
def edit_asset_form(request: Request, asset_id: int, db: Session = Depends(get_db), ):
    asset_data = db.query(Assets).filter(Assets.id == asset_id).first()
    if not asset_data:
        raise HTTPException(status_code=404, detail="Asset not found")

    if asset_data.amount and asset_data.amount.is_integer():
        asset_data.amount = int(asset_data.amount)
    
    return templates.TemplateResponse("edit_asset.html", {
        "request": request,
        "asset_data": asset_data,
        "today": date.today().isoformat()
    })

@router.post("/edit_asset/{asset_id}", response_class=RedirectResponse)
def update_asset(
    asset_id: int,
    date: date = Form(...),
    category: str = Form(...),
    item: str = Form(...),
    amount: float = Form(...),
    notes: str | None = Form(None),
    db: Session = Depends(get_db)
):
    asset = db.query(Assets).filter(Assets.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    asset.date = date
    asset.category = category
    asset.item = item
    asset.amount = amount
    asset.notes = notes
    db.commit()
    return RedirectResponse(url="/", status_code=303)


@router.post("/delete_asset", response_class=RedirectResponse)
def delete_asset(asset_id: int = Form(...), db: Session = Depends(get_db), ):
    asset = db.query(Assets).filter(Assets.id == asset_id).first()
    if asset:
        db.delete(asset)
        db.commit()
    return RedirectResponse(url="/", status_code=303)

