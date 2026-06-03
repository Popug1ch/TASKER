from pydantic import BaseModel, ConfigDict
from datetime import datetime


class STaskIn(BaseModel):
    name: str
    start_time: datetime
    end_time: datetime
    category: str
    priority: str
    is_completed: bool = False


class STaskAdd(STaskIn):
    pass


class STaskUpdate(STaskIn):
    pass


class STask(STaskIn):
    id: int
    duration: int
    model_config = ConfigDict(from_attributes=True)
