from fastapi import FastAPI, Depends, HTTPException, status, APIRouter
from app.database import get_session
from fastapi.security import OAuth2PasswordRequestForm
import jwt
from datetime import datetime, timezone, timedelta
from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from app.models import User, RevokedToken, Token, UserCreate
from .security import verify_password, hash_password, oauth2_scheme

AuthRoutes = APIRouter()

@AuthRoutes.post("/register/")
def register(user: UserCreate, db: Session = Depends(get_session)):
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pwd = hash_password(user.password)
    
    # Fixed: Pass username and use hashed_password
    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_pwd
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User registered successfully"}

@AuthRoutes.post("/token/", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_session)):
    # OAuth2PasswordRequestForm expects 'username' and 'password' fields (we use email as username)
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create JWT token
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": user.email, "exp": expire}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return {"access_token": encoded_jwt, "token_type": "bearer"}

@AuthRoutes.post("/logout/")
async def logout(token: str = Depends(oauth2_scheme), db: Session = Depends(get_session)):
    # Check if token is already blacklisted
    existing = db.query(RevokedToken).filter(RevokedToken.token == token).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already logged out")
    
    # Add token to blacklist
    db_token = RevokedToken(token=token)
    db.add(db_token)
    db.commit()
    
    return {"message": "Successfully logged out"}