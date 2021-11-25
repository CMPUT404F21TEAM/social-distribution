from django.urls import path
from . import views

app_name = 'socialDistribution'
urlpatterns = [
  path('', views.index, name='index'),

  path('login/', views.loginPage, name='login'),
  path('register/', views.register, name='register'),
  path('logout/', views.logoutUser, name='logout'),
  path('inbox/', views.inbox, name='inbox'),

  path('author/', views.authors, name='authors'),
  path('author/<int:author_id>/', views.author, name='author'),
  path('home/', views.home, name='home'),
  path('author/<int:author_id>/posts/', views.posts, name='posts'),
  path('unlisted/<int:post_id>', views.unlisted_post_image, name='unlisted-post-image'),
  path('author/<int:author_id>/befriend/', views.befriend, name='befriend'),
  path('author/<int:author_id>/un-befriend/', views.un_befriend, name='un-befriend'),
  path('author/<int:author_id>/friend-request/<str:action>', views.friend_request, name='friend-request'),
  path('create/', views.create, name='create'),
  path('profile/', views.profile, name='profile'),
  path('user/', views.user, name='user'),

  path('like-post/<int:id>/<str:post_host>', views.like_post, name='like-post'),
  path('posts/<str:post_type>/<int:id>/', views.single_post, name='single-post'),
  path('like-comment/', views.like_comment, name='like-comment'),
  path('delete-post/<int:id>', views.delete_post, name='delete-post'),
  path('edit-post/<int:id>', views.edit_post, name='edit-post'),
  path('share-post/<int:id>', views.share_post, name='share-post')
]
