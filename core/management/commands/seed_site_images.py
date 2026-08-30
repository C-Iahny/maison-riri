"""Recopie les visuels d'origine de ``static/img`` dans les images du site.

Sans cette étape, le back-office afficherait une liste vide alors que le site
montre déjà des images : les gabarits retombent en effet sur les fichiers
statiques tant qu'aucun envoi n'a été fait. La commande donne donc à
l'administratrice un point de départ visible et remplaçable.

    python manage.py seed_site_images
    python manage.py seed_site_images --reset   # revient aux visuels d'origine
"""
from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from core.models import SiteImage

SOURCE = settings.BASE_DIR / "static" / "img"

STARTERS = {
    SiteImage.Slot.LOGO: (
        "logo.jpg",
        "Maison Riri Design",
        "Maison Riri Design",
    ),
    SiteImage.Slot.HERO: (
        "hero.jpg",
        "Arche décorative en ballons réalisée par Maison Riri Design",
        "Dekorativer Ballonbogen von Maison Riri Design",
    ),
    SiteImage.Slot.PORTRAIT: (
        "portrait.jpg",
        "Rinazar Andriampeno, fondatrice de Maison Riri Design",
        "Rinazar Andriampeno, Gründerin von Maison Riri Design",
    ),
    SiteImage.Slot.ATMOSPHERE: (
        "atmosphere.jpg",
        "Moodboard Red Wine — ambiance, tablescape et détails floraux",
        "Moodboard Red Wine — Stimmung, Tablescape und florale Details",
    ),
    SiteImage.Slot.SHARE: (
        "hero.jpg",
        "Maison Riri Design",
        "Maison Riri Design",
    ),
}


class Command(BaseCommand):
    help = "Charge les visuels d'origine dans les images administrables du site."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Remplace les images déjà envoyées par les visuels d'origine.",
        )

    def handle(self, *args, **options):
        if not SOURCE.is_dir():
            self.stderr.write("Dossier d'images introuvable : %s" % SOURCE)
            return

        for slot, (filename, alt_fr, alt_de) in STARTERS.items():
            origin = SOURCE / filename
            if not origin.is_file():
                self.stderr.write("• %s ignoré : %s est absent." % (slot, filename))
                continue

            existing = SiteImage.objects.filter(slot=slot).first()
            if existing and not options["reset"]:
                self.stdout.write("• %s déjà défini, ignoré (--reset pour recharger)." % slot)
                continue

            image = existing or SiteImage(slot=slot)
            if image.image:
                # Sans cela, chaque --reset laisserait une copie « nom_XyZ.jpg ».
                image.image.delete(save=False)
            image.alt_fr, image.alt_de = alt_fr, alt_de
            with open(origin, "rb") as handle:
                image.image.save("%s.jpg" % slot, File(handle), save=False)
            image.save()
            self.stdout.write(self.style.SUCCESS("• %s chargé depuis %s." % (slot, filename)))
