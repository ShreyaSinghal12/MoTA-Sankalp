from pydantic import BaseModel

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    email: str
    role: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    active: bool

    class Config:
        from_attributes = True