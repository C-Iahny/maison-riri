"""Plan de site — utile pour le référencement local (Freiburg, Alsace, Bâle)."""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Project


class StaticSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.8
    i18n = True

    def items(self):
        return ["core:home", "core:about", "core:services", "core:portfolio", "core:contact"]

    def location(self, item):
        return reverse(item)


class ProjectSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.6
    i18n = True

    def items(self):
        return Project.objects.published()

    def lastmod(self, obj):
        return obj.created_at
