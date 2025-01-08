# movie_manager/serializers.py

from rest_framework import serializers
from .models import Movie, TVShow, Documentary, Genre ,Actor

class ActorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actor
        fields = ['name', 'picture']  # Include only the fields you need


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ['id', 'name']

class MovieSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True)

    class Meta:
        model = Movie
        fields = ['id', 'title', 'release_date', 'plot', 'genres', 'cast','poster','duration','rating']
        

class TVShowSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True)

    class Meta:
        model = TVShow
        fields = ['id', 'title', 'release_date', 'plot', 'seasons', 'genres', 'cast','poster','duration','rating']

class DocumentarySerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True)

    class Meta:
        model = Documentary
        fields = ['id', 'title', 'release_date', 'plot', 'genres', 'cast']
