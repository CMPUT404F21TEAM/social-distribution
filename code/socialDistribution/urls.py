from django.urls import path
from django.contrib import admin
from . import views

urlpatterns = [
  path('', views.index, name='index'),
  path('home/', views.home, name='home'),
  path('authors/', views.authors, name='authors'),
  path('create/', views.create, name='create'),
  path('post/', views.post, name='post'),
  path('profile/', views.profile, name='profile'),
  path('register/', views.register, name='register'),
  path('user/', views.user, name='user'),
]