"""Réglages Django pour le site Maison Riri Design."""
import os
from pathlib import Path

from django.templatetags.static import static
from django.urls import reverse_lazy

BASE_DIR = Path(__file__).resolve().parent.parent


def env(name, default=""):
    return os.environ.get(name, default)


def env_bool(name, default=False):
    return env(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    """Découpe une variable « a,b,c ».

    Les espaces autour des valeurs sont tolérés : une liste recopiée avec des
    espaces est une cause classique de ``DisallowedHost``, difficile à voir.
    """
    return [item.strip() for item in env(name, default).split(",") if item.strip()]


SECRET_KEY = env("DJANGO_SECRET_KEY", "dev-insecure-change-me-before-production")
DEBUG = env_bool("DJANGO_DEBUG", True)

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,[::1]")
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

INSTALLED_APPS = [
    "unfold",  # habillage du back-office, à placer avant django.contrib.admin
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.template.context_processors.i18n",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.site_settings",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Base de données et fichiers envoyés vivent au même endroit : sur un hébergeur
# à conteneurs (Railway, Render…), le disque est remis à zéro à chaque
# déploiement. Pointer DJANGO_DATA_DIR vers un volume persistant met donc à
# l'abri, d'un seul réglage, la base ET les images changées depuis l'admin.
DATA_DIR = Path(env("DJANGO_DATA_DIR", str(BASE_DIR)))

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": DATA_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Internationalisation : le site vit en français et en allemand -----------
LANGUAGE_CODE = "fr"
LANGUAGES = [("fr", "Français"), ("de", "Deutsch")]
LOCALE_PATHS = [BASE_DIR / "locale"]
TIME_ZONE = "Europe/Paris"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
# Le manifeste (noms de fichiers versionnés) suppose un collectstatic préalable :
# on ne l'active donc qu'en dehors du mode développement et des tests.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        )
    },
}

MEDIA_URL = "media/"
MEDIA_ROOT = DATA_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 30 * 1024 * 1024
DATA_UPLOAD_MAX_NUMBER_FILES = 12

# --- Coordonnées affichées sur le site --------------------------------------
SITE_INFO = {
    "brand": "Maison Riri Design",
    "founder": "Rinazar Andriampeno",
    "email": env("MRD_EMAIL", "hello.maisonriri@gmail.com"),
    # Adresse postale complète (mentions légales). Sauts de ligne : « | ».
    "address": env("MRD_ADDRESS", "").replace("|", "\n").strip(),
    "phone": env("MRD_PHONE", ""),
    "instagram": env("MRD_INSTAGRAM", "https://www.instagram.com/maisonriri.design/"),
    "facebook": env("MRD_FACEBOOK", ""),
    "regions": ["Freiburg im Breisgau", "Alsace", "Basel"],
}

# --- Passerelle vers le formulaire Google existant ---------------------------
# Les demandes sont enregistrées en base puis recopiées dans le Google Form du
# client, afin que la feuille de calcul déjà en place continue d'être alimentée.
GOOGLE_FORM_ACTION = env(
    "MRD_GOOGLE_FORM_ACTION",
    "https://docs.google.com/forms/d/e/"
    "1FAIpQLSfqS62pgb44k0osi1hDn9S3DV0xWws3nHlLE-y9oZwQEX0J2A/formResponse",
)
GOOGLE_FORM_ENABLED = env_bool("MRD_GOOGLE_FORM_ENABLED", True)
GOOGLE_FORM_TIMEOUT = float(env("MRD_GOOGLE_FORM_TIMEOUT", "8"))

# --- E-mail : notification de nouvelle demande ------------------------------
EMAIL_BACKEND = env("DJANGO_EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = env("DJANGO_EMAIL_HOST", "")
EMAIL_PORT = int(env("DJANGO_EMAIL_PORT", "587"))
EMAIL_HOST_USER = env("DJANGO_EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = env("DJANGO_EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("DJANGO_EMAIL_USE_TLS", True)
DEFAULT_FROM_EMAIL = env("DJANGO_DEFAULT_FROM_EMAIL", "Maison Riri Design <no-reply@localhost>")
QUOTE_NOTIFICATION_RECIPIENTS = env_list("MRD_NOTIFY_EMAILS", SITE_INFO["email"])

if not DEBUG:
    # Derrière le proxy d'un hébergeur (Railway, Render, Heroku…), la connexion
    # arrive en HTTP dans le conteneur alors que le visiteur est bien en HTTPS.
    # Sans cet en-tête, SECURE_SSL_REDIRECT boucle indéfiniment.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_REFERRER_POLICY = "same-origin"
    X_FRAME_OPTIONS = "DENY"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}


# --- Back-office (django-unfold) ---------------------------------------------
# Une interface simple, en français, pensée pour une utilisation sans
# connaissance technique : quatre rubriques, un tableau de bord, une page d'aide.
UNFOLD = {
    "SITE_TITLE": "Maison Riri Design",
    "SITE_HEADER": "Maison Riri Design",
    "SITE_SUBHEADER": "Administration du site",
    "SITE_SYMBOL": "celebration",
    "SITE_URL": "/",
    "SHOW_HISTORY": False,
    "SHOW_VIEW_ON_SITE": True,
    "SHOW_BACK_BUTTON": True,
    "DASHBOARD_CALLBACK": "core.admin.dashboard_callback",
    "STYLES": [lambda request: static("css/admin.css")],
    "COLORS": {
        "primary": {
            "50": "#fbf3f4", "100": "#f6e3e6", "200": "#eec5cb", "300": "#de9aa5",
            "400": "#c6667a", "500": "#a83f57", "600": "#8e2a45", "700": "#6f1d35",
            "800": "#55182b", "900": "#4a1220", "950": "#2c0a12",
        },
    },
    "SIDEBAR": {
        "show_search": False,
        "show_all_applications": False,
        "navigation": [
            {
                "title": "Le site",
                "items": [
                    {"title": "Tableau de bord", "icon": "dashboard", "link": reverse_lazy("admin:index")},
                    {"title": "Images du site", "icon": "image", "link": reverse_lazy("admin:core_siteimage_changelist")},
                    {"title": "Textes du site", "icon": "edit_note", "link": reverse_lazy("admin:core_sitetext_changelist")},
                    {"title": "Portfolio", "icon": "photo_library", "link": reverse_lazy("admin:core_project_changelist")},
                ],
            },
            {
                "title": "Clients",
                "separator": True,
                "items": [
                    {
                        "title": "Demandes de devis", "icon": "mail",
                        "link": reverse_lazy("admin:core_quoterequest_changelist"),
                        "badge": "core.admin.new_quotes_badge",
                    },
                ],
            },
            {
                "title": "Réglages",
                "separator": True,
                "items": [
                    {"title": "Aide", "icon": "help", "link": reverse_lazy("admin_help")},
                    {
                        "title": "Comptes", "icon": "person",
                        "link": reverse_lazy("admin:auth_user_changelist"),
                        "permission": lambda request: request.user.is_superuser,
                    },
                    {"title": "Voir le site", "icon": "open_in_new", "link": "/"},
                ],
            },
        ],
    },
}
