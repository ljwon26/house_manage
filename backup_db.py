import os
import shutil
from datetime import datetime, timedelta

# --- 설정 ---
# 1. 백업할 데이터베이스 파일 경로
# 현재 위치의 'data' 폴더 안에 있는 'sql_app.db'를 대상으로 합니다.
DB_FILE = os.path.join('data', 'sql_app.db')

# 2. 백업 파일을 저장할 디렉터리
# 'backups'라는 이름의 폴더를 생성하여 관리합니다.
BACKUP_DIR = 'backups'

# 3. 백업 보관 기간 (일)
# 7일이 지난 백업은 자동으로 삭제됩니다.
RETENTION_DAYS = 7
# --- 설정 끝 ---

def backup_database():
    """
    데이터베이스 파일을 백업하고 오래된 백업을 삭제합니다.
    """
    # 1. 백업 디렉터리가 없으면 생성합니다.
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        print(f"'{BACKUP_DIR}' 디렉터리를 생성했습니다.")

    # 2. 원본 데이터베이스 파일이 존재하는지 확인합니다.
    if not os.path.exists(DB_FILE):
        print(f"오류: 원본 데이터베이스 파일('{DB_FILE}')을 찾을 수 없습니다.")
        return

    # 3. 타임스탬프를 포함한 백업 파일 이름을 생성합니다. (예: sql_app_20250831.db)
    timestamp = datetime.now().strftime('%Y%m%d')
    backup_file_name = f"sql_app_{timestamp}.db"
    backup_file_path = os.path.join(BACKUP_DIR, backup_file_name)

    # 4. 데이터베이스 파일을 백업 디렉터리로 복사합니다.
    try:
        shutil.copy2(DB_FILE, backup_file_path)
        print(f"백업 성공: '{backup_file_path}'")
    except Exception as e:
        print(f"오류: 데이터베이스 백업 중 문제가 발생했습니다 - {e}")
        return

def cleanup_old_backups():
    """
    설정된 보관 기간(RETENTION_DAYS)보다 오래된 백업 파일을 삭제합니다.
    """
    if not os.path.exists(BACKUP_DIR):
        return

    # 삭제 기준이 될 날짜를 계산합니다. (오늘 - 보관 기간)
    cutoff_date = datetime.now() - timedelta(days=RETENTION_DAYS)
    
    # 백업 디렉터리의 모든 파일을 확인합니다.
    for filename in os.listdir(BACKUP_DIR):
        file_path = os.path.join(BACKUP_DIR, filename)
        
        # 파일의 최종 수정 시간을 가져옵니다.
        file_mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
        
        # 파일이 삭제 기준 날짜보다 오래되었으면 삭제합니다.
        if file_mod_time < cutoff_date:
            try:
                os.remove(file_path)
                print(f"오래된 백업 삭제: '{filename}'")
            except Exception as e:
                print(f"오류: '{filename}' 파일 삭제 중 문제가 발생했습니다 - {e}")

if __name__ == "__main__":
    print("--- 데이터베이스 백업 및 정리 시작 ---")
    backup_database()
    cleanup_old_backups()
    print("--- 작업 완료 ---")