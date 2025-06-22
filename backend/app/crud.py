"""Lightweight CRUD helper functions."""

from sqlalchemy.orm import Session

from .auth import get_password_hash
from .models import Move, Task, User


# Users ----------------------------------------------------------------------


def create_user(db: Session, email: str, password: str, full_name: str | None = None) -> User:
    user = User(email=email, hashed_password=get_password_hash(password), full_name=full_name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# Moves ----------------------------------------------------------------------


def create_move(db: Session, user: User, **data) -> Move:
    move = Move(user_id=user.id, **data)
    db.add(move)
    db.commit()
    db.refresh(move)
    return move


def get_moves(db: Session, user: User):
    return db.query(Move).filter(Move.user_id == user.id).all()


# Tasks ----------------------------------------------------------------------


def create_task(db: Session, move: Move, **data) -> Task:
    task = Task(move_id=move.id, **data)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_tasks(db: Session, move: Move):
    return db.query(Task).filter(Task.move_id == move.id).all()
