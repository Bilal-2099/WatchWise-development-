from fastapi import Depends, HTTPException, status, APIRouter, FastAPI, Path, Query
from sqlmodel import Session, select
from typing import List, Optional
from app.auth.security import get_current_user
from app.database import get_session
from app.models import User, DiaryEntryCreate, DiaryEntry, DiaryEntryPublic, DiaryEntryUpdate, Watched
from app.service import remove_item_from_watchlist, add_item_to_watched
from sqlalchemy import func
from app.discover.services.search import get_rec_shows, get_recs_movies, get_show_minor, get_movie_minor
import logging

# Setup logger for API errors
logger = logging.getLogger(__name__)

DiaryEntryRoutes = APIRouter()

def _safe_get(obj, key, default=None):
    """Helper to safely get values from TMDb objects/dicts whether they act as dicts or attributes."""
    try:
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)
    except Exception:
        return default

def validate_media_type(media_type: str):
    if media_type not in ["movie", "tv"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="media_type must be either 'movie' or 'tv'."
        )

@DiaryEntryRoutes.get("/health")
async def root():
    return {"message": "Just starting"}

@DiaryEntryRoutes.post("/create", response_model=DiaryEntryPublic, status_code=status.HTTP_201_CREATED)
def create_diary_entry(
    entry_in: DiaryEntryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Log a new watch event to the user's diary, ensure it is recorded 
    in their Watched history, and remove it from their watchlist.
    """
    try:
        validate_media_type(entry_in.media_type)

        existing_entry_query = select(DiaryEntry).where(
            DiaryEntry.user_id == current_user.id,
            DiaryEntry.tmdb_id == entry_in.tmdb_id,
            DiaryEntry.media_type == entry_in.media_type
        )
        has_watched_before = db.exec(existing_entry_query).first() is not None
        
        entry_data = entry_in.model_dump()

        if has_watched_before:
            entry_data["is_rewatch"] = True

        db_entry = DiaryEntry(**entry_data, user_id=current_user.id)
        db.add(db_entry)

        add_item_to_watched(db, current_user.id, entry_in.tmdb_id, entry_in.media_type)
        remove_item_from_watchlist(db, current_user.id, entry_in.tmdb_id, entry_in.media_type)

        db.commit()
        db.refresh(db_entry)
        return db_entry
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating diary entry for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating the diary entry: {str(e)}"
        )

@DiaryEntryRoutes.get("/", response_model=List[DiaryEntryPublic], status_code=status.HTTP_200_OK)
def get_diary_entries(
    tmdb_id: Optional[int] = Query(None, description="Filter by specific TMDB ID"),
    media_type: Optional[str] = Query(None, description="Filter by 'movie' or 'tv'"),
    limit: int = Query(20, ge=1, le=100, description="Number of entries to return"),
    offset: int = Query(0, ge=0, description="Number of entries to skip"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Retrieve the logged-in user's diary history,
    sorted newest watch date first.
    """
    try:
        statement = select(DiaryEntry).where(DiaryEntry.user_id == current_user.id)

        if tmdb_id is not None:
            statement = statement.where(DiaryEntry.tmdb_id == tmdb_id)

        if media_type is not None:
            validate_media_type(media_type)
            statement = statement.where(DiaryEntry.media_type == media_type)

        statement = statement.order_by(DiaryEntry.watch_date.desc(), DiaryEntry.created_at.desc())
        statement = statement.offset(offset).limit(limit)
        entries = db.exec(statement).all()
        return entries
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching diary entries for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching diary entries: {str(e)}"
        )

@DiaryEntryRoutes.get("/{entry_id}", response_model=DiaryEntryPublic, status_code=status.HTTP_200_OK)
def get_diary_entry(
    entry_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Retrieve a single diary entry by its ID.
    """
    try:
        entry = db.get(DiaryEntry, entry_id)
        
        if not entry or entry.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diary entry not found."
            )
            
        return entry
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching diary entry {entry_id} for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching the diary entry: {str(e)}"
        )

@DiaryEntryRoutes.patch("/update/{entry_id}", response_model=DiaryEntryPublic, status_code=status.HTTP_200_OK)
def update_diary_entry(
    entry_id: int,
    entry_update: DiaryEntryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Update specific fields (rating, review, watch date, rewatch status) of a diary entry.
    """
    try:
        entry = db.get(DiaryEntry, entry_id)
        
        if not entry or entry.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diary entry not found."
            )
            
        update_data = entry_update.model_dump(exclude_unset=True)
        
        for key, value in update_data.items():
            setattr(entry, key, value)
            
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating diary entry {entry_id} for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating the diary entry: {str(e)}"
        )

@DiaryEntryRoutes.delete("/delete/{entry_id}", status_code=status.HTTP_200_OK)
def delete_diary_entry(
    entry_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Delete a diary entry completely.
    """
    try:
        entry = db.get(DiaryEntry, entry_id)
        
        if not entry or entry.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Diary entry not found."
            )
            
        db.delete(entry)
        db.commit()
        return {"message": "Diary entry deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting diary entry {entry_id} for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while deleting the diary entry: {str(e)}"
        )

@DiaryEntryRoutes.get("/media-entries/", response_model=List[DiaryEntryPublic], status_code=status.HTTP_200_OK)
def get_diary_entries_by_media_query(
    tmdb_id: int = Query(..., description="The TMDB ID of the movie or TV show"),
    media_type: str = Query(..., description="Either 'movie' or 'tv'"),
    limit: int = Query(20, ge=1, le=100, description="Number of entries to return"),
    offset: int = Query(0, ge=0, description="Number of entries to skip"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Retrieve all diary entries for a specific movie or TV show via query parameters.
    """
    try:
        validate_media_type(media_type)

        statement = select(DiaryEntry).where(
            DiaryEntry.user_id == current_user.id,
            DiaryEntry.tmdb_id == tmdb_id,
            DiaryEntry.media_type == media_type
        ).order_by(DiaryEntry.watch_date.desc(), DiaryEntry.created_at.desc())

        statement = statement.offset(offset).limit(limit)
        entries = db.exec(statement).all()
        return entries
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching media entries for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching media diary entries: {str(e)}"
        )

@DiaryEntryRoutes.get("/you-liked/", status_code=status.HTTP_200_OK)
def get_random_high_rated_recommendation(
    media_type: Optional[str] = Query(None, description="Filter by 'movie' or 'tv'"),
    min_rating: float = Query(8.0, description="Minimum rating threshold to consider 'high rated'"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Get a random high-rated diary entry for the user, and return recommendations 
    for it that the user has not watched yet. 
    Returns {"results": None} if no entry or recommendation is found.
    """
    try:
        if media_type and media_type not in ["movie", "tv"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="media_type must be either 'movie' or 'tv'."
            )

        # 1. Base query for user's diary entries meeting the high rating threshold
        statement = select(DiaryEntry).where(
            DiaryEntry.user_id == current_user.id,
            DiaryEntry.rating >= min_rating
        )
        
        if media_type:
            statement = statement.where(DiaryEntry.media_type == media_type)
            
        statement = statement.order_by(func.random())
        high_rated_entry = db.exec(statement).first()

        # If no entry matches, return {"results": None} as requested
        if not high_rated_entry:
            return {"results": None}

        # 2. Fetch all tmdb_ids of items the user has already logged/watched 
        watched_tmdb_ids = set(
            db.exec(
                select(DiaryEntry.tmdb_id).where(DiaryEntry.user_id == current_user.id)
            ).all()
        )

        # 3. Fetch details and raw recommendations based on media type safely
        if high_rated_entry.media_type == "movie":
            details = get_movie_minor(high_rated_entry.tmdb_id)
            rec_data = get_recs_movies(high_rated_entry.tmdb_id, limit=20)
        else:
            details = get_show_minor(high_rated_entry.tmdb_id)
            rec_data = get_rec_shows(high_rated_entry.tmdb_id, limit=20)

        details_results = _safe_get(details, "results", {})
        media_name = _safe_get(details_results, "title") or _safe_get(details_results, "name")
        raw_recommendations = _safe_get(rec_data, "results", []) or []

        # 4. Filter out recommendations that the user has already watched
        filtered_recommendations = [
            item for item in raw_recommendations 
            if _safe_get(item, "id") not in watched_tmdb_ids
        ]

        # If no unwatched recommendations are left, return {"results": None}
        if not filtered_recommendations:
            return {"results": None}

        # Limit to top 10 final recommendations
        final_recommendations = filtered_recommendations[:10]

        return {
            "id": high_rated_entry.id,
            "media_type": high_rated_entry.media_type,
            "tmdb_id": high_rated_entry.tmdb_id,
            "media_name": media_name,
            "rating": high_rated_entry.rating,
            "recommendations": final_recommendations
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching high-rated recommendation for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching your recommendation: {str(e)}"
        )