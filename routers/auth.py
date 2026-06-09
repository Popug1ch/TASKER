"""
Модуль маршрутов для аутентификации и управления пользователями.
Регистрация, вход, выход, получение данных текущего пользователя.
"""

from fastapi import APIRouter, HTTPException, Response, Request
from core.database import SessionDep
from schemas.auth import UserRegister, UserLogin, UserOut
from repository.user_repository import UserRepository
from repository.session_repository import SessionRepository

router = APIRouter(prefix="/auth", tags=["Авторизация"])


@router.post("/register", response_model=UserOut, status_code=200)
async def register(user_data: UserRegister, session: SessionDep) -> UserOut:
    """
    Регистрация нового пользователя.

    Параметры:
        user_data (UserRegister): JSON с полями username, email, password.
        session (SessionDep): зависимость для получения сессии БД.

    Возвращает:
        UserOut: объект созданного пользователя (id, username, email).

    Исключения:
        400: если email уже зарегистрирован.
    """
    existing = await UserRepository.get_by_email(session, user_data.email)
    if existing:
        raise HTTPException(400, "Email уже зарегистрирован")
    user = await UserRepository.create(
        session, user_data.username, user_data.email, user_data.password
    )
    return user


@router.post("/login")
async def login(
    response: Response, user_data: UserLogin, session: SessionDep
) -> dict:
    """
    Аутентификация пользователя и установка сессионной cookie.

    Параметры:
        response (Response): объект ответа FastAPI (для установки cookie).
        user_data (UserLogin): email и пароль.
        session (SessionDep): сессия БД.

    Возвращает:
        dict: сообщение об успехе и данные пользователя.

    Исключения:
        401: неверный email или пароль.
    """
    user = await UserRepository.get_by_email(session, user_data.email)
    if not user or not UserRepository.verify_password(
        user_data.password, user.hashed_password
    ):
        raise HTTPException(401, "Неверный email или пароль")
    token = await SessionRepository.create(session, user.id)
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,               # защита от XSS
        max_age=30 * 24 * 3600,      # 30 дней
        samesite="lax",              # защита от CSRF
    )
    return {
        "message": "Успешный вход",
        "user": {"id": user.id, "username": user.username, "email": user.email},
    }


@router.post("/logout")
async def logout(request: Request, response: Response, session: SessionDep) -> dict:
    """
    Выход пользователя – удаление сессии и cookie.

    Параметры:
        request (Request): входящий запрос (для чтения cookie).
        response (Response): исходящий ответ (для удаления cookie).
        session (SessionDep): сессия БД.

    Возвращает:
        dict: сообщение об успешном выходе.
    """
    token = request.cookies.get("session_token")
    if token:
        await SessionRepository.delete(session, token)
    response.delete_cookie("session_token")
    return {"message": "Выход выполнен"}


@router.get("/me")
async def me(request: Request, session: SessionDep) -> dict:
    """
    Возвращает данные текущего авторизованного пользователя.

    Параметры:
        request (Request): запрос с cookie session_token.
        session (SessionDep): сессия БД.

    Возвращает:
        dict: id, username, email пользователя.

    Исключения:
        401: отсутствует или недействителен токен.
    """
    token = request.cookies.get("session_token")
    if not token:
        raise HTTPException(401, "Не авторизован")
    user = await SessionRepository.get_user_by_token(session, token)
    if not user:
        raise HTTPException(401, "Сессия истекла")
    return {"id": user.id, "username": user.username, "email": user.email}