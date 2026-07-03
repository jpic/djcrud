from django.db import models


class Article(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    category = models.CharField(max_length=50, blank=True)
    published = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class Post(models.Model):
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.title