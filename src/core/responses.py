from typing import Any

from pydantic import BaseModel


class NotReadResponse(BaseModel):
    status: int
    detail: dict | str | Any
