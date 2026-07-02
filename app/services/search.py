from tmdbv3api import TMDb, Movie, TV
from app.config import tmdb_api

tmdb = TMDb()
tmdb.api_key = tmdb_api
tmdb.language = 'en' 
base_image_url = "https://image.tmdb.org/t/p/w500"
movie_api = Movie()
show_api = TV()

# Search Movies
def search_movie(query, limit=10):
    if not query.strip():
        return {"results": []}

    
    search_results = movie_api.search(query)
    results = list(search_results)[:limit]

    return {
        "results": [
        {
            "id": item["id"],
            "title": item["title"],
            "rating": item["vote_average"] if item["vote_average"] else None,
            "poster": base_image_url + item["poster_path"] if item["poster_path"] else None
        }
        for item in results
    ]
   }

# Search Shows
def search_show(query, limit=10):
    if not query.strip():
        return {"results": []}

    search_results = show.search(query)
    results = list(search_results)[:limit]

    return {
        "results": [
        {
            "id": item["id"],
            "title": item["name"],
            "rating": item["vote_average"] if item["vote_average"] else None,
            "poster": base_image_url + item["poster_path"] if item["poster_path"] else None
        }
        for item in results
    ]
   }

# Get a Movie
def get_movie(id):
    movie_detail = movie_api.details(id)

    return {
        "results": {
            "id": movie_detail.id,
            "title": movie_detail.title,
            "rating": movie_detail.vote_average if movie_detail.vote_average else None,
            "description": movie_detail.overview,
            "release_date": movie_detail.release_date,
            "poster": base_image_url + movie_detail.poster_path if movie_detail.poster_path else None,
            "backdrop_pic": base_image_url + movie_detail.backdrop_path if movie_detail.backdrop_path else None
        }
   }


def get_show(id):
    show_detail = show_api.details(id)

    return {
        "results": {
            "id": show_detail.id,
            "title": show_detail.name,
            "rating": show_detail.vote_average if show_detail.vote_average else None,
            "description": show_detail.overview,
            "release_date": show_detail.release_date,
            "poster": base_image_url + show_detail.poster_path if show_detail.poster_path else None,
            "backdrop_pic": base_image_url + show_detail.backdrop_path if show_detail.backdrop_path else None
        }
   }
