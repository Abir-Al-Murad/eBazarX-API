from uuid import UUID
from fastapi import Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.security import decode_token
from app.infrastructure.database.session import get_async_session
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.infrastructure.database.models import User
from app.application.services.auth_service import AuthService
from app.core.security import oauth2_scheme

async def get_uow(session: AsyncSession = Depends(get_async_session)) -> UnitOfWork:
    return UnitOfWork(session)

async def get_auth_service(uow: UnitOfWork = Depends(get_uow)) -> AuthService:
    return AuthService(uow)

# async def get_current_user(request: Request, uow: UnitOfWork = Depends(get_uow)) -> User:
#     token = request.headers.get("Authorization")
#     if not token or not token.startswith("Bearer "):
#         raise HTTPException(status_code=401, detail="Missing token")
#     payload = decode_token(token[7:])
#     if not payload:
#         raise HTTPException(status_code=401, detail="Invalid token")
#     user_id = payload.get("sub")
#     if not user_id:
#         raise HTTPException(status_code=401, detail="Invalid token")
#     user = await uow.users.get(UUID(user_id))
#     if not user or not user.is_active:
#         raise HTTPException(status_code=401, detail="User not found or inactive")
#     return user

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    uow: UnitOfWork = Depends(get_uow),
) -> User:

    payload = decode_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await uow.users.get(UUID(user_id))

    if not user or not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="User not found or inactive",
        )

    return user