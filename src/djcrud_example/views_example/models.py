from django.conf import settings
from django.db import models


class Article(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    category = models.CharField(max_length=50, blank=True)
    published = models.BooleanField(default=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="articles",
        null=True,
        blank=True,
    )

    def publish(self):
        self.published = True
        self.save(update_fields=["published"])

    def __str__(self):
        return self.title
