import hashlib
import secrets

from django.conf import settings
from django.db import models
from django.utils import timezone


class Token(models.Model):
    """Bearer token for JSON API access without session or CSRF."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="djcrud_api_tokens",
    )
    name = models.CharField(max_length=255)
    key_hash = models.CharField(max_length=64, unique=True)
    prefix = models.CharField(max_length=8)
    created = models.DateTimeField(auto_now_add=True)
    expires = models.DateTimeField(null=True, blank=True)
    last_used = models.DateTimeField(null=True, blank=True)

    class Meta:
        default_permissions = ("add", "delete", "view")
        verbose_name = "API token"
        verbose_name_plural = "API tokens"

    def __str__(self):
        return f"{self.name} ({self.prefix}…)"

    @classmethod
    def hash_key(cls, raw_key):
        return hashlib.sha256(raw_key.encode()).hexdigest()

    @classmethod
    def generate(cls, user, name, expires=None):
        """Create a token row and return ``(instance, raw_key)`` (shown once)."""
        raw_key = secrets.token_urlsafe(32)
        token = cls.objects.create(
            user=user,
            name=name,
            key_hash=cls.hash_key(raw_key),
            prefix=raw_key[:8],
            expires=expires,
        )
        return token, raw_key

    def is_expired(self):
        if self.expires is None:
            return False
        return timezone.now() >= self.expires

    @classmethod
    def authenticate(cls, raw_key):
        """Return a valid token for *raw_key*, or ``None``."""
        if not raw_key:
            return None
        try:
            token = cls.objects.select_related("user").get(
                key_hash=cls.hash_key(raw_key),
            )
        except cls.DoesNotExist:
            return None
        if token.is_expired() or not token.user.is_active:
            return None
        return token

    def touch_last_used(self):
        self.last_used = timezone.now()
        self.save(update_fields=["last_used"])
