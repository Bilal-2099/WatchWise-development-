from fastapi import Depends, HTTPException, status, APIRouter, FastAPI, Path, Query
from sqlmodel import Session, select
from app.auth.security import get_current_user
from app.database import get_session
from app.models import User, WatchedPublic, WatchedCreate, Watched
from tmdbv3api import TMDb, Movie, TV
from app.config import tmdb_api, base_image_url
from app.service import remove_item_from_watchlist

tmdb = TMDb()
tmdb.api_key = tmdb_api
tmdb.language = 'en' 

WatchedRoutes = APIRouter()
movie_api = Movie()
show_api = TV()

# Mark as Watched
@WatchedRoutes.post("/add/", response_model=WatchedPublic, status_code=status.HTTP_201_CREATED)
def mark_as_watched(
    watched_in: WatchedCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Mark a movie or TV show as watched.
    """
    if watched_in.media_type not in ["movie", "tv"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="media_type must be either 'movie' or 'tv'."
        )

    # Check if already marked as watched
    existing = db.exec(
        select(Watched).where(
            Watched.user_id == current_user.id,
            Watched.tmdb_id == watched_in.tmdb_id,
            Watched.media_type == watched_in.media_type
        )
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Item is already marked as watched."
        )

    db_watched = Watched(**watched_in.model_dump(), user_id=current_user.id)
    db.add(db_watched)

    # Remove from watchlist
    remove_item_from_watchlist(db, current_user.id, watched_in.tmdb_id, watched_in.media_type)

    db.commit()
    db.refresh(db_watched)
    return db_watched

# Remove from Watched
@WatchedRoutes.delete("/{watched_id}/", status_code=status.HTTP_204_NO_CONTENT)
def remove_watched(
    watched_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Remove a movie or TV show from the user's watched history by its watched ID.
    """
    db_watched = db.get(Watched, watched_id)
    if not db_watched:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watched record not found."
        )
    
    if db_watched.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this record."
        )
    
    db.delete(db_watched)
    db.commit()
    return { "message": "Successfully removed from watched history." }

@WatchedRoutes.get("/", status_code=status.HTTP_200_OK)
def get_user_watched_list(
    limit: int = Query( 10, ge=1, le=100, description="Number of entries to return"),
    offset: int = Query(0, ge=0, description="Number of entries to skip"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Fetch the logged-in user's watched history and enrich it with live data from TMDB.
    """
    statement = select(Watched).where(Watched.user_id == current_user.id)
    statement = statement.offset(offset).limit(limit)
    watched_items = db.exec(statement).all()
    enriched_results = []

    for item in watched_items:
        try:
            if item.media_type == "movie":
                tmdb_data = movie_api.details(item.tmdb_id)
                title = tmdb_data.get("title")
            else:
                tmdb_data = show_api.details(item.tmdb_id)
                title = tmdb_data.get("name")

            poster_path = tmdb_data.get("poster_path")
            poster_url = base_image_url + poster_path if poster_path else None

            enriched_results.append({
                "watched_id": item.id,
                "id": item.tmdb_id,
                "media_type": item.media_type,
                "title": title,
                "rating": tmdb_data.get("vote_average"),
                "poster": poster_url,
                "watched_at": item.watched_at
            })
        except Exception as e:
            print(f"Could not fetch TMDB details for {item.media_type} ID {item.tmdb_id}: {e}")

    return {"results": enriched_results}

# Check from Watched
@WatchedRoutes.get("/check/", status_code=status.HTTP_200_OK)
def check_watched_status(
    tmdb_id: int = Query(..., description="The TMDB ID of the movie or TV show"),
    media_type: str = Query(..., description="Must be 'movie' or 'tv'"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Check if a specific movie or TV show is marked as watched by the logged-in user.
    Returns the status and the watched_id if it exists.
    """
    if media_type not in ["movie", "tv"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="media_type must be either 'movie' or 'tv'."
        )

    statement = select(Watched).where(
        Watched.user_id == current_user.id,
        Watched.tmdb_id == tmdb_id,
        Watched.media_type == media_type
    )
    watched_item = db.exec(statement).first()

    if watched_item:
        return {
            "is_watched": True,
            "watched_id": watched_item.id
        }
    
    return {
        "is_watched": False,
        "watched_id": None
    }

