from tmdbv3api import TMDb, Discover, Genre
from app.config import tmdb_api, base_image_url

tmdb = TMDb()
tmdb.api_key = tmdb_api
tmdb.language = 'en' 

discover = Discover()
genre_api = Genre()

# Get Genre
def get_movie_genres():
    return genre_api.movie_list()

def get_show_genres():
    return genre_api.tv_list()

# Get Movies by Genre ID
def get_movies_by_genre(genre_id, limit=20):
    discover_results = discover.discover_movies({
        "with_genres": genre_id,
        "sort_by": "popularity.desc"
    })
    
    results = list(discover_results["results"])[:limit]

    return {
        "results": [
            {
                "id": m["id"],
                "title": m["title"],
                "rating": m["vote_average"],
                "poster": base_image_url + m["poster_path"] if m["poster_path"] else None,
            }
            for m in results
        ]
    }

# Get Shows by Genre ID
def get_shows_by_genre(genre_id, limit=20):
    discover_results = discover.discover_tv_shows({
        "with_genres": genre_id,
        "sort_by": "popularity.desc"
    })
    
    results = list(discover_results["results"])[:limit]

    return {
        "results": [
            {
                "id": s["id"],
                "title": s["name"],
                "rating": s["vote_average"],
                "poster": base_image_url + s["poster_path"] if s["poster_path"] else None,
            }
            for s in results
        ]
    }