from fastapi import APIRouter, Depends, Form, Request, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional

# 데이터베이스 및 모델을 정확한 경로에서 가져옵니다.
from app.core.database import get_db
from app.core.models import Expense, Income

# Jinja2 템플릿 설정을 가져옵니다.
templates = Jinja2Templates(directory="templates")

# 라우터 객체를 생성합니다.
router = APIRouter()

@router.get("/expenses", response_class=HTMLResponse)
def get_expenses_page(request: Request, db: Session = Depends(get_db)):
    """
    월급 및 지출 내역을 보여주는 메인 페이지를 렌더링합니다.
    """
    incomes = db.query(Income).order_by(Income.id.desc()).all()
    expenses = db.query(Expense).order_by(Expense.id.desc()).all()
    
    total_income = sum(income.amount for income in incomes)
    total_expense = sum(expense.amount for expense in expenses)
    balance = total_income - total_expense

    return templates.TemplateResponse("expenses.html", {
        "request": request,
        "incomes": incomes,
        "expenses": expenses,
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": balance
    })

@router.post("/add_income", response_class=RedirectResponse)
def add_income(
    income_type: str = Form(...),
    amount: int = Form(...),
    db: Session = Depends(get_db)
):
    """
    새로운 수입 항목을 추가합니다.
    """
    new_income = Income(
        income_type=income_type,
        amount=amount,
        income_date=date.today()
    )
    db.add(new_income)
    db.commit()
    return RedirectResponse(url="/expenses", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/add_expense", response_class=RedirectResponse)
def add_expense(
    expense_type: str = Form(...),
    category: str = Form(...),
    item: str = Form(...),
    amount: int = Form(...),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    새로운 지출 항목을 추가합니다.
    """
    new_expense = Expense(
        expense_type=expense_type,
        category=category,
        item=item,
        amount=amount,
        notes=notes,
        expense_date=date.today()
    )
    db.add(new_expense)
    db.commit()
    return RedirectResponse(url="/expenses", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/delete_income", response_class=RedirectResponse)
def delete_income(income_id: int = Form(...), db: Session = Depends(get_db)):
    """
    수입 항목을 삭제합니다.
    """
    income_to_delete = db.query(Income).filter(Income.id == income_id).first()
    if not income_to_delete:
        raise HTTPException(status_code=404, detail="Income not found")
    
    db.delete(income_to_delete)
    db.commit()
    return RedirectResponse(url="/expenses", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/delete_expense", response_class=RedirectResponse)
def delete_expense(expense_id: int = Form(...), db: Session = Depends(get_db)):
    """
    지출 항목을 삭제합니다.
    """
    expense_to_delete = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense_to_delete:
        raise HTTPException(status_code=404, detail="Expense not found")
        
    db.delete(expense_to_delete)
    db.commit()
    return RedirectResponse(url="/expenses", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/edit_expense/{expense_id}", response_class=HTMLResponse)
def edit_expense_form(request: Request, expense_id: int, db: Session = Depends(get_db)):
    """
    특정 지출 항목의 수정 폼을 렌더링합니다.
    """
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    return templates.TemplateResponse("edit_expense.html", {
        "request": request,
        "expense": expense
    })

@router.post("/edit_expense/{expense_id}", response_class=RedirectResponse)
def update_expense(
    expense_id: int,
    expense_date: date = Form(...),
    expense_type: str = Form(...),
    category: str = Form(...),
    item: str = Form(...),
    amount: int = Form(...),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    수정된 지출 정보를 데이터베이스에 업데이트합니다.
    """
    expense_to_update = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense_to_update:
        raise HTTPException(status_code=404, detail="Expense not found")

    expense_to_update.expense_date = expense_date
    expense_to_update.expense_type = expense_type
    expense_to_update.category = category
    expense_to_update.item = item
    expense_to_update.amount = amount
    expense_to_update.notes = notes
    
    db.commit()
    return RedirectResponse(url="/expenses", status_code=status.HTTP_303_SEE_OTHER)

# ▼▼▼ [수입 수정 기능] 이 부분이 추가되었습니다. ▼▼▼
@router.get("/edit_income/{income_id}", response_class=HTMLResponse)
def edit_income_form(request: Request, income_id: int, db: Session = Depends(get_db)):
    """
    특정 수입 항목의 수정 폼을 렌더링합니다.
    """
    income = db.query(Income).filter(Income.id == income_id).first()
    if not income:
        raise HTTPException(status_code=404, detail="Income not found")
    
    return templates.TemplateResponse("edit_income.html", {
        "request": request,
        "income": income
    })

@router.post("/edit_income/{income_id}", response_class=RedirectResponse)
def update_income(
    income_id: int,
    income_date: date = Form(...),
    income_type: str = Form(...),
    amount: int = Form(...),
    db: Session = Depends(get_db)
):
    """
    수정된 수입 정보를 데이터베이스에 업데이트합니다.
    """
    income_to_update = db.query(Income).filter(Income.id == income_id).first()
    if not income_to_update:
        raise HTTPException(status_code=404, detail="Income not found")

    income_to_update.income_date = income_date
    income_to_update.income_type = income_type
    income_to_update.amount = amount
    
    db.commit()
    return RedirectResponse(url="/expenses", status_code=status.HTTP_303_SEE_OTHER)
