"""
Главный модуль приложения "Таскер".

Запускает FastAPI сервер, подключает роутеры, обрабатывает статические файлы,
управляет жизненным циклом (создание таблиц БД, перенос недель),
а также предоставляет HTML-страницы для входа, регистрации и основного интерфейса.
"""

import os
import uvicorn
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from core.database import engine, Model, new_session
from routers.task import router as tasks_router
from routers.event import router as events_router
from routers.deadline import router as deadlines_router
from routers.auth import router as auth_router
from repository.task_repository import TaskRepository
from repository.session_repository import SessionRepository


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Асинхронный контекстный менеджер для управления жизненным циклом FastAPI.
    Выполняется при старте и остановке приложения.

    Параметры:
        app (FastAPI): экземпляр приложения FastAPI (передаётся автоматически).

    Возвращает:
        None (yield) – после инициализации управление возвращается приложению.
    """
    async with engine.begin() as conn:
        # Создание всех таблиц в базе данных на основе моделей SQLAlchemy
        await conn.run_sync(Model.metadata.create_all)

    async with new_session() as session:
        # Получаем начало текущей недели (понедельник)
        current_start = await TaskRepository.get_current_week_start(session)
        now = datetime.now()
        next_week_start = current_start + timedelta(days=7)
        # Если текущая дата >= понедельник следующей недели, выполняем перенос
        if now.date() >= next_week_start.date():
            await TaskRepository.rollover_week(session)

    print("База данных готова")
    yield  # Здесь приложение работает
    print("Выключение сервера")


app = FastAPI(lifespan=lifespan)

# Подключение роутеров
app.include_router(tasks_router)  # задачи
app.include_router(events_router)  # события
app.include_router(deadlines_router)  # дедлайны
app.include_router(auth_router)  # авторизация

# Подключение статических файлов (CSS, JS, изображения)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/favicon.ico", include_in_schema=False)
async def get_favicon() -> FileResponse:
    """
    Возвращает иконку сайта (favicon.ico) из папки static.

    Параметры:
        Нет.

    Возвращает:
        FileResponse: ответ с файлом favicon.ico.
    """
    favicon_path = os.path.join("static", "favicon.ico")
    return FileResponse(favicon_path)


@app.get("/", response_class=HTMLResponse)
async def get_html_page(request: Request) -> HTMLResponse:
    """
    Главная страница приложения.

    Параметры:
        request (Request): объект HTTP-запроса (содержит cookies).

    Возвращает:
        HTMLResponse: HTML-контент главной страницы,
        либо RedirectResponse на страницу входа.
    """
    token = request.cookies.get("session_token")
    if not token:
        return RedirectResponse(url="/login")

    async with new_session() as session:
        user = await SessionRepository.get_user_by_token(session, token)
        if not user:
            return RedirectResponse(url="/login")

    with open("templates/index.html", "r", encoding="utf-8") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content)


@app.get("/login", response_class=HTMLResponse)
async def login_page() -> HTMLResponse:
    """
    Страница входа пользователя.

    Параметры:
        Нет.

    Возвращает:
        HTMLResponse: HTML-форму входа.
    """
    with open("templates/login.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/register", response_class=HTMLResponse)
async def register_page() -> HTMLResponse:
    """
    Страница регистрации нового пользователя.

    Параметры:
        Нет.

    Возвращает:
        HTMLResponse: HTML-форму регистрации.
    """
    with open("templates/register.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


if __name__ == "__main__":
    # Запуск сервера Uvicorn
    uvicorn.run(
        "main:app",  # путь к объекту app
        host="127.0.0.1",  # локальный хост
        port=8000,  # порт
        reload=True,  # автоматическая перезагрузка при изменении кода
    )
