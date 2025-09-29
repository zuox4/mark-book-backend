from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None

class UserLogin(BaseModel):
    email: str
    external_id: int

class UserCreate(BaseModel):
    email: str
    external_id: int
    display_name: Optional[str] = None

class RegisterRequest(BaseModel):

    email: str
    password: str
    user_data: dict = None

class LoginRequest(BaseModel):
    email: str
    password: str

class VerifyEmailRequest(BaseModel):
    token: str

class UserResponse(BaseModel):
    email: str
    display_name: Optional[str] = None


