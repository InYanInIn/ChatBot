from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)


class UserOut(BaseModel):
    id: str
    username: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
