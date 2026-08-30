from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from core import views as core_views
from core.sitemaps import ProjectSitemap, StaticSitemap

sitemaps = {"pages": StaticSitemap(), "projects": ProjectSitemap()}

urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
    path("robots.txt", core_views.robots_txt, name="robots"),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap"),
]

urlpatterns += i18n_patterns(
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    prefix_default_language=True,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = "core.views.page_not_found"
handler500 = "core.views.server_error"

admin.site.site_header = "Maison Riri Design"
admin.site.site_title = "Maison Riri Design"
admin.site.index_title = "Administration du site"
