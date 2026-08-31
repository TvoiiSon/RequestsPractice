from pydantic import RootModel, BaseModel, ConfigDict
from typing import Generic, TypeVar, Any

class MessageResponse(RootModel[str]):
    pass

class EmptyResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    detail: str

class ValidationErrorItem(BaseModel):
    type: str
    loc: list[str | int]
    msg: str
    input: Any = None
    ctx: dict | None = None
    url: str | None = None

class ValidationErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    detail: list[ValidationErrorItem]

T = TypeVar("T")

class Page(BaseModel, Generic[T]):
    model_config = ConfigDict(extra="forbid")
    items: list[T]
    total: int
    page: int
    per_page: int
    total_pages: int
