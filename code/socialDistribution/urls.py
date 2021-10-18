from django.urls import path
from . import views

app_name = 'socialDistribution'
urlpatterns = [
  path('', views.index, name='index'),
  path('app/login/', views.loginPage, name='login'),
  path('app/register/', views.register, name='register'),
  path('app/logout/', views.logoutUser, name='logout'),
  path('app/author/', views.authors, name='authors'),
  path('app/author/<int:author_id>/', views.author, name='author'),
  path('app/author/<int:author_id>/home/', views.home, name='home'),
  path('app/author/<int:author_id>/posts/', views.posts, name='posts'),
  path('app/author/<int:author_id>/befriend/', views.befriend, name='befriend'),
  path('app/author/<int:author_id>/un-befriend/', views.un_befriend, name='un-befriend'),
  path('app/<int:author_id>/accept-friend/', views.accept_friend, name='accept-friend'),
  path('app/create/', views.create, name='create'),
  path('app/profile/', views.profile, name='profile'),
  path('app/user/', views.user, name='user'),
  path('app/like-post/<int:id>', views.likePost, name='likePost'),
  path('app/delete-post/<int:id>', views.deletePost, name='deletePost'),
  path('app/edit-post/<int:id>', views.editPost, name='editPost'),
]