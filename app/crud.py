#this will keep you DB logics from API end-points...

from sqlalchemy.orm import Session
from app import models, schemas

def get_user_by_email(db:Session, email:str):
    return db.query(models.Users).filter(models.Users.email_id == email).first()

def get_users(db:Session):
    return db.query(models.Users).all()

def create_user(db:Session, user:schemas.UserCreate):
    db_user = models.Users(name=user.name, email_id=user.email_id)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user