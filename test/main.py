from tmdbv3api import TMDb, Movie, TV, Person, Discover, Genre
from dotenv import load_dotenv
import os

load_dotenv()

tmdb_api = os.getenv('API_Key')
tmdb = TMDb()
tmdb.api_key = tmdb_api
tmdb.language = 'en' 
base_image_url = "https://image.tmdb.org/t/p/w500"

# trending = Trending()
movie = Movie()
show = TV()
discover = Discover()
genre_api = Genre()


from fastapi import HTTPException, status
from passlib.context import CryptContext
from pydantic import BaseModel

# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Pydantic schemas for request payloads
class UserRegister(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str


# --- AUTHENTICATION ROUTES ---

@app.post("/auth/register", status_code=201)
def register_user(payload: UserRegister, db: Session = Depends(get_session)):
    """Register a new user with a hashed password."""
    # Check if email or username already exists
    existing_user = db.exec(
        select(User).where((User.email == payload.email) | (User.username == payload.username))
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    # Create new user instance
    new_user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password)
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Hide password in response
    return {
        "status": "success",
        "message": "User registered successfully",
        "user": {
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email
        }
    }


@app.post("/auth/login", status_code=200)
def login_user(payload: UserLogin, db: Session = Depends(get_session)):
    """Authenticate a user and return basic profile info."""
    user = db.exec(select(User).where(User.email == payload.email)).first()
    
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    return {
        "status": "success",
        "message": "Login successful",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    }