from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from routers.task import router as tasks_router
import uvicorn
from contextlib import asynccontextmanager
from database import engine, Model


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Model.metadata.create_all)
    print("База данных готова")
    yield
    print("Выключение сервера")


app = FastAPI(lifespan=lifespan)
app.include_router(tasks_router)


@app.get("/", response_class=HTMLResponse)
async def get_html_page():
    with open("templates/index.html", "r", encoding="utf-8") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content)


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
