import requests
from django.core.management.base import BaseCommand
from MovieApp.models import TVShow, Genre, Actor
from django.core.files import File
from io import BytesIO

class Command(BaseCommand):
    help = 'Imports TV shows of different genres and languages from TMDb API'

    def handle(self, *args, **kwargs):
        tmdb_api_key = 'e66bff8fbb5a2cb36bd3d0ca4052885f'  # Replace with your TMDb API key
        tmdb_base_url = "https://api.themoviedb.org/3"
        genres = ["28", "35", "53", "878", "27"]  # Updated genres: Action, Comedy, Thriller, Science Fiction, Horror
        languages = ["en", "es", "hi", "ml", "ta"]  # Updated languages: English, Spanish, Hindi, Malayalam, Tamil
        max_tvshows_per_genre = 30  # Limit of 30 TV shows per genre

        # Language mapping
        language_mapping = {
            "en": "English",
            "es": "Spanish",
            "hi": "Hindi",
            "ml": "Malayalam",
            "ta": "Tamil",  # Added Tamil
        }

        # Define a dictionary for genre IDs and their names
        genre_name_mapping = {
            "28": "Action",
            "35": "Comedy",
            "53": "Thriller",
            "878": "Science Fiction",
            "27": "Horror"
        }

        try:
            for genre_id in genres:
                print(f"Fetching TV shows for genre {genre_name_mapping.get(genre_id, 'Unknown')}...")

                for language in languages:
                    print(f"Fetching TV shows in {language}...")

                    total_tvshows_fetched = 0
                    page = 1

                    while total_tvshows_fetched < max_tvshows_per_genre:
                        response = requests.get(f"{tmdb_base_url}/discover/tv", params={
                            'api_key': tmdb_api_key,
                            'page': page,
                            'with_genres': genre_id,
                            'language': language,
                            'include_adult': 'false'
                        })

                        if response.status_code != 200:
                            self.stdout.write(self.style.ERROR(f"Error fetching data from API. Status code: {response.status_code}"))
                            return  # Stop execution if the API call fails

                        data = response.json()

                        if data.get('results'):
                            for tvshow_data in data.get('results', []):
                                if total_tvshows_fetched >= max_tvshows_per_genre:
                                    break

                                tmdb_id = tvshow_data.get('id', None)
                                if not tmdb_id:
                                    self.stdout.write(self.style.ERROR(f"TV Show missing TMDb ID: {tvshow_data.get('name')}"))
                                    continue

                                # Check if the TV show already exists in the database
                                if TVShow.objects.filter(tmdb_id=tmdb_id).exists():
                                    print(f"TV Show with TMDb ID {tmdb_id} already exists, skipping...")
                                    continue

                                genre_name = genre_name_mapping.get(genre_id, 'Unknown Genre')
                                genre, created = Genre.objects.get_or_create(name=genre_name)

                                # Fetch full TV show details
                                tvshow_details_response = requests.get(f"{tmdb_base_url}/tv/{tmdb_id}", params={
                                    'api_key': tmdb_api_key,
                                    'language': language
                                })
                                tvshow_details = tvshow_details_response.json()

                                # Fetch the TV show's cast
                                cast_response = requests.get(f"{tmdb_base_url}/tv/{tmdb_id}/credits", params={
                                    'api_key': tmdb_api_key,
                                    'language': language
                                })
                                cast_data = cast_response.json()

                                # Extract release year and convert it to a valid date
                                release_date = tvshow_details.get('first_air_date', '1900-01-01')
                                seasons = tvshow_details.get('number_of_seasons', 0)
                                rating = tvshow_details.get('vote_average', None)

                                # Map language code to full name
                                language_name = language_mapping.get(language, "Unknown Language")

                                # Handle the poster image
                                poster_path = tvshow_details.get('poster_path', None)

                                tvshow = None
                                if poster_path:
                                    poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
                                    img_response = requests.get(poster_url)
                                    if img_response.status_code == 200:
                                        image_file = BytesIO(img_response.content)
                                        tvshow = TVShow.objects.create(
                                            tmdb_id=tmdb_id,
                                            title=tvshow_details.get('name', 'Unknown Title'),
                                            release_date=release_date,
                                            plot=tvshow_details.get('overview', 'No plot available'),
                                            language=language_name,  # Save the full language name
                                            seasons=seasons,  # Save the number of seasons
                                            rating=rating
                                        )
                                        tvshow.poster.save(f"{tvshow.title}_poster.jpg", File(image_file), save=True)
                                    else:
                                        self.stdout.write(self.style.ERROR(f"Failed to fetch image for {tvshow_details.get('name')}"))
                                else:
                                    tvshow = TVShow.objects.create(
                                        tmdb_id=tmdb_id,
                                        title=tvshow_details.get('name', 'Unknown Title'),
                                        release_date=release_date,
                                        plot=tvshow_details.get('overview', 'No plot available'),
                                        language=language_name,  # Save the full language name
                                        seasons=seasons,  # Save the number of seasons
                                        rating=rating
                                    )

                                # Add genre to TV show (many-to-many relationship)
                                tvshow.genres.add(genre)

                                # Add cast to TV show (including pictures)
                                cast_names = cast_data.get('cast', [])
                                for actor in cast_names:
                                    actor_name = actor.get('name', 'Unknown Actor')
                                    actor_image_path = actor.get('profile_path', None)

                                    # Handle actor's image
                                    actor_picture = None
                                    if actor_image_path:
                                        actor_picture_url = f"https://image.tmdb.org/t/p/w500{actor_image_path}"
                                        actor_picture_response = requests.get(actor_picture_url)
                                        if actor_picture_response.status_code == 200:
                                            actor_picture = BytesIO(actor_picture_response.content)

                                    # Get or create the actor object and add the picture
                                    actor_obj, created = Actor.objects.get_or_create(name=actor_name)

                                    if actor_picture:
                                        actor_obj.picture.save(f"{actor_name}_picture.jpg", File(actor_picture), save=True)

                                    # Add the actor to the TV show
                                    tvshow.cast.add(actor_obj)

                                tvshow.save()

                                total_tvshows_fetched += 1

                            if total_tvshows_fetched >= max_tvshows_per_genre:
                                break

                        if len(data.get('results', [])) < 10:
                            break
                        else:
                            page += 1

        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f"Error fetching data from API: {e}"))
