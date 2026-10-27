from fastapi import Depends, HTTPException, status, APIRouter, FastAPI, Path, Query
from sqlmodel import Session, select
from app.auth.security import get_current_user
from app.database import get_session
from app.models import User, Watchlist, WatchlistCreate, WatchedPublic, WatchedCreate, Watched
from tmdbv3api import TMDb, Movie, TV
from app.config import tmdb_api, base_image_url
import logging

# Setup logger for API errors
logger = logging.getLogger(__name__)

tmdb = TMDb()
tmdb.api_key = tmdb_api
tmdb.language = 'en' 

WatchListRoutes = APIRouter()
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

# Add to Watchlist
@WatchListRoutes.post("/add", status_code=status.HTTP_201_CREATED)
def add_to_watchlist(
    item_data: WatchlistCreate, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_session)
):
    """
    Add a movie or TV show to the current user's watchlist using its TMDB ID.
    Prevents adding items that have already been watched or logged in the diary.
    """
    try:
        if item_data.media_type not in ["movie", "tv"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="media_type must be either 'movie' or 'tv'."
            )

        # Check if the item is already in the user's watched history or diary
        watched_record = db.exec(
            select(Watched).where(
                Watched.user_id == current_user.id,
                Watched.tmdb_id == item_data.tmdb_id,
                Watched.media_type == item_data.media_type
            )
        ).first()

        if watched_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already Watched it."
            )

        # Check if already in the watchlist
        statement = select(Watchlist).where(
            Watchlist.user_id == current_user.id,
            Watchlist.tmdb_id == item_data.tmdb_id,
            Watchlist.media_type == item_data.media_type
        )
        existing_item = db.exec(statement).first()

        if existing_item:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="This item is already in your watchlist."
            )

        new_watchlist_item = Watchlist(
            user_id=current_user.id,
            tmdb_id=item_data.tmdb_id,
            media_type=item_data.media_type
        )

        db.add(new_watchlist_item)
        db.commit()
        db.refresh(new_watchlist_item)

        return {"message": "Successfully added to watchlist", "watchlist_item": new_watchlist_item}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding item to watchlist for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while adding to watchlist: {str(e)}"
        )

# Remove from Watchlist
@WatchListRoutes.delete("/remove/{watchlist_id}", status_code=status.HTTP_200_OK)
def remove_from_watchlist(
    watchlist_id: int, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_session)
):
    """
    Remove an item from the user's watchlist by its unique watchlist entry ID.
    """
    try:
        watchlist_item = db.get(Watchlist, watchlist_id)

        if not watchlist_item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watchlist item not found.")

        if watchlist_item.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to delete this item.")

        db.delete(watchlist_item)
        db.commit()

        return {"message": "Successfully removed from watchlist"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error removing watchlist item {watchlist_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while removing from watchlist: {str(e)}"
        )

# Get all Watchlist
@WatchListRoutes.get("/", status_code=status.HTTP_200_OK)
def get_user_watchlist(
    limit: int = Query(10, ge=1, le=100, description="Number of entries to return"),
    offset: int = Query(0, ge=0, description="Number of entries to skip"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Fetch the logged-in user's watchlist and enrich it with live data from TMDB.
    """
    try:
        statement = select(Watchlist).where(Watchlist.user_id == current_user.id)
        statement = statement.offset(offset).limit(limit)
        watchlist_items = db.exec(statement).all()
        enriched_results = []

        for item in watchlist_items:
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
                    "watchlist_id": item.id,
                    "id": item.tmdb_id,
                    "media_type": item.media_type,
                    "title": title,
                    "rating": _safe_get(tmdb_data, "vote_average", 0.0),
                    "poster": poster_url,
                    "added_at": item.added_at
                })
            except Exception as tmdb_error:
                logger.warning(f"Could not fetch TMDB details for {item.media_type} ID {item.tmdb_id}: {str(tmdb_error)}")
                # Append fallback entry so user can still see the watchlist item even if TMDB fails
                enriched_results.append({
                    "watchlist_id": item.id,
                    "id": item.tmdb_id,
                    "media_type": item.media_type,
                    "title": "Unknown Title",
                    "rating": 0.0,
                    "poster": None,
                    "added_at": item.added_at
                })

        return {"results": enriched_results}
    except Exception as e:
        logger.error(f"Error fetching watchlist for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching your watchlist: {str(e)}"
        )

# Check from Watchlist
@WatchListRoutes.get("/check", status_code=status.HTTP_200_OK)
def check_watchlist_status(
    tmdb_id: int = Query(..., description="The TMDB ID of the movie or TV show"),
    media_type: str = Query(..., description="Must be 'movie' or 'tv'"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Check if a specific movie or TV show is in the logged-in user's watchlist.
    Returns the status and the watchlist_id if it exists.
    """
    try:
        if media_type not in ["movie", "tv"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="media_type must be either 'movie' or 'tv'."
            )

        statement = select(Watchlist).where(
            Watchlist.user_id == current_user.id,
            Watchlist.tmdb_id == tmdb_id,
            Watchlist.media_type == media_type
        )
        watchlist_item = db.exec(statement).first()

        if watchlist_item:
            return {
                "in_watchlist": True,
                "watchlist_id": watchlist_item.id
            }
        
        return {
            "in_watchlist": False,
            "watchlist_id": None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking watchlist status for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while checking watchlist status: {str(e)}"
        )