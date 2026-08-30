from django.urls import path
from django.utils.translation import gettext_lazy as _

from . import views

app_name = "core"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path(_("a-propos/"), views.AboutView.as_view(), name="about"),
    path(_("prestations/"), views.ServicesView.as_view(), name="services"),
    path(_("portfolio/"), views.PortfolioView.as_view(), name="portfolio"),
    path(_("portfolio/<slug:slug>/"), views.ProjectDetailView.as_view(), name="project_detail"),
    path(_("contact/"), views.ContactView.as_view(), name="contact"),
    path(_("contact/merci/"), views.ContactSuccessView.as_view(), name="contact_success"),
    path(_("mentions-legales/"), views.LegalView.as_view(), name="legal"),
    path(_("confidentialite/"), views.PrivacyView.as_view(), name="privacy"),
]
