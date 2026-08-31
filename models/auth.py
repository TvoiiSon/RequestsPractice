from typing import Literal
from pydantic import BaseModel, EmailStr, Field, ConfigDict

class RegisterRequest(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    password: str = Field(min_length=6)
    phone: str | None = None

class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    model_config = ConfigDict(extra="forbid")
    access_token: str
    token_type: Literal["bearer"]
