#this will keep you DB logics from API end-points...

from sqlalchemy.orm import Session
from app import auth, models, schemas

def get_user_by_email(db:Session, email:str):
    return db.query(models.Users).filter(models.Users.email_id == email).first()

def get_user_by_mobile(db:Session, mobile:str):
    return db.query(models.Users).filter(models.Users.mobile == mobile).first()

def get_users(db:Session):
    return db.query(models.Users).all()

def get_user(db:Session, user_id:int):
    return db.query(models.Users).filter(models.Users.id == user_id).first()

def create_user(db:Session, user:schemas.UserCreate):
    user_data = user.model_dump()
    password = user_data.pop("password")
    db_user = models.Users(**user_data, password_hash=auth.hash_password(password))
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db:Session, db_user:models.Users, user:schemas.UserUpdate):
    user_data = user.model_dump()
    password = user_data.pop("password", None)
    for field, value in user_data.items():
        setattr(db_user, field, value)
    if password:
        db_user.password_hash = auth.hash_password(password)
    db.commit()
    db.refresh(db_user)
    return db_user

def patch_user(db:Session, db_user:models.Users, user:schemas.UserPatch):
    user_data = user.model_dump(exclude_unset=True)
    password = user_data.pop("password", None)
    for field, value in user_data.items():
        setattr(db_user, field, value)
    if password:
        db_user.password_hash = auth.hash_password(password)
    db.commit()
    db.refresh(db_user)
    return db_user
