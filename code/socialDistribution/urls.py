from django.urls import path
from . import views

urlpatterns = [
  path('', views.index, name='index'),
  path('login/', views.loginPage, name='login'),
  path('register/', views.register, name='register'),
  path('logout/', views.logoutUser, name='logout'),
  path('home/', views.home, name='home'),
  path('authors/', views.authors, name='authors'),
  path('posts/', views.posts, name='posts'),
  path('create/', views.create, name='create'),
  path('profile/', views.profile, name='profile'),
  path('user/', views.user, name='user'),
]