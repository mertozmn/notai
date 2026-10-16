from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    email: str
    password: str = Field(min_length=8)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str


class NoteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str


class NoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"