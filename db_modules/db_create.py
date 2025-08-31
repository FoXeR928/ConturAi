from sqlalchemy.orm import mapped_column, Mapped, DeclarativeBase, Session
from sqlalchemy import ForeignKey, create_engine, func, DateTime
from datetime import datetime
import secrets
import bcrypt
from loguru import logger

from instance.config_read import init_confg

config = init_confg()


def init_db():
    try:
        engine = create_engine(config["SQLALCHEMY_DATABASE_URI"])
        Base.metadata.create_all(engine)
        logger.info("База данных инициализирована")
        return engine
    except Exception as err:
        logger.critical(f"Не удалось инициализировать базу данных Ошибка: {err}")
        exit()


def session_create():
    from api.api_app import engine

    session = Session(bind=engine)
    return session


class Base(DeclarativeBase):
    pass


class Users(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, unique=True, nullable=False)
    login: Mapped[str] = mapped_column(nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(nullable=True)
    user_name: Mapped[str] = mapped_column(nullable=True)
    user_role: Mapped[str] = mapped_column(nullable=False, default="user")
    admin: Mapped[bool] = mapped_column(nullable=False, default=False)
    system: Mapped[bool] = mapped_column(nullable=False, default=False)
    chat_role: Mapped[str] = mapped_column(nullable=False, default="user")
    disabled: Mapped[bool] = mapped_column(nullable=False, default=False)
    date_create: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=datetime.now()
    )
    date_update: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    def set_password(self, password: str):
        generate_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        self.password_hash = generate_hash

    def check_password(self, password: str):
        check_password_func = bcrypt.checkpw(password.encode(), self.password_hash)
        check_active = self.disabled == False
        return check_password_func and check_active


class Chats(Base):
    __tablename__ = "chats"

    id: Mapped[int] = mapped_column(primary_key=True, unique=True, nullable=False)
    user_login: Mapped[str] = mapped_column(
        ForeignKey("users.login", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    chat_name: Mapped[str] = mapped_column(nullable=False)
    chat_del: Mapped[bool] = mapped_column(nullable=False, default=False)
    date_create: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=datetime.now()
    )
    date_update: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )


class Messages(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, unique=True, nullable=False)
    user_login: Mapped[str] = mapped_column(
        ForeignKey("users.login", onupdate="CASCADE"), nullable=False
    )
    chat_id: Mapped[int] = mapped_column(
        ForeignKey("chats.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False
    )
    text: Mapped[str]
    date_create: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=datetime.now()
    )
    date_update: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )


class Configs(Base):
    __tablename__ = "configs"

    id: Mapped[int] = mapped_column(primary_key=True, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    about: Mapped[str] = mapped_column(nullable=False)
    value: Mapped[str] = mapped_column(nullable=False)
    input_format: Mapped[str] = mapped_column(nullable=False)
    date_create: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=datetime.now()
    )
    date_update: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )


class Configs_ai(Base):
    __tablename__ = "configs_ai"

    id: Mapped[int] = mapped_column(primary_key=True, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    about: Mapped[str] = mapped_column(nullable=False)
    value: Mapped[str] = mapped_column(nullable=False)
    input_format: Mapped[str] = mapped_column(nullable=False)
    date_create: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=datetime.now()
    )
    date_update: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )


class Token_API(Base):
    __tablename__ = "token_api"

    id: Mapped[int] = mapped_column(primary_key=True, unique=True, nullable=False)
    token: Mapped[str] = mapped_column(unique=True, nullable=True)
    date_create: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), default=datetime.now()
    )

    def generate_token(self):
        self.token = secrets.token_hex(64)

    def check_token(self, check_token):
        if self.token == check_token:
            return True
        else:
            return False
