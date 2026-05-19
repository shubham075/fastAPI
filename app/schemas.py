#These control what data enters into API and what data leave the API
#pydantic models defines the payload structure...

from datetime import date, datetime

from pydantic import BaseModel, EmailStr

#base properties...
class UserBase(BaseModel):
    first_name: str
    last_name: str
    email_id: EmailStr
    mobile: str
    date_of_birth: date
    gender: str
    is_active: bool = True
    role: str = "user"

#for creating a new users...
class UserCreate(UserBase):
    password: str

#for replacing all editable user fields...
class UserUpdate(UserBase):
    password: str | None = None

#for updating one or more user fields...
class UserPatch(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email_id: EmailStr | None = None
    mobile: str | None = None
    password: str | None = None
    date_of_birth: date | None = None
    gender: str | None = None
    is_active: bool | None = None
    role: str | None = None

#reading a user...
class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        # allow pydantic to read from sqlalchemy models...
        from_attributes=True
