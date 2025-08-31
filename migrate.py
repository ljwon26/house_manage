import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import SessionLocal as LocalSession, Base, engine as LocalEngine
from app.core.models import Income, Expense, Assets, HouseData, Task, LedgerExpense, MonthlyBudget

# --- [1] 서버 데이터베이스 연결 설정 ---
# 서버의 DATABASE_URL을 여기에 직접 입력하거나 환경 변수에서 가져옵니다.
# 예: Docker 컨테이너의 경우 volumes로 마운트된 sql_app.db를 가리킵니다.
SERVER_DATABASE_URL = "sqlite:///./data/sql_app.db" # docker-compose.yml의 volumes 설정에 맞춰 수정

ServerEngine = create_engine(SERVER_DATABASE_URL, connect_args={"check_same_thread": False})
ServerSession = sessionmaker(autocommit=False, autoflush=False, bind=ServerEngine)

# --- [2] 마이그레이션 로직 ---
def migrate_data():
    """
    로컬 DB의 모든 데이터를 서버 DB로 마이그레이션합니다.
    """
    print("Starting data migration...")

    # 로컬 DB와 서버 DB에 대한 세션 생성
    local_db = LocalSession()
    server_db = ServerSession()

    try:
        # 마이그레이션 대상 모델 목록
        models = [
            Income, Expense, Assets, HouseData, Task, LedgerExpense, MonthlyBudget
        ]

        for model in models:
            # 로컬 DB에서 모든 데이터 조회
            local_data = local_db.query(model).all()

            if local_data:
                print(f"Migrating {len(local_data)} records for table: {model.__tablename__}")

                # 서버 DB에 기존 데이터가 있다면 모두 삭제 (덮어쓰기)
                server_db.query(model).delete()

                # 로컬 데이터를 서버 DB에 삽입
                for record in local_data:
                    # detached 객체를 서버 세션에 다시 바인딩
                    server_db.merge(record)

        server_db.commit()
        print("Data migration completed successfully!")

    except Exception as e:
        print(f"An error occurred during migration: {e}")
        server_db.rollback()
    finally:
        local_db.close()
        server_db.close()

if __name__ == "__main__":
    # 마이그레이션을 실행하기 전에 서버 DB의 테이블을 먼저 생성합니다.
    Base.metadata.create_all(bind=ServerEngine)
    migrate_data()