"""Auth request/response schemas"""

from pydantic import BaseModel


class RegisterRequest(BaseModel):
    email: str
    password: str
    nickname: str


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    id: str
    email: str
    nickname: str
    token: str
