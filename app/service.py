from fastapi import Depends, HTTPException, status, APIRouter, FastAPI, Path, Query
from sqlmodel import Session, select
from typing import List, Optional
from app.auth.security import get_current_user
from app.database import get_session
from app.models import User, Watchlist, Watched

def remove_item_from_watchlist(db: Session, user_id: int, tmdb_id: int, media_type: str):
    """
    Helper function to remove an item from the user's watchlist if it exists.
    """
    watchlist_item = db.exec(
        select(Watchlist).where(
            Watchlist.user_id == user_id,
            Watchlist.tmdb_id == tmdb_id,
            Watchlist.media_type == media_type
        )
    ).first()
    
    if watchlist_item:
        db.delete(watchlist_item)

def add_item_to_watched(db: Session, user_id: int, tmdb_id: int, media_type: str):
    """
    Helper function to automatically add an item to the user's watched history 
    if it isn't already logged there.
    """
    watched_record = db.exec(
        select(Watched).where(
            Watched.user_id == user_id,
            Watched.tmdb_id == tmdb_id,
            Watched.media_type == media_type
        )
    ).first()

    if not watched_record:
        db_watched = Watched(
            user_id=user_id,
            tmdb_id=tmdb_id,
            media_type=media_type
        )
        db.add(db_watched)