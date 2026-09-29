"""« Sweet Table » et « Coin gourmandises » deviennent « Candy Bar ».

Ne touche que le projet Dreamland chargé par ``seed_content`` et uniquement
lorsque ses valeurs sont encore celles d'origine : un texte modifié dans
l'administration est laissé tel quel.
"""
from django.db import migrations

KEYWORDS = (
    ("keywords_fr",
     "Arc-en-ciel, Ballons organiques, Backdrop, Lettres lumineuses, Sweet table",
     "Arc-en-ciel, Ballons organiques, Backdrop, Lettres lumineuses, Candy Bar"),
    ("keywords_de",
     "Regenbogen, Organische Ballons, Backdrop, Leuchtbuchstaben, Sweet Table",
     "Regenbogen, Organische Ballons, Backdrop, Leuchtbuchstaben, Candy Bar"),
)

CAPTIONS = (
    ("caption_fr", "Coin gourmandises et composition florale", "Candy Bar et composition florale"),
    ("caption_de", "Sweet Table und florale Komposition", "Candy Bar und florale Komposition"),
)


def forwards(apps, schema_editor):
    Project = apps.get_model("core", "Project")
    ProjectImage = apps.get_model("core", "ProjectImage")

    for field, old, new in KEYWORDS:
        Project.objects.filter(slug="dreamland", **{field: old}).update(**{field: new})

    for field, old, new in CAPTIONS:
        ProjectImage.objects.filter(project__slug="dreamland", **{field: old}).update(**{field: new})


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_auto_translation"),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
