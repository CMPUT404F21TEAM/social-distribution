from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('authors/', views.authors, name='authors'),
    path('authors/<author_id>/', views.author, name='author'),
    path('authors/<author_id>/followers/', views.followers, name='followers'),
    path('authors/<author_id>/liked/', views.liked, name='liked'),
    path('authors/<author_id>/posts/<post_id>/', views.post, name='post'),
    path('authors/<author_id>/posts/<post_id>/likes/', views.post_likes, name='post_likes'),
    path('authors/<author_id>/posts/<post_id>/comments/', views.post_comments, name='post_comments'),
    path('authors/<author_id>/posts/<post_id>/comments/<comment_id>/likes/', views.comment_likes, name='comment_likes'),
    path('authors/<author_id>/inbox/', views.inbox, name='inbox'),
]