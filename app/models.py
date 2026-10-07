from datetime import datetime, timezone, date
from typing import Optional, Literal
from sqlmodel import Field, SQLModel, Relationship
from pydantic import BaseModel
from sqlalchemy.orm import Mapped

# User
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True) # Should be unique
    email: str = Field(index=True, unique=True) # Should be unique
    hashed_password: str
    profile_photo: Optional[str] = Field(default=None) # It is optional cause I am still thinking about it
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc)) # Just to when user is added

class UserPublic(BaseModel):
    id: int
    username: str
    email: str
    profile_photo: Optional[str] = None
    created_at: datetime

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

#Access Token
class Token(BaseModel):
    access_token: str
    token_type: str

# For logging out
class RevokedToken(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    token: str = Field(index=True)

# Watchlist
class Watchlist(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True) # Foreign key from User class
    tmdb_id: int # We will get this from TMDB
    media_type: str # "movie" or "tv"
    added_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc)) # Just to when user adds

class WatchlistCreate(BaseModel):
    tmdb_id: int
    media_type: str = Field(..., description="Must be 'movie' or 'tv'")

# Dairy/Review
class DiaryEntry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True) # Foreign key from User class
    tmdb_id: int # We will get this from TMDB
    media_type: str # "movie" or "tv"
    rating: Optional[float] = Field(default=None, ge=0.5, le=10.0, description="Star rating from 0.5 to 10.0")
    review_text: Optional[str] = None
    watch_date: date = Field(default_factory=date.today)
    is_rewatch: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc)) # Just to when user adds

class DiaryEntryCreate(SQLModel):
    tmdb_id: int
    media_type: str
    rating: Optional[float] = Field(default=None, ge=0.5, le=10.0)
    review_text: Optional[str] = None
    watch_date: date = Field(default_factory=date.today)
    is_rewatch: bool = Field(default=False)

class DiaryEntryUpdate(SQLModel):
    rating: Optional[float] = Field(default=None, ge=0.5, le=10.0)
    review_text: Optional[str] = None
    watch_date: Optional[date] = None
    is_rewatch: Optional[bool] = None

class DiaryEntryPublic(DiaryEntryCreate):
    id: int
    user_id: int
    created_at: datetime

class CustomList(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    title: str = Field(index=True)
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ListItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    list_id: int = Field(foreign_key="customlist.id", index=True)
    tmdb_id: int
    media_type: str # "movie" or "tv"
    added_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Watched(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    tmdb_id: int
    media_type: str # "movie" or "tv"
    watched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CustomListCreate(SQLModel):
    title: str
    description: Optional[str] = None

class CustomListUpdate(SQLModel):
    title: Optional[str] = None
    description: Optional[str] = None

class CustomListPublic(CustomListCreate):
    id: int
    user_id: int
    created_at: datetime

# List Item Schemas
class ListItemCreate(SQLModel):
    tmdb_id: int
    media_type: str = Field(..., description="Must be 'movie' or 'tv'")

class ListItemPublic(ListItemCreate):
    id: int
    list_id: int
    added_at: datetime

# Watched Schemas
class WatchedCreate(SQLModel):
    tmdb_id: int
    media_type: str = Field(..., description="Must be 'movie' or 'tv'")

class WatchedPublic(WatchedCreate):
    id: int
    user_id: int
    watched_at: datetime