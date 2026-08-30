"""Point d'entrée WSGI.

WhiteNoise sert déjà les fichiers statiques via le middleware. On l'enveloppe
ici une seconde fois pour ``MEDIA_ROOT`` : le logo, le hero et le portrait sont
désormais administrables, donc servis depuis ``media/``. ``autorefresh`` est
indispensable — sans lui, seules les images présentes au démarrage seraient
visibles, et un envoi fait en admin resterait introuvable jusqu'au redémarrage.

Un serveur frontal (nginx, Caddy…) qui sert déjà ``/media/`` prend simplement
la main avant d'arriver ici ; les deux réglages ne se gênent pas.
"""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
application = get_wsgi_application()

from django.conf import settings  # noqa: E402 — après l'initialisation de Django
from whitenoise import WhiteNoise  # noqa: E402

application = WhiteNoise(
    application,
    root=settings.MEDIA_ROOT,
    prefix=settings.MEDIA_URL,
    autorefresh=True,
)
