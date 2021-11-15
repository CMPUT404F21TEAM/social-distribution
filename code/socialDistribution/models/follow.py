from django.db import models

from urllib.parse import quote_plus, urljoin

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
        encoded_object_url = quote_plus(self.object.url)
        actor_url = self.object.url
        endpoint = urljoin(actor_url, f"follow/{encoded_object_url}")
        response_body = api_requests.get(endpoint)

        return True if response_body.get("status") else False
