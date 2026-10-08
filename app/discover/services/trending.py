from tmdbv3api import Trending, TMDb, Movie, TV
from app.config import tmdb_api, base_image_url

tmdb = TMDb()
tmdb.api_key = tmdb_api
tmdb.language = 'en' 

trending = Trending()
movie = Movie()
show_api = TV()

# Get trending movies
def get_trending_movie(page: int = 1):
    trending_movies = trending.movie_week(page=page)

    movies = getattr(trending_movies, "results", [])

    return {
        "page" : page,
        "results": [
        {
            "id": m["id"],
            "title": m["title"],
            "rating": m["vote_average"],
            "year": m.release_date[:4] if m.release_date else None, # Added year
            "poster": base_image_url + m["poster_path"] if m["poster_path"] else None,
        }
        for m in movies
    ]
    }

# Get trending shows
def get_trending_show(page: int = 1):
    trending_shows = trending.tv_week(page=page)

    shows = getattr(trending_shows, "results", [])

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
        for s in shows
    ]
    }

# Get popular movies
def popular_movies(page: int = 1):
    popular_movies = movie.popular(page=page)

    popular_movies = getattr(popular_movies, "results", [])

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
        for m in popular_movies
    ]
    }

# Get popular shows
def popular_shows(page: int = 1):
    popular_shows = show_api.popular(page=page)

    popular_shows = getattr(popular_shows, "results", [])

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
        for s in popular_shows
    ]
    }

# Get top rated movies
def top_rated_movies(page: int = 1):
    top_rated_movies = movie.top_rated(page=page)

    top_rated_movies = getattr(top_rated_movies, "results", [])

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
        for m in top_rated_movies
    ]
    }

# Get top rated shows
def top_rated_shows(page: int = 1):
    top_rated_shows = show_api.top_rated(page=page)

    top_rated_shows = getattr(top_rated_shows, "results", [])

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
        for s in top_rated_shows
    ]
    }