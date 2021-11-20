from django.db import models

from socialDistribution import requests as api_requests


class Follow(models.Model):
    object = models.ForeignKey('LocalAuthor', on_delete=models.CASCADE, related_name="follows")
    actor = models.ForeignKey('Author', on_delete=models.CASCADE, related_name="following")

    class Meta:
        # Django Software Foundation, "UniqueConstraint", 2021-11-06,
        # https://docs.djangoproject.com/en/3.2/ref/models/constraints/#uniqueconstraint
        constraints = [
            # do not allow actor to follow same object more than once
            models.UniqueConstraint(fields=['actor', 'object'], name='unique_follow'),
        ]

    def is_friend(self):
        # make api request
        actor_url = self.actor.url.strip('/')
        object_url = self.object.url.strip('/')
        endpoint = actor_url + '/followers/' + object_url
        status_code, response_body = api_requests.get(endpoint)

        # check if GET request came back with author object
        if status_code == 200 and response_body and response_body.get("id") == object_url:
            return True
        else:
            return False
