from http import HTTPStatus
from sqlite3 import IntegrityError
from typing import Iterable, Type

from fastapi import HTTPException
from sqlmodel import Session, select
from app.database.engine import engine
from app.models.User import User


def get_user(user_id: int) -> User | None:
    with Session(engine) as session:
        return session.get(User, user_id)


def get_users() -> Iterable[User]:
    with Session(engine) as session:
        statement = select(User)
        return session.exec(statement).all()


def create_user(user: User) -> User:
    with Session(engine) as session:
        try:
            user.id = None
            session.add(user)
            session.commit()
            session.refresh(user)
            return user
        except IntegrityError:
            session.rollback()
            raise HTTPException(status_code=409, detail="User already exists")


def update_user(user_id: int, user: User) -> Type[User]:
    with Session(engine) as session:
        db_user = session.get(User, user_id)
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")
        user_data = user.model_dump(exclude_unset=True)
        db_user.sqlmodel_update(user_data)
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        return db_user


def delete_user(user_id: int):
    with Session(engine) as session:
        user = session.get(User, user_id)
        if user is None:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"User with id={user_id} not found"
            )
        session.delete(user)
        session.commit()
