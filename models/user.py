from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr

class UserResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: int
    email: EmailStr
    first_name: str
    last_name: str
    phone: str | None = None
    photo_path: str | None = None
    created_at: datetime

class UserUpdateRequest(BaseModel):
    email: EmailStr | None = None
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    password: str | None = None
