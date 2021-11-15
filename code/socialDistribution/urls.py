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
  path('author/<int:author_id>/posts/<int:post_id>', views.post, name='post'),
  path('author/<int:author_id>/befriend/', views.befriend, name='befriend'),
  path('author/<int:author_id>/un-befriend/', views.un_befriend, name='un-befriend'),
  path('author/<int:author_id>/friend-request/<str:action>', views.friend_request, name='friend-request'),
  path('create/', views.create, name='create'),
  path('profile/', views.profile, name='profile'),
  path('user/', views.user, name='user'),

  path('like-post/<int:id>', views.likePost, name='likePost'),
  path('comment-post/<int:id>', views.commentPost, name='commentPost'),
  path('like-comment/<int:id>', views.likeComment, name='likeComment'),
  path('delete-post/<int:id>', views.deletePost, name='deletePost'),
  path('edit-post/<int:id>', views.editPost, name='editPost'),
  path('share-post/<int:id>', views.sharePost, name='sharePost'),
  
]
