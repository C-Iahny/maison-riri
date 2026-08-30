"""Vues publiques du site Maison Riri Design."""
import logging

from django.conf import settings
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.utils.translation import get_language
from django.views.generic import DetailView, FormView, ListView, TemplateView

from . import google_form
from .forms import QuoteRequestForm
from .models import InspirationImage, Project

logger = logging.getLogger(__name__)


class HomeView(TemplateView):
    template_name = "core/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        featured = list(Project.objects.featured().prefetch_related("images")[:3])
        if not featured:
            featured = list(Project.objects.published().prefetch_related("images")[:3])
        context["featured_projects"] = featured
        return context


class AboutView(TemplateView):
    template_name = "core/about.html"


class ServicesView(TemplateView):
    template_name = "core/services.html"


class PortfolioView(ListView):
    template_name = "core/portfolio.html"
    context_object_name = "projects"

    def get_queryset(self):
        queryset = Project.objects.published().prefetch_related("images", "palette")
        kind = self.request.GET.get("type")
        if kind in dict(Project.Kind.choices):
            queryset = queryset.filter(kind=kind)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_kind"] = self.request.GET.get("type", "")
        context["kinds"] = Project.Kind.choices
        return context


class ProjectDetailView(DetailView):
    template_name = "core/project_detail.html"
    context_object_name = "project"

    def get_queryset(self):
        return Project.objects.published().prefetch_related("images", "palette")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        others = Project.objects.published().exclude(pk=self.object.pk)
        context["other_projects"] = list(others[:2])
        return context


class ContactView(FormView):
    template_name = "core/contact.html"
    form_class = QuoteRequestForm
    success_url = reverse_lazy("core:contact_success")

    def get_initial(self):
        initial = super().get_initial()
        language = (get_language() or "fr").split("-")[0]
        initial["preferred_language"] = "Deutsch" if language == "de" else "Français"
        return initial

    def form_valid(self, form):
        quote = form.save(commit=False)
        quote.submitted_language = (get_language() or "fr").split("-")[0]
        quote.save()

        for upload in form.cleaned_data.get("inspirations") or []:
            InspirationImage.objects.create(request=quote, image=upload)

        google_form.forward(quote)
        self._notify(quote)
        return super().form_valid(form)

    def _notify(self, quote):
        recipients = getattr(settings, "QUOTE_NOTIFICATION_RECIPIENTS", [])
        if not recipients:
            return
        detail_url = self.request.build_absolute_uri(
            reverse("admin:core_quoterequest_change", args=[quote.pk])
        )
        lines = [
            "Nouvelle demande de devis — Maison Riri Design",
            "",
            "Nom          : %s" % quote.full_name,
            "E-mail       : %s" % quote.email,
            "Téléphone    : %s" % (quote.phone or "—"),
            "Langue       : %s" % quote.preferred_language,
            "Événement    : %s" % (quote.event_type or "—"),
            "Date         : %s" % (quote.event_date or "—"),
            "Lieu         : %s" % (quote.event_location or "—"),
            "Invités      : %s" % (quote.guest_count or "—"),
            "Budget       : %s" % (quote.budget or "—"),
            "Prestations  : %s" % ", ".join(quote.service_list),
            "Thème        : %s" % (quote.theme or "—"),
            "Photos       : %s" % quote.inspirations.count(),
            "",
            quote.message,
            "",
            "Transmise au Google Form : %s" % ("oui" if quote.forwarded_to_google else "non"),
            detail_url,
        ]
        try:
            send_mail(
                subject="Demande de devis — %s" % quote.full_name,
                message="\n".join(lines),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipients,
                fail_silently=True,
            )
        except Exception:  # noqa: BLE001 — une notification ratée ne doit rien casser
            logger.exception("Notification e-mail impossible pour la demande #%s", quote.pk)


class ContactSuccessView(TemplateView):
    template_name = "core/contact_success.html"


class LegalView(TemplateView):
    template_name = "core/legal.html"


class PrivacyView(TemplateView):
    template_name = "core/privacy.html"


def robots_txt(request):
    sitemap = request.build_absolute_uri("/sitemap.xml")
    body = "User-agent: *\nDisallow: /admin/\nAllow: /\n\nSitemap: %s\n" % sitemap
    return HttpResponse(body, content_type="text/plain")


def page_not_found(request, exception, template_name="404.html"):
    return render(request, template_name, status=404)


def server_error(request, template_name="500.html"):
    return render(request, template_name, status=500)
