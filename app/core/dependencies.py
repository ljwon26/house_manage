from fastapi import Request, HTTPException, status, Depends
from fastapi.templating import Jinja2Templates

# templates는 이 파일 내에서만 사용되므로 별도로 정의합니다.
templates = Jinja2Templates(directory="templates")

async def verify_login(request: Request):
    if not request.session.get("logged_in", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Basic"},
        )
    return True