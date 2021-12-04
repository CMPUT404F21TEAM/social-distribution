from django.urls import path

from .views import *

app_name = 'api'
urlpatterns = [
    path('', index, name='index'),
    path('authors/', AuthorsView.as_view(), name='authors'),
    path('author/<uuid:author_id>', AuthorView.as_view(), name='author'),
    path('author/<uuid:author_id>/followers', FollowersView.as_view(), name='followers'),
    path('author/<uuid:author_id>/followers/<path:foreign_author_id>', FollowersSingleView.as_view(), name='followers-single'),
    path('author/<uuid:author_id>/liked', LikedView.as_view(), name='liked'),
    path('author/<uuid:author_id>/posts', PostsView.as_view(), name='posts'),
    path('author/<uuid:author_id>/posts/<uuid:post_id>', PostView.as_view(), name='post'),
    path('author/<uuid:author_id>/posts/<uuid:post_id>/likes', PostLikesView.as_view(), name='post_likes'),
    path('author/<uuid:author_id>/posts/<uuid:post_id>/comments', PostCommentsView.as_view(), name='post_comments'),
    path('author/<uuid:author_id>/posts/<uuid:post_id>/comments/', PostCommentsView.as_view(), name='post_comments'),
    path('author/<uuid:author_id>/posts/<uuid:post_id>/comments/<uuid:comment_id>', PostCommentsSingleView.as_view(), name='post_comments_single'),
    path('author/<uuid:author_id>/posts/<uuid:post_id>/comments/<uuid:comment_id>/', PostCommentsSingleView.as_view(), name='post_comments_single'),
    path('author/<uuid:author_id>/posts/<uuid:post_id>/comments/<uuid:comment_id>/likes', CommentLikesView.as_view(), name='comment_likes'),
    path('author/<uuid:author_id>/inbox', InboxView.as_view(), name='inbox'),
    path('author/<uuid:author_id>/inbox/', InboxView.as_view(), name='inbox'),
]