"""
Django settings for cleo_web project.

Generated by 'django-admin startproject' using Django 5.0.6.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

from pathlib import Path

import environ

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
    INTERNAL_IPS=(list, []),
    YGOR_TELESCOPE=(str, "/home/gbt"),
    CACHE_MIDDLEWARE_SECONDS=(int, 60),
)
environ.Env.read_env(env.str("ENV_PATH", "cleo_web/.env"))

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

CHALICE_HOST=env("CHALICE_HOST")
CHALICE_PORT=env("CHALICE_PORT")

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")

ALLOWED_HOSTS = env("ALLOWED_HOSTS")
INTERNAL_IPS = env("INTERNAL_IPS")
STATIC_ROOT = env("STATIC_ROOT")

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "pgtrigger",
    "debug_toolbar",
    "django_extensions",
    "alda.audit",
    "alda.atoll",
    "alda.disk",
    "tortoise",
    "devex",
]

STATIC_URL = env("STATIC_URL")
FORCE_SCRIPT_NAME = env("FORCE_SCRIPT_NAME")

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.cache.UpdateCacheMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.cache.FetchFromCacheMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

ROOT_URLCONF = "cleo_web.urls"

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
            ],
        },
    },
]

WSGI_APPLICATION = "cleo_web.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASE_ROUTERS = ["cleo_web.db_routers.DbRouter"]

DATABASES = {
    "default": {
        **env.db("DJANGO_DB_URL"),
        "CONN_MAX_AGE": 3600,
        "TEST": {"DEPENDENCIES": []},
    },
    "turtle": {
        **env.db("TURTLE_DB_URL"),
        "OPTIONS": {"sql_mode": "STRICT_ALL_TABLES"},
        "CONN_MAX_AGE": 3600,
        "TIME_ZONE": "UTC",
        "TEST": {"DEPENDENCIES": []},
    },
    "alda": {
        **env.db("ALDA_DB_URL"),
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "America/New_York"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SHOW_TOOLBAR_CALLBACK = lambda request: True


CACHES = {
    "default": {
        **env.cache(),
        "OPTIONS": {
            "binary": True,
            "behaviors": {
                "ketama": True,
            },
        },
    },
}
CACHE_MIDDLEWARE_SECONDS = env("CACHE_MIDDLEWARE_SECONDS")
KEY_PREFIX="chip"
