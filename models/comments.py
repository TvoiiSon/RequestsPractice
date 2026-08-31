from pydantic import BaseModel, ConfigDict
from datetime import datetime
from .user import UserResponse

class CreateCommentRequest(BaseModel):
    text: str

class CommentResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: int
    text: str
    author: UserResponse
    created_at: datetime
