# from tmdbv3api import TMDb, Movie, TV, Person, Discover, Genre
# from dotenv import load_dotenv
# import os

# load_dotenv()
# discover = Discover()
# genre_api = Genre()
# show_api = TV()
# tmdb_api = os.getenv('API_Key')
# tmdb = TMDb()
# movie = Movie()
# tmdb.api_key = tmdb_api
# tmdb.language = 'en' 
# base_image_url = "https://image.tmdb.org/t/p/w500"

from fastapi import FastAPI, Depends, HTTPException, Query, Path
from sqlmodel import Session, select
from typing import List
from app.database import get_session
from app.models import User, Watchlist, DiaryEntry

# --- WATCHLIST ENDPOINTS ---

@app.post("/watchlist", status_code=201)
def add_to_watchlist(entry: Watchlist, db: Session = Depends(get_session)):
    """Add a movie or show to a user's watchlist."""
    # Optional: Check if user exists first
    user = db.get(User, entry.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return {"status": "success", "data": entry}


@app.get("/watchlist/{user_id}", response_model=List[Watchlist])
def get_user_watchlist(
    user_id: int = Path(..., description="The ID of the user"),
    db: Session = Depends(get_session)
):
    """Retrieve all items in a user's watchlist."""
    statement = select(Watchlist).where(Watchlist.user_id == user_id)
    watchlist_items = db.exec(statement).all()
    return watchlist_items


@app.delete("/watchlist/{watchlist_id}", status_code=200)
def remove_from_watchlist(
    watchlist_id: int = Path(..., description="The ID of the watchlist item to remove"),
    db: Session = Depends(get_session)
):
    """Remove an item from the watchlist by its entry ID."""
    item = db.get(Watchlist, watchlist_id)
    if not item:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
        
    db.delete(item)
    db.commit()
    return {"status": "success", "message": "Item removed from watchlist"}


# DIARY & REVIEW ENDPOINTS
@app.post("/diary/log", status_code=201)
def log_media(entry: DiaryEntry, db: Session = Depends(get_session)):
    """Log a watched movie or show with a rating and review."""
    user = db.get(User, entry.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return {"status": "success", "data": entry}


@app.get("/diary/{user_id}", response_model=List[DiaryEntry])
def get_user_diary(
    user_id: int = Path(..., description="The ID of the user"),
    limit: int = Query(20, ge=1, le=100, description="Number of diary entries to return"),
    db: Session = Depends(get_session)
):
    """Retrieve a user's viewing history/diary entries, sorted by most recent watch date."""
    statement = (
        select(DiaryEntry)
        .where(DiaryEntry.user_id == user_id)
        .order_by(DiaryEntry.watch_date.desc())
        .limit(limit)
    )
    entries = db.exec(statement).all()
    return entries