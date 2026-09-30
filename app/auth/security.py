import bcrypt
from fastapi import Depends, HTTPException, status
from app.database import get_session
from fastapi.security import OAuth2PasswordBearer
from app.models import User, RevokedToken, Token, UserCreate
import jwt
from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from sqlmodel import Session, select

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def hash_password(password: str) -> str:
    # Encode password to bytes, generate salt, and hash it
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Check plain password against the stored hash
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), 
        hashed_password.encode("utf-8")
    )

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_session)):
    is_revoked = db.exec(select(RevokedToken).where(RevokedToken.token == token)).first()
    if is_revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked (logged out)",
            headers={"WWW-Authenticate": "Bearer"},
        )

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
        
    statement = select(User).where(User.email == email)
    user = db.exec(statement).first()
    
    if user is None:
        raise credentials_exception
        
    return user