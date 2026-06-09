from fastapi import HTTPException, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from repository.session_repository import SessionRepository


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)):
    token = request.cookies.get("session_token")
    if not token:
        raise HTTPException(status_code=401, detail="Не авторизован")
    user = await SessionRepository.get_user_by_token(db, token)
    if not user:
        raise HTTPException(status_code=401, detail="Сессия истекла")
    return user
