"""Test models for E2E testing."""
from django.db import models


class Article(models.Model):
    """Simple test model for CRUD testing."""
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)

    class Meta:
        app_label = 'tests'

    def __str__(self):
        return self.title
