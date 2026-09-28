"""Back-office : images et textes du site, portfolio, demandes de devis.

L'interface s'appuie sur django-unfold (voir ``UNFOLD`` dans les réglages) et
est pensée pour une utilisation sans connaissance technique : libellés en
français, aperçus d'images partout, aucun champ inutile.
"""
from django.contrib import admin, messages
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group, User
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from . import content, google_form
from .models import (
    InspirationImage,
    PaletteColor,
    Project,
    ProjectImage,
    QuoteRequest,
    SiteImage,
    SiteText,
)


def _thumbnail(image_field, height=90):
    """Petite vignette pour repérer une image d'un coup d'œil dans l'admin."""
    if not image_field:
        return "—"
    return format_html(
        '<img src="{}" style="max-height:{}px;border-radius:6px">', image_field.url, height
    )


class TranslationStateMixin:
    """Affiche quels champs ont été remplis par la traduction automatique."""

    @admin.display(description=_("Traduction automatique"))
    def translation_state(self, obj):
        if obj is None or not obj.pk:
            return _("Laissez une langue vide : elle sera traduite automatiquement à l'enregistrement.")
        fields = obj.machine_translated_fields()
        if not fields:
            return _("Aucun champ traduit automatiquement.")
        return format_html("{} {}", _("Champs traduits automatiquement :"), ", ".join(fields))


# --- Tableau de bord ----------------------------------------------------------

def new_quotes_badge(request):
    """Pastille « nouvelles demandes » dans le menu latéral."""
    count = QuoteRequest.objects.filter(status=QuoteRequest.Status.NEW).count()
    return count or None


def dashboard_callback(request, context):
    """Chiffres et raccourcis affichés sur la page d'accueil du back-office."""
    context["dashboard"] = {
        "new_quotes": QuoteRequest.objects.filter(status=QuoteRequest.Status.NEW).count(),
        "projects": Project.objects.published().count(),
        "custom_images": SiteImage.objects.count(),
        "custom_texts": SiteText.objects.exclude(text_fr="", text_de="").count(),
        "latest_quotes": QuoteRequest.objects.order_by("-created_at")[:5],
    }
    return context


# --- Images du site -----------------------------------------------------------

@admin.register(SiteImage)
class SiteImageAdmin(TranslationStateMixin, ModelAdmin):
    """Les visuels fixes du site : logo, accueil, portrait, ambiance, partage.

    Un emplacement laissé vide affiche l'image d'origine livrée avec le site ;
    il suffit d'en envoyer une nouvelle pour la remplacer partout, aussitôt.
    """

    list_display = ("preview", "slot", "updated_at")
    list_display_links = ("preview", "slot")
    readonly_fields = ("preview_large", "updated_at", "translation_state")
    fieldsets = (
        (None, {"fields": ("slot", "image", "preview_large")}),
        (_("Description de l'image"), {
            "fields": ("alt_fr", "alt_de", "translation_state"),
            "description": _("Une phrase qui décrit l'image, lue par les lecteurs d'écran et les moteurs de recherche. Facultatif. Remplissez une seule langue : l'autre est traduite automatiquement."),
        }),
        (None, {"fields": ("updated_at",)}),
    )

    @admin.display(description=_("Aperçu"))
    def preview(self, obj):
        return _thumbnail(obj.image)

    @admin.display(description=_("Image actuelle"))
    def preview_large(self, obj):
        return _thumbnail(obj.image, height=260)

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        """N'affiche que les emplacements encore libres lors d'une création."""
        if db_field.name == "slot":
            taken = set(SiteImage.objects.values_list("slot", flat=True))
            current = request.resolver_match.kwargs.get("object_id")
            if current:
                taken -= {SiteImage.objects.filter(pk=current).values_list("slot", flat=True).first()}
            kwargs["choices"] = [c for c in SiteImage.Slot.choices if c[0] not in taken]
        return super().formfield_for_choice_field(db_field, request, **kwargs)


# --- Textes du site -----------------------------------------------------------

class PageFilter(admin.SimpleListFilter):
    title = _("page")
    parameter_name = "page"

    def lookups(self, request, model_admin):
        return content.PAGES

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(key__startswith=self.value() + ".")
        return queryset


@admin.register(SiteText)
class SiteTextAdmin(TranslationStateMixin, ModelAdmin):
    """Chaque texte de page, avec sa valeur d'origine et la version personnalisée."""

    list_display = ("label", "page", "state", "updated_at")
    list_display_links = ("label",)
    list_filter = (PageFilter,)
    search_fields = ("key", "text_fr", "text_de")
    readonly_fields = ("label", "page", "help", "default_fr", "translation_state")
    fieldsets = (
        (None, {"fields": ("label", "page", "help", "default_fr")}),
        (_("Votre texte"), {
            "fields": ("text_fr", "text_de", "translation_state"),
            "description": _("Ce que vous écrivez ici remplace le texte d'origine sur le site, immédiatement. Écrivez dans une seule langue : l'autre est traduite automatiquement à l'enregistrement. Videz les deux champs pour revenir au texte d'origine."),
        }),
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        SiteText.ensure_all()
        return super().changelist_view(request, extra_context)

    @admin.display(description=_("Texte"))
    def label(self, obj):
        return str(obj)

    @admin.display(description=_("Page"))
    def page(self, obj):
        return obj.spec.page_label if obj.spec else "—"

    @admin.display(description=_("Conseil"))
    def help(self, obj):
        if not obj.spec:
            return "—"
        hint = str(obj.spec.help) if obj.spec.help else ""
        forms = {
            "text": _("Une seule ligne."),
            "paragraphs": _("Plusieurs paragraphes possibles, séparés par une ligne vide."),
            "lines": _("Un élément par ligne."),
        }
        return ("%s %s" % (hint, forms[obj.spec.kind])).strip()

    @admin.display(description=_("Texte d'origine (FR)"))
    def default_fr(self, obj):
        return format_html("<pre style=\"white-space:pre-wrap;font:inherit;margin:0\">{}</pre>",
                           obj.spec.default_text() if obj.spec else "")

    @admin.display(description=_("État"))
    def state(self, obj):
        return _("Personnalisé") if obj.is_custom else _("Texte d'origine")

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        rows = 3 if obj and obj.spec and obj.spec.kind == "text" else 10
        for name in ("text_fr", "text_de"):
            if name in form.base_fields:
                form.base_fields[name].widget.attrs["rows"] = rows
        return form


# --- Portfolio ----------------------------------------------------------------

class ProjectImageInline(TabularInline):
    model = ProjectImage
    extra = 1
    readonly_fields = ("preview",)
    fields = ("preview", "image", "stage", "caption_fr", "caption_de", "order")
    verbose_name = _("photo")
    verbose_name_plural = _("Galerie — photos du projet")

    @admin.display(description=_("Aperçu"))
    def preview(self, obj):
        return _thumbnail(obj.image)


class PaletteColorInline(TabularInline):
    model = PaletteColor
    extra = 1
    fields = ("swatch", "hex_code", "name", "name_de", "order")
    readonly_fields = ("swatch",)
    verbose_name = _("couleur")
    verbose_name_plural = _("Palette — couleurs du projet")

    @admin.display(description="")
    def swatch(self, obj):
        if not obj.hex_code:
            return ""
        return format_html(
            '<span style="display:inline-block;width:28px;height:28px;border-radius:6px;background:{};border:1px solid rgba(0,0,0,.1)"></span>',
            obj.hex_code,
        )


@admin.register(Project)
class ProjectAdmin(TranslationStateMixin, ModelAdmin):
    list_display = ("cover_thumb", "title_fr", "kind", "location", "year", "is_featured", "is_published", "order")
    list_display_links = ("cover_thumb", "title_fr")
    list_editable = ("is_featured", "is_published", "order")
    list_filter = ("kind", "is_published", "is_featured", "year")
    search_fields = ("title_fr", "title_de", "summary_fr", "summary_de", "location")
    prepopulated_fields = {"slug": ("title_fr",)}
    inlines = [ProjectImageInline, PaletteColorInline]
    readonly_fields = ("cover_preview", "translation_state")
    warn_unsaved_form = True
    fieldsets = (
        (_("L'essentiel"), {
            "fields": ("kind", "cover", "cover_preview", ("is_featured", "is_published", "order"), "slug"),
            "description": _("« Concept créatif » signale un projet imaginé mais pas encore réalisé : l'étiquette s'affiche automatiquement sur le site."),
        }),
        (_("Textes en français"), {
            "fields": ("title_fr", "subtitle_fr", "event_type_fr", "summary_fr", "story_fr", "keywords_fr"),
        }),
        (_("Textes en allemand"), {
            "fields": ("title_de", "subtitle_de", "event_type_de", "summary_de", "story_de", "keywords_de", "translation_state"),
            "description": _("Facultatif : un champ laissé vide est traduit automatiquement à partir du français à l'enregistrement. Ce que vous écrivez ici à la main est conservé tel quel."),
            "classes": ("collapse",),
        }),
        (_("Repères"), {"fields": ("location", "year")}),
    )

    @admin.display(description=_("Couverture"))
    def cover_thumb(self, obj):
        return _thumbnail(obj.cover, height=60)

    @admin.display(description=_("Couverture actuelle"))
    def cover_preview(self, obj):
        return _thumbnail(obj.cover, height=220)


# --- Demandes de devis --------------------------------------------------------

class InspirationImageInline(TabularInline):
    model = InspirationImage
    extra = 0
    readonly_fields = ("preview", "uploaded_at")
    fields = ("preview", "image", "uploaded_at")
    verbose_name_plural = _("Photos d'inspiration envoyées")

    @admin.display(description=_("Aperçu"))
    def preview(self, obj):
        return _thumbnail(obj.image, height=120)


@admin.register(QuoteRequest)
class QuoteRequestAdmin(ModelAdmin):
    list_display = (
        "created_at",
        "full_name",
        "event_type",
        "event_date",
        "budget",
        "status",
        "forwarded_to_google",
    )
    list_filter = ("status", "forwarded_to_google", "budget", "submitted_language", "event_date")
    search_fields = ("full_name", "email", "phone", "event_location", "message")
    date_hierarchy = "created_at"
    list_editable = ("status",)
    inlines = [InspirationImageInline]
    readonly_fields = (
        "created_at",
        "submitted_language",
        "forwarded_to_google",
        "forward_error",
    )
    fieldsets = (
        (_("Contact"), {"fields": ("full_name", "email", "phone", "preferred_language")}),
        (_("Événement"), {"fields": ("event_type", "event_date", "event_location", "guest_count")}),
        (_("Projet"), {"fields": ("services", "theme", "budget", "message", "referral")}),
        (_("Suivi"), {"fields": ("status", "consent", "created_at", "submitted_language",
                                 "forwarded_to_google", "forward_error")}),
    )
    actions = ["retry_google_forward"]

    @admin.action(description=_("Renvoyer vers le Google Form"))
    def retry_google_forward(self, request, queryset):
        sent = 0
        for quote in queryset:
            if google_form.forward(quote):
                sent += 1
        self.message_user(
            request,
            _("%(sent)s demande(s) transmise(s) sur %(total)s.")
            % {"sent": sent, "total": queryset.count()},
            messages.SUCCESS if sent else messages.WARNING,
        )


# --- Comptes (habillage unfold des écrans Django) -----------------------------

admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass
