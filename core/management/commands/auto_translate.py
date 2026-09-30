"""Traduit les textes dont une seule langue est renseignée (rattrapage).

Utile après l'activation de la traduction automatique, ou après une panne :
tout ce qui a été enregistré avec une langue vide est complété. La même
opération existe dans l'admin (action « Compléter les traductions manquantes »).

    python manage.py auto_translate
"""
from django.core.management.base import BaseCommand

from core import translate
from core.models import PaletteColor, Project, ProjectImage, SiteImage, SiteText


class Command(BaseCommand):
    help = "Complète, par traduction automatique, les champs FR/DE laissés vides."

    def handle(self, *args, **options):
        if not translate.is_enabled():
            self.stderr.write("Traduction automatique désactivée (MRD_AUTO_TRANSLATE=0 ou mode test).")
            return
        done = 0
        for model in (Project, ProjectImage, PaletteColor, SiteImage, SiteText):
            for obj in model.objects.all():
                touched = translate.fill_missing(obj)
                if touched:
                    done += 1
                    self.stdout.write("• %s : %s" % (obj, ", ".join(sorted(touched))))
        self.stdout.write(self.style.SUCCESS("%s objet(s) complété(s)." % done))
