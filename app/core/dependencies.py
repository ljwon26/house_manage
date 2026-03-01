from fastapi import Request, HTTPException, status

def login_required(request: Request):
    # auth.py에서 저장한 세션 키("authenticated")와 이름을 똑같이 맞춰야 합니다.
    if not request.session.get("authenticated"):
        
        # 원래 접속하려던 URL을 기억해둡니다 (선택 사항)
        request.session["redirect_after_login"] = str(request.url)
        
        # [핵심] return RedirectResponse가 아니라 raise 예외처리를 해야 완벽히 차단됩니다!
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/login"}
        )
        
    return True