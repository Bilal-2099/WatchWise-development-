
from tmdbv3api import TMDb, Movie, TV, Person, Discover
from dotenv import load_dotenv
import os

load_dotenv()

tmdb_api = os.getenv('API_Key')
tmdb = TMDb()
tmdb.api_key = tmdb_api
tmdb.language = 'en' 
base_image_url = "https://image.tmdb.org/t/p/w500"

movie = Movie()

# # --- Get Popular or Top Rated Movies ---
popular_movies = movie.popular()
popular_movies = list(popular_movies["results"])

for m in popular_movies[:10]: # Just printing the top 5
    print(f"{m.title} (Rating: {m.vote_average})")

# # --- Get Specific Details by TMDB ID ---
# # Let's look up Interstellar (ID: 157336)
# detail = movie.details(157336)
# print(f"Tagline: {detail.tagline}")
# print(f"Budget: ${detail.budget:,}")
# print(f"Overview: {detail.overview}")

# # # --- Get Movie Recommendations ---
# recs = movie.recommendations(157336)

# tv = TV()

# # --- Search for a Show ---
# shows = tv.search('Breaking Bad')
# for show in shows:
#     print(f"{show.name} - First Air Date: {show.first_air_date}")

# # --- Get Popular TV Shows ---
# popular_shows = tv.popular()

# discover = Discover()

# # Find highly rated dramas (Genre ID for Drama is 18)
# best_dramas = discover.discover_movies({
#     'with_genres': 18,
#     'sort_by': 'vote_average.desc',
#     'vote_count.gte': 500 # Ensure it has a decent number of votes
# })

# for d in best_dramas:
#     print(d.title)

# movie = Movie()
# detail = movie.details(157336)

# base_image_url = "https://image.tmdb.org/t/p/w500"
# full_poster_url = base_image_url + detail.poster_path
# print(full_poster_url)