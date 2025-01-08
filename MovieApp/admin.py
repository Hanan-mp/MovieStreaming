from django.contrib import admin

# Register your models here.
from . models import Profile,Movie,Genre
# Register your models here.
class registerAdmin(admin.ModelAdmin):
    list_display = ["image","phone","country"]
    admin.site.register(Profile)
    admin.site.register(Movie)
    admin.site.register(Genre)
  