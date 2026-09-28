"""Traduit les textes dont une seule langue est renseignée (rattrapage).

Utile après l'activation de la traduction automatique, ou après une panne :
tout ce qui a été enregistré avec une langue vide est complété.

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
                touched = set()
                for fr_field, de_field in model.TRANSLATED_PAIRS:
                    fr = (getattr(obj, fr_field) or "").strip()
                    de = (getattr(obj, de_field) or "").strip()
                    if fr and not de:
                        output = translate.translate(fr, "fr", "de")
                        if output:
                            setattr(obj, de_field, output); obj.machine_translations[de_field] = True; touched.add(de_field)
                    elif de and not fr:
                        output = translate.translate(de, "de", "fr")
                        if output:
                            setattr(obj, fr_field, output); obj.machine_translations[fr_field] = True; touched.add(fr_field)
                if touched:
                    obj._db_values = {}  # évite une seconde passe dans save()
                    obj.machine_translations = dict(obj.machine_translations)
                    model.objects.filter(pk=obj.pk).update(
                        machine_translations=obj.machine_translations,
                        **{name: getattr(obj, name) for name in touched},
                    )
                    done += 1
                    self.stdout.write("• %s : %s" % (obj, ", ".join(sorted(touched))))
        self.stdout.write(self.style.SUCCESS("%s objet(s) complété(s)." % done))
