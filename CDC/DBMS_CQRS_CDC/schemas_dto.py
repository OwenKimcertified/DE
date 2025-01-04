from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class DenormalizedDataSchema(BaseModel):
    id: int
    user_id: int
    user_name: str
    order_id: int
    order_details: str
    updated_at: datetime

    class Config:
        orm_mode = True