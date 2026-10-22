from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import BLOB, ForeignKey
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


class Users(UserMixin, db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, unique=True, nullable=False)
    login: Mapped[str] = mapped_column(nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(nullable=True)
    user_name: Mapped[str] = mapped_column(nullable=True)
    user_role: Mapped[str] = mapped_column(nullable=False, default="user")
    chat_role: Mapped[str] = mapped_column(nullable=False, default="user")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Chats(db.Model):
    __tablename__ = "chats"

    id: Mapped[int] = mapped_column(primary_key=True, unique=True, nullable=False)
    user_login: Mapped[str] = mapped_column(
        ForeignKey("users.login", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    chat_name: Mapped[str] = mapped_column(nullable=False)
    chat_del: Mapped[bool] = mapped_column(nullable=False, default=False)


class Messages(db.Model):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, unique=True, nullable=False)
    user_login: Mapped[str] = mapped_column(
        ForeignKey("users.login", onupdate="CASCADE"), nullable=False
    )
    chat_id: Mapped[int] = mapped_column(
        ForeignKey("chats.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False
    )
    text: Mapped[str]


class Files(db.Model):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(primary_key=True, unique=True, nullable=False)
    file_type: Mapped[str] = mapped_column(nullable=False)
    file_name: Mapped[int] = mapped_column(nullable=False)
    file: Mapped[str] = mapped_column(BLOB)


class Configs(db.Model):
    __tablename__ = "configs"

    id: Mapped[int] = mapped_column(primary_key=True, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    about: Mapped[str] = mapped_column(nullable=False)
    value: Mapped[str] = mapped_column(nullable=False)
    input_format: Mapped[str] = mapped_column(nullable=False)


class Configs_ai(db.Model):
    __tablename__ = "configs_ai"

    id: Mapped[int] = mapped_column(primary_key=True, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    about: Mapped[str] = mapped_column(nullable=False)
    value: Mapped[str] = mapped_column(nullable=False)
    input_format: Mapped[str] = mapped_column(nullable=False)
