from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0004_sitetext"),
    ]

    operations = [
        migrations.AddField(model_name=name, name="machine_translations",
                            field=models.JSONField(blank=True, default=dict, editable=False))
        for name in ("project", "projectimage", "palettecolor", "siteimage", "sitetext")
    ] + [
        migrations.AlterField(
            model_name="palettecolor", name="name_de",
            field=models.CharField(blank=True, help_text="Laissé vide, il est traduit automatiquement à partir du nom français.", max_length=60, verbose_name="nom (DE)"),
        ),
        migrations.AlterField(
            model_name="sitetext", name="text_de",
            field=models.TextField(blank=True, help_text="Laissé vide, il est traduit automatiquement à partir du texte français.", verbose_name="texte (DE)"),
        ),
    ]
