"""Nom de couleur en allemand + libellés retouchés des projets de départ.

La partie « données » ne touche que les projets chargés par ``seed_content``
et uniquement lorsque leurs valeurs sont encore celles d'origine : un texte
modifié dans l'administration est laissé tel quel.
"""
from django.db import migrations, models

COLOR_NAMES_DE = {
    "Corail": "Koralle",
    "Abricot": "Aprikose",
    "Lavande": "Lavendel",
    "Menthe": "Mint",
    "Rose poudré": "Puderrosa",
    "Bleu ciel": "Himmelblau",
    "Burgundy": "Burgundy",
    "Vin": "Weinrot",
    "Bordeaux clair": "Helles Bordeaux",
    "Rosé poudré": "Puderrosé",
    "Crème": "Creme",
}

EVENT_TYPES = {
    "dreamland": (
        ("Remise de diplômes", "Cérémonie de fin d'études"),
        ("Abschlussfeier", "Abschlussfeier"),
    ),
    "thirty-and-fabulous-red-wine": (
        ("Anniversaire — 30 ans", "30ᵉ anniversaire"),
        ("Geburtstag — 30 Jahre", "30. Geburtstag"),
    ),
}


def forwards(apps, schema_editor):
    PaletteColor = apps.get_model("core", "PaletteColor")
    Project = apps.get_model("core", "Project")

    for color in PaletteColor.objects.filter(name_de=""):
        translated = COLOR_NAMES_DE.get(color.name)
        if translated:
            color.name_de = translated
            color.save(update_fields=["name_de"])

    for slug, ((old_fr, new_fr), (old_de, new_de)) in EVENT_TYPES.items():
        Project.objects.filter(slug=slug, event_type_fr=old_fr).update(event_type_fr=new_fr)
        Project.objects.filter(slug=slug, event_type_de=old_de).update(event_type_de=new_de)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_siteimage"),
    ]

    operations = [
        migrations.AlterField(
            model_name="palettecolor",
            name="name",
            field=models.CharField(blank=True, max_length=60, verbose_name="nom (FR)"),
        ),
        migrations.AddField(
            model_name="palettecolor",
            name="name_de",
            field=models.CharField(
                blank=True,
                help_text="Laissé vide, le nom français est affiché sur le site allemand.",
                max_length=60,
                verbose_name="nom (DE)",
            ),
        ),
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
