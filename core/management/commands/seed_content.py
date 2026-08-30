"""Charge le portfolio de départ (photos fournies + concept « Red Wine »).

Les visuels sont stockés dans ``core/assets`` et recopiés dans ``MEDIA_ROOT``
au moment du chargement, ce qui rend la commande rejouable sur n'importe quelle
installation. Utilisation :

    python manage.py seed_content
    python manage.py seed_content --reset   # remplace les projets existants
"""
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand

from core.models import PaletteColor, Project, ProjectImage

ASSETS = Path(__file__).resolve().parents[2] / "assets"

DREAMLAND = {
    "slug": "dreamland",
    "kind": Project.Kind.REALIZED,
    "title_fr": "Dreamland",
    "title_de": "Dreamland",
    "subtitle_fr": "Remise de diplômes · Arc-en-ciel & lettres lumineuses",
    "subtitle_de": "Abschlussfeier · Regenbogen & Leuchtbuchstaben",
    "event_type_fr": "Remise de diplômes",
    "event_type_de": "Abschlussfeier",
    "keywords_fr": "Arc-en-ciel, Ballons organiques, Backdrop, Lettres lumineuses, Sweet table",
    "keywords_de": "Regenbogen, Organische Ballons, Backdrop, Leuchtbuchstaben, Sweet Table",
    "summary_fr": (
        "Une remise de diplômes transformée en parcours coloré : on franchit une arche "
        "de ballons, on avance vers la scène, et l'on termine devant des lettres "
        "lumineuses géantes."
    ),
    "summary_de": (
        "Eine Abschlussfeier als farbenfroher Parcours: Man tritt durch einen Ballonbogen, "
        "geht auf die Bühne zu und endet vor riesigen Leuchtbuchstaben."
    ),
    "story_fr": (
        "Le point de départ était une phrase : « You just have to start ». Elle devait se "
        "lire dès l'entrée, avant même que les invités ne découvrent la salle.\n\n"
        "L'arche d'accueil ouvre le parcours et cadre la perspective vers la scène. "
        "Les guirlandes organiques de ballons y sont montées en dégradés — corail, "
        "abricot, lavande, menthe — pour donner du relief sans jamais casser la lecture "
        "de l'ensemble.\n\n"
        "Au centre, un backdrop en panneaux découpés reprend les mêmes teintes et sert "
        "de fond au coin gâteau : socles cylindriques, présentoirs à hauteurs multiples, "
        "bouquets de gerberas et de roses orangées.\n\n"
        "La piste s'achève sur les lettres lumineuses « Dreamland », posées devant un mur "
        "de ballons pastel : le point de rendez-vous des photos de fin de soirée."
    ),
    "story_de": (
        "Am Anfang stand ein Satz: „You just have to start“. Er sollte schon am Eingang "
        "zu lesen sein, bevor die Gäste den Saal überhaupt betreten.\n\n"
        "Der Empfangsbogen öffnet den Parcours und rahmt den Blick auf die Bühne. Die "
        "organischen Ballongirlanden sind in Verläufen gesetzt — Koralle, Aprikose, "
        "Lavendel, Mint — für Tiefe, ohne das Gesamtbild zu zerreißen.\n\n"
        "In der Mitte greift ein Backdrop aus geschnittenen Paneelen dieselben Töne auf "
        "und bildet den Hintergrund der Kuchenecke: zylindrische Sockel, Etageren in "
        "unterschiedlichen Höhen, Sträuße aus Gerbera und orangefarbenen Rosen.\n\n"
        "Den Abschluss bilden die Leuchtbuchstaben „Dreamland“ vor einer Wand aus "
        "Pastellballons — der Treffpunkt für die Fotos am Ende des Abends."
    ),
    "cover": "dreamland-corridor.jpg",
    "is_featured": True,
    "order": 1,
    "palette": [
        ("#F0605F", "Corail"),
        ("#F49A4C", "Abricot"),
        ("#B49CD6", "Lavande"),
        ("#9FD7B0", "Menthe"),
        ("#F4A9C0", "Rose poudré"),
        ("#A9CCE3", "Bleu ciel"),
    ],
    "images": [
        ("dreamland-entrance.jpg", ProjectImage.Stage.SETUP,
         "Arche d'accueil « You just have to start »",
         "Empfangsbogen „You just have to start“"),
        ("dreamland-signage.jpg", ProjectImage.Stage.DETAILS,
         "Panneau « Great things never came from comfort zone »",
         "Schild „Great things never came from comfort zone“"),
        ("dreamland-sweettable.jpg", ProjectImage.Stage.DETAILS,
         "Coin gourmandises et composition florale",
         "Sweet Table und florale Komposition"),
        ("dreamland-stage.jpg", ProjectImage.Stage.RESULT,
         "Scène principale et backdrop en panneaux découpés",
         "Hauptbühne und Backdrop aus geschnittenen Paneelen"),
        ("dreamland-stage-portrait.jpg", ProjectImage.Stage.RESULT,
         "Le coin gâteau vu de face",
         "Die Kuchenecke von vorn"),
        ("dreamland-letters.jpg", ProjectImage.Stage.RESULT,
         "Lettres lumineuses « Dreamland »",
         "Leuchtbuchstaben „Dreamland“"),
        ("dreamland-corridor.jpg", ProjectImage.Stage.RESULT,
         "Perspective depuis l'entrée de la salle",
         "Perspektive vom Saaleingang"),
    ],
}

RED_WINE = {
    "slug": "thirty-and-fabulous-red-wine",
    "kind": Project.Kind.CONCEPT,
    "title_fr": "Thirty & Fabulous",
    "title_de": "Thirty & Fabulous",
    "subtitle_fr": "30e anniversaire · Bordeaux • Vin • Crème",
    "subtitle_de": "30. Geburtstag · Bordeaux • Wein • Creme",
    "event_type_fr": "Anniversaire — 30 ans",
    "event_type_de": "Geburtstag — 30 Jahre",
    "keywords_fr": "Élégant, Chaleureux, Féminin, Moderne, Atmosphérique, Souci du détail",
    "keywords_de": "Elegant, Warm, Feminin, Modern, Atmosphärisch, Detailorientiert",
    "summary_fr": (
        "Une ambiance de soirée chaleureuse et élégante, inspirée des nuances du vin "
        "rouge, de la lumière des bougies et d'un dîner contemporain."
    ),
    "summary_de": (
        "Eine warme, elegante Abendstimmung, inspiriert von Rotwein-Nuancen, "
        "Kerzenlicht und einem modernen Dinner-Ambiente."
    ),
    "story_fr": (
        "Le bordeaux et les tons de vin profonds posent les accents, tandis que la crème "
        "et les neutres chauds apportent de la légèreté à l'ensemble.\n\n"
        "Principes de conception : une harmonie chromatique plutôt qu'une décoration "
        "surchargée ; la lumière et les bougies comme couche atmosphérique ; des accents "
        "floraux en rouge vin, bordeaux et rosés doux ; une mise en table élégante aux "
        "détails modernes et nets ; une continuité visuelle entre le dîner, le styling et "
        "le moment de célébration.\n\n"
        "Look & feel : le concept associe la profondeur du bordeaux à des surfaces claires "
        "et élégantes. Verres transparents, bougies, formes florales et tissus fluides "
        "créent une atmosphère intime et haut de gamme."
    ),
    "story_de": (
        "Burgundy und tiefe Weintöne setzen Akzente, während Creme und warme Neutraltöne "
        "dem Konzept Leichtigkeit geben.\n\n"
        "Gestaltungsprinzipien: harmonische Farbwelt statt überladener Dekoration; "
        "stimmungsvolles Licht und Kerzen als atmosphärische Ebene; florale Akzente in "
        "Weinrot, Burgundy und soften Rosé-Tönen; elegante Tischgestaltung mit klaren, "
        "modernen Details; visuelle Verbindung zwischen Dinner, Styling und Celebration.\n\n"
        "Look & Feel: Das Konzept verbindet die Tiefe von Burgundy mit hellen, eleganten "
        "Flächen. Transparente Gläser, Kerzen, florale Formen und fließende Stoffe "
        "schaffen eine hochwertige, intime Atmosphäre."
    ),
    "cover": "redwine-cover.jpg",
    "is_featured": True,
    "order": 2,
    "palette": [
        ("#4F141C", "Burgundy"),
        ("#6D1E2B", "Vin"),
        ("#8E3D44", "Bordeaux clair"),
        ("#B78477", "Rosé poudré"),
        ("#F2EADB", "Crème"),
    ],
    "images": [
        ("redwine-moodboard-1.jpg", ProjectImage.Stage.MOODBOARD,
         "Stimmung & Atmosphäre — planche 1",
         "Stimmung & Atmosphäre — Tafel 1"),
        ("redwine-moodboard-2.jpg", ProjectImage.Stage.MOODBOARD,
         "Stimmung & Atmosphäre — planche 2",
         "Stimmung & Atmosphäre — Tafel 2"),
    ],
}


class Command(BaseCommand):
    help = "Crée les projets de démarrage du portfolio à partir des visuels fournis."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Supprime les projets portant les mêmes identifiants avant de les recréer.",
        )

    def handle(self, *args, **options):
        if not ASSETS.is_dir():
            self.stderr.write("Dossier d'images introuvable : %s" % ASSETS)
            return

        for data in (DREAMLAND, RED_WINE):
            self._load(data, reset=options["reset"])

        self.stdout.write(self.style.SUCCESS("Portfolio de départ chargé."))

    def _load(self, data, reset):
        slug = data["slug"]
        if reset:
            Project.objects.filter(slug=slug).delete()
        if Project.objects.filter(slug=slug).exists():
            self.stdout.write("• %s existe déjà, ignoré (--reset pour recharger)." % slug)
            return

        fields = {k: v for k, v in data.items() if k not in {"cover", "palette", "images"}}
        project = Project(**fields)
        with open(ASSETS / data["cover"], "rb") as handle:
            project.cover.save(data["cover"], File(handle), save=False)
        project.save()

        for index, (hex_code, name) in enumerate(data["palette"]):
            PaletteColor.objects.create(project=project, hex_code=hex_code, name=name, order=index)

        for index, (filename, stage, caption_fr, caption_de) in enumerate(data["images"]):
            image = ProjectImage(
                project=project,
                stage=stage,
                caption_fr=caption_fr,
                caption_de=caption_de,
                order=index,
            )
            with open(ASSETS / filename, "rb") as handle:
                image.image.save(filename, File(handle), save=False)
            image.save()

        self.stdout.write(self.style.SUCCESS("• %s créé (%s images)." % (slug, len(data["images"]))))
