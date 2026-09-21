from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import verify_password, get_password_hash, create_access_token
from datetime import timedelta
from app.core.config import settings

class AuthService:
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> User:
        user = db.query(User).filter(User.email == email).first()
        if not user or not verify_password(password, user.password_hash):
            return None
        return user
    
    @staticmethod
    def create_access_token_for_user(user: User) -> str:
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role},
            expires_delta=access_token_expires
        )
        return access_token
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> User:
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def create_user(db: Session, name: str, email: str, password: str, role: str) -> User:
        hashed_password = get_password_hash(password)
        user = User(
            name=name,
            email=email,
            password_hash=hashed_password,
            role=role,
            active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user