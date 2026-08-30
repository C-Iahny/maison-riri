"""Back-office : gestion du portfolio et suivi des demandes de devis."""
from django.contrib import admin, messages
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from . import google_form
from .models import (
    InspirationImage,
    PaletteColor,
    Project,
    ProjectImage,
    QuoteRequest,
    SiteImage,
)


def _thumbnail(image_field, height=90):
    """Petite vignette pour repérer une image d'un coup d'œil dans l'admin."""
    if not image_field:
        return "—"
    return format_html(
        '<img src="{}" style="max-height:{}px;border-radius:4px">', image_field.url, height
    )


@admin.register(SiteImage)
class SiteImageAdmin(admin.ModelAdmin):
    """Les visuels fixes du site : logo, accueil, portrait, ambiance, partage.

    Un emplacement laissé vide affiche l'image d'origine livrée avec le site ;
    il suffit d'en envoyer une nouvelle pour la remplacer partout, aussitôt.
    """

    list_display = ("preview", "slot", "updated_at")
    list_display_links = ("preview", "slot")
    readonly_fields = ("preview_large", "updated_at")
    fields = ("slot", "image", "preview_large", "alt_fr", "alt_de", "updated_at")

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


class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 3
    readonly_fields = ("preview",)
    fields = ("preview", "image", "stage", "caption_fr", "caption_de", "order")

    @admin.display(description=_("Aperçu"))
    def preview(self, obj):
        return _thumbnail(obj.image)


class PaletteColorInline(admin.TabularInline):
    model = PaletteColor
    extra = 5
    fields = ("hex_code", "name", "order")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title_fr", "kind", "location", "year", "is_featured", "is_published", "order")
    list_editable = ("is_featured", "is_published", "order")
    list_filter = ("kind", "is_published", "is_featured", "year")
    search_fields = ("title_fr", "title_de", "summary_fr", "summary_de", "location")
    prepopulated_fields = {"slug": ("title_fr",)}
    inlines = [ProjectImageInline, PaletteColorInline]
    readonly_fields = ("cover_preview",)
    fieldsets = (
        (None, {"fields": ("slug", "kind", "cover", "cover_preview",
                           ("is_featured", "is_published", "order"))}),
        (_("Français"), {"fields": ("title_fr", "subtitle_fr", "event_type_fr", "summary_fr", "story_fr", "keywords_fr")}),
        (_("Deutsch"), {"fields": ("title_de", "subtitle_de", "event_type_de", "summary_de", "story_de", "keywords_de")}),
        (_("Repères"), {"fields": ("location", "year")}),
    )

    @admin.display(description=_("Couverture actuelle"))
    def cover_preview(self, obj):
        return _thumbnail(obj.cover, height=220)


class InspirationImageInline(admin.TabularInline):
    model = InspirationImage
    extra = 0
    readonly_fields = ("preview", "uploaded_at")
    fields = ("preview", "image", "uploaded_at")

    @admin.display(description=_("Aperçu"))
    def preview(self, obj):
        return _thumbnail(obj.image, height=120)


@admin.register(QuoteRequest)
class QuoteRequestAdmin(admin.ModelAdmin):
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
