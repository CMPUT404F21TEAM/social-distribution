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
  path('author/<uuid:author_id>/', views.author, name='author'),
  path('home/', views.home, name='home'),
  path('author/<uuid:author_id>/posts/', views.posts, name='posts'),
  path('unlisted/<uuid:post_id>', views.unlisted_post_image, name='unlisted-post-image'),
  path('author/<uuid:author_id>/befriend/', views.befriend, name='befriend'),
  path('author/<uuid:author_id>/un-befriend/', views.un_befriend, name='un-befriend'),
  path('author/<uuid:author_id>/friend-request/<str:action>', views.friend_request, name='friend-request'),
  path('author/unlisted-posts', views.unlisted_posts, name='unlisted-posts'),
  path('create/', views.create, name='create'),
  path('profile/', views.profile, name='profile'),
  path('user/', views.user, name='user'),

  path('posts/<str:post_type>/<uuid:id>/', views.single_post, name='single-post'),
  path('posts/<str:post_type>/<uuid:id>/like', views.like_post, name='like-post'),
  path('like-comment/', views.like_comment, name='like-comment'),
  path('author/<author_id>/posts/<uuid:post_id>/comments/', views.post_comment, name='post-comment'),
  path('delete-post/<uuid:id>', views.delete_post, name='delete-post'),
  path('edit-post/<uuid:id>', views.edit_post, name='edit-post'),
  path('share-post/<uuid:id>', views.share_post, name='share-post'),
  path('copy-link/<uuid:id>', views.copy_link, name='copy-link'),
  path('public-share/<str:id>/', views.public_share, name='public-share'),

]
