"""Tests du site Maison Riri Design."""
import datetime
import io
import shutil
import tempfile
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import translation
from PIL import Image

from . import choices, google_form
from .models import Project, ProjectImage, QuoteRequest, SiteImage

MEDIA = tempfile.mkdtemp()


def a_png(name="inspiration.png", size=(40, 40)):
    buffer = io.BytesIO()
    Image.new("RGB", size, (120, 30, 45)).save(buffer, "PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


def valid_post(**overrides):
    data = {
        "full_name": "Marie Dupont",
        "email": "marie@example.com",
        "phone": "+33 6 12 34 56 78",
        "preferred_language": "Français",
        "event_type": "Hochzeit | Mariage",
        "event_date": "2027-05-15",
        "event_location": "Colmar",
        "guest_count": "51–100 Personen | 51 à 100 personnes",
        "services": ["Sweet Table", "Tischdekoration | Décoration de table"],
        "theme": "Bordeaux & crème",
        "budget": "3.000 € –  4.500 €",
        "message": "Nous fêtons nos trente ans.",
        "referral": "Instagram",
        "consent": "on",
        "website": "",
    }
    data.update(overrides)
    return data


@override_settings(MEDIA_ROOT=MEDIA, GOOGLE_FORM_ENABLED=False, QUOTE_NOTIFICATION_RECIPIENTS=[])
class QuoteRequestFormTests(TestCase):
    def setUp(self):
        # Le middleware de langue laisse la locale active d'un test à l'autre.
        translation.activate("fr")
        self.addCleanup(translation.activate, "fr")

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def test_valid_submission_is_saved_and_redirects(self):
        response = self.client.post(reverse("core:contact"), valid_post())

        self.assertRedirects(response, reverse("core:contact_success"))
        quote = QuoteRequest.objects.get()
        self.assertEqual(quote.full_name, "Marie Dupont")
        self.assertEqual(quote.event_date, datetime.date(2027, 5, 15))
        self.assertEqual(sorted(quote.service_list), ["Sweet Table", "Tischdekoration | Décoration de table"])
        self.assertEqual(quote.submitted_language, "fr")
        self.assertTrue(quote.consent)

    def test_phone_is_optional_but_consent_is_not(self):
        self.client.post(reverse("core:contact"), valid_post(phone=""))
        self.assertEqual(QuoteRequest.objects.count(), 1)

        response = self.client.post(reverse("core:contact"), valid_post(consent=""))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(QuoteRequest.objects.count(), 1)
        self.assertIn("consent", response.context["form"].errors)

    def test_inspiration_photos_are_attached(self):
        self.client.post(
            reverse("core:contact"),
            valid_post(inspirations=[a_png("une.png"), a_png("deux.png")]),
        )
        quote = QuoteRequest.objects.get()
        self.assertEqual(quote.inspirations.count(), 2)

    def test_oversized_upload_is_rejected(self):
        heavy = SimpleUploadedFile("gros.png", b"x" * (9 * 1024 * 1024), content_type="image/png")
        response = self.client.post(reverse("core:contact"), valid_post(inspirations=heavy))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(QuoteRequest.objects.count(), 0)
        self.assertIn("inspirations", response.context["form"].errors)

    def test_honeypot_blocks_robots(self):
        response = self.client.post(reverse("core:contact"), valid_post(website="http://spam"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(QuoteRequest.objects.count(), 0)

    def test_german_submission_records_its_language(self):
        self.client.post("/de/kontakt/", valid_post())
        self.assertEqual(QuoteRequest.objects.get().submitted_language, "de")


@override_settings(GOOGLE_FORM_ENABLED=True, GOOGLE_FORM_ACTION="https://example.invalid/formResponse")
class GoogleFormBridgeTests(TestCase):
    def make_quote(self, **kwargs):
        defaults = dict(
            full_name="Marie Dupont",
            email="marie@example.com",
            phone="",
            preferred_language="Français",
            event_type="Hochzeit | Mariage",
            event_date=datetime.date(2027, 5, 15),
            event_location="Colmar",
            guest_count="51–100 Personen | 51 à 100 personnes",
            services="Sweet Table\nBeratung | Conseil",
            budget="+ 4.500 €",
            message="Bonjour",
            consent=True,
            submitted_language="fr",
        )
        defaults.update(kwargs)
        return QuoteRequest.objects.create(**defaults)

    def test_payload_uses_the_expected_entry_ids(self):
        payload = dict(google_form.build_payload(self.make_quote()))

        self.assertEqual(payload[choices.ENTRY_FULL_NAME], "Marie Dupont")
        self.assertEqual(payload["%s_year" % choices.ENTRY_EVENT_DATE], "2027")
        self.assertEqual(payload["%s_month" % choices.ENTRY_EVENT_DATE], "5")
        self.assertEqual(payload["%s_day" % choices.ENTRY_EVENT_DATE], "15")
        self.assertEqual(payload[choices.ENTRY_CONSENT], choices.CONSENT_FR)

    def test_missing_phone_is_replaced_rather_than_left_empty(self):
        payload = dict(google_form.build_payload(self.make_quote()))
        self.assertEqual(payload[choices.ENTRY_PHONE], "Non communiqué")

    def test_multiple_services_are_sent_as_repeated_keys(self):
        pairs = google_form.build_payload(self.make_quote())
        services = [value for key, value in pairs if key == choices.ENTRY_SERVICES]
        self.assertEqual(services, ["Sweet Table", "Beratung | Conseil"])

    def test_german_submission_sends_the_german_consent_text(self):
        quote = self.make_quote(submitted_language="de", phone="")
        payload = dict(google_form.build_payload(quote))
        self.assertEqual(payload[choices.ENTRY_CONSENT], choices.CONSENT_DE)
        self.assertEqual(payload[choices.ENTRY_PHONE], "Nicht angegeben")

    def test_network_failure_is_recorded_without_raising(self):
        quote = self.make_quote()
        with mock.patch("core.google_form.request.urlopen", side_effect=OSError("réseau coupé")):
            self.assertFalse(google_form.forward(quote))

        quote.refresh_from_db()
        self.assertFalse(quote.forwarded_to_google)
        self.assertIn("réseau", quote.forward_error)


@override_settings(MEDIA_ROOT=MEDIA)
class PageTests(TestCase):
    def setUp(self):
        translation.activate("fr")
        self.addCleanup(translation.activate, "fr")

    @classmethod
    def setUpTestData(cls):
        cls.project = Project.objects.create(
            slug="dreamland",
            title_fr="Dreamland",
            title_de="Dreamland",
            summary_fr="Une remise de diplômes colorée.",
            summary_de="Eine farbenfrohe Abschlussfeier.",
            cover=a_png("cover.png"),
            is_featured=True,
        )
        cls.concept = Project.objects.create(
            slug="red-wine",
            kind=Project.Kind.CONCEPT,
            title_fr="Thirty & Fabulous",
            cover=a_png("cover2.png"),
        )
        ProjectImage.objects.create(
            project=cls.project, image=a_png("g.png"), stage=ProjectImage.Stage.RESULT
        )

    def test_public_pages_answer(self):
        for name in ("home", "about", "services", "portfolio", "contact", "legal", "privacy"):
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse("core:%s" % name)).status_code, 200)

    def test_project_detail_groups_images_by_stage(self):
        response = self.client.get(self.project.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        stages = response.context["project"].images_by_stage()
        self.assertEqual([bucket["key"] for bucket in stages], ["result"])

    def test_portfolio_filter_by_kind(self):
        response = self.client.get(reverse("core:portfolio"), {"type": "concept"})
        self.assertEqual(list(response.context["projects"]), [self.concept])

    def test_german_urls_and_translations(self):
        response = self.client.get("/de/ueber-mich/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Über mich")

    def test_localized_fields_follow_the_active_language(self):
        response = self.client.get("/de/portfolio/dreamland/")
        self.assertContains(response, "Eine farbenfrohe Abschlussfeier.")

    def test_root_redirects_to_a_language_prefix(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith(("/fr/", "/de/")))

    def test_robots_and_sitemap(self):
        self.assertContains(self.client.get("/robots.txt"), "Sitemap:")
        self.assertEqual(self.client.get("/sitemap.xml").status_code, 200)


@override_settings(MEDIA_ROOT=MEDIA)
class SiteImageTests(TestCase):
    """Les visuels fixes du site doivent être remplaçables sans redéploiement."""

    def setUp(self):
        translation.activate("fr")
        self.addCleanup(translation.activate, "fr")

    def test_pages_fall_back_to_the_shipped_visuals(self):
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, "img/hero.jpg")
        self.assertFalse(SiteImage.all_slots()["hero"].is_custom)

    def test_uploading_replaces_the_visual_everywhere(self):
        SiteImage.objects.create(slot=SiteImage.Slot.LOGO, image=a_png("nouveau-logo.png"))

        for name in ("home", "about"):
            with self.subTest(page=name):
                response = self.client.get(reverse("core:%s" % name))
                self.assertContains(response, "nouveau-logo")
                self.assertNotContains(response, "img/logo.jpg")

    def test_alt_text_follows_the_active_language(self):
        SiteImage.objects.create(
            slot=SiteImage.Slot.PORTRAIT,
            image=a_png("portrait.png"),
            alt_fr="Portrait de la fondatrice",
            alt_de="Porträt der Gründerin",
        )
        self.assertContains(self.client.get(reverse("core:about")), "Portrait de la fondatrice")
        self.assertContains(self.client.get("/de/ueber-mich/"), "Porträt der Gründerin")

    def test_alt_text_defaults_when_left_blank(self):
        SiteImage.objects.create(slot=SiteImage.Slot.HERO, image=a_png("hero.png"))
        self.assertEqual(
            SiteImage.all_slots()["hero"].alt, str(SiteImage.DEFAULT_ALTS[SiteImage.Slot.HERO])
        )

    def test_removing_an_upload_restores_the_shipped_visual(self):
        image = SiteImage.objects.create(slot=SiteImage.Slot.HERO, image=a_png("hero.png"))
        self.assertTrue(SiteImage.all_slots()["hero"].is_custom)

        image.delete()
        self.assertContains(self.client.get(reverse("core:home")), "img/hero.jpg")
