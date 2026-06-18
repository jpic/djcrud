"""
Django settings for djcrud tests.

Uses os.getenv('DJCRUD_FRONTEND', 'djcrud_bulma') to dynamically include only one frontend in INSTALLED_APPS.
This avoids having both packages loaded simultaneously.
"""
import os

SECRET_KEY = "test-secret-key-for-djcrud-tests"

DEBUG = True

ALLOWED_HOSTS = ["testserver"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_tables2",
    "crispy_forms",
    "crispy_bootstrap5",  # for bootstrap frontend (only loaded when selected)
    "crispy_bulma",  # required for bulma template pack and its templates (INSTALLED_APPS per crispy-bulma docs)
    "djcrud",
    os.getenv("DJCRUD_FRONTEND", "djcrud_bulma"),
    "djcrud_auth",
]

# Frontend is selected via DJCRUD_FRONTEND env var (default: djcrud_bulma).
# Only one frontend app is added to INSTALLED_APPS (via os.getenv above). The selected
# frontend's AppConfig.ready() auto-configures CRISPY_*, DJCRUD_TABLES2_*, etc.
# CRISPY settings are set by the frontend AppConfig.ready() based on DJCRUD_FRONTEND.
# djcrud_bulma/apps.py sets CRISPY_TEMPLATE_PACK="bulma" and CRISPY_ALLOWED_TEMPLATE_PACKS.
# crispy-bulma package (installed via [bulma] extra) provides all bulma/ templates
# (uni_form.html, field.html, layout/*, errors.html). No local overrides in djcrud_bulma/templates/bulma/.
# This uses crispy-bulma exclusively and removes all traces of legacy uni_form.

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "djcrud_example.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                # No djcrud.context_processors needed: mvc.View.get_context_data injects `view` + `site_controller=root_controller`
            ],
        },
    },
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
