from fastapi import FastAPI, Depends, HTTPException, status, APIRouter, File, UploadFile, Request
from app.database import get_session
from fastapi.security import OAuth2PasswordRequestForm
import jwt
import shutil
import os
from pathlib import Path
from sqlmodel import Session
from datetime import datetime, timezone, timedelta
from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from app.models import User, RevokedToken, Token, UserCreate, UserPublic
from .security import verify_password, hash_password, oauth2_scheme, get_current_user

AuthRoutes = APIRouter()
MAX_FILE_SIZE = 5 * 1024 * 1024
UPLOAD_DIR = Path("static/profiles")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

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

@AuthRoutes.post("/login/", response_model=Token)
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
    # access_token = create_access_token(data={"sub": user.email})
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


@AuthRoutes.get("/user/", response_model=UserPublic)
def get_user_profile(current_user: User = Depends(get_current_user)):
    """
    Retrieve the profile of the currently authenticated user.
    """
    return current_user


@AuthRoutes.patch("/user/photo/", response_model=UserPublic)
async def upload_profile_photo(
    request: Request, # Inject the request object
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Upload a new profile photo with type & size validation, 
    deleting the old one from disk if it exists.
    """
    # 1. Validate MIME type
    allowed_content_types = ["image/jpeg", "image/png", "image/webp"]
    if file.content_type not in allowed_content_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types are: {', '.join(allowed_content_types)}"
        )

    # 2. Validate File Size
    # FastAPI's UploadFile stores spooled files; we can check size using seek/tell or read chunk length
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)  # Reset file pointer back to the beginning!

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds the maximum limit of {MAX_FILE_SIZE / (1024 * 1024)}MB"
        )

    # 3. Delete the old profile photo from disk if it exists
    if current_user.profile_photo:
        try:
            if "/static/" in current_user.profile_photo:
                relative_path = current_user.profile_photo.split("/static/")[-1]
                old_file_path = Path("static") / relative_path
                
                if old_file_path.exists() and old_file_path.is_file():
                    old_file_path.unlink()
        except Exception as e:
            print(f"Could not delete old profile photo: {e}")

    # 4. Create unique filename and save new file
    file_extension = Path(file.filename).suffix
    unique_filename = f"user_{current_user.id}_{os.urandom(6).hex()}{file_extension}"
    new_file_path = UPLOAD_DIR / unique_filename

    try:
        with new_file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save the uploaded file."
        )
        
    # 5. Update Database
    base_url = str(request.base_url).rstrip("/")
    current_user.profile_photo = f"{base_url}/static/profiles/{unique_filename}"
    
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    
    return current_user