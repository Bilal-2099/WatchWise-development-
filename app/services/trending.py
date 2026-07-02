from tmdbv3api import Trending, TMDb, Movie, TV
from app.config import tmdb_api, base_image_url

tmdb = TMDb()
tmdb.api_key = tmdb_api
tmdb.language = 'en' 

trending = Trending()
movie = Movie()
show_api = TV()

# Get trending movies
def get_trending_movie(limit=20):
    trending_movies = trending.movie_week()

    movies = list(trending_movies["results"])[:limit]

    return {
        "results": [
        {
            "id": m["id"],
            "title": m["title"],
            "rating": m["vote_average"],
            "poster": base_image_url + m["poster_path"] if m["poster_path"] else None,
        }
        for m in movies
    ]
    }

# Get trending shows
def get_trending_show(limit=20):
    trending_shows = trending.tv_week()

    shows = list(trending_shows["results"])[:limit]

    return {
        "results": [
        {
            "id": s["id"],
            "title": s["name"],
            "rating": s["vote_average"],
            "poster": base_image_url + s["poster_path"] if s["poster_path"] else None,
        }
        for s in shows
    ]
    }

# Get popular movies
def popular_movies(limit=20):
    popular_movies = movie.popular()

    popular_movies = list(popular_movies["results"])[:limit]

    return {
        "results": [
        {
            "id": m["id"],
            "title": m["title"],
            "rating": m["vote_average"],
            "poster": base_image_url + m["poster_path"] if m["poster_path"] else None,
        }
        for m in popular_movies
    ]
    }

# Get popular shows
def popular_shows(limit=20):
    popular_shows = show_api.popular()

    popular_shows = list(popular_shows["results"])[:limit]

    return {
        "results": [
        {
            "id": s["id"],
            "title": s["name"],
            "rating": s["vote_average"],
            "poster": base_image_url + s["poster_path"] if s["poster_path"] else None,
        }
        for s in popular_shows
    ]
    }

# Get top rated movies
def top_rated_movies(limit=20):
    top_rated_movies = movie.top_rated()

    top_rated_movies = list(top_rated_movies["results"])[:limit]

    return {
        "results": [
        {
            "id": m["id"],
            "title": m["title"],
            "rating": m["vote_average"],
            "poster": base_image_url + m["poster_path"] if m["poster_path"] else None,
        }
        for m in top_rated_movies
    ]
    }

# Get top rated shows
def top_rated_shows(limit=20):
    top_rated_shows = show_api.top_rated()

    top_rated_shows = list(top_rated_shows["results"])[:limit]

    return {
        "results": [
        {
            "id": s["id"],
            "title": s["name"],
            "rating": s["vote_average"],
            "poster": base_image_url + s["poster_path"] if s["poster_path"] else None,
        }
        for s in top_rated_shows
    ]
    }