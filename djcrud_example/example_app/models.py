from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse


class User(AbstractUser):
    """Custom User model for the example application.

    Adds get_absolute_url() so that CreateView/UpdateView success_url works
    (returns the detail view URL for the user object). This is the recommended
    Django pattern when you need model-specific URL behavior.
    """

    class Meta:
        """Meta options for the custom User model."""
        # swappable inherited from AbstractUser via AUTH_USER_MODEL setting.
        # No db_table to allow proper migrations as per user instruction.

    def get_absolute_url(self):
        """Return the URL to this user's detail view.

        Uses the namespaced URL from the UserController ('auth:user:detail').
        See tests/test_url_consistency.py for how namespace + urlname works.
        """
        return reverse('auth:user:detail', args=[self.pk])
