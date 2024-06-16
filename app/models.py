from datetime import datetime, timezone

import sqlalchemy as sa
import sqlalchemy.orm as so
from flask_login import UserMixin

from app import db, login


@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))


class User(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    created_at: so.Mapped[datetime] = so.mapped_column(index=True, default=lambda: datetime.now(timezone.utc))
    is_active: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=True)
    is_edited: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=False, nullable=True, )
    user_id: so.Mapped[int] = so.mapped_column(sa.BigInteger, nullable=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(50), index=True)
    telegram_id: so.Mapped[int] = so.mapped_column(sa.BigInteger, nullable=True)
    phone: so.Mapped[int] = so.mapped_column(sa.BigInteger, nullable=True)
    user_request_history: so.WriteOnlyMapped["UserRequestHistory"] = so.relationship(back_populates="executor")
    user_request: so.WriteOnlyMapped["UserRequest"] = so.relationship(
        back_populates="user", foreign_keys="[UserRequest.user_id]"
    )
    executor_request: so.WriteOnlyMapped["UserRequest"] = so.relationship(
        back_populates="executor", foreign_keys="[UserRequest.executor_id]"
    )
    comment: so.WriteOnlyMapped["Comment"] = so.relationship(back_populates="executor")

    def __repr__(self):
        return "<{}>".format(self.name)


class Status(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    created_at: so.Mapped[datetime] = so.mapped_column(index=True, default=lambda: datetime.now(timezone.utc))
    is_active: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(20), index=True)
    user_request: so.WriteOnlyMapped["UserRequest"] = so.relationship(
        back_populates="status", foreign_keys="[UserRequest.status_id]"
    )
    user_request_history: so.WriteOnlyMapped["UserRequestHistory"] = so.relationship(back_populates="status")

    def __repr__(self):
        return "<{}>".format(self.name)


class Branch(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    created_at: so.Mapped[datetime] = so.mapped_column(index=True, default=lambda: datetime.now(timezone.utc))
    is_active: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(20), index=True)
    user_request: so.WriteOnlyMapped["UserRequest"] = so.relationship(
        back_populates="branch", foreign_keys="[UserRequest.branch_id]"
    )

    def __repr__(self):
        return "<{}>".format(self.name)


class UserRequest(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    created_at: so.Mapped[datetime] = so.mapped_column(index=True, default=lambda: datetime.now(timezone.utc))
    closed_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, index=True, nullable=True)
    status_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Status.id), index=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)
    user: so.Mapped[User] = so.relationship(back_populates="user_request", foreign_keys=[user_id])
    theme: so.Mapped[str] = so.mapped_column(sa.String(50), nullable=True)
    cabinet_number: so.Mapped[int] = so.mapped_column(sa.BigInteger, nullable=True)
    text: so.Mapped[str] = so.mapped_column(sa.Text)
    executor_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True, default=None, nullable=True)
    executor: so.Mapped[User] = so.relationship(back_populates="executor_request", foreign_keys=[executor_id])
    channel: so.Mapped[str] = so.mapped_column(sa.String(60), comment="Канал откуда пришло обращение")
    comment: so.WriteOnlyMapped["Comment"] = so.relationship(back_populates="user_request")
    history: so.WriteOnlyMapped["UserRequestHistory"] = so.relationship(back_populates="user_request")
    status: so.Mapped[Status] = so.relationship(back_populates="user_request")
    branch_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Branch.id), index=True)
    branch: so.Mapped[Branch] = so.relationship(back_populates="user_request")

    def to_dict(self):
        try:
            executor_name = self.executor.name
        except AttributeError:
            executor_name = "Не назначен"
        return {
            "id": self.id,
            "created_at": self.created_at,
            "closed_at": self.closed_at,
            "user_id": self.user.id,
            "cabinet_number": self.cabinet_number,
            "branch_name": self.branch.name,
            "status_name": self.status.name,
            "executor_name": executor_name,
            "theme": self.theme,
            "fio": self.user.name,
            "text": self.text,
        }

    def __repr__(self):
        return "<{}>".format(self.text)


class Comment(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    created_at: so.Mapped[datetime] = so.mapped_column(index=True, default=lambda: datetime.now(timezone.utc))
    text: so.Mapped[str] = so.mapped_column(sa.Text, nullable=False)
    executor_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)
    executor: so.Mapped[User] = so.relationship(back_populates="comment")
    user_request_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(UserRequest.id), index=True)
    user_request: so.Mapped[UserRequest] = so.relationship(back_populates="comment")

    def __repr__(self):
        return "<{}>".format(self.executor)


class UserRequestHistory(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    created_at: so.Mapped[datetime] = so.mapped_column(index=True, default=lambda: datetime.now(timezone.utc))
    executor_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True, default=None, nullable=True)
    executor: so.Mapped[User] = so.relationship(back_populates="user_request_history")
    status_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Status.id), index=True)
    user_request_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(UserRequest.id), index=True)
    user_request: so.Mapped[UserRequest] = so.relationship(back_populates="history")
    status: so.Mapped[Status] = so.relationship(back_populates="user_request_history")

    def __repr__(self):
        return "<{}>".format(self.status_id)
