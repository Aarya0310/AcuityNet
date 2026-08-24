from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.persistence.models import Bed, Nurse, User


def get_user(session: Session, user_id: str): return session.get(User, user_id)
def list_prototype_users(session: Session): return list(session.scalars(select(User).order_by(User.user_id)))
def create_user(session: Session, user: User): session.add(user); session.flush(); return user
def update_user(session: Session, user: User, **fields):
    for key, value in fields.items(): setattr(user, key, value)
    session.flush(); return user
def update_nurse_status(session: Session, nurse: Nurse, available: bool): nurse.available = available; session.flush(); return nurse
def list_beds(session: Session): return list(session.scalars(select(Bed).order_by(Bed.bed_id)))
def update_bed(session: Session, bed: Bed, **fields):
    for key, value in fields.items(): setattr(bed, key, value)
    session.flush(); return bed