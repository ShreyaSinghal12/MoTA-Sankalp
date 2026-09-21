import sys
sys.path.insert(0, '/home/claude' if '/home/claude' in __file__ else '.')

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.auth import AuthService
from app.models.user import RoleEnum

def seed_admin_user():
    db = SessionLocal()
    
    try:
        existing_admin = AuthService.get_user_by_email(db, "admin@mota.gov.in")
        if existing_admin:
            print("Admin user already exists")
            return
        
        admin_user = AuthService.create_user(
            db=db,
            name="MoTA Admin",
            email="admin@mota.gov.in",
            password="ChangeMe@123",
            role=RoleEnum.ADMIN
        )
        print(f"Created admin user: {admin_user.email}")
        
        ministry_user = AuthService.create_user(
            db=db,
            name="Ministry Officer",
            email="ministry@mota.gov.in",
            password="ChangeMe@123",
            role=RoleEnum.MINISTRY_NODAL_OFFICER
        )
        print(f"Created ministry user: {ministry_user.email}")
        
        scrutiny_user = AuthService.create_user(
            db=db,
            name="Scrutiny Officer",
            email="scrutiny@mota.gov.in",
            password="ChangeMe@123",
            role=RoleEnum.SCRUTINY_OFFICER
        )
        print(f"Created scrutiny user: {scrutiny_user.email}")
        
    finally:
        db.close()

if __name__ == "__main__":
    seed_admin_user()