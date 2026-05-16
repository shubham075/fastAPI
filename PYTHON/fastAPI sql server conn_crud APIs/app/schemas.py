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

    class config:
        #allow pydantic to read fro sqlalchemy models...
        from_attributes=True