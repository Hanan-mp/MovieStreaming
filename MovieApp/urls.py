
from django.urls import path,include
from . import views
from rest_framework.routers import DefaultRouter
from .views import ActorViewSet, MovieViewSet, TVShowViewSet, DocumentaryViewSet, GenreViewSet

router = DefaultRouter()
router.register(r'movies', MovieViewSet)
router.register(r'tvshows', TVShowViewSet)
router.register(r'documentaries', DocumentaryViewSet)
router.register(r'genres', GenreViewSet)
router.register(r'actor', ActorViewSet) 

urlpatterns = [
    path('',views.getStart,name="in"),
    path('home/',views.home,name="home"),
    #authentication
    path('signup/',views.signup,name="signup"),
    path('signin/',views.signin,name="signin"),
    path('logout/',views.user_logout,name="logout"),
    #forget password
    path('forget_password/',views.forgot_password,name="forget_password"),
    path('password_reset_sent/<str:reset_id>/',views.password_reset_sent,name="password_reset_sent"),
    path('change_password/<str:reset_id>/',views.change_password,name="change_password"),
    #upadate user profile
    path('view_user/',views.view_user,name="view_user"),
    path('update_user/',views.update_user,name="update_user"),
    path('update_user_password',views.update_user_password,name="update_user_password"),
    path('add_profile',views.add_profile,name="add_profile"),
    #movie details
    path("movie_details/<int:movie_id>/",views.movie_details,name="movie_details"),
    path('api/', include(router.urls)),
    path('movies/genre/<int:genre_id>/', views.movie_list_by_genre, name='movie_list_by_genre'),
    path('tvshows/',views.tvshow_list,name="tvshows"),
    path('tvshows/genre/<int:genre_id>/', views.tvshow_list_by_genre, name='tvshow_list_by_genre'),
    path("tvshow_details/<int:tv_id>/",views.tv_details,name="tvshow_details"),
   
]