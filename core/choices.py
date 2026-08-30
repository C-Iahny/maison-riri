"""Listes de choix du formulaire de devis.

Les valeurs sont celles attendues par le Google Form déjà utilisé par Maison
Riri Design : elles sont donc conservées **au caractère près**. Ce sont des
libellés bilingues du type ``"Geburtstag | Anniversaire"`` ; ``label()``
n'affiche que la moitié correspondant à la langue active du site.
"""
from django.utils.translation import get_language

# Identifiants des champs du Google Form (docs.google.com/forms/.../formResponse)
ENTRY_FULL_NAME = "entry.794662135"
ENTRY_EMAIL = "entry.1533935099"
ENTRY_PHONE = "entry.1263770564"
ENTRY_LANGUAGE = "entry.1895325410"
ENTRY_EVENT_TYPE = "entry.493420342"
ENTRY_EVENT_DATE = "entry.988676294"
ENTRY_EVENT_LOCATION = "entry.1777726582"
ENTRY_GUESTS = "entry.1285264539"
ENTRY_SERVICES = "entry.15485219"
ENTRY_THEME = "entry.202855988"
ENTRY_BUDGET = "entry.1667074640"
ENTRY_MESSAGE = "entry.663339902"
ENTRY_REFERRAL = "entry.144471733"
ENTRY_CONSENT = "entry.1521884522"


def label(value):
    """Rend la moitié allemande ou française d'un libellé ``"DE | FR"``."""
    if " | " not in value:
        return value
    german, french = value.split(" | ", 1)
    return german if (get_language() or "fr").startswith("de") else french


def as_choices(values):
    """Transforme une liste de valeurs Google en couples ``(valeur, libellé)``."""
    return [(v, label(v)) for v in values]


LANGUAGES = ["Deutsch", "Français", "Malagasy"]

EVENT_TYPES = [
    "Geburtstag | Anniversaire",
    "Kindergeburtstag | Anniversaire enfant",
    "Baby Shower",
    "Gender Reveal",
    "Taufe | Baptême",
    "Hochzeit | Mariage",
    "Verlobung | Fiançailles",
    "Firmenveranstaltung | Événement professionnel",
    "Private Feier | Événement privé",
    "Sonstiges | Autre",
]

GUEST_COUNTS = [
    "Unter 20 Personen | Moins de 20 personnes",
    "20–50 Personen | 20 à 50 personnes",
    "51–100 Personen | 51 à 100 personnes",
    "101–150 Personen | 101 à 150 personnes",
    "Über 150 Personen | Plus de 150 personnes",
]

SERVICES = [
    "Ballondekoration | Décoration en ballons",
    "Tischdekoration | Décoration de table",
    "Blumendekoration | Décoration florale",
    "Backdrop / Fotobereich | Arche & fond photo",
    "Sweet Table",
    "Komplettes Dekorationskonzept | Décoration complète",
    "Eventplanung | Organisation de l'événement",
    "Beratung | Conseil",
    "Sonstiges | Autre",
]

# Attention : l'espacement de ces valeurs reproduit exactement celui du Google Form.
BUDGETS = [
    "900 € – 1.500 €",
    "1.500 € – 3.000 €",
    "3.000 € –  4.500 €",
    "+ 4.500 €",
]

REFERRALS = [
    "Instagram",
    "Facebook",
    "TikTok",
    "Google",
    "Empfehlung | Recommandation",
    "Familie / Freunde | Famille / Amis",
    "Sonstiges | Autre",
]

CONSENT_DE = (
    "Ich stimme zu, dass Maison Riri Design meine personenbezogenen Daten "
    "ausschließlich zur Bearbeitung meiner Anfrage verwenden darf."
)
CONSENT_FR = (
    "J'accepte que Maison Riri Design utilise mes données personnelles "
    "uniquement afin de traiter ma demande."
)


def consent_value():
    """Le Google Form attend le texte de consentement dans la langue du visiteur."""
    return CONSENT_DE if (get_language() or "fr").startswith("de") else CONSENT_FR
