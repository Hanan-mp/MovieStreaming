from django.db import models
from django.contrib.auth.models import User
import uuid
# Create your models here.

class PasswordReset(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    reset_id = models.UUIDField(default=uuid.uuid4,unique=True,editable=False)
    created_when = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Password reset for {self.user.username} at {self.created_when}"
    
class Profile(models.Model):
    user = models.OneToOneField(User, null=True, on_delete=models.CASCADE)
    
    # New fields
    phone = models.CharField(max_length=15, blank=True, null=True)  # Phone number
    country = models.CharField(max_length=100, blank=True, null=True)  # Country

    def __str__(self):
        return f'{self.user.username} Profile'

class Profile_picture(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, default=1)  # Ensure one profile picture per user
    image = models.ImageField(upload_to='profile_pictures/')

    def __str__(self):
        return f"Profile picture of {self.user.username}"

class Genre(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Actor(models.Model):
    name = models.CharField(max_length=255)
    picture = models.ImageField(upload_to='actors/', null=True, blank=True)

    def __str__(self):
        return self.name

class Movie(models.Model):
    tmdb_id = models.IntegerField(unique=True)
    title = models.CharField(max_length=255)
    release_date = models.DateField()
    plot = models.TextField()
    genres = models.ManyToManyField(Genre)
    cast = models.ManyToManyField(Actor, related_name='movies')  # Many-to-many relationship
    poster = models.ImageField(upload_to='posters/', null=True, blank=True)
    language = models.CharField(max_length=255, null=True, blank=True)  # New field for language
    duration = models.PositiveIntegerField(null=True, blank=True)  # Duration of the movie in minutes
    rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)  # Rating (e.g., IMDb rating)
    
    def __str__(self):
        return self.title

class TVShow(models.Model):
    tmdb_id = models.IntegerField(unique=True)
    title = models.CharField(max_length=255)
    release_date = models.DateField()
    plot = models.TextField()
    seasons = models.IntegerField()
    genres = models.ManyToManyField(Genre)
    cast = models.ManyToManyField(Actor, related_name='tvshows')  # Many-to-many relationship
    poster = models.ImageField(upload_to='posters/', null=True, blank=True)
    language = models.CharField(max_length=255, null=True, blank=True)  # New field for language
    duration = models.PositiveIntegerField(null=True, blank=True)  # Duration of a single episode or the series in minutes
    rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)  # Rating (e.g., IMDb rating)
    
    def __str__(self):
        return self.title

class Documentary(models.Model):
    title = models.CharField(max_length=255)
    release_date = models.DateField()
    plot = models.TextField()
    genres = models.ManyToManyField(Genre)
    cast = models.ManyToManyField(Actor, related_name='documentaries')  # Many-to-many relationship
    poster = models.ImageField(upload_to='posters/', null=True, blank=True)
    language = models.CharField(max_length=255, null=True, blank=True)  # New field for language
    duration = models.PositiveIntegerField(null=True, blank=True)  # Duration of the documentary in minutes
    rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)  # Rating (e.g., IMDb rating)
    
    def __str__(self):
        return self.title

class Upcoming(models.Model):
    tmdb_id = models.IntegerField(unique=True)
    title = models.CharField(max_length=255)
    release_date = models.DateField()
    plot = models.TextField()
    seasons = models.IntegerField()
    genres = models.ManyToManyField(Genre)
    poster = models.ImageField(upload_to='posters/', null=True, blank=True)
    language = models.CharField(max_length=255, null=True, blank=True)  # New field for language
    duration = models.PositiveIntegerField(null=True, blank=True)  # Duration of a single episode or the series in minutes
    rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)  # Rating (e.g., IMDb rating)
    
    def __str__(self):
        return self.title