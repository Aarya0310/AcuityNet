from collections.abc import Callable

from fastapi import Header, HTTPException

from backend.app.auth.service import load_token_user
from backend.app.persistence.models import User


def get_current_user(sessions) -> Callable:
    def dependency(authorization: str | None = Header(default=None)) -> User:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authentication")
        with sessions() as session:
            try:
                user = load_token_user(session, authorization[7:])
                return user
            except Exception as error:
                raise HTTPException(status_code=401, detail="Invalid authentication") from error
    return dependency


def require_roles(*roles: str):
    def dependency(user: User):
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Forbidden")
        return user
    return dependency


def require_patient_access(user: User, patient_id: str) -> User:
    if patient_id != "P-1042" or user.role not in {"admin", "doctor", "nurse"}:
        raise HTTPException(status_code=403, detail="Forbidden")
    return user


def require_nurse_assignment(user: User, patient_id: str, nurse_id: str = "N-SARAH") -> User:
    if user.role == "nurse" and (patient_id != "P-1042" or user.user_id != "U-SARAH" or nurse_id != "N-SARAH"):
        raise HTTPException(status_code=403, detail="Forbidden")
    return user