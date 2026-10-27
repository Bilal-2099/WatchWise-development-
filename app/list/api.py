from fastapi import Depends, HTTPException, status, APIRouter
from sqlmodel import Session, select
from app.auth.security import get_current_user
from app.database import get_session
from app.models import (
    User, 
    CustomList, 
    ListItem, 
    CustomListCreate, 
    CustomListUpdate, 
    ListItemCreate
)
from tmdbv3api import TMDb, Movie, TV
from app.config import tmdb_api, base_image_url
import logging

# Setup logger for API errors
logger = logging.getLogger(__name__)

tmdb = TMDb()
tmdb.api_key = tmdb_api
tmdb.language = 'en'

CustomListRoutes = APIRouter(tags=["Custom Lists"])
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

@CustomListRoutes.post("/create/", status_code=status.HTTP_201_CREATED)
def create_custom_list(
    list_data: CustomListCreate, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_session)
):
    """
    Create a new custom list for the logged-in user.
    """
    try:
        new_list = CustomList(
            user_id=current_user.id,
            title=list_data.title,
            description=list_data.description
        )
        db.add(new_list)
        db.commit()
        db.refresh(new_list)
        
        return {"message": "Custom list created successfully", "list": new_list}
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating custom list for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating the custom list: {str(e)}"
        )

@CustomListRoutes.get("/", status_code=status.HTTP_200_OK)
def get_user_custom_lists(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Fetch all custom lists created by the logged-in user.
    """
    try:
        statement = select(CustomList).where(CustomList.user_id == current_user.id)
        lists = db.exec(statement).all()
        
        return {"results": lists}
    except Exception as e:
        logger.error(f"Error fetching custom lists for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching custom lists: {str(e)}"
        )

@CustomListRoutes.patch("/update/{list_id}/", status_code=status.HTTP_200_OK)
def update_custom_list(
    list_id: int, 
    list_data: CustomListUpdate, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_session)
):
    """
    Update the title or description of a custom list.
    """
    try:
        custom_list = db.get(CustomList, list_id)
        if not custom_list:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Custom list not found.")
        
        if custom_list.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to edit this list.")

        if list_data.title is not None:
            custom_list.title = list_data.title
        if list_data.description is not None:
            custom_list.description = list_data.description

        db.add(custom_list)
        db.commit()
        db.refresh(custom_list)

        return {"message": "Custom list updated successfully", "list": custom_list}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating custom list {list_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating the custom list: {str(e)}"
        )

@CustomListRoutes.delete("/delete/{list_id}/", status_code=status.HTTP_200_OK)
def delete_custom_list(
    list_id: int, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_session)
):
    """
    Delete an entire custom list and all associated items.
    """
    try:
        custom_list = db.get(CustomList, list_id)
        if not custom_list:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Custom list not found.")
        
        if custom_list.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to delete this list.")

        statement = select(ListItem).where(ListItem.list_id == list_id)
        items = db.exec(statement).all()
        for item in items:
            db.delete(item)

        db.delete(custom_list)
        db.commit()

        return {"message": "Custom list deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting custom list {list_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while deleting the custom list: {str(e)}"
        )

@CustomListRoutes.post("/{list_id}/add/", status_code=status.HTTP_201_CREATED)
def add_item_to_custom_list(
    list_id: int, 
    item_data: ListItemCreate, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_session)
):
    """
    Add a movie or TV show to a specific custom list.
    """
    try:
        if item_data.media_type not in ["movie", "tv"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="media_type must be either 'movie' or 'tv'.")

        custom_list = db.get(CustomList, list_id)
        if not custom_list:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Custom list not found.")
        
        if custom_list.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to modify this list.")

        # Check if item already exists in this list
        statement = select(ListItem).where(
            ListItem.list_id == list_id, 
            ListItem.tmdb_id == item_data.tmdb_id, 
            ListItem.media_type == item_data.media_type
        )
        existing_item = db.exec(statement).first()
        if existing_item:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This item is already in the list.")

        new_list_item = ListItem(
            list_id=list_id,
            tmdb_id=item_data.tmdb_id,
            media_type=item_data.media_type
        )
        db.add(new_list_item)
        db.commit()
        db.refresh(new_list_item)

        return {"message": "Successfully added item to custom list", "item": new_list_item}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding item to custom list {list_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while adding the item to the custom list: {str(e)}"
        )

@CustomListRoutes.delete("/{list_id}/delete/{item_id}/", status_code=status.HTTP_200_OK)
def remove_item_from_custom_list(
    list_id: int, 
    item_id: int, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_session)
):
    """
    Remove an individual movie or TV show entry from a custom list.
    """
    try:
        custom_list = db.get(CustomList, list_id)
        if not custom_list:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Custom list not found.")
        
        if custom_list.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to modify this list.")

        list_item = db.get(ListItem, item_id)
        if not list_item or list_item.list_id != list_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="List item not found.")

        db.delete(list_item)
        db.commit()

        return {"message": "Successfully removed item from custom list"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error removing item {item_id} from custom list {list_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while removing the item from the custom list: {str(e)}"
        )

@CustomListRoutes.get("/{list_id}/", status_code=status.HTTP_200_OK)
def get_custom_list_details(
    list_id: int, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_session)
):
    """
    Fetch a specific custom list and all its items enriched with live TMDB data.
    """
    try:
        custom_list = db.get(CustomList, list_id)
        if not custom_list:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Custom list not found.")
        
        if custom_list.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to view this list.")

        statement = select(ListItem).where(ListItem.list_id == list_id)
        items = db.exec(statement).all()
        
        enriched_items = []
        for item in items:
            try:
                if item.media_type == "movie":
                    tmdb_data = movie_api.details(item.tmdb_id)
                    title = _safe_get(tmdb_data, "title")
                else:
                    tmdb_data = show_api.details(item.tmdb_id)
                    title = _safe_get(tmdb_data, "name")

                poster_path = _safe_get(tmdb_data, "poster_path")
                poster_url = f"{base_image_url}{poster_path}" if poster_path else None

                enriched_items.append({
                    "item_id": item.id,
                    "id": item.tmdb_id,
                    "media_type": item.media_type,
                    "title": title,
                    "rating": _safe_get(tmdb_data, "vote_average", 0.0),
                    "poster": poster_url,
                    "added_at": item.added_at
                })
            except Exception as tmdb_error:
                logger.warning(f"Could not fetch TMDB details for custom list item {item.media_type} ID {item.tmdb_id}: {str(tmdb_error)}")
                enriched_items.append({
                    "item_id": item.id,
                    "id": item.tmdb_id,
                    "media_type": item.media_type,
                    "title": "Unknown Title",
                    "rating": 0.0,
                    "poster": None,
                    "added_at": item.added_at
                })

        return {
            "list_id": custom_list.id,
            "title": custom_list.title,
            "description": custom_list.description,
            "user_id": custom_list.user_id,
            "created_at": custom_list.created_at,
            "items": enriched_items
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching details for custom list {list_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching custom list details: {str(e)}"
        )