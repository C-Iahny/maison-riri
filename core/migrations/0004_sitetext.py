from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_palettecolor_name_de"),
    ]

    operations = [
        migrations.CreateModel(
            name="SiteText",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("key", models.CharField(editable=False, max_length=60, unique=True, verbose_name="clé")),
                ("position", models.PositiveIntegerField(default=0, editable=False, verbose_name="ordre")),
                ("text_fr", models.TextField(blank=True, help_text="Laissez vide pour conserver le texte d'origine.", verbose_name="texte (FR)")),
                ("text_de", models.TextField(blank=True, help_text="Laissé vide, le texte français saisi ci-dessus — ou, à défaut, la traduction d'origine — est affiché.", verbose_name="texte (DE)")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="mise à jour le")),
            ],
            options={
                "verbose_name": "texte du site",
                "verbose_name_plural": "textes du site",
                "ordering": ["position"],
            },
        ),
    ]
