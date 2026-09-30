from fastapi import Depends, HTTPException, status, APIRouter, FastAPI, Path, Query
from sqlmodel import Session, select
from app.auth.security import get_current_user
from app.database import get_session
from app.models import User, Watchlist, WatchlistCreate
from tmdbv3api import TMDb, Movie, TV
from app.config import tmdb_api, base_image_url

tmdb = TMDb()
tmdb.api_key = tmdb_api
tmdb.language = 'en' 

UserEntry = APIRouter()
movie_api = Movie()
show_api = TV()

@UserEntry.get("")
async def root():
    return {"message": "Just starting"}

@UserEntry.post("/watchlist/add/", status_code=status.HTTP_201_CREATED)
def add_to_watchlist(item_data: WatchlistCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_session)):
    """
    Add a movie or TV show to the current user's watchlist using its TMDB ID.
    """
    # 1. Validate media_type
    if item_data.media_type not in ["movie", "tv"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="media_type must be either 'movie' or 'tv'.")

    # 2. Check if this item is already in the user's watchlist
    statement = select(Watchlist).where(Watchlist.user_id == current_user.id, Watchlist.tmdb_id == item_data.tmdb_id, Watchlist.media_type == item_data.media_type)
    existing_item = db.exec(statement).first()

    if existing_item:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This item is already in your watchlist.")

    # 3. Create the new watchlist entry
    new_watchlist_item = Watchlist(
        user_id=current_user.id,
        tmdb_id=item_data.tmdb_id,
        media_type=item_data.media_type)

    db.add(new_watchlist_item)
    db.commit()
    db.refresh(new_watchlist_item)

    return {"message": "Successfully added to watchlist", "watchlist_item": new_watchlist_item}

@UserEntry.delete("/watchlist/remove/{watchlist_id}/", status_code=status.HTTP_200_OK)
def remove_from_watchlist(watchlist_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_session)):
    """
    Remove an item from the user's watchlist by its unique watchlist entry ID.
    """
    # 1. Fetch the watchlist item by its ID
    watchlist_item = db.get(Watchlist, watchlist_id)

    # 2. Check if it exists
    if not watchlist_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watchlist item not found.")

    # 3. Security check: Ensure the item belongs to the currently logged-in user!
    if watchlist_item.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to delete this item.")

    # 4. Delete the item from the database
    db.delete(watchlist_item)
    db.commit()

    return {"message": "Successfully removed from watchlist"}

@UserEntry.get("/watchlist/", status_code=status.HTTP_200_OK)
def get_user_watchlist(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Fetch the logged-in user's watchlist and enrich it with live data from TMDB.
    """
    # 1. Fetch all watchlist records for this user from the database
    print(f"Fetching watchlist for User ID: {current_user.id}")

    statement = select(Watchlist).where(Watchlist.user_id == current_user.id)
    watchlist_items = db.exec(statement).all()

    print(f"Found {len(watchlist_items)} items in database.")

    enriched_results = []

    for item in watchlist_items:
        try:
            # 2. Fetch details from TMDB depending on media type
            if item.media_type == "movie":
                # Assuming you have a helper like movie_api.details(item.tmdb_id)
                tmdb_data = movie_api.details(item.tmdb_id)
                title = tmdb_data.get("title")
            else:
                # Assuming you have a helper like show_api.details(item.tmdb_id)
                tmdb_data = show_api.details(item.tmdb_id)
                title = tmdb_data.get("name") # TV shows use 'name'

            poster_path = tmdb_data.get("poster_path")
            poster_url = base_image_url + poster_path if poster_path else None

            # 3. Format to match your search results structure
            enriched_results.append({
                "watchlist_id": item.id, # Useful so the frontend knows what ID to delete!
                "id": item.tmdb_id,
                "media_type": item.media_type,
                "title": title,
                "rating": tmdb_data.get("vote_average"),
                "poster": poster_url,
                "added_at": item.added_at
            })
        except Exception as e:
            # If TMDB fails for a specific item, don't crash the whole list; log it and skip or pass placeholder
            print(f"Could not fetch TMDB details for {item.media_type} ID {item.tmdb_id}: {e}")

    return {"results": enriched_results}


@UserEntry.get("/watchlist/check", status_code=status.HTTP_200_OK)
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

    # Search the database for an existing entry
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