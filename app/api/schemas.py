from pydantic import BaseModel
from datetime import date

class ExpenseCreate(BaseModel):
    date: date
    category: str
    item: str
    amount: float
    notes: str | None = None

class IncomeCreate(BaseModel):
    date: date
    income_type: str
    amount: float

class AssetCreate(BaseModel):
    date: date
    category: str
    item: str
    amount: float
    notes: str | None = None

class HouseDataCreate(BaseModel):
    initial_amount: float
    monthly_payment: float
    total_term_months: int
    interest_rate: float

class TaskCreate(BaseModel):
    title: str
    due_date: date
