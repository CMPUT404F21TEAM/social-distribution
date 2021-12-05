from django.contrib.auth.models import User
from mixer.backend.django import mixer
import base64
from socialDistribution.models import LocalAuthor

TEST_PASSWORD = "123456"


def create_author():
    user = mixer.blend(User)
    user.set_password(TEST_PASSWORD)
    user.save()
    author = LocalAuthor.objects.create(username=user.username, user=user)
    return LocalAuthor.objects.get(id=author.id)  # refetch to get the generated ID


def get_basic_auth(author):
    username = author.user.username
    credentials = str.encode(f'{username}:{TEST_PASSWORD}')
    return {
        'HTTP_AUTHORIZATION': 'Basic %s' % base64.b64encode(credentials).decode("ascii"),
    }
