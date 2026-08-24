from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from backend.app.admin.configuration import update_typed_configuration
from backend.app.admin.kpis import get_admin_kpis
from backend.app.admin.repository import list_beds, list_prototype_users, update_bed, update_nurse_status
from backend.app.contracts.admin import AdminKpiResponse, UserCreateRequest, UserResponse
from backend.app.contracts.configuration import RefreshSettingsUpdate, ResearchRulesUpdate, RiskThresholdsUpdate
from backend.app.persistence.models import Bed, Nurse, User
from backend.app.seed.demo_data import password_digest


def admin_router(sessions, current_user):
    router = APIRouter(prefix="/api/v1/admin")
    def admin(user=Depends(current_user)):
        if user.role != "admin": raise HTTPException(status_code=403, detail="Forbidden")
        return user
    @router.get("/users", response_model=list[UserResponse])
    def users(_=Depends(admin)):
        with sessions() as s: return list_prototype_users(s)
    @router.post("/users", response_model=UserResponse)
    def create(request: UserCreateRequest, _=Depends(admin)):
        with sessions.begin() as s:
            if s.scalar(select(User).where(User.username == request.username)): raise HTTPException(409, "Username already exists")
            user = User(user_id=f"U-{request.username.upper()}", username=request.username, display_name=request.display_name, role=request.role, password_digest=password_digest(request.password), active=True)
            s.add(user); s.flush(); return user
    @router.get("/beds")
    def beds(_=Depends(admin)):
        with sessions() as s: return list_beds(s)
    @router.get("/kpis", response_model=AdminKpiResponse)
    def kpis(_=Depends(admin)):
        with sessions() as s: return get_admin_kpis(s)
    @router.patch("/configuration/risk-thresholds")
    def thresholds(request: RiskThresholdsUpdate, _=Depends(admin)):
        with sessions.begin() as s: return update_typed_configuration(s, request.model_dump())
    @router.patch("/configuration/research-rules")
    def rules(request: ResearchRulesUpdate, _=Depends(admin)):
        with sessions.begin() as s: return update_typed_configuration(s, request.model_dump())
    @router.patch("/configuration/refresh")
    def refresh(request: RefreshSettingsUpdate, _=Depends(admin)):
        return request
    return router