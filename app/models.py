from datetime import datetime, date
from typing import Optional
from sqlmodel import Field, SQLModel

# User
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: str = Field(index=True, unique=True)
    profile_photo: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Watchlist
class Watchlist(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    tmdb_id: int
    media_type: str # "movie" or "tv"
    added_at: datetime = Field(default_factory=datetime.utcnow)

# Dairy/Review
class DiaryEntry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    tmdb_id: int
    media_type: str # "movie" or "tv"
    rating: float = Field(description="Star rating from 0.5 to 10.0")
    review_text: Optional[str] = Field(default=None)
    watch_date: date = Field(default_factory=date.today)
    is_rewatch: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)