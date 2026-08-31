from pydantic import RootModel, BaseModel, ConfigDict
from typing import Generic, TypeVar

class MessageResponse(RootModel[str]):
    pass

class EmptyResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    detail: str

T = TypeVar("T")

class Page(BaseModel, Generic[T]):
    model_config = ConfigDict(extra="forbid")
    items: list[T]
    total: int
    page: int
    per_page: int
    total_pages: int
    