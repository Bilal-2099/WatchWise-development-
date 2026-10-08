from tmdbv3api import TMDb, Discover, Genre
from app.config import tmdb_api, base_image_url

tmdb = TMDb()
tmdb.api_key = tmdb_api
tmdb.language = 'en' 

discover = Discover()
genre_api = Genre()

# Get Genre
def get_movie_genres():
    result = genre_api.movie_list()
    
    return {
        "genres": [
            {
                "id": genre.id,
                "name": genre.name,
            }
            for genre in result.genres
        ]
    }

def get_show_genres():
    result = genre_api.tv_list()

    return {
        "genres": [
            {
                "id": genre.id,
                "name": genre.name,
            }
            for genre in result.genres
        ]
    }

# Get Movies by Genre ID
def get_movies_by_genre(genre_id, page: int = 1):
    discover_results = discover.discover_movies({
        "with_genres": genre_id,
        "sort_by": "popularity.desc"
    })
    
    results = getattr(discover_results, "results", [])

    return {
        "page": page,
        "results": [
            {
                "id": m["id"],
                "title": m["title"],
                "rating": m["vote_average"],
                "year": m.release_date[:4] if m.release_date else None, # Added year
                "poster": base_image_url + m["poster_path"] if m["poster_path"] else None,
            }
            for m in results
        ]
    }

# Get Shows by Genre ID
def get_shows_by_genre(genre_id, page: int = 1):
    discover_results = discover.discover_tv_shows({
        "with_genres": genre_id,
        "sort_by": "popularity.desc"
    })
    
    results = getattr(discover_results, "results", [])

    return {
        "page": page,
        "results": [
            {
                "id": s["id"],
                "title": s["name"],
                "rating": s["vote_average"],
                "year": s.first_air_date[:4] if s.first_air_date else None, # Added year
                "poster": base_image_url + s["poster_path"] if s["poster_path"] else None,
            }
            for s in results
        ]
    }

# Movies by Provider ID
def get_movies_by_platform(provider_id, page: int = 1, region="US"):
    filters = {
        "with_watch_providers": provider_id,
        "watch_region": region,
        "sort_by": "popularity.desc",
        "page": page,
    }
    
    results = discover.discover_movies(filters)
    title_key = "title"
        
    items = getattr(results, "results", [])
    
    return {
        "page": page,
        "results": [
            {
                "id": item["id"],
                "title": item[title_key],
                "rating": item["vote_average"],
                "year": item.release_date[:4] if item.release_date else None, # Added year
                "poster": base_image_url + item["poster_path"] if item["poster_path"] else None,
            }
            for item in items
        ]
    }

# Shows by Provider ID
def get_shows_by_platform(provider_id, page: int = 1, region="US"):
    filters = {
        "with_watch_providers": provider_id,
        "watch_region": region,
        "sort_by": "popularity.desc",
        "page": page,
    }
    
    results = discover.discover_tv_shows(filters)
    title_key = "name"
        
    items = getattr(results, "results", [])
    
    return {
        "page": page,
        "results": [
            {
                "id": item["id"],
                "title": item[title_key],
                "rating": item["vote_average"],
                "year": item.first_air_date[:4] if item.first_air_date else None, # Added year
                "poster": base_image_url + item["poster_path"] if item["poster_path"] else None,
            }
            for item in items
        ]
    }