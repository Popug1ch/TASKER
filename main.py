import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi import Body
from typing import Dict, Any, List
from datetime import datetime

app = FastAPI()

tasks = {
    "1": {
        "id": "1",
        "Название": "Выучить стих",
        "Начало выполнения": "01.06.2026 13:00",
        "Конец выполнения": "01.06.2026 15:00",
        "Длительность": 120,
        "Категория": "Не указана",
        "Важность": "Очень высокая",
        "Состояние": False,
    },
    "2": {
        "id": "2",
        "Название": "Сделать домашнее задание",
        "Начало выполнения": "01.06.2026 10:00",
        "Конец выполнения": "01.06.2026 12:30",
        "Длительность": 150,
        "Категория": "Учеба",
        "Важность": "Высокая",
        "Состояние": False,
    },
    "3": {
        "id": "3",
        "Название": "Купить продукты",
        "Начало выполнения": "03.06.2026 18:00",
        "Конец выполнения": "03.06.2026 19:00",
        "Длительность": 60,
        "Категория": "Покупки",
        "Важность": "Средняя",
        "Состояние": True,
    },
    "4": {
        "id": "4",
        "Название": "Позвонить врачу",
        "Начало выполнения": "02.06.2026 09:00",
        "Конец выполнения": "02.06.2026 09:30",
        "Длительность": 30,
        "Категория": "Личное",
        "Важность": "Высокая",
        "Состояние": False,
    },
    "5": {
        "id": "5",
        "Название": "Сходить в спортзал",
        "Начало выполнения": "02.06.2026 18:00",
        "Конец выполнения": "02.06.2026 19:30",
        "Длительность": 90,
        "Категория": "Здоровье",
        "Важность": "Средняя",
        "Состояние": False,
    },
    "6": {
        "id": "6",
        "Название": "Подготовить отчёт",
        "Начало выполнения": "04.06.2026 14:00",
        "Конец выполнения": "04.06.2026 17:00",
        "Длительность": 180,
        "Категория": "Работа",
        "Важность": "Очень высокая",
        "Состояние": False,
    },
    "7": {
        "id": "7",
        "Название": "Полить цветы",
        "Начало выполнения": "05.06.2026 08:30",
        "Конец выполнения": "05.06.2026 08:45",
        "Длительность": 15,
        "Категория": "Дом",
        "Важность": "Низкая",
        "Состояние": False,
    },
}


def parse_datetime(date_string: str) -> datetime:
    date_part, time_part = date_string.split(" ")
    day, month, year = date_part.split(".")
    hour, minute = time_part.split(":")
    return datetime(int(year), int(month), int(day), int(hour), int(minute))


def sort_tasks(tasks_dict: Dict) -> List:
    items = list(tasks_dict.values())
    items.sort(
        key=lambda task: (
            task["Состояние"],
            parse_datetime(task["Начало выполнения"]),
            task["Длительность"],
        )
    )
    return items


@app.get("/", response_class=HTMLResponse)
async def get_html_page():
    with open("templates/index.html", "r", encoding="utf-8") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content)


@app.get("/api/tasks")
async def get_list_task():
    sorted_tasks = sort_tasks(tasks)
    return {"message": sorted_tasks}


@app.put("/api/tasks/{task_id}")
async def update_task_status(task_id: str, data: Dict[str, Any] = Body(...)):
    if task_id in tasks:
        tasks[task_id]["Состояние"] = data.get("Состояние", tasks[task_id]["Состояние"])
        return {"success": True, "message": "Статус задачи обновлен"}
    return {"success": False, "message": "Задача не найдена"}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
