from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: Optional[str]


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str]
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MoveCreate(BaseModel):
    origin_country: str
    destination_country: str
    start_date: Optional[date]


class MoveOut(BaseModel):
    id: int
    origin_country: str
    destination_country: str
    start_date: Optional[date]
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class TaskCreate(BaseModel):
    title: str
    description: Optional[str]
    category: Optional[str]
    due_date: Optional[date]


class TaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    category: Optional[str]
    due_date: Optional[date]
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class MoveWithTasks(MoveOut):
    tasks: List[TaskOut] = []
