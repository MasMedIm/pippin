from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id: int = Column(Integer, primary_key=True, index=True)
    email: str = Column(String(256), unique=True, nullable=False, index=True)
    hashed_password: str = Column(String(256), nullable=False)
    full_name: Optional[str] = Column(String(256))
    is_active: bool = Column(Boolean, default=True)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)

    moves = relationship("Move", back_populates="user", cascade="all, delete-orphan")


class Move(Base):
    __tablename__ = "moves"

    id: int = Column(Integer, primary_key=True, index=True)
    user_id: int = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    origin_country: str = Column(String(64), nullable=False)
    destination_country: str = Column(String(64), nullable=False)
    start_date: datetime = Column(Date, nullable=True)
    status: str = Column(String(32), default="planning")
    created_at: datetime = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="moves")
    tasks = relationship("Task", back_populates="move", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"

    id: int = Column(Integer, primary_key=True, index=True)
    move_id: int = Column(Integer, ForeignKey("moves.id", ondelete="CASCADE"), nullable=False)
    title: str = Column(String(256), nullable=False)
    description: Optional[str] = Column(Text)
    category: Optional[str] = Column(String(64))
    due_date: Optional[datetime] = Column(Date)
    status: str = Column(String(32), default="pending")
    created_at: datetime = Column(DateTime, default=datetime.utcnow)

    move = relationship("Move", back_populates="tasks")
