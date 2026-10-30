from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..deps import get_current_user, require_admin
from ..models import User
from ..schemas import TokenResponse, UserCreate, UserRead
from ..security import create_access_token
from ..services import user_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    user = await user_service.authenticate(db, form.username, form.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(str(user.id), user.role)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserRead)
async def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.post("/users", response_model=UserRead, status_code=201)
async def create_user(
    payload: UserCreate,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> User:
    existing = await user_service.get_user_by_username(db, payload.username)
    if existing:
        raise HTTPException(status_code=409, detail="Username already taken")
    return await user_service.create_user(
        db, payload.username, payload.password, payload.role
    )