from fastapi import Depends, HTTPException, status, APIRouter, FastAPI, Path, Query
from sqlmodel import Session, select
from app.auth.security import get_current_user
from app.database import get_session
from app.models import User, WatchedPublic, WatchedCreate, Watched
from tmdbv3api import TMDb, Movie, TV
from app.config import tmdb_api, base_image_url
from app.service import remove_item_from_watchlist
from typing import Optional
from sqlalchemy import func
from app.discover.services.search import get_rec_shows, get_recs_movies, get_show_minor, get_movie_minor
import logging

# Setup logger for API errors
logger = logging.getLogger(__name__)

tmdb = TMDb()
tmdb.api_key = tmdb_api
tmdb.language = 'en' 

WatchedRoutes = APIRouter()
movie_api = Movie()
show_api = TV()

def _safe_get(obj, key, default=None):
    """Helper to safely get values from TMDb objects whether they act as dicts or attributes."""
    try:
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)
    except Exception:
        return default

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
    try:
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
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error marking item as watched for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while marking as watched: {str(e)}"
        )

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
    try:
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
        return None
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting watched record {watched_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while removing from watched history: {str(e)}"
        )

@WatchedRoutes.get("/", status_code=status.HTTP_200_OK)
def get_user_watched_list(
    limit: int = Query(10, ge=1, le=100, description="Number of entries to return"),
    offset: int = Query(0, ge=0, description="Number of entries to skip"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Fetch the logged-in user's watched history and enrich it with live data from TMDB.
    """
    try:
        statement = select(Watched).where(Watched.user_id == current_user.id)
        statement = statement.offset(offset).limit(limit)
        watched_items = db.exec(statement).all()
        enriched_results = []

        for item in watched_items:
            try:
                if item.media_type == "movie":
                    tmdb_data = movie_api.details(item.tmdb_id)
                    title = _safe_get(tmdb_data, "title")
                else:
                    tmdb_data = show_api.details(item.tmdb_id)
                    title = _safe_get(tmdb_data, "name")

                poster_path = _safe_get(tmdb_data, "poster_path")
                poster_url = f"{base_image_url}{poster_path}" if poster_path else None

                enriched_results.append({
                    "watched_id": item.id,
                    "id": item.tmdb_id,
                    "media_type": item.media_type,
                    "title": title,
                    "rating": _safe_get(tmdb_data, "vote_average", 0.0),
                    "poster": poster_url,
                    "watched_at": item.watched_at
                })
            except Exception as tmdb_error:
                logger.warning(f"Could not fetch TMDB details for watched {item.media_type} ID {item.tmdb_id}: {str(tmdb_error)}")
                enriched_results.append({
                    "watched_id": item.id,
                    "id": item.tmdb_id,
                    "media_type": item.media_type,
                    "title": "Unknown Title",
                    "rating": 0.0,
                    "poster": None,
                    "watched_at": item.watched_at
                })

        return {"results": enriched_results}
    except Exception as e:
        logger.error(f"Error fetching watched list for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching your watched history: {str(e)}"
        )

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
    try:
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking watched status for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while checking watched status: {str(e)}"
        )


@WatchedRoutes.get("/you-watched/", status_code=status.HTTP_200_OK)
def get_random_watched(
    media_type: Optional[str] = Query(None, description="Filter by 'movie' or 'tv'"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Get a random watched item for the logged-in user, along with its details, 
    fetched media name, and 10 recommendations.
    """
    try:
        if media_type and media_type not in ["movie", "tv"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="media_type must be either 'movie' or 'tv'."
            )

        statement = select(Watched).where(Watched.user_id == current_user.id)
        
        if media_type:
            statement = statement.where(Watched.media_type == media_type)
            
        statement = statement.order_by(func.random())
        watched_item = db.exec(statement).first()

        if not watched_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No watched items found."
            )

        # Fetch details and recommendations using your functions based on the item's media_type
        if watched_item.media_type == "movie":
            details = get_movie_minor(watched_item.tmdb_id)
            rec_data = get_recs_movies(watched_item.tmdb_id, limit=10)
        else:
            details = get_show_minor(watched_item.tmdb_id)
            rec_data = get_rec_shows(watched_item.tmdb_id, limit=10)

        media_name = _safe_get(_safe_get(details, "results", {}), "title")

        return {
            "id": watched_item.id,
            "media_type": watched_item.media_type,
            "tmdb_id": watched_item.tmdb_id,
            "media_name": media_name,
            "recommendations": _safe_get(rec_data, "results", [])
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching random watched item for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching random watched item: {str(e)}"
        )