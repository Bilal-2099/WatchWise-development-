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

tmdb = TMDb()
tmdb.api_key = tmdb_api
tmdb.language = 'en'

CustomListRoutes = APIRouter(tags=["Custom Lists"])
movie_api = Movie()
show_api = TV()

@CustomListRoutes.post("/create/", status_code=status.HTTP_201_CREATED)
def create_custom_list(
    list_data: CustomListCreate, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_session)
):
    """
    Create a new custom list for the logged-in user.
    """
    new_list = CustomList(
        user_id=current_user.id,
        title=list_data.title,
        description=list_data.description
    )
    db.add(new_list)
    db.commit()
    db.refresh(new_list)
    
    return {"message": "Custom list created successfully", "list": new_list}

@CustomListRoutes.get("/", status_code=status.HTTP_200_OK)
def get_user_custom_lists(
    current_user: User = Depends(get_current_user),
    # limit: int = Query(20, ge=1, le=100, description="Number of entries to return"),
    # offset: int = Query(0, ge=0, description="Number of entries to skip"),
    db: Session = Depends(get_session)
):
    """
    Fetch all custom lists created by the logged-in user.
    """
    statement = select(CustomList).where(CustomList.user_id == current_user.id)
    # statement.offset(offset).limit(limit)
    lists = db.exec(statement).all()
    
    return {"results": lists}

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

@CustomListRoutes.delete("/delete/{list_id}/", status_code=status.HTTP_200_OK)
def delete_custom_list(
    list_id: int, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_session)
):
    """
    Delete an entire custom list and all associated items.
    """
    custom_list = db.get(CustomList, list_id)
    if not custom_list:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Custom list not found.")
    
    if custom_list.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to delete this list.")

    # Optional: Delete child items manually if cascade delete isn't configured in your database relationship
    statement = select(ListItem).where(ListItem.list_id == list_id)
    items = db.exec(statement).all()
    for item in items:
        db.delete(item)

    db.delete(custom_list)
    db.commit()

    return {"message": "Custom list deleted successfully"}

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


@CustomListRoutes.get("/{list_id}/", status_code=status.HTTP_200_OK)
def get_custom_list_details(
    list_id: int, 
    # limit: int = Query(20, ge=1, le=100, description="Number of entries to return"),
    # offset: int = Query(0, ge=0, description="Number of entries to skip"),
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_session)
):
    """
    Fetch a specific custom list and all its items enriched with live TMDB data.
    """
    custom_list = db.get(CustomList, list_id)
    if not custom_list:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Custom list not found.")
    
    # Optional: Decide if lists are public or private. Here we ensure only the owner can view private details, 
    # or you can remove this check if lists are meant to be public for everyone.
    if custom_list.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to view this list.")

    statement = select(ListItem).where(ListItem.list_id == list_id)
    items = db.exec(statement).all()
    
    enriched_items = []
    for item in items:
        try:
            if item.media_type == "movie":
                tmdb_data = movie_api.details(item.tmdb_id)
                title = tmdb_data.get("title")
            else:
                tmdb_data = show_api.details(item.tmdb_id)
                title = tmdb_data.get("name")

            poster_path = tmdb_data.get("poster_path")
            poster_url = base_image_url + poster_path if poster_path else None

            enriched_items.append({
                "item_id": item.id,
                "id": item.tmdb_id,
                "media_type": item.media_type,
                "title": title,
                "rating": tmdb_data.get("vote_average"),
                "poster": poster_url,
                "added_at": item.added_at
            })
        except Exception as e:
            print(f"Could not fetch TMDB details for {item.media_type} ID {item.tmdb_id}: {e}")

    return {
        "list_id": custom_list.id,
        "title": custom_list.title,
        "description": custom_list.description,
        "user_id": custom_list.user_id,
        "created_at": custom_list.created_at,
        "items": enriched_items
    }