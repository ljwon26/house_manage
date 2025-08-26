import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# --- 데이터베이스 연결 설정 ---
# 'DATABASE_URL' 환경 변수가 설정되어 있지 않으면 기본 SQLite 데이터베이스를 사용합니다.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sql_app.db")

# SQLite는 기본적으로 동일 스레드에서만 접근이 가능하므로,
# `check_same_thread=False` 옵션을 추가하여 멀티스레드 환경에서도 사용할 수 있게 합니다.
# (FastAPI는 기본적으로 여러 스레드에서 요청을 처리합니다)
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

# 세션 생성을 위한 `sessionmaker`를 설정합니다.
# `autocommit=False`와 `autoflush=False`를 사용하여 수동으로 트랜잭션을 제어합니다.
# `expire_on_commit=False`는 커밋 후 객체가 만료되지 않도록 합니다.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# SQLAlchemy 모델의 기본 클래스를 정의합니다.
# 모든 모델(테이블) 클래스는 이 `Base` 클래스를 상속받아야 합니다.
class Base(DeclarativeBase):
    pass

# --- 데이터베이스 세션 의존성 주입 함수 ---
# FastAPI에서 `Depends(get_db)`를 통해 요청마다 독립적인 데이터베이스 세션을 제공합니다.
# 이 함수는 요청이 끝나면 세션을 자동으로 닫아 자원을 해제합니다.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
