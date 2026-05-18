#These control what data enters into API and what data leave the API

from pydantic import BaseModel, EmailStr

#base properties...
class UserBase(BaseModel):
    name:str
    email_id:EmailStr

#for creating a new users...
class UserCreate(UserBase):
    pass

#reading a user...
class UserResponse(UserBase):
    id:int

    class Config:
        # allow pydantic to read from sqlalchemy models...
        from_attributes=True