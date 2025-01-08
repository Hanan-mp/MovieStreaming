from django.core.management.base import BaseCommand
from MovieApp.models import Upcoming, Genre
from django.core.files import File
from io import BytesIO
import requests
import time
from requests.exceptions import Timeout, RequestException
from datetime import datetime

class Command(BaseCommand):
    help = 'Imports upcoming movies from TMDb API'

    def handle(self, *args, **kwargs):
        tmdb_api_key = 'e66bff8fbb5a2cb36bd3d0ca4052885f'  # Replace with your TMDb API key
        tmdb_base_url = "https://api.themoviedb.org/3"
        languages = ["en", "es", "hi", "ml", "ta"]  # List of languages
        max_movies_to_fetch = 30  # Limit of 30 upcoming movies per language

        # Language mapping (for saving language in full)
        language_mapping = {
            "en": "English",
            "es": "Spanish",
            "hi": "Hindi",
            "ml": "Malayalam",
            "ta": "Tamil",
        }

        # Track processed movie TMDb IDs to avoid duplicates
        processed_tmdb_ids = set()

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
            for language in languages:
                print(f"Fetching upcoming movies in {language_mapping.get(language, 'Unknown')}...")

                total_movies_fetched = 0
                page = 1

                while total_movies_fetched < max_movies_to_fetch:
                    try:
                        print(f"Fetching data for page {page}...")

                        # Fetch upcoming movies from TMDb API
                        response = requests.get(f"{tmdb_base_url}/movie/upcoming", params={
                            'api_key': tmdb_api_key,
                            'page': page,
                            'language': language,
                            'include_adult': 'false'  # Exclude adult content
                        })

                        if response.status_code != 200:
                            print(f"Error fetching data from API. Status code: {response.status_code}")
                            return  # Stop execution if the API call fails

                        data = response.json()

                        if data.get('results'):
                            print(f"Found {len(data['results'])} upcoming movies in {language_mapping.get(language)}...")

                            for movie_data in data.get('results', []):
                                if total_movies_fetched >= max_movies_to_fetch:
                                    break

                                tmdb_id = movie_data.get('id', None)
                                if not tmdb_id:
                                    print(f"Movie missing TMDb ID: {movie_data.get('title')}")
                                    continue

                                # Skip this movie if it's already been processed (check if movie exists in DB)
                                if tmdb_id in processed_tmdb_ids:
                                    continue  # Skip the movie if it's already in the set

                                # Mark this movie as processed
                                processed_tmdb_ids.add(tmdb_id)

                                # Check if movie already exists in the database (to avoid duplicates)
                                movie_exists = Upcoming.objects.filter(tmdb_id=tmdb_id).exists()
                                if movie_exists:
                                    print(f"Movie with TMDb ID {tmdb_id} already exists in the database. Skipping...")
                                    continue

                                # Fetch full movie details
                                movie_details_response = requests.get(f"{tmdb_base_url}/movie/{tmdb_id}", params={
                                    'api_key': tmdb_api_key,
                                    'language': language
                                })
                                movie_details = movie_details_response.json()

                                # Extract and validate release date
                                release_date = movie_details.get('release_date', '1900-01-01')

                                try:
                                    # Validate and convert release date to the correct format
                                    release_date_obj = datetime.strptime(release_date, '%Y-%m-%d')
                                    release_date = release_date_obj.date()  # Convert to date object
                                except ValueError:
                                    print(f"Invalid release date format for movie: {movie_details.get('title')}. Using default date '1900-01-01'.")
                                    release_date = '1900-01-01'

                                seasons = movie_details.get('number_of_seasons', 1)  # Default to 1 season if not available
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
                                        movie = Upcoming.objects.create(
                                            title=movie_details.get('title', 'Unknown Title'),
                                            release_date=release_date,
                                            plot=movie_details.get('overview', 'No plot available'),
                                            seasons=seasons,  # Added the seasons field
                                            language=language_name,  # Save the full language name
                                            duration=runtime,
                                            rating=rating,
                                            tmdb_id=tmdb_id  # Save the TMDb ID to prevent future duplicates
                                        )
                                        movie.poster.save(f"{movie.title}_poster.jpg", File(image_file), save=True)
                                    else:
                                        print(f"Failed to fetch image for {movie_details.get('title')}")
                                else:
                                    movie = Upcoming.objects.create(
                                        title=movie_details.get('title', 'Unknown Title'),
                                        release_date=release_date,
                                        plot=movie_details.get('overview', 'No plot available'),
                                        seasons=seasons,  # Added the seasons field
                                        language=language_name,  # Save the full language name
                                        duration=runtime,
                                        rating=rating,
                                        tmdb_id=tmdb_id  # Save the TMDb ID to prevent future duplicates
                                    )

                                # Handle genres
                                genres = movie_details.get('genres', [])
                                for genre in genres:
                                    genre_name = genre.get('name')
                                    genre_obj, created = Genre.objects.get_or_create(name=genre_name)
                                    movie.genres.add(genre_obj)

                                movie.save()

                                total_movies_fetched += 1

                            if total_movies_fetched >= max_movies_to_fetch:
                                break

                        if len(data.get('results', [])) < 20:
                            break
                        else:
                            page += 1

                    except RequestException as e:
                        print(f"Error fetching data from TMDb API: {str(e)}")
                        time.sleep(5)  # Retry after waiting for a short duration

        except Exception as e:
            print(f"Unexpected error occurred: {str(e)}")
