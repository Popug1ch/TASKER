from fastapi import APIRouter, HTTPException, Response, Request
from database import SessionDep
from schemas.auth import UserRegister, UserLogin, UserOut
from repository import UserRepository, SessionRepository

router = APIRouter(prefix="/auth", tags=["Авторизация"])


@router.post("/register", response_model=UserOut)
async def register(user_data: UserRegister, session: SessionDep):
    existing = await UserRepository.get_by_email(session, user_data.email)
    if existing:
        raise HTTPException(400, "Email уже зарегистрирован")
    user = await UserRepository.create(
        session, user_data.username, user_data.email, user_data.password
    )
    return user


@router.post("/login")
async def login(response: Response, user_data: UserLogin, session: SessionDep):
    user = await UserRepository.get_by_email(session, user_data.email)
    if not user or not UserRepository.verify_password(
        user_data.password, user.hashed_password
    ):
        raise HTTPException(401, "Неверный email или пароль")
    token = await SessionRepository.create(session, user.id)
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        max_age=30 * 24 * 3600,
        samesite="lax",
    )
    return {
        "message": "Успешный вход",
        "user": {"id": user.id, "username": user.username, "email": user.email},
    }


@router.post("/logout")
async def logout(request: Request, response: Response, session: SessionDep):
    token = request.cookies.get("session_token")
    if token:
        await SessionRepository.delete(session, token)
    response.delete_cookie("session_token")
    return {"message": "Выход выполнен"}


@router.get("/me")
async def me(request: Request, session: SessionDep):
    token = request.cookies.get("session_token")
    if not token:
        raise HTTPException(401, "Не авторизован")
    user = await SessionRepository.get_user_by_token(session, token)
    if not user:
        raise HTTPException(401, "Сессия истекла")
    return {"id": user.id, "username": user.username, "email": user.email}
