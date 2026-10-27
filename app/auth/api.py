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
import logging

# Setup logger for API errors
logger = logging.getLogger(__name__)

AuthRoutes = APIRouter()
MAX_FILE_SIZE = 5 * 1024 * 1024
UPLOAD_DIR = Path("static/profiles")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@AuthRoutes.post("/register/")
def register(user: UserCreate, db: Session = Depends(get_session)):
    """
    Register a new user account.
    """
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        hashed_pwd = hash_password(user.password)
        
        new_user = User(
            username=user.username,
            email=user.email,
            hashed_password=hashed_pwd
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return {"message": "User registered successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error registering user with email {user.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during registration: {str(e)}"
        )

@AuthRoutes.post("/login/", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_session)):
    """
    Authenticate user and return JWT access token.
    """
    try:
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during login for user {form_data.username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during login: {str(e)}"
        )

@AuthRoutes.post("/logout/")
async def logout(token: str = Depends(oauth2_scheme), db: Session = Depends(get_session)):
    """
    Logout user by blacklisting the active token.
    """
    try:
        # Check if token is already blacklisted
        existing = db.query(RevokedToken).filter(RevokedToken.token == token).first()
        if existing:
            raise HTTPException(status_code=400, detail="Already logged out")
        
        # Add token to blacklist
        db_token = RevokedToken(token=token)
        db.add(db_token)
        db.commit()
        
        return {"message": "Successfully logged out"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error during logout: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during logout: {str(e)}"
        )

@AuthRoutes.get("/user/", response_model=UserPublic)
def get_user_profile(current_user: User = Depends(get_current_user)):
    """
    Retrieve the profile of the currently authenticated user.
    """
    try:
        return current_user
    except Exception as e:
        logger.error(f"Error fetching profile for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching user profile: {str(e)}"
        )

@AuthRoutes.patch("/user/photo/", response_model=UserPublic)
async def upload_profile_photo(
    request: Request, 
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Upload a new profile photo with type & size validation, 
    deleting the old one from disk if it exists.
    """
    new_file_path = None
    try:
        # 1. Validate MIME type
        allowed_content_types = ["image/jpeg", "image/png", "image/webp"]
        if file.content_type not in allowed_content_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed types are: {', '.join(allowed_content_types)}"
            )

        # 2. Validate File Size
        file.file.seek(0, os.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)  # Reset file pointer back to the beginning

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
            except Exception as old_file_error:
                logger.warning(f"Could not delete old profile photo: {old_file_error}")

        # 4. Create unique filename and save new file
        file_extension = Path(file.filename).suffix if file.filename else ".jpg"
        unique_filename = f"user_{current_user.id}_{os.urandom(6).hex()}{file_extension}"
        new_file_path = UPLOAD_DIR / unique_filename

        try:
            with new_file_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as file_save_error:
            logger.error(f"File write failed: {str(file_save_error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not save the uploaded file."
            )
            
        # 5. Update Database
        base_url = str(request.base_url).rstrip("/")
        old_db_photo = current_user.profile_photo # Keep backup in case of DB rollback
        current_user.profile_photo = f"{base_url}/static/profiles/{unique_filename}"
        
        db.add(current_user)
        db.commit()
        db.refresh(current_user)
        
        return current_user
    except HTTPException:
        # Cleanup newly written file if validation or database error occurred after save
        if new_file_path and new_file_path.exists():
            try:
                new_file_path.unlink()
            except Exception:
                pass
        raise
    except Exception as e:
        db.rollback()
        if new_file_path and new_file_path.exists():
            try:
                new_file_path.unlink()
            except Exception:
                pass
        logger.error(f"Error uploading profile photo for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while uploading profile photo: {str(e)}"
        )