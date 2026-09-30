"""Modèles du site Maison Riri Design.

Le site est bilingue français / allemand. Plutôt que d'ajouter une dépendance
de traduction de modèles, chaque champ éditorial existe en deux versions
(``_fr`` / ``_de``) et ``localized()`` renvoie la version de la langue active,
avec repli sur le français lorsque la traduction manque.
"""
from django.db import models
from django.templatetags.static import static
from django.urls import reverse
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _


class LocalizedMixin:
    """Donne accès aux champs bilingues via ``obj.localized("title")``."""

    def localized(self, field):
        lang = (get_language() or "fr").split("-")[0]
        value = getattr(self, "%s_%s" % (field, lang), "")
        if not value:
            value = getattr(self, "%s_fr" % field, "") or getattr(self, "%s_de" % field, "")
        return value


class AutoTranslated(models.Model):
    """Remplit automatiquement la langue manquante d'un couple FR / DE.

    ``TRANSLATED_PAIRS`` liste les couples ``(champ_fr, champ_de)``. À
    l'enregistrement, si un seul des deux a changé et que l'autre est vide
    — ou n'était lui-même qu'une traduction automatique —, l'autre est
    régénéré via l'API Claude (``core/translate.py``). Une traduction saisie
    à la main est reconnue comme telle et n'est jamais écrasée. Le champ
    ``machine_translations`` mémorise quels champs ont été générés.
    """

    TRANSLATED_PAIRS = ()

    machine_translations = models.JSONField(default=dict, blank=True, editable=False)

    class Meta:
        abstract = True

    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super().from_db(db, field_names, values)
        instance._db_values = {name: getattr(instance, name, "") for pair in cls.TRANSLATED_PAIRS for name in pair}
        return instance

    def save(self, *args, **kwargs):
        touched = self._auto_translate()
        update_fields = kwargs.get("update_fields")
        if touched and update_fields is not None:
            kwargs["update_fields"] = list(set(update_fields) | touched | {"machine_translations"})
        super().save(*args, **kwargs)
        self._db_values = {name: getattr(self, name, "") for pair in self.TRANSLATED_PAIRS for name in pair}

    def _auto_translate(self):
        from . import translate

        if not translate.is_enabled():
            return set()
        before = getattr(self, "_db_values", {})
        flags = dict(self.machine_translations or {})
        touched = set()
        for fr_field, de_field in self.TRANSLATED_PAIRS:
            fr = (getattr(self, fr_field) or "").strip()
            de = (getattr(self, de_field) or "").strip()
            fr_changed = fr != (before.get(fr_field) or "").strip()
            de_changed = de != (before.get(de_field) or "").strip()
            # Un champ modifié à la main cesse d'être une traduction automatique.
            if fr_changed:
                flags.pop(fr_field, None)
            if de_changed:
                flags.pop(de_field, None)
            if fr_changed and de_changed:
                continue  # les deux versions ont été écrites : rien à générer
            if not fr_changed and not de_changed:
                # Réenregistrement sans modification : on complète la langue vide
                # (cas d'un texte saisi alors que la traduction ne fonctionnait pas).
                if fr and not de:
                    output = translate.translate(fr, "fr", "de")
                    if output:
                        setattr(self, de_field, output); flags[de_field] = True; touched.add(de_field)
                elif de and not fr:
                    output = translate.translate(de, "de", "fr")
                    if output:
                        setattr(self, fr_field, output); flags[fr_field] = True; touched.add(fr_field)
                continue
            if fr_changed:
                if not fr and flags.get(de_field):
                    setattr(self, de_field, "")  # source effacée : sa traduction disparaît
                    flags.pop(de_field, None); touched.add(de_field)
                elif fr and (not de or flags.get(de_field)):
                    output = translate.translate(fr, "fr", "de")
                    if output:
                        setattr(self, de_field, output); flags[de_field] = True; touched.add(de_field)
            elif de_changed:
                if not de and flags.get(fr_field):
                    setattr(self, fr_field, "")
                    flags.pop(fr_field, None); touched.add(fr_field)
                elif de and (not fr or flags.get(fr_field)):
                    output = translate.translate(de, "de", "fr")
                    if output:
                        setattr(self, fr_field, output); flags[fr_field] = True; touched.add(fr_field)
        if flags != (self.machine_translations or {}):
            self.machine_translations = flags
            touched.add("machine_translations")
        return touched

    def machine_translated_fields(self):
        """Libellés des champs actuellement issus d'une traduction automatique."""
        names = []
        for name, flag in (self.machine_translations or {}).items():
            if flag:
                try:
                    names.append(str(self._meta.get_field(name).verbose_name))
                except Exception:  # noqa: BLE001
                    names.append(name)
        return names


class ProjectQuerySet(models.QuerySet):
    def published(self):
        return self.filter(is_published=True)

    def featured(self):
        return self.published().filter(is_featured=True)


class Project(LocalizedMixin, AutoTranslated):
    """Une réalisation ou une étude de concept présentée au portfolio."""

    TRANSLATED_PAIRS = (
        ("title_fr", "title_de"), ("subtitle_fr", "subtitle_de"), ("summary_fr", "summary_de"),
        ("story_fr", "story_de"), ("event_type_fr", "event_type_de"), ("keywords_fr", "keywords_de"),
    )

    class Kind(models.TextChoices):
        REALIZED = "realized", _("Réalisation")
        CONCEPT = "concept", _("Concept créatif")

    slug = models.SlugField(_("identifiant URL"), unique=True)
    kind = models.CharField(
        _("type de projet"), max_length=16, choices=Kind.choices, default=Kind.REALIZED
    )

    title_fr = models.CharField(_("titre (FR)"), max_length=160)
    title_de = models.CharField(_("titre (DE)"), max_length=160, blank=True)
    subtitle_fr = models.CharField(_("sous-titre (FR)"), max_length=200, blank=True)
    subtitle_de = models.CharField(_("sous-titre (DE)"), max_length=200, blank=True)
    summary_fr = models.TextField(_("résumé (FR)"), blank=True)
    summary_de = models.TextField(_("résumé (DE)"), blank=True)
    story_fr = models.TextField(
        _("texte long (FR)"), blank=True, help_text=_("Séparez les paragraphes par une ligne vide.")
    )
    story_de = models.TextField(_("texte long (DE)"), blank=True)

    event_type_fr = models.CharField(_("type d'événement (FR)"), max_length=120, blank=True)
    event_type_de = models.CharField(_("type d'événement (DE)"), max_length=120, blank=True)
    location = models.CharField(_("lieu"), max_length=120, blank=True)
    year = models.PositiveIntegerField(_("année"), null=True, blank=True)
    keywords_fr = models.CharField(
        _("mots-clés (FR)"), max_length=240, blank=True, help_text=_("Séparés par des virgules.")
    )
    keywords_de = models.CharField(_("mots-clés (DE)"), max_length=240, blank=True)

    cover = models.ImageField(_("image de couverture"), upload_to="projects/covers/")
    is_featured = models.BooleanField(_("mis en avant sur l'accueil"), default=False)
    is_published = models.BooleanField(_("publié"), default=True)
    order = models.PositiveIntegerField(_("ordre d'affichage"), default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ProjectQuerySet.as_manager()

    class Meta:
        ordering = ["order", "-created_at"]
        verbose_name = _("projet")
        verbose_name_plural = _("projets")

    def __str__(self):
        return self.title_fr

    def get_absolute_url(self):
        return reverse("core:project_detail", kwargs={"slug": self.slug})

    @property
    def title(self):
        return self.localized("title")

    @property
    def subtitle(self):
        return self.localized("subtitle")

    @property
    def summary(self):
        return self.localized("summary")

    @property
    def event_type(self):
        return self.localized("event_type")

    @property
    def story_paragraphs(self):
        return [p.strip() for p in self.localized("story").split("\n\n") if p.strip()]

    @property
    def keyword_list(self):
        return [k.strip() for k in self.localized("keywords").split(",") if k.strip()]

    @property
    def is_concept(self):
        return self.kind == self.Kind.CONCEPT

    def images_by_stage(self):
        """Regroupe la galerie : moodboard, détails, installation, résultat final."""
        buckets = []
        for value, label in ProjectImage.Stage.choices:
            items = [img for img in self.images.all() if img.stage == value]
            if items:
                buckets.append({"key": value, "label": label, "images": items})
        return buckets


class ProjectImage(LocalizedMixin, AutoTranslated):
    TRANSLATED_PAIRS = (("caption_fr", "caption_de"),)

    class Stage(models.TextChoices):
        MOODBOARD = "moodboard", _("Moodboard")
        DETAILS = "details", _("Détails")
        SETUP = "setup", _("Installation")
        RESULT = "result", _("Résultat final")

    project = models.ForeignKey(Project, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(_("image"), upload_to="projects/gallery/")
    stage = models.CharField(_("étape"), max_length=16, choices=Stage.choices, default=Stage.RESULT)
    caption_fr = models.CharField(_("légende (FR)"), max_length=200, blank=True)
    caption_de = models.CharField(_("légende (DE)"), max_length=200, blank=True)
    order = models.PositiveIntegerField(_("ordre"), default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = _("image de projet")
        verbose_name_plural = _("images de projet")

    def __str__(self):
        return "%s / %s" % (self.project.title_fr, self.get_stage_display())

    @property
    def caption(self):
        return self.localized("caption")


class PaletteColor(AutoTranslated):
    """Un aplat de la palette chromatique d'un projet."""

    TRANSLATED_PAIRS = (("name", "name_de"),)

    project = models.ForeignKey(Project, related_name="palette", on_delete=models.CASCADE)
    hex_code = models.CharField(_("code couleur"), max_length=7, help_text="#4A1220")
    name = models.CharField(_("nom (FR)"), max_length=60, blank=True)
    name_de = models.CharField(
        _("nom (DE)"), max_length=60, blank=True,
        help_text=_("Laissé vide, il est traduit automatiquement à partir du nom français."),
    )
    order = models.PositiveIntegerField(_("ordre"), default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = _("couleur de palette")
        verbose_name_plural = _("palette")

    def __str__(self):
        return "%s %s" % (self.hex_code, self.name)

    @property
    def label(self):
        """Nom de la couleur dans la langue active, repli sur le français."""
        lang = (get_language() or "fr").split("-")[0]
        if lang == "de" and self.name_de:
            return self.name_de
        return self.name or self.name_de


class QuoteRequest(models.Model):
    """Demande de devis envoyée depuis le site."""

    class Status(models.TextChoices):
        NEW = "new", _("Nouvelle")
        IN_PROGRESS = "in_progress", _("En cours")
        QUOTED = "quoted", _("Devis envoyé")
        WON = "won", _("Confirmée")
        CLOSED = "closed", _("Classée")

    full_name = models.CharField(_("nom et prénom"), max_length=150)
    email = models.EmailField(_("adresse e-mail"))
    phone = models.CharField(_("téléphone"), max_length=40, blank=True)
    preferred_language = models.CharField(_("langue souhaitée"), max_length=20, default="Français")

    event_type = models.CharField(_("type d'événement"), max_length=80, blank=True)
    event_date = models.DateField(_("date de l'événement"), null=True, blank=True)
    event_location = models.CharField(_("lieu de l'événement"), max_length=180, blank=True)
    guest_count = models.CharField(_("nombre d'invités"), max_length=60, blank=True)

    services = models.TextField(_("prestations souhaitées"), blank=True)
    theme = models.CharField(_("thème ou palette"), max_length=250, blank=True)
    budget = models.CharField(_("budget"), max_length=60, blank=True)
    message = models.TextField(_("message"), blank=True)
    referral = models.CharField(_("comment nous a connus"), max_length=80, blank=True)
    consent = models.BooleanField(_("consentement RGPD"), default=False)

    submitted_language = models.CharField(_("langue du formulaire"), max_length=5, default="fr")
    forwarded_to_google = models.BooleanField(_("transmis au Google Form"), default=False)
    forward_error = models.TextField(_("erreur de transmission"), blank=True)
    status = models.CharField(_("statut"), max_length=16, choices=Status.choices, default=Status.NEW)
    created_at = models.DateTimeField(_("reçue le"), auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("demande de devis")
        verbose_name_plural = _("demandes de devis")

    def __str__(self):
        return "%s (%s)" % (self.full_name, self.created_at.date())

    @property
    def service_list(self):
        return [s.strip() for s in self.services.split("\n") if s.strip()]


class InspirationImage(models.Model):
    """Photo d'inspiration jointe à une demande de devis."""

    request = models.ForeignKey(QuoteRequest, related_name="inspirations", on_delete=models.CASCADE)
    image = models.ImageField(_("photo d'inspiration"), upload_to="inspirations/%Y/%m/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]
        verbose_name = _("photo d'inspiration")
        verbose_name_plural = _("photos d'inspiration")

    def __str__(self):
        return "Inspiration #%s" % self.pk


class SiteImage(AutoTranslated):
    """Une image « fixe » du site (logo, hero, portrait…), remplaçable en admin.

    Tant qu'aucun fichier n'a été envoyé pour un emplacement, le site retombe
    sur le visuel livré dans ``static/img``. L'administratrice peut donc changer
    n'importe quelle image à tout moment sans toucher au code ni redéployer.
    """

    class Slot(models.TextChoices):
        LOGO = "logo", _("Logo (en-tête, pied de page, favicon)")
        HERO = "hero", _("Grande image de l'accueil")
        PORTRAIT = "portrait", _("Portrait — page À propos")
        ATMOSPHERE = "atmosphere", _("Ambiance — page À propos")
        SHARE = "share", _("Image de partage (réseaux sociaux)")

    TRANSLATED_PAIRS = (("alt_fr", "alt_de"),)

    #: Visuel statique utilisé tant que l'emplacement n'a pas été personnalisé.
    FALLBACKS = {
        Slot.LOGO: "img/logo.jpg",
        Slot.HERO: "img/hero.jpg",
        Slot.PORTRAIT: "img/portrait.jpg",
        Slot.ATMOSPHERE: "img/atmosphere.jpg",
        Slot.SHARE: "img/hero.jpg",
    }

    #: Texte alternatif par défaut, quand l'admin n'en a pas saisi.
    DEFAULT_ALTS = {
        Slot.LOGO: _("Maison Riri Design"),
        Slot.HERO: _("Arche décorative en ballons réalisée par Maison Riri Design"),
        Slot.PORTRAIT: _("Rinazar Andriampeno, fondatrice de Maison Riri Design"),
        Slot.ATMOSPHERE: _("Moodboard Red Wine — ambiance, tablescape et détails floraux"),
        Slot.SHARE: _("Maison Riri Design"),
    }

    slot = models.CharField(
        _("emplacement"), max_length=24, choices=Slot.choices, unique=True,
        help_text=_("Chaque emplacement ne peut recevoir qu'une seule image."),
    )
    image = models.ImageField(_("image"), upload_to="site/")
    alt_fr = models.CharField(
        _("texte alternatif (FR)"), max_length=200, blank=True,
        help_text=_("Description de l'image pour l'accessibilité et le référencement."),
    )
    alt_de = models.CharField(_("texte alternatif (DE)"), max_length=200, blank=True)
    updated_at = models.DateTimeField(_("mise à jour le"), auto_now=True)

    class Meta:
        ordering = ["slot"]
        verbose_name = _("image du site")
        verbose_name_plural = _("images du site")

    def __str__(self):
        return self.get_slot_display()

    @classmethod
    def all_slots(cls):
        """Dictionnaire ``{slot: ResolvedImage}`` couvrant tous les emplacements.

        Une seule requête par page, sans cache : un changement fait en admin est
        ainsi visible immédiatement, y compris derrière plusieurs processus.
        """
        custom = {obj.slot: obj for obj in cls.objects.all()}
        return {slot: ResolvedImage(slot, custom.get(slot)) for slot in cls.FALLBACKS}


class ResolvedImage(LocalizedMixin):
    """Ce que les gabarits manipulent : une URL et un texte alternatif.

    Volontairement distinct de ``SiteImage`` : l'objet reste utilisable pour un
    emplacement que personne n'a encore personnalisé, et le gabarit n'a donc
    jamais à savoir si l'image vient de la base ou des fichiers d'origine.
    """

    def __init__(self, slot, obj=None):
        self.slot = slot
        self._url = obj.image.url if obj and obj.image else ""
        self.alt_fr = obj.alt_fr if obj else ""
        self.alt_de = obj.alt_de if obj else ""

    def __str__(self):
        return self.url

    @property
    def is_custom(self):
        """Vrai si une image a été envoyée depuis l'administration."""
        return bool(self._url)

    @property
    def url(self):
        return self._url or static(SiteImage.FALLBACKS[self.slot])

    @property
    def alt(self):
        return self.localized("alt") or SiteImage.DEFAULT_ALTS[self.slot]


class SiteText(AutoTranslated):
    """Un texte de page modifiable depuis l'administration.

    La liste des textes possibles vit dans ``core/content.py`` (clé, libellé,
    valeur par défaut). Une ligne vide ici signifie « garder le texte par
    défaut » ; une ligne renseignée le remplace immédiatement sur le site.
    """

    TRANSLATED_PAIRS = (("text_fr", "text_de"),)

    key = models.CharField(_("clé"), max_length=60, unique=True, editable=False)
    position = models.PositiveIntegerField(_("ordre"), default=0, editable=False)
    text_fr = models.TextField(
        _("texte (FR)"), blank=True,
        help_text=_("Laissez vide pour conserver le texte d'origine."),
    )
    text_de = models.TextField(
        _("texte (DE)"), blank=True,
        help_text=_("Laissé vide, il est traduit automatiquement à partir du texte français."),
    )
    updated_at = models.DateTimeField(_("mise à jour le"), auto_now=True)

    class Meta:
        ordering = ["position"]
        verbose_name = _("texte du site")
        verbose_name_plural = _("textes du site")

    def __str__(self):
        spec = self.spec
        return str(spec.label) if spec else self.key

    @property
    def spec(self):
        from . import content

        return content.REGISTRY.get(self.key)

    @property
    def is_custom(self):
        return bool(self.text_fr or self.text_de)

    @classmethod
    def ensure_all(cls):
        """Crée les lignes manquantes pour que l'admin liste tous les textes."""
        from . import content

        existing = set(cls.objects.values_list("key", flat=True))
        cls.objects.bulk_create(
            [cls(key=spec.key, position=spec.position)
             for spec in content.REGISTRY.values() if spec.key not in existing]
        )
        # Les positions suivent le registre, même s'il a été réordonné.
        for obj in cls.objects.all():
            spec = content.REGISTRY.get(obj.key)
            if spec and obj.position != spec.position:
                cls.objects.filter(pk=obj.pk).update(position=spec.position)

    @classmethod
    def custom_texts(cls):
        """Dictionnaire ``{clé: objet}`` des seuls textes personnalisés."""
        return {obj.key: obj for obj in cls.objects.exclude(text_fr="", text_de="")}
