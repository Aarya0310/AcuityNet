from sqlalchemy.orm import Session

from backend.app.auth.security import create_access_token, decode_access_token, verify_password
from backend.app.contracts.auth import CurrentUserResponse, SessionResponse
from backend.app.persistence.models import User


def current_user_response(user: User) -> CurrentUserResponse:
    return CurrentUserResponse(user_id=user.user_id, username=user.username, display_name=user.display_name, role=user.role)


def authenticate(session: Session, username: str, password: str) -> SessionResponse | None:
    user = session.query(User).filter(User.username == username).one_or_none()
    if user is None or not user.active or not verify_password(password, user.password_digest):
        return None
    return SessionResponse(access_token=create_access_token(user.user_id), expires_in=3600, user=current_user_response(user))


def load_token_user(session: Session, token: str) -> User:
    user_id = decode_access_token(token)
    user = session.get(User, user_id)
    if user is None or not user.active or user.role not in {"admin", "doctor", "nurse"}:
        raise ValueError("Invalid user")
    return user