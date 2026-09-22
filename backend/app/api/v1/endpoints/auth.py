from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.security import hash_password, create_access_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

USERS_DB = {
    "admin@mota.gov.in": {"hashed": hash_password("admin123"), "role": "ADMIN"},
    "officer@mota.gov.in": {"hashed": hash_password("officer123"), "role": "SCRUTINY_OFFICER"},
}

@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    if req.email not in USERS_DB:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    user = USERS_DB[req.email]
    if not verify_password(req.password, user["hashed"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": req.email, "role": user["role"]})
    return {"access_token": token}

@router.get("/me")
async def get_me(current_user = None):
    return {"email": current_user}
