from sqlalchemy.orm import mapped_column, Mapped,DeclarativeBase,Session
from sqlalchemy import BLOB, ForeignKey,create_engine
import secrets
import bcrypt
from loguru import logger

from instance.config_read import init_confg

config=init_confg()

def session_create():
    session=Session(bind=engine)
    return session

class Base(DeclarativeBase):
    pass

class Users(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, unique=True, nullable=False)
    login: Mapped[str] = mapped_column(nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(nullable=True)
    token: Mapped[str]=mapped_column(nullable=True,unique=True)
    user_name: Mapped[str] = mapped_column(nullable=True)
    user_role: Mapped[str] = mapped_column(nullable=False, default="user")
    chat_role: Mapped[str] = mapped_column(nullable=False, default="user")

    def set_password(self, password:str):
        generate_hash=bcrypt.hashpw(password.encode(),bcrypt.gensalt())
        self.password_hash = generate_hash

    def check_password(self, password:str):
        return bcrypt.checkpw(password.encode(),self.password_hash)

    def generate_token(self):
        self.token=secrets.token_hex(32)
    
    def check_token(self,check_token):
        return self.token==check_token
    
    def check_admin(self,token_to_check):
        check_role=(self.user_role=='admin')
        check_token=(self.token==token_to_check)
        return check_role and check_token


class Chats(Base):
    __tablename__ = "chats"

    id: Mapped[int] = mapped_column(primary_key=True, unique=True, nullable=False)
    user_login: Mapped[str] = mapped_column(
        ForeignKey("users.login", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    chat_name: Mapped[str] = mapped_column(nullable=False)
    chat_del: Mapped[bool] = mapped_column(nullable=False, default=False)


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


class Files(Base):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(primary_key=True, unique=True, nullable=False)
    file_type: Mapped[str] = mapped_column(nullable=False)
    file_name: Mapped[int] = mapped_column(nullable=False)
    file: Mapped[str] = mapped_column(BLOB)


class Configs(Base):
    __tablename__ = "configs"

    id: Mapped[int] = mapped_column(primary_key=True, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    about: Mapped[str] = mapped_column(nullable=False)
    value: Mapped[str] = mapped_column(nullable=False)
    input_format: Mapped[str] = mapped_column(nullable=False)


class Configs_ai(Base):
    __tablename__ = "configs_ai"

    id: Mapped[int] = mapped_column(primary_key=True, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    about: Mapped[str] = mapped_column(nullable=False)
    value: Mapped[str] = mapped_column(nullable=False)
    input_format: Mapped[str] = mapped_column(nullable=False)

class Token_API(Base):
    __tablename__ = "token_api"

    id: Mapped[int] = mapped_column(primary_key=True, unique=True, nullable=False)
    token: Mapped[str] = mapped_column(unique=True, nullable=True)

    def generate_token(self):
        self.token=secrets.token_hex(64)
    
    def check_token(self,check_token):
        if self.token==check_token:
            return True
        else:
            return False

try:
    engine=create_engine(config['SQLALCHEMY_DATABASE_URI'])
    Base.metadata.create_all(engine)
    logger.info("База данных инициализирована")
except Exception as err:
    logger.critical(f"Не удалось инициализировать базу данных Ошибка: {err}")
    exit()