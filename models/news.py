from pydantic import BaseModel, ConfigDict
from .user import UserResponse
from datetime import datetime

class TagResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: int
    name: str

class NewsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: int
    title: str
    subtitle: str | None
    text: str
    image_path: str | None
    author: UserResponse
    tags: list[TagResponse]
    created_at: datetime
    comments_count: int

class CreateNewsRequest(BaseModel):
    title: str
    text: str
    subtitle: str | None = None
    tags: str | None = None
