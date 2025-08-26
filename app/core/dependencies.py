from fastapi import Request
from fastapi.responses import RedirectResponse

def login_required(request: Request):
    """
    사용자가 로그인했는지 세션을 확인합니다.
    로그인하지 않은 경우, 로그인 페이지로 리디렉션합니다.
    """
    if not request.session.get("logged_in"):
        # 원래 접속하려던 URL을 세션에 저장합니다.
        request.session["redirect_after_login"] = str(request.url)
        return RedirectResponse(url="/login", status_code=303)
    return True
