"""Formulaire « Demander un devis »."""
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from . import choices
from .models import QuoteRequest

MAX_INSPIRATION_FILES = 8
MAX_INSPIRATION_SIZE = 8 * 1024 * 1024  # 8 Mo par photo
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"}


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    """Champ acceptant plusieurs fichiers (Django ne le fournit pas nativement)."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput(attrs={"accept": "image/*", "multiple": True}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single = super().clean
        if isinstance(data, (list, tuple)):
            return [single(item, initial) for item in data if item]
        return [single(data, initial)] if data else []


class QuoteRequestForm(forms.ModelForm):
    """Reprend, champ pour champ, le questionnaire de Maison Riri Design."""

    preferred_language = forms.ChoiceField(
        label=_("Langue de communication souhaitée"),
        choices=[],
    )
    event_type = forms.ChoiceField(label=_("Type d'événement"), choices=[])
    guest_count = forms.ChoiceField(label=_("Nombre d'invités"), choices=[])
    budget = forms.ChoiceField(label=_("Budget prévu"), choices=[])
    referral = forms.ChoiceField(
        label=_("Comment avez-vous découvert Maison Riri Design ?"), choices=[], required=False
    )
    services = forms.MultipleChoiceField(
        label=_("Prestations souhaitées"),
        choices=[],
        widget=forms.CheckboxSelectMultiple,
    )
    consent = forms.BooleanField(label=_("Protection des données & consentement"))
    inspirations = MultipleFileField(
        label=_("Photos d'inspiration"),
        required=False,
        help_text=_("Jusqu'à 8 images (JPEG, PNG ou WebP), 8 Mo maximum par photo."),
    )
    # Champ leurre : invisible pour les visiteurs, rempli par les robots.
    website = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = QuoteRequest
        fields = [
            "full_name",
            "email",
            "phone",
            "preferred_language",
            "event_type",
            "event_date",
            "event_location",
            "guest_count",
            "services",
            "theme",
            "budget",
            "message",
            "referral",
            "consent",
        ]
        labels = {
            "full_name": _("Nom et prénom"),
            "email": _("Adresse e-mail"),
            "phone": _("Numéro de téléphone"),
            "event_date": _("Date de l'événement"),
            "event_location": _("Lieu de l'événement"),
            "theme": _("Avez-vous déjà un thème ou une palette de couleurs ?"),
            "message": _("Message / souhaits particuliers"),
        }
        widgets = {
            "event_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "message": forms.Textarea(attrs={"rows": 6}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        blank = [("", _("Choisir…"))]
        self.fields["preferred_language"].choices = blank + choices.as_choices(choices.LANGUAGES)
        self.fields["event_type"].choices = blank + choices.as_choices(choices.EVENT_TYPES)
        self.fields["guest_count"].choices = blank + choices.as_choices(choices.GUEST_COUNTS)
        self.fields["budget"].choices = blank + choices.as_choices(choices.BUDGETS)
        self.fields["referral"].choices = blank + choices.as_choices(choices.REFERRALS)
        self.fields["services"].choices = choices.as_choices(choices.SERVICES)

        self.fields["phone"].required = False
        self.fields["theme"].required = False
        for name in ("event_date", "event_location", "message"):
            self.fields[name].required = True

        placeholders = {
            "full_name": _("Marie Dupont"),
            "email": _("marie@exemple.com"),
            "phone": _("+33 6 12 34 56 78"),
            "event_location": _("Freiburg, Colmar, Bâle…"),
            "theme": _("Bordeaux & crème, bohème, minimaliste…"),
            "message": _("Racontez-moi votre événement, vos envies, ce qui compte pour vous."),
        }
        for name, text in placeholders.items():
            self.fields[name].widget.attrs.setdefault("placeholder", text)

        for name, field in self.fields.items():
            if name in ("services", "consent", "inspirations", "website"):
                continue
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = ("%s field__input" % css).strip()

    def clean_website(self):
        if self.cleaned_data.get("website"):
            raise ValidationError(_("Envoi refusé."))
        return ""

    def clean_services(self):
        # Le modèle stocke les prestations en texte, une par ligne.
        return "\n".join(self.cleaned_data.get("services") or [])

    def clean_inspirations(self):
        files = self.cleaned_data.get("inspirations") or []
        if len(files) > MAX_INSPIRATION_FILES:
            raise ValidationError(
                _("Merci de joindre au maximum %(count)s photos.") % {"count": MAX_INSPIRATION_FILES}
            )
        for upload in files:
            if upload.size > MAX_INSPIRATION_SIZE:
                raise ValidationError(
                    _("« %(name)s » dépasse 8 Mo.") % {"name": upload.name}
                )
            content_type = (getattr(upload, "content_type", "") or "").lower()
            if content_type and content_type not in ALLOWED_IMAGE_TYPES:
                raise ValidationError(
                    _("« %(name)s » n'est pas une image prise en charge.") % {"name": upload.name}
                )
        return files
