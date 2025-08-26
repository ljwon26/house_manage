import os
import aiosmtplib
from email.mime.text import MIMEText

async def send_email(to_email: str, subject: str, body: str):
    # 환경 변수에서 SMTP 설정 가져오기
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")

    if not all([sender_email, sender_password]):
        print("이메일 전송 환경 변수가 설정되지 않았습니다. 이메일을 건너뜁니다.")
        return

    msg = MIMEText(body, "html")
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = to_email

    try:
        smtp = aiosmtplib.SMTP(hostname=smtp_server, port=smtp_port, use_tls=True)
        await smtp.connect()
        await smtp.login(sender_email, sender_password)
        await smtp.send_message(msg)
        await smtp.quit()
        print("이메일이 성공적으로 전송되었습니다.")
    except Exception as e:
        print(f"이메일 전송 실패: {e}")
