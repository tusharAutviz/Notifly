from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from app.core.config import settings
from app.db.session import SessionLocal
from app.db.models.user import User
from app.core.security import verify_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# DB SESSION DEPENDENCY
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Current User Dependency (Authenticated)
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    payload = verify_token(token)
    if not token:
        raise  credentials_exception
    
    user = db.query(User).filter(User.email == payload.get("sub")).first()
    if not user:
        raise credentials_exception
    
    return user


