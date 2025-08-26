# app/api/routers/monthly_ledger.py
import json
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.models import LedgerExpense
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# 생활비 예산 설정
LIVING_EXPENSE_BUDGET = 700000

@router.get("/monthly_ledger", response_class=HTMLResponse)
def get_monthly_ledger(request: Request, db: Session = Depends(get_db), month: str = None):
    try:
        # URL에 월 정보가 있으면 해당 월의 1일, 없으면 오늘 날짜를 기준으로 설정
        base_date = datetime.strptime(month, "%Y-%m").date().replace(day=1) if month else date.today()
    except ValueError:
        base_date = date.today()

    # --- [수정된 부분] 월급일 기준 정산 기간 계산 ---
    # 만약 오늘이 24일 이전이라면, 이번 달 가계부는 '이번 달'을 기준으로 함 (예: 9월 20일 -> 9월 가계부)
    if base_date.day < 25:
        display_month_date = base_date.replace(day=1)
    # 만약 오늘이 25일 이후라면, 이번 달 가계부는 '다음 달'을 기준으로 함 (예: 8월 26일 -> 9월 가계부)
    else:
        display_month_date = (base_date + relativedelta(months=1)).replace(day=1)

    # 정산 시작일 (표시되는 달의 전달 25일)
    start_date = (display_month_date - relativedelta(months=1)).replace(day=25)
    # 정산 종료일 (표시되는 달의 24일)
    end_date = display_month_date.replace(day=24)
    # --- [수정 끝] ---

    # 수정된 기간으로 데이터베이스 조회
    expenses = db.query(LedgerExpense).filter(
        LedgerExpense.expense_date.between(start_date, end_date)
    ).order_by(LedgerExpense.expense_date.desc()).all()
    
    category_totals = {}
    for expense in expenses:
        category_totals[expense.category] = category_totals.get(expense.category, 0) + expense.amount

    total_spent = sum(e.amount for e in expenses)
    remaining_budget = LIVING_EXPENSE_BUDGET - total_spent
    usage_percentage = (total_spent / LIVING_EXPENSE_BUDGET * 100) if LIVING_EXPENSE_BUDGET > 0 else 0

    # 이전/다음 달 링크 계산
    prev_month = (display_month_date - relativedelta(months=1)).strftime("%Y-%m")
    next_month = (display_month_date + relativedelta(months=1)).strftime("%Y-%m")

    return templates.TemplateResponse("monthly_ledger.html", {
        "request": request,
        "expenses": expenses,
        "budget": LIVING_EXPENSE_BUDGET,
        "total_spent": total_spent,
        "remaining_budget": remaining_budget,
        "usage_percentage": usage_percentage,
        "current_month_display": display_month_date.strftime("%Y년 %m월"), # 화면 표시
        "prev_month": prev_month,
        "next_month": next_month,
        "chart_data": json.dumps(category_totals)
    })

@router.post("/add_ledger_expense", response_class=RedirectResponse)
async def add_ledger_expense(
    expense_date: date = Form(...),
    category: str = Form(...),
    item: str = Form(...),
    amount: int = Form(...),
    db: Session = Depends(get_db)
):
    new_expense = LedgerExpense(
        expense_date=expense_date,
        category=category,
        item=item,
        amount=amount,
    )
    db.add(new_expense)
    db.commit()
    # 저장 후 해당 지출일이 속한 월의 가계부로 이동
    return RedirectResponse(url=f"/monthly_ledger?month={expense_date.strftime('%Y-%m')}", status_code=303)
