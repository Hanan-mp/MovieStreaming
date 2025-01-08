from django.core.management.base import BaseCommand
from MovieApp.models import Movie, Genre, Actor
from django.core.files import File
from io import BytesIO
import requests
import time
from requests.exceptions import Timeout, RequestException
from datetime import datetime

class Command(BaseCommand):
    help = 'Imports movies of different genres and languages from TMDb API'

    def handle(self, *args, **kwargs):
        tmdb_api_key = 'e66bff8fbb5a2cb36bd3d0ca4052885f'  # Replace with your TMDb API key
        tmdb_base_url = "https://api.themoviedb.org/3"
        genres = ["28", "35", "53", "878", "27"]  # Updated genres: Action, Comedy, Thriller, Science Fiction, Horror
        languages = ["en", "es", "hi", "ml", "ta"]  # Added Tamil language ('ta')
        max_movies_per_genre = 30  # Limit of 30 movies per genre

        # Language mapping
        language_mapping = {
            "en": "English",
            "es": "Spanish",
            "hi": "Hindi",
            "ml": "Malayalam",
            "ta": "Tamil",  # Added Tamil language mapping
        }

        # Define a dictionary for genre IDs and their names
        genre_name_mapping = {
            "28": "Action",
            "35": "Comedy",
            "53": "Thriller",
            "878": "Science Fiction",
            "27": "Horror"
        }

        # Track processed movie TMDb IDs to avoid duplicates
        processed_tmdb_ids = set()  # Set to store processed movie TMDb IDs

        def fetch_image_with_retry(url, retries=3, delay=5):
            """ Function to retry image fetch if there is a timeout or error. """
            for _ in range(retries):
                try:
                    img_response = requests.get(url, timeout=10)
                    if img_response.status_code == 200:
                        return img_response.content
                    else:
                        print(f"Failed to fetch image from {url}")
                        break
                except Timeout:
                    print(f"Timeout occurred while fetching image, retrying...")
                    time.sleep(delay)  # Wait for a few seconds before retrying
            return None  # Return None if image could not be fetched

        try:
            for genre_id in genres:
                print(f"Fetching movies for genre {genre_name_mapping.get(genre_id, 'Unknown')}...")

                for language in languages:
                    print(f"Fetching movies in {language_mapping.get(language, 'Unknown')}...")

                    total_movies_fetched = 0
                    page = 1

                    while total_movies_fetched < max_movies_per_genre:
                        try:
                            print(f"Fetching data for page {page}...")

                            response = requests.get(f"{tmdb_base_url}/discover/movie", params={
                                'api_key': tmdb_api_key,
                                'page': page,
                                'with_genres': genre_id,
                                'language': language,
                                'include_adult': 'false'
                            })

                            if response.status_code != 200:
                                print(f"Error fetching data from API. Status code: {response.status_code}")
                                return  # Stop execution if the API call fails

                            data = response.json()

                            if data.get('results'):
                                print(f"Found {len(data['results'])} movies for genre '{genre_name_mapping.get(genre_id)}' in {language_mapping.get(language)}...")

                                for movie_data in data.get('results', []):
                                    if total_movies_fetched >= max_movies_per_genre:
                                        break

                                    tmdb_id = movie_data.get('id', None)
                                    if not tmdb_id:
                                        print(f"Movie missing TMDb ID: {movie_data.get('title')}")
                                        continue

                                    # Skip this movie if it's already been processed (check if movie exists in DB)
                                    if tmdb_id in processed_tmdb_ids:
                                        continue  # Skip the movie if it's already in the set

                                    # Mark this movie as processed
                                    processed_tmdb_ids.add(tmdb_id)  # Add the TMDb ID to the processed set

                                    # Check if movie already exists in the database (to avoid duplicates)
                                    movie_exists = Movie.objects.filter(tmdb_id=tmdb_id).exists()
                                    if movie_exists:
                                        print(f"Movie with TMDb ID {tmdb_id} already exists in the database. Skipping...")
                                        continue

                                    genre_name = genre_name_mapping.get(genre_id, 'Unknown Genre')
                                    genre, created = Genre.objects.get_or_create(name=genre_name)

                                    # Fetch full movie details
                                    movie_details_response = requests.get(f"{tmdb_base_url}/movie/{tmdb_id}", params={
                                        'api_key': tmdb_api_key,
                                        'language': language
                                    })
                                    movie_details = movie_details_response.json()

                                    # Fetch the movie's cast
                                    cast_response = requests.get(f"{tmdb_base_url}/movie/{tmdb_id}/credits", params={
                                        'api_key': tmdb_api_key,
                                        'language': language
                                    })
                                    cast_data = cast_response.json()

                                    # Extract and validate release date
                                    release_date = movie_details.get('release_date', '1900-01-01')

                                    try:
                                        # Validate and convert release date to the correct format
                                        release_date_obj = datetime.strptime(release_date, '%Y-%m-%d')
                                        release_date = release_date_obj.date()  # Convert to date object
                                    except ValueError:
                                        print(f"Invalid release date format for movie: {movie_details.get('title')}. Using default date '1900-01-01'.")
                                        release_date = '1900-01-01'

                                    runtime = movie_details.get('runtime', None)
                                    rating = movie_details.get('vote_average', None)

                                    # Map language code to full name
                                    language_name = language_mapping.get(language, "Unknown Language")

                                    # Handle the poster image
                                    poster_path = movie_details.get('poster_path', None)

                                    if poster_path:
                                        poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
                                        image_data = fetch_image_with_retry(poster_url)
                                        if image_data:
                                            image_file = BytesIO(image_data)
                                            movie = Movie.objects.create(
                                                title=movie_details.get('title', 'Unknown Title'),
                                                release_date=release_date,
                                                plot=movie_details.get('overview', 'No plot available'),
                                                language=language_name,  # Save the full language name
                                                duration=runtime,
                                                rating=rating,
                                                tmdb_id=tmdb_id  # Save the TMDb ID to prevent future duplicates
                                            )
                                            movie.poster.save(f"{movie.title}_poster.jpg", File(image_file), save=True)
                                        else:
                                            print(f"Failed to fetch image for {movie_details.get('title')}")
                                    else:
                                        movie = Movie.objects.create(
                                            title=movie_details.get('title', 'Unknown Title'),
                                            release_date=release_date,
                                            plot=movie_details.get('overview', 'No plot available'),
                                            language=language_name,  # Save the full language name
                                            duration=runtime,
                                            rating=rating,
                                            tmdb_id=tmdb_id  # Save the TMDb ID to prevent future duplicates
                                        )

                                    # Add genre to movie (many-to-many relationship)
                                    movie.genres.add(genre)

                                    # Add cast to movie (including names and pictures)
                                    cast_names = cast_data.get('cast', [])
                                    for actor in cast_names:
                                        actor_name = actor.get('name', 'Unknown Actor')
                                        actor_picture_path = actor.get('profile_path', None)

                                        # Handle actor's image
                                        actor_picture = None
                                        if actor_picture_path:
                                            actor_picture_url = f"https://image.tmdb.org/t/p/w500{actor_picture_path}"
                                            actor_picture_response = requests.get(actor_picture_url)
                                            if actor_picture_response.status_code == 200:
                                                actor_picture = BytesIO(actor_picture_response.content)

                                        # Get or create the actor object and add the picture
                                        actor_obj, created = Actor.objects.get_or_create(name=actor_name)

                                        if actor_picture:
                                            actor_obj.picture.save(f"{actor_name}_picture.jpg", File(actor_picture), save=True)

                                        # Add the actor to the movie
                                        movie.cast.add(actor_obj)

                                    movie.save()

                                    total_movies_fetched += 1

                                if total_movies_fetched >= max_movies_per_genre:
                                    break

                            if len(data.get('results', [])) < 20:
                                break
                            else:
                                page += 1

                        except RequestException as e:
                            # Log the error with more information
                            print(f"Error fetching data from TMDb API: {str(e)}")
                            time.sleep(5)  # Retry after waiting for a short duration

        except Exception as e:
            # Log the unexpected error with more details
            print(f"Unexpected error occurred: {str(e)}")
