# app/api/routers/monthly_ledger.py
import json
from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.models import LedgerExpense, MonthlyBudget
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import openpyxl
from io import BytesIO
from urllib.parse import quote

router = APIRouter()
templates = Jinja2Templates(directory="templates")

DEFAULT_BUDGET = 700000
def adjust_date_for_weekend(target_date: date) -> date:
    """
    주어진 날짜가 토요일이면 금요일로, 일요일이면 금요일로 조정합니다.
    (월=0, 화=1, 수=2, 목=3, 금=4, 토=5, 일=6)
    """
    # 토요일(5)이면 하루 전으로
    if target_date.weekday() == 5:
        return target_date - timedelta(days=1)
    # 일요일(6)이면 이틀 전으로
    elif target_date.weekday() == 6:
        return target_date - timedelta(days=2)
    # 평일이면 그대로 반환
    else:
        return target_date


@router.get("/monthly_ledger", response_class=HTMLResponse)
def get_monthly_ledger(request: Request, db: Session = Depends(get_db), month: str = None):
    try:
        base_date = datetime.strptime(month, "%Y-%m").date().replace(day=1) if month else date.today()
    except ValueError:
        base_date = date.today()

    if base_date.day < 25:
        display_month_date = base_date.replace(day=1)
    else:
        display_month_date = (base_date + relativedelta(months=1)).replace(day=1)

    # --- [수정] 시작일과 종료일을 계산하고 주말인지 확인하여 조정 ---
    # 1. 기본 시작일/종료일 계산
    initial_start_date = (display_month_date - relativedelta(months=1)).replace(day=25)
    initial_end_date = display_month_date.replace(day=24)

    # 2. 주말 조정 함수를 적용하여 최종 시작일/종료일 확정
    start_date = adjust_date_for_weekend(initial_start_date)
    end_date = adjust_date_for_weekend(initial_end_date)
    
    today = date.today()
    if today.day > 24:
        d_day_target = today.replace(day=25) + relativedelta(months=1)
    else:
        d_day_target = today.replace(day=25)
    
    # 보고 있는 페이지의 월과 D-Day 기준일의 월이 일치하는지 확인
    if d_day_target.strftime("%Y-%m") == display_month_date.strftime("%Y-%m"):
        days_left = (d_day_target - today).days
        d_day_to_pass = days_left
    else:
        d_day_to_pass = None
    


    display_month_str = display_month_date.strftime("%Y-%m")
    budget_record = db.query(MonthlyBudget).filter(MonthlyBudget.month == display_month_str).first()
    current_budget = budget_record.amount if budget_record else DEFAULT_BUDGET

    expenses = db.query(LedgerExpense).filter(
        LedgerExpense.expense_date.between(start_date, end_date)
    ).order_by(LedgerExpense.expense_date.desc()).all()
    
    category_totals = {}
    for expense in expenses:
        category_totals[expense.category] = category_totals.get(expense.category, 0) + expense.amount

    total_spent = sum(e.amount for e in expenses)
    remaining_budget = current_budget - total_spent
    usage_percentage = (total_spent / current_budget * 100) if current_budget > 0 else 0

    prev_month = (display_month_date - relativedelta(months=1)).strftime("%Y-%m")
    next_month = (display_month_date + relativedelta(months=1)).strftime("%Y-%m")

    return templates.TemplateResponse("monthly_ledger.html", {
        "request": request,
        "expenses": expenses,
        "budget": current_budget,
        "total_spent": total_spent,
        "remaining_budget": remaining_budget,
        "usage_percentage": usage_percentage,
        "current_month_display": display_month_date.strftime("%Y년 %m월"),
        "prev_month": prev_month,
        "next_month": next_month,
        "chart_data": category_totals,
        "d_day": d_day_to_pass
    })

@router.get("/monthly_ledger/download_excel")
def download_excel(request: Request, db: Session = Depends(get_db), month: str = None):
    # 1. 기존 get_monthly_ledger 함수에서 지출 내역을 가져오는 부분 재사용
    try:
        base_date = datetime.strptime(month, "%Y-%m").date().replace(day=1) if month else date.today()
    except ValueError:
        base_date = date.today()

    if base_date.day < 25:
        display_month_date = base_date.replace(day=1)
    else:
        display_month_date = (base_date + relativedelta(months=1)).replace(day=1)
        
    initial_start_date = (display_month_date - relativedelta(months=1)).replace(day=25)
    initial_end_date = display_month_date.replace(day=24)
    start_date = adjust_date_for_weekend(initial_start_date)
    end_date = adjust_date_for_weekend(initial_end_date)

    expenses = db.query(LedgerExpense).filter(
        LedgerExpense.expense_date.between(start_date, end_date)
    ).order_by(LedgerExpense.expense_date.desc()).all()

    # 2. openpyxl을 사용하여 메모리에 엑셀 파일 생성
    output = BytesIO()
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "월별 지출 내역"

    # 헤더 작성
    headers = ["날짜", "카테고리", "항목", "금액"]
    sheet.append(headers)

    # 데이터 작성
    for expense in expenses:
        sheet.append([
            expense.expense_date.strftime("%Y-%m-%d"),
            expense.category,
            expense.item,
            expense.amount
        ])

    # 3. 파일 저장 및 스트리밍 응답 반환
    workbook.save(output)
    output.seek(0)

    filename = f"가계부_{display_month_date.strftime('%Y년%m월')}_지출내역.xlsx"
    # --- 이 부분을 수정합니다. ---
    encoded_filename = quote(filename)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
    )  

@router.post("/set_budget", response_class=RedirectResponse)
async def set_budget(
    month: str = Form(...), # "YYYY-MM"
    amount: int = Form(...),
    db: Session = Depends(get_db)
):
    budget_record = db.query(MonthlyBudget).filter(MonthlyBudget.month == month).first()
    if budget_record:
        budget_record.amount = amount
    else:
        new_budget = MonthlyBudget(month=month, amount=amount)
        db.add(new_budget)
    db.commit()
    return RedirectResponse(url=f"/monthly_ledger?month={month}", status_code=303)

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
    
    if expense_date.day < 25:
        month_to_return = expense_date.strftime('%Y-%m')
    else:
        next_month_date = expense_date + relativedelta(months=1)
        month_to_return = next_month_date.strftime('%Y-%m')
        
    return RedirectResponse(url=f"/monthly_ledger?month={month_to_return}", status_code=303)

@router.post("/delete_ledger_expense/{expense_id}", response_class=RedirectResponse)
async def delete_ledger_expense(
    expense_id: int, 
    request: Request,
    db: Session = Depends(get_db)
):
    expense_to_delete = db.query(LedgerExpense).filter(LedgerExpense.id == expense_id).first()
    if not expense_to_delete:
        raise HTTPException(status_code=404, detail="지출 항목을 찾을 수 없습니다.")
    
    deleted_date = expense_to_delete.expense_date
    
    db.delete(expense_to_delete)
    db.commit()
    
    if deleted_date.day < 25:
        month_to_return = deleted_date.strftime('%Y-%m')
    else:
        next_month_date = deleted_date + relativedelta(months=1)
        month_to_return = next_month_date.strftime('%Y-%m')
    
    return RedirectResponse(url=f"/monthly_ledger?month={month_to_return}", status_code=303)
