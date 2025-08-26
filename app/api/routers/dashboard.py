from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

# 'Assets'와 'Task' 모델을 import 합니다.
from app.core.models import Income, Expense, Assets, Task
# get_db 의존성을 정확한 경로에서 가져와야 합니다.
from app.core.database import get_db

# Jinja2 템플릿 설정을 가져옵니다.
templates = Jinja2Templates(directory="templates")

# 라우터 객체를 생성합니다.
router = APIRouter()

@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    """
    대시보드 페이지를 렌더링합니다.
    수입, 지출, 자산, 알림 데이터를 모두 가져와 템플릿에 전달합니다.
    """
    incomes = db.query(Income).all()
    expenses = db.query(Expense).all()
    assets = db.query(Assets).all()
    
    # 등록된 알림(Task) 데이터를 조회합니다.
    tasks = db.query(Task).order_by(Task.due_date.asc()).all()

    # JavaScript에서 바로 사용할 수 있도록 자산 데이터를 가공합니다.
    assets_data = [
        {"id": asset.id, "category": asset.category, "item": asset.item, "amount": asset.amount, "notes": asset.notes}
        for asset in assets
    ]

    total_income_sum = sum(income.amount for income in incomes)
    total_expense_sum = sum(expense.amount for expense in expenses)

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "incomes": incomes,
            "expenses": expenses,
            "total_income_sum": total_income_sum,
            "total_expense_sum": total_expense_sum,
            "assets_data": assets_data,
            # 조회된 알림 데이터를 HTML에 전달합니다.
            "tasks_data": tasks
        }
    )
