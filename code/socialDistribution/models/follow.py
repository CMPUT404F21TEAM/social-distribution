from django.db import models
from django.utils import timezone


import datetime


import socialDistribution.requests as api_requests


class Follow(models.Model):
    object = models.ForeignKey('Author', on_delete=models.CASCADE, related_name="follows")
    actor = models.ForeignKey('Author', on_delete=models.CASCADE, related_name="following")

    _last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        # Django Software Foundation, "UniqueConstraint", 2021-11-06,
        # https://docs.djangoproject.com/en/3.2/ref/models/constraints/#uniqueconstraint
        constraints = [
            # do not allow actor to follow same object more than once
            models.UniqueConstraint(fields=['actor', 'object'], name='unique_follow'),
        ]

    @classmethod
    def are_friends(cls, author1, author2):
        """ Checks if bidirectional follows exist between author1 and author2. That is, checks if author1
            and author2 are friends.
        """

        first = cls.objects.filter(actor_id=author1.id, object_id=author2.id).exists()
        second = cls.objects.filter(actor_id=author2.id, object_id=author1.id).exists()
        return first and second

    def up_to_date(self):
        """ Checks if the follow data is currently up do date. Returns true if either the 
            data is always maintained up-to-date or if the data was recently refreshed
        """

        limit = timezone.now()-datetime.timedelta(seconds=3)
        was_recent_update = self._last_updated > limit

        # return true if just updated
        return was_recent_update
