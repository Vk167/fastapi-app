from pydantic import BaseModel
from fastapi_users import schemas

import uuid

class postCreate(BaseModel):
    title:str
    content:str

class postResponse(BaseModel):
    title: str
    content: str

class UserRead(schemas.BaseUser[uuid.UUID]):
    pass

class UserCreate(schemas.BaseUserCreate):
    pass

class UserUpdate(schemas.BaseUserUpdate):
    pass
