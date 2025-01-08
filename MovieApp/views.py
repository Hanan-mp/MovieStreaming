from django.db import IntegrityError
from django.utils import timezone  
from datetime import timedelta    
from django.core.mail import EmailMessage
import uuid
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.models import User
from django.contrib.auth import login,logout
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from MovieApp.models import PasswordReset, Profile,Profile_picture
from MovieStreaming import settings
from rest_framework import viewsets
from .models import Actor, Movie, TVShow, Documentary, Genre
from .serializers import ActorSerializer, MovieSerializer, TVShowSerializer, DocumentarySerializer, GenreSerializer
import requests
from django.core.paginator import Paginator


# Create your views here.
def getStart(request):
    return render(request,'getStarted.html')

def home(request):
    if request.user.is_authenticated:  # Check if the user is logged in
        genres = Genre.objects.all().distinct()  # Fetch unique genres only

        api_url = "http://127.0.0.1:8000/api/movies/"  # The URL of your DRF API

        # Fetch movie data from the DRF API
        response = requests.get(api_url)

        print("API Status Code:", response.status_code)  # Log the response status

        if response.status_code == 200:  # If the API response is successful
            try:
                movie_data = response.json()  # Parse the JSON response

                # Debugging: Check the response structure
                print("Response Data:", movie_data)

                if isinstance(movie_data, list):  # If the response is a list, directly assign it to movies
                    movies = movie_data
                else:
                    movies = []  # Handle case where the response format is unexpected
            except ValueError:
                print("Error: Unable to parse the response JSON.")
                movies = []  # If there was an error parsing the JSON, set movies to an empty list
        else:
            print(f"API request failed with status code: {response.status_code}")
            movies = []  # If the API request failed (status code != 200), set movies to an empty list

        # Get distinct languages from the Movie model
        languages = Movie.objects.values_list('language', flat=True).distinct()

        # Pagination logic
        page_number = request.GET.get('page')  # Get the current page number from the request
        paginator = Paginator(movies, 24)  # Show 16 movies per page
        page_obj = paginator.get_page(page_number)  # Get the current page object

        # Debugging: Check the page object data before passing it to the template
        print("Page Object:", page_obj)

        # Pass the movies and genres data along with languages to the template
        return render(request, 'index.html', {
            'page_obj': page_obj,
            'genres': genres,
            'languages': languages
        })

    return redirect('signin')  # If the user is not logged in, redirect to the login page




from django.core.paginator import Paginator
import requests

def movie_list_by_genre(request, genre_id):
    """
    View function to display movies filtered by genre.
    """
    # Check if the user is logged in
    if request.user.is_authenticated:
        # Get the selected genre from the database
        try:
            selected_genre = Genre.objects.get(id=genre_id)
        except Genre.DoesNotExist:
            selected_genre = None
            print(f"Genre with id {genre_id} not found.")
        
        # API URL to fetch all movies
        api_url = "http://127.0.0.1:8000/api/movies/"

        # Fetch movie data from the API
        response = requests.get(api_url)

        if response.status_code == 200:
            try:
                movie_data = response.json()
                print("Response Data:", movie_data)
                
                # Ensure response is a list of movies
                if isinstance(movie_data, list):  # Check if the response is a list
                    # If a genre is selected, filter the movies based on that genre
                    if selected_genre:
                        # Filter the movies based on the selected genre
                        movies = [movie for movie in movie_data if selected_genre.id in [genre['id'] for genre in movie.get('genres', [])]]
                    else:
                        movies = movie_data
                else:
                    print("Error: API did not return a list of movies.")
                    movies = []  # Handle the case where the response is not a list
            except ValueError:
                print("Error: Unable to parse the response JSON.")
                movies = []  # Handle JSON parsing errors
        else:
            print(f"API request failed with status code: {response.status_code}")
            movies = []  # Handle API request failure

        # Pagination logic
        page_number = request.GET.get('page')  # Get the current page number from the request
        paginator = Paginator(movies, 24)  # Show 16 movies per page
        page_obj = paginator.get_page(page_number)  # Get the current page object

        # Get all genres to display in the navbar (so users can select another genre)
        genres = Genre.objects.all()

        # Return the template with filtered movies
        return render(request, 'index.html', {
            'page_obj': page_obj,  # Paginator object for pagination
            'genres': genres,  # List of all genres
            'selected_genre': selected_genre  # The selected genre for filtering
        })

    return redirect('signin')  # If not logged in, redirect to login page


def tvshow_list(request):
    # Fetch only genres that have associated TV shows
    genres = Genre.objects.filter(tvshow__isnull=False).distinct()

    # Get the selected genre from the request (e.g., from URL query parameters)
    selected_genre_id = request.GET.get('genre', None)

    # API URL for fetching TV shows
    api_url = "http://127.0.0.1:8000/api/tvshows/"  # The URL of your DRF API

    # Fetch TV show data from the DRF API
    response = requests.get(api_url)

    print("API Status Code:", response.status_code)  # Log the response status

    if response.status_code == 200:  # If the API response is successful
        try:
            tvshow_data = response.json()  # Parse the JSON response

            # Debugging: Check the response structure
            print("Response Data:", tvshow_data)
            
            if isinstance(tvshow_data, list):  # If the response is a list, directly assign it to tvshows
                tvshows = tvshow_data

                # If a genre is selected, filter the TV shows based on that genre
                if selected_genre_id:
                    tvshows = [tvshow for tvshow in tvshows if str(tvshow['genre_id']) == selected_genre_id]

                # Add full URL for poster images
                for tvshow in tvshows:
                    if tvshow.get('poster'):
                        # Make sure to use build_absolute_uri for the image URL
                        tvshow['poster'] = request.build_absolute_uri(tvshow['poster'])
            else:
                tvshows = []  # Handle case where the response format is unexpected

        except ValueError:
            print("Error: Unable to parse the response JSON.")
            tvshows = []  # If there was an error parsing the JSON, set tvshows to an empty list
    else:
        print(f"API request failed with status code: {response.status_code}")
        tvshows = []  # If the API request failed (status code != 200), set tvshows to an empty list

    # Pagination logic
    page_number = request.GET.get('page', 1)  # Default to page 1 if no page is specified

    if tvshows:  # Only apply pagination if tvshows are available
        paginator = Paginator(tvshows, 24)  # Show 24 TV shows per page
        page_obj = paginator.get_page(page_number)  # Get the current page object
    else:
        page_obj = None  # If no TV shows, set page_obj to None to avoid pagination issues

    # Debugging: Check the tvshows data before passing it to the template
    print("TV Shows data to be passed to template:", tvshows)

    # Pass the filtered TV shows data, genres, and the selected genre to the template
    return render(request, 'tvshows/tvshows.html', {
        'page_obj': page_obj,  # Paginator object for pagination
        'genres': genres,
        'selected_genre_id': selected_genre_id,  # Pass the selected genre to the template (optional)
    })



def tvshow_list_by_genre(request, genre_id):
    # Fetch only genres that have associated TV shows
    genres = Genre.objects.filter(tvshow__isnull=False).distinct()

    # Get the selected genre from the database
    selected_genre = Genre.objects.get(id=genre_id)

    # API URL for fetching TV shows
    api_url = "http://127.0.0.1:8000/api/tvshows/"  # The URL of your DRF API

    # Fetch TV show data from the DRF API
    response = requests.get(api_url)

    print("API Status Code:", response.status_code)  # Log the response status

    if response.status_code == 200:  # If the API response is successful
        try:
            tvshow_data = response.json()  # Parse the JSON response

            # Debugging: Check the response structure
            print("Response Data:", tvshow_data)
            
            if isinstance(tvshow_data, list):  # If the response is a list, directly assign it to tvshows
                tvshows = tvshow_data

                # Filter the TV shows based on the selected genre
                tvshows = [
                    tvshow for tvshow in tvshows
                    if any(genre['id'] == genre_id for genre in tvshow['genres'])
                ]

                # Add full URL for poster images
                for tvshow in tvshows:
                    if tvshow.get('poster'):
                        tvshow['poster'] = request.build_absolute_uri(tvshow['poster'])
            else:
                tvshows = []  # Handle case where the response format is unexpected
            
            page_number = request.GET.get('page', 1)  # Default to page 1 if no page is specified

            if tvshows:  # Only apply pagination if tvshows are available
                paginator = Paginator(tvshows, 24)  # Show 24 TV shows per page
                page_obj = paginator.get_page(page_number)  # Get the current page object
            else:
                page_obj = None  # If no TV shows, set page_obj to None to avoid pagination issues

        except ValueError:
            print("Error: Unable to parse the response JSON.")
            tvshows = []  # If there was an error parsing the JSON, set tvshows to an empty list
    else:
        print(f"API request failed with status code: {response.status_code}")
        tvshows = []  # If the API request failed (status code != 200), set tvshows to an empty list

    # Debugging: Check the tvshows data before passing it to the template
    print("TV Shows data to be passed to template:", tvshows)

    # Pass the filtered TV shows data, genres, and the selected genre to the template
    return render(request, 'tvshows/tvshows.html', {
        'page_obj': page_obj,  # Paginator object for pagination
        'genres': genres,
        'selected_genre': selected_genre,  # Pass the selected genre to the template
    })






def signup(request):
    if request.method == "POST":
        uname = request.POST.get('username')
        email = request.POST.get('email')
        pass1 = request.POST.get('password1')
        pass2 = request.POST.get('password2')
        
        # Validation for required fields
        if not uname:
            error = "Username required"
            return render(request, 'signup/signup.html', {'message': error, 'username': uname, 'email': email, 'password1': pass1, 'password2': pass2})
        
        if not email:
            error = "Email field is required"
            return render(request, 'signup/signup.html', {'message': error, 'username': uname, 'email': email, 'password1': pass1, 'password2': pass2})
        
        if '@' not in email:
            error = "Invalid email address. It must contain an '@' symbol"
            return render(request, 'signup/signup.html', {'message': error, 'username': uname, 'email': email, 'password1': pass1, 'password2': pass2})
        
        if not pass1 or not pass2:
            error = "Password required"
            return render(request, 'signup/signup.html', {'message': error, 'username': uname, 'email': email, 'password1': pass1, 'password2': pass2})
        
        if len(pass1) < 8:
            error = "password must be Atleast 8 charecter"
            return render(request, 'signup/signup.html', {'message': error,'username': uname, 'email': email, 'password1': pass1, 'password2': pass2})
        
        # Check if passwords match
        if pass1 != pass2:
            error = "Passwords are not matching"
            return render(request, 'signup/signup.html', {'message': error, 'username': uname, 'email': email, 'password1': pass1, 'password2': pass2})
        
        if User.objects.filter(username=uname).exists():
            error = "This username already exists"
            return render(request, 'signup/signup.html', {'message': error, 'username': uname, 'email': email, 'password1': pass1, 'password2': pass2})
        
        if User.objects.filter(email=email).exists():
            error = "This email already exists"
            return render(request, 'signup/signup.html', {'message': error, 'username': uname, 'email': email, 'password1': pass1, 'password2': pass2})
        
        # Create the user
        try:
            user = User.objects.create_user(username=uname, password=pass1, email=email)
            user.save()
            success = "User created successfully"
            return render(request, 'signup/signup.html', {'success': success})
        except Exception as e:
            return HttpResponse(f"Error creating user: {str(e)}", status=400)
    
    return render(request, 'signup/signup.html')


def signin(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        print("Email:", email)
        print("Password:", password)
        
        #validation
        if not email:
             error = "Email field is required"
             return render(request, 'login/login.html', {'message': error,'email': email, 'password': password})
        
        if '@' not in email:
            error = "Invalid email address. It must contain an '@' symbol"
            return render(request, 'login/login.html', {'message': error,'email': email, 'password': password})
        
        if not password:
            error = "Password required"
            return render(request, 'login/login.html', {'message': error,'email': email, 'password': password})
        
        if len(password) < 8:
            error = "password must be Atleast 8 charecter"
            return render(request, 'login/login.html', {'message': error,'email': email, 'password': password})
        
       
        # Try to get the user by email
        try:
            # Query the User model based on email
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = None
        
        if user is not None and user.check_password(password):
            # If user is found and password is correct, authenticate and login
            login(request, user)
            print("Authentication successful")
            if request.user.is_authenticated:
                return redirect('home')  # Adjust to your actual home page URL
        else:
            # Authentication failed, add error message
            print("Authentication failed")
            error = "email and password is incorrect"
            return render(request, 'login/login.html', {'message': error,'email': email, 'password': password})
    
    return render(request, 'login/login.html')

def user_logout(request):
    if request.user.is_authenticated:
        logout(request)
    return redirect('signin') 



def forgot_password(request):
   
    if request.method == 'POST':
        email = request.POST.get('email') 
            
        try:
            user = User.objects.get(email=email)
            new_password_reset = PasswordReset(user = user)
            new_password_reset.save()
            password_reset_url = reverse('change_password',kwargs={'reset_id':new_password_reset.reset_id})
            full_password_reset_url = f'{request.scheme}://{request.get_host()}{password_reset_url}'
            email_body = f'Reset your password using the link below:\n\n\n{full_password_reset_url}'
            
            email_message = EmailMessage(
                'Reset your password', #email subject
                email_body,
                settings.EMAIL_HOST_USER,#email sender
                [email] # receiver
            )
            
            email_message.fail_silently = True
            email_message.send()
            
            return redirect('password_reset_sent',reset_id=new_password_reset.reset_id)
        
                
        except User.DoesNotExist:
            error = f"No user with email '{email}' found."
            return render(request, 'forget_password/forget_password.html', {"message": error})
            
    return render(request, 'forget_password/forget_password.html')

def password_reset_sent(request,reset_id):
    if PasswordReset.objects.filter(reset_id=reset_id).exists():
        return render(request,'forget_password/password_reset_sent.html')
    else:
        #redirect to forgot password page if code does not exist
        return redirect('forget_password')
    
def change_password(request,reset_id):
    try:
        password_reset_id = PasswordReset.objects.get(reset_id=reset_id)
        
        if request.method=="POST":
            password = request.POST.get('new_password1')
            confirm_password = request.POST.get('new_password2')
            
            password_have_error = False
            
            if not password:
                password_have_error = True
                error = "Password required"
                return render(request,'forget_password/change_password.html',{"message":error})
            
            if len(password) < 8:
                password_have_error = True
                error = "password must be Atleast 8 charecter"
                return render(request,'forget_password/change_password.html',{"message":error})
            
            if password != confirm_password:
                password_have_error = True
                error = "Password is not matching together"
                return render(request,'forget_password/change_password.html',{"message":error})
            
            
            
            expiration_time = password_reset_id.created_when + timedelta(minutes=10)
            
            if timezone.now() > expiration_time:
                password_have_error = True
                error = "reset link has expired"
                password_reset_id.delete()
                return render(request,'forget_password/change_password.html',{"message":error})
            
            if not password_have_error:
                user = password_reset_id.user
                user.set_password(password)
                user.save()
                
                #delete reset id after use
                password_reset_id.delete()
                
                return render(request,'forget_password/password_reset_complete.html')
            else:
                return redirect('change_password',reset_id=reset_id)
            
    except PasswordReset.DoesNotExist:
        return redirect('forget_password')
    
    return render(request,'forget_password/change_password.html')

@login_required
def view_user(request):
    try:
        obj = Profile.objects.get(user=request.user)  # Retrieve the single profile for the user
    except Profile.DoesNotExist:
        obj = None  # Handle the case if the user doesn't have a profile
        
    profile_pictures = Profile_picture.objects.filter(user=request.user)

    # If there are any profile pictures, get the first one (or choose logic to pick the correct one)
    if profile_pictures.exists():
        profile_picture = profile_pictures.first()  # Get the first profile picture (or use other logic)
    else:
        profile_picture = None  # No profile picture found for the user
    
    return render(request,'user/view_user.html',{'data':obj,'user': request.user,'profile_picture': profile_picture})


@login_required
def update_user(request):
    # Get or create the profile for the logged-in user
    try:
        obj = Profile.objects.get(user=request.user)  # Retrieve the single profile for the user
    except Profile.DoesNotExist:
        # If profile does not exist, create one
        obj = Profile(user=request.user)
        obj.save()  # Save the newly created profile
    
    if request.method == "POST":
        # Update the user model
        user = request.user
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        
        # Validate the username and email
        if not user.username:
            error = "Username required"
            return render(request, 'user/update_user.html', {'message': error, 'data': obj})
        
        if not user.email:
            error = "Email field is required"
            return render(request, 'user/update_user.html', {'message': error, 'data': obj})
        
        if '@' not in user.email:
            error = "Invalid email address. It must contain an '@' symbol"
            return render(request, 'user/update_user.html', {'message': error, 'data': obj})
        
        user.save()  # Save changes to the User model
        
        # Update the profile model if it exists
        obj.phone = request.POST.get('phone')
        obj.country = request.POST.get('country')
        
        # Validate the profile fields
        if not obj.phone:
            error = "Phone number required"
            return render(request, 'user/update_user.html', {'message': error, 'data': obj})
        
        if len(obj.phone) != 10:
            error = "Phone number must be 10 digits."
            return render(request, 'user/update_user.html', {'message': error, 'data': obj})

        if not obj.country:
            error = "Country is required"
            return render(request, 'user/update_user.html', {'message': error, 'data': obj})
        
        obj.save()  # Save changes to the Profile model
        
        success = "Profile updated"
        return render(request, 'user/update_user.html', {'success': success, 'data': obj})  # Success message
    
    # Pass the profile to the template
    return render(request, 'user/update_user.html', {'data': obj})

@login_required
def update_user_password(request):
    if request.method == "POST":
        # Get the old and new passwords from the form
        old_password = request.POST["last_password"]
        new_password = request.POST["new_password1"]
        confirm_password = request.POST["new_password2"]
        
        if not old_password:
            error = "Old Password is required"
            return render(request,'user/update_password.html',{"message":error, "old_password":old_password,"new_password":new_password,"confirm_password":confirm_password})
        
        if not new_password:
            error = "New Password is required"
            return render(request,'user/update_password.html',{"message":error,  "old_password":old_password,"new_password":new_password,"confirm_password":confirm_password})
            
        if len(new_password) < 8:
           
            error = "password must be Atleast 8 charecter"
            return render(request,'user/update_password.html',{"message":error,  "old_password":old_password,"new_password":new_password,"confirm_password":confirm_password})
        
        if not confirm_password:
            error = "confirm Password is required"
            return render(request,'user/update_password.html',{"message":error,  "old_password":old_password,"new_password":new_password,"confirm_password":confirm_password})
            
        if new_password != confirm_password:
            error = "Password is not matching together"
            return render(request,'user/update_password.html',{"message":error,  "old_password":old_password,"new_password":new_password,"confirm_password":confirm_password})
        
        # Get the current user
        user = request.user
        
        # Check if the old password matches
        if user.check_password(old_password):  # Use check_password() method here
            # Set the new password
            user.set_password(new_password)
            user.save()
            
            # Update the session to keep the user logged in after password change
            update_session_auth_hash(request, user)  # Important to keep the user logged in
            
            success = "Password changed successfully"
            return render(request, 'user/update_password.html', {'success': success})
        else:
            # If the old password is incorrect
            error = "Last password is incorrect"
            return render(request, 'user/update_password.html', {"message": error})

    # If it's not a POST request, render the password update page
    return render(request, 'user/update_password.html')

@login_required      
def add_profile(request):
    if request.method == 'POST' and request.FILES.get('image'):
        uploaded_image = request.FILES['image']
        user = request.user

        try:
            # Try to create a new profile picture
            profile_picture = Profile_picture(user=user, image=uploaded_image)
            profile_picture.save()
        except IntegrityError:
            # If an IntegrityError occurs (due to duplicate user_id), update the existing profile picture
            profile_picture = Profile_picture.objects.get(user=user)
            profile_picture.image = uploaded_image
            profile_picture.save()

        return redirect('view_user')  # Redirect after successful upload

    return render(request, "user/add_profile.html")

@login_required
def movie_details(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)  # Fetch the movie with the given ID
    # Get the first 6 actors that have a picture associated with them
    actors = movie.cast.filter(picture__isnull=False)[:8]  # Filter out actors with no picture
    return render(request, 'movie_detail.html', {'movie': movie, 'actors': actors})

def tv_details(request,tv_id):
    tv_show = get_object_or_404(TVShow,id=tv_id)
    actors = tv_show.cast.filter(picture__isnull=False)[:8]
    return render(request,'tv_details.html',{'tvshows': tv_show,'actors':actors})

class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

class TVShowViewSet(viewsets.ModelViewSet):
    queryset = TVShow.objects.all()
    serializer_class = TVShowSerializer

class DocumentaryViewSet(viewsets.ModelViewSet):
    queryset = Documentary.objects.all()
    serializer_class = DocumentarySerializer

class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer

class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer
