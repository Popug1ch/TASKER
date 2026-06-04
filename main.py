import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
import os
from database import engine, Model, new_session
from routers.task import router as tasks_router
from routers.event import router as events_router
from repository import TaskRepository
from datetime import datetime, timedelta
from fastapi.staticfiles import StaticFiles


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Model.metadata.create_all)
    # Проверяем, нужно ли перенести неделю
    async with new_session() as session:
        current_start = await TaskRepository.get_current_week_start(session)
        now = datetime.now()
        # Если текущая неделя уже закончилась (сегодня >= понедельник следующей недели)
        next_week_start = current_start + timedelta(days=7)
        if now.date() >= next_week_start.date():
            await TaskRepository.rollover_week(session)
    print("База данных готова")
    yield
    print("Выключение сервера")


app = FastAPI(lifespan=lifespan)
app.include_router(tasks_router)
app.include_router(events_router)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/favicon.ico", include_in_schema=False)
async def get_favicon():
    favicon_path = os.path.join("static", "favicon.ico")
    return FileResponse(favicon_path)


@app.get("/", response_class=HTMLResponse)
async def get_html_page():
    with open("templates/index.html", "r", encoding="utf-8") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content)


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
