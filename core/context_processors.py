"""Expose les coordonnées de la maison et ses visuels à tous les gabarits."""
from django.conf import settings

from .models import SiteImage


def site_settings(request):
    return {
        "site": settings.SITE_INFO,
        "google_form_url": settings.GOOGLE_FORM_ACTION.replace("formResponse", "viewform"),
        # Logo, hero, portrait… : administrables depuis le back-office.
        "site_images": SiteImage.all_slots(),
    }
