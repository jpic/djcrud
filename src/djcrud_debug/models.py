from django.db import models

from .routing_debug import RouteCollection, get_built_site, walk_site


class RouterManager(models.Manager):
    def get_queryset(self):
        site = get_built_site()
        return RouteCollection(walk_site(site)["routers"])


class URLManager(models.Manager):
    def get_queryset(self):
        site = get_built_site()
        return RouteCollection(walk_site(site)["urls"])


class Router(models.Model):
    app = models.CharField(max_length=255, blank=True, default="")
    model = models.CharField(max_length=255, blank=True, default="")
    codename = models.CharField(max_length=255, blank=True, default="")
    urlpath = models.CharField(max_length=255, blank=True, default="")
    urlname = models.CharField(max_length=255, blank=True, default="")

    objects = RouterManager()

    class Meta:
        managed = False

    def __str__(self):
        return self.pk


class URL(models.Model):
    router = models.ForeignKey(
        Router,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="urls",
    )
    urlpath = models.CharField(max_length=255, blank=True, default="")
    fullurlpath = models.CharField(max_length=512, blank=True, default="")
    urlname = models.CharField(max_length=255, blank=True, default="")
    urlfullname = models.CharField(max_length=512, blank=True, default="")
    view_class = models.CharField(max_length=255, blank=True, default="")
    view_module = models.CharField(max_length=255, blank=True, default="")
    tags = models.CharField(max_length=255, blank=True, default="")

    objects = URLManager()

    class Meta:
        managed = False

    def __str__(self):
        return self.urlfullname or self.view_class
