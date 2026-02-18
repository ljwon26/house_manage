from sqlalchemy import Column, Integer, String, Date, REAL, Float
from .database import Base
from pydantic import BaseModel
from datetime import date 

class Expense(Base):
    __tablename__ = "expenses"
    id = Column(Integer, primary_key=True, index=True)
    expense_type = Column(String, index=True)
    expense_date = Column(Date, index=True)
    category = Column(String(50))
    item = Column(String(100))
    amount = Column(Float)
    notes = Column(String(255), nullable=True)

class Income(Base):
    __tablename__ = "incomes"
    id = Column(Integer, primary_key=True, index=True)
    income_date = Column(Date, index=True)
    income_type = Column(String(50))
    amount = Column(Float)

class Assets(Base):
    __tablename__ = "assets"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True)
    category = Column(String(50))
    item = Column(String(100))
    amount = Column(REAL)
    notes = Column(String(255), nullable=True)

class HouseData(Base):
    __tablename__ = "house_data"
    id = Column(Integer, primary_key=True, index=True)
    initial_amount = Column(Float) 
    monthly_payment = Column(Float)
    total_term_months = Column(Integer)
    interest_rate = Column(Float)

class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True, index=True)

    # ▼▼▼ 아래 필드들이 폼과 일치하도록 수정/추가해주세요. ▼▼▼
    item_name = Column(String, index=True)
    model_name = Column(String, nullable=True) # 선택 사항이므로 nullable=True
    due_date = Column(Date)
    email = Column(String)
    
class TaskCreate(BaseModel):
    title: str
    due_date: date
    
    
class LedgerExpense(Base):
    __tablename__ = "ledger_expenses"
    id = Column(Integer, primary_key=True, index=True)
    expense_date = Column(Date, index=True)
    category = Column(String(50))
    item = Column(String(100))
    amount = Column(Float)
    
class MonthlyBudget(Base):
    __tablename__ = "monthly_budgets"
    id = Column(Integer, primary_key=True, index=True)
    # "YYYY-MM" 형식으로 월 정보를 저장합니다. (예: "2025-09")
    month = Column(String(7), unique=True, index=True) 
    amount = Column(Float, nullable=False)
    
class FamilyMember(Base): # Base 상속 확인
    __tablename__ = "family_members"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

class Insurance(Base):
    __tablename__ = "insurances"

    id = Column(Integer, primary_key=True, index=True)
    family_member_id = Column(Integer, index=True) # FamilyMember의 id 참조
    family_member_name = Column(String) # 편의를 위해 이름도 저장
    
    insurance_name = Column(String)      # 보험이름
    company = Column(String)             # 보험사
    memo = Column(String, nullable=True) # 보장내역(메모)
    file_path = Column(String, nullable=True) # 보험 증서 파일 경로