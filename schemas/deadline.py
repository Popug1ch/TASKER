from pydantic import BaseModel, ConfigDict
from datetime import datetime


class DeadlineIn(BaseModel):
    name: str
    deadline_time: datetime
    is_completed: bool = False


class DeadlineAdd(DeadlineIn):
    pass


class DeadlineUpdate(DeadlineIn):
    pass


class Deadline(DeadlineIn):
    id: int
    model_config = ConfigDict(from_attributes=True)
