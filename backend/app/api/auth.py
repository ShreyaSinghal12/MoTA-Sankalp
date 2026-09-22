from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_current_user, verify_password
from app.db.database import get_db
from app.models.models import User
from app.schemas.schemas import LoginRequest, TokenResponse, user_to_dict
from app.services import audit_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email.strip().lower()).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(401, "Invalid email or password")
    audit_service.log(db, None, "USER_LOGIN", user.email, {"role": user.role})
    return {"access_token": create_access_token(user.email, user.role), "token_type": "bearer", "user": user_to_dict(user)}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return user_to_dict(user)
