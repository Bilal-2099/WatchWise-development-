from fastapi import Depends, HTTPException, status, APIRouter, FastAPI, Path, Query
from sqlmodel import Session, select
from app.auth.security import get_current_user
from app.database import get_session
from app.models import User, Watchlist, WatchlistCreate, WatchedPublic, WatchedCreate, Watched
from tmdbv3api import TMDb, Movie, TV
from app.config import tmdb_api, base_image_url

tmdb = TMDb()
tmdb.api_key = tmdb_api
tmdb.language = 'en' 

WatchListRoutes = APIRouter()
movie_api = Movie()
show_api = TV()

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

# Remove from Watchlist
@WatchListRoutes.delete("/remove/{watchlist_id}", status_code=status.HTTP_200_OK)
def remove_from_watchlist(watchlist_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_session)):
    """
    Remove an item from the user's watchlist by its unique watchlist entry ID.
    """
    watchlist_item = db.get(Watchlist, watchlist_id)

    if not watchlist_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watchlist item not found.")

    if watchlist_item.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to delete this item.")

    db.delete(watchlist_item)
    db.commit()

    return {"message": "Successfully removed from watchlist"}

# Get all Watchlist
@WatchListRoutes.get("/", status_code=status.HTTP_200_OK)
def get_user_watchlist(
    limit: int = Query( 10, ge=1, le=100, description="Number of entries to return"),
    offset: int = Query(0, ge=0, description="Number of entries to skip"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Fetch the logged-in user's watchlist and enrich it with live data from TMDB.
    """
    statement = select(Watchlist).where(Watchlist.user_id == current_user.id)
    statement = statement.offset(offset).limit(limit)
    watchlist_items = db.exec(statement).all()
    enriched_results = []

    for item in watchlist_items:
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
                "watchlist_id": item.id,
                "id": item.tmdb_id,
                "media_type": item.media_type,
                "title": title,
                "rating": tmdb_data.get("vote_average"),
                "poster": poster_url,
                "added_at": item.added_at
            })
        except Exception as e:
            print(f"Could not fetch TMDB details for {item.media_type} ID {item.tmdb_id}: {e}")

    return {"results": enriched_results}

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

