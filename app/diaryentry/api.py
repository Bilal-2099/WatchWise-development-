from fastapi import Depends, HTTPException, status, APIRouter, FastAPI, Path, Query
from sqlmodel import Session, select
from typing import List, Optional
from app.auth.security import get_current_user
from app.database import get_session
from app.models import User, DiaryEntryCreate, DiaryEntry, DiaryEntryPublic, DiaryEntryUpdate

DiaryEntryRoutes = APIRouter()

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
    Log a new watch event to the user's diary.
    """
    validate_media_type(entry_in.media_type)
    # Check if the user has logged this movie/show previously
    existing_entry_query = select(DiaryEntry).where(
        DiaryEntry.user_id == current_user.id,
        DiaryEntry.tmdb_id == entry_in.tmdb_id,
        DiaryEntry.media_type == entry_in.media_type
    )
    has_watched_before = db.exec(existing_entry_query).first() is not None
    print(has_watched_before)
    # Convert Pydantic model to dictionary
    entry_data = entry_in.model_dump()
   

    # Automatically set is_rewatch to True if they've watched it before
    if has_watched_before:
        entry_data["is_rewatch"] = True

    print(entry_data)

    db_entry = DiaryEntry(
        **entry_data,
        user_id=current_user.id
    )
    
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry

@DiaryEntryRoutes.get("/", response_model=List[DiaryEntryPublic], status_code=status.HTTP_200_OK)
def get_diary_entries(
    tmdb_id: Optional[int] = Query(None, description="Filter by specific TMDB ID"),
    media_type: Optional[str] = Query(None, description="Filter by 'movie' or 'tv'"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Retrieve the logged-in user's diary history, sorted newest watch date first.
    """
    statement = select(DiaryEntry).where(DiaryEntry.user_id == current_user.id)
    
    # Optional filters if user wants to see history for a specific movie/show
    if tmdb_id is not None:
        statement = statement.where(DiaryEntry.tmdb_id == tmdb_id)
    if media_type is not None:
        statement = statement.where(DiaryEntry.media_type == media_type)
        
    # Sort by watch date descending (most recent diary entries first)
    statement = statement.order_by(DiaryEntry.watch_date.desc(), DiaryEntry.created_at.desc())
    
    entries = db.exec(statement).all()
    return entries

@DiaryEntryRoutes.get("/{entry_id}", response_model=DiaryEntryPublic, status_code=status.HTTP_200_OK)
def get_diary_entry(
    entry_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Retrieve a single diary entry by its ID.
    """
    entry = db.get(DiaryEntry, entry_id)
    
    if not entry or entry.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diary entry not found."
        )
        
    return entry

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

@DiaryEntryRoutes.delete("/delete/{entry_id}", status_code=status.HTTP_200_OK)
def delete_diary_entry(
    entry_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Delete a diary entry completely.
    """
    entry = db.get(DiaryEntry, entry_id)
    
    if not entry or entry.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diary entry not found."
        )
        
    db.delete(entry)
    db.commit()
    return None

@DiaryEntryRoutes.get("/media-entries/", response_model=List[DiaryEntryPublic], status_code=status.HTTP_200_OK)
def get_diary_entries_by_media_query(
    tmdb_id: int = Query(..., description="The TMDB ID of the movie or TV show"),
    media_type: str = Query(..., description="Either 'movie' or 'tv'"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Retrieve all diary entries for a specific movie or TV show via query parameters.
    """
    validate_media_type(media_type)

    statement = select(DiaryEntry).where(
        DiaryEntry.user_id == current_user.id,
        DiaryEntry.tmdb_id == tmdb_id,
        DiaryEntry.media_type == media_type
    ).order_by(DiaryEntry.watch_date.desc(), DiaryEntry.created_at.desc())

    entries = db.exec(statement).all()
    return entries