from tmdbv3api import Trending, TMDb, Movie, TV
from app.config import tmdb_api

tmdb = TMDb()
tmdb.api_key = tmdb_api
tmdb.language = 'en' 
base_image_url = "https://image.tmdb.org/t/p/w500"

trending = Trending()
movie = Movie()
show = TV()

# Get trending movies
def get_trending_movie(limit=20):
    trending_movies = trending.movie_week()

    movies = list(trending_movies["results"])[:limit]

    return {
        "results": [
        {
            "id": movie["id"],
            "title": movie["title"],
            "raing": movie["vote_average"],
            "poster": base_image_url + movie["poster_path"] if movie["poster_path"] else None,
        }
        for movie in movies
    ]
    }


# Get trending shows
def get_trending_show(limit=20):
    trending_shows = trending.tv_week()

    shows = list(trending_shows["results"])[:limit]

    return {
        "results": [
        {
            "id": show["id"],
            "title": show["name"],
            "description": show["overview"],
            "poster": base_image_url + show["poster_path"] if show["poster_path"] else None,
        }
        for show in shows
    ]
    }

# Get popular movies
def popular_movies(limit=20):
    popular_movies = movie.popular()

    popular_movies = list(popular_movies["results"])[:limit]

    return {
        "results": [
        {
            "id": movie["id"],
            "title": movie["title"],
            "raing": movie["vote_average"],
            "poster": base_image_url + movie["poster_path"] if movie["poster_path"] else None,
        }
        for movie in popular_movies
    ]
    }

# Get popular shows
def popular_shows(limit=20):
    popular_shows = show.popular()

    popular_shows = list(popular_shows["results"])[:limit]

    return {
        "results": [
        {
            "id": show["id"],
            "title": show["name"],
            "description": show["overview"],
            "poster": base_image_url + show["poster_path"] if show["poster_path"] else None,
        }
        for show in popular_shows
    ]
    }