from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.auth.service import authenticate, current_user_response, load_token_user
from backend.app.contracts.auth import CurrentUserResponse, LoginRequest, SessionResponse


def auth_router(sessions) -> APIRouter:
    router = APIRouter(prefix="/api/v1/auth")

    def bearer_user(authorization: str | None = Header(default=None)):
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authentication")
        with sessions() as session:
            try:
                return current_user_response(load_token_user(session, authorization[7:]))
            except Exception as error:
                raise HTTPException(status_code=401, detail="Invalid authentication") from error

    @router.post("/login", response_model=SessionResponse)
    def login(request: LoginRequest):
        with sessions() as session:
            result = authenticate(session, request.username, request.password)
        if result is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return result

    @router.get("/me", response_model=CurrentUserResponse)
    def me(user: CurrentUserResponse = Depends(bearer_user)):
        return user

    @router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
    def logout(user: CurrentUserResponse = Depends(bearer_user)):
        return None

    return router