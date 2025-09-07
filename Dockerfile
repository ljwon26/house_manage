# 1. 베이스 이미지 선택 (파이썬 3.12 슬림 버전)
FROM python:3.12-slim

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. requirements.txt 파일을 먼저 복사하여 라이브러리 설치 (캐시 활용)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV TZ=Asia/Seoul
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 4. 프로젝트의 나머지 모든 파일들을 작업 디렉토리로 복사
COPY . .

# 5. Docker 컨테이너 외부로 노출할 포트 설정
EXPOSE 8000

# 6. 컨테이너가 시작될 때 실행할 명령어
# uvicorn을 이용해 main.py의 app을 실행합니다.
# --host 0.0.0.0 옵션은 외부에서 접속 가능하도록 합니다.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]
