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
from .models import PaletteColor, Project, ProjectImage, QuoteRequest, SiteImage, SiteText

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
        "services": ["Candy Bar", "Tischdekoration | Décoration de table"],
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
        self.assertEqual(sorted(quote.service_list), ["Candy Bar", "Tischdekoration | Décoration de table"])
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
            services="Candy Bar\nBeratung | Conseil",
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
        # « Candy Bar » part sous le nom que porte encore l'option côté Google.
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

    def test_project_facts_use_a_neutral_label_not_the_form_question(self):
        self.project.event_type_fr = "Cérémonie de fin d'études"
        self.project.event_type_de = "Abschlussfeier"
        self.project.save()
        response = self.client.get("/de/portfolio/dreamland/")
        self.assertContains(response, "Art der Veranstaltung")
        self.assertNotContains(response, "Welche Veranstaltung planen Sie?")

    def test_palette_names_follow_the_active_language(self):
        PaletteColor.objects.create(project=self.project, hex_code="#F0605F", name="Corail", name_de="Koralle")
        PaletteColor.objects.create(project=self.project, hex_code="#F49A4C", name="Abricot")
        self.assertContains(self.client.get("/fr/portfolio/dreamland/"), "Corail")
        german = self.client.get("/de/portfolio/dreamland/")
        self.assertContains(german, "Koralle")
        self.assertNotContains(german, "Corail")
        self.assertContains(german, "Abricot")  # repli sur le français

    def test_legal_pages_carry_no_placeholder(self):
        for url in ("/fr/mentions-legales/", "/fr/confidentialite/", "/de/impressum/", "/de/datenschutz/"):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertNotContains(response, "compléter")
                self.assertNotContains(response, "Modèle")
                self.assertNotContains(response, "Vorlage")
                self.assertNotContains(response, "ergänzen")
        self.assertContains(self.client.get("/fr/mentions-legales/"), "Railway")

    def test_contact_announces_two_working_days(self):
        self.assertContains(self.client.get("/fr/contact/"), "sous 2 jours ouvrés")
        self.assertContains(self.client.get("/de/kontakt/"), "innerhalb von 2 Werktagen")
        self.assertContains(self.client.get("/de/kontakt/"), "Wobei darf ich Sie unterstützen?")

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


@override_settings(MEDIA_ROOT=MEDIA)
class SiteTextTests(TestCase):
    """Textes de pages modifiables depuis le back-office."""

    def setUp(self):
        translation.activate("fr")
        self.addCleanup(translation.activate, "fr")

    def test_defaults_are_shown_and_translated_when_nothing_is_customised(self):
        self.assertContains(self.client.get("/fr/"), "Des événements qui racontent votre histoire.")
        self.assertContains(self.client.get("/de/"), "Events, die Ihre Geschichte erzählen.")

    def test_custom_text_replaces_the_default_and_is_escaped(self):
        SiteText.objects.create(key="home.hero_title", text_fr="Mon <titre>")
        response = self.client.get("/fr/")
        self.assertContains(response, "<h1>Mon &lt;titre&gt;</h1>", html=False)
        self.assertNotContains(response, "<h1>Des événements qui racontent votre histoire.</h1>")

    def test_german_falls_back_on_the_custom_french_text(self):
        SiteText.objects.create(key="home.hero_title", text_fr="Titre perso")
        self.assertContains(self.client.get("/de/"), "Titre perso")
        SiteText.objects.filter(key="home.hero_title").update(text_de="Eigener Titel")
        self.assertContains(self.client.get("/de/"), "Eigener Titel")

    def test_paragraphs_and_lines_are_rendered_as_html_blocks(self):
        SiteText.objects.create(key="about.story", text_fr="Un.\n\nDeux.")
        SiteText.objects.create(key="contact.good_to_know", text_fr="A\nB")
        self.assertContains(self.client.get("/fr/a-propos/"), "<p>Un.</p>")
        self.assertContains(self.client.get("/fr/a-propos/"), "<p>Deux.</p>")
        self.assertContains(self.client.get("/fr/contact/"), "<li>B</li>")

    def test_ensure_all_creates_one_row_per_registered_text(self):
        from . import content

        SiteText.ensure_all()
        self.assertEqual(SiteText.objects.count(), len(content.REGISTRY))
        SiteText.ensure_all()
        self.assertEqual(SiteText.objects.count(), len(content.REGISTRY))


@override_settings(MEDIA_ROOT=MEDIA)
class BackOfficeTests(TestCase):
    """Le back-office s'affiche et permet les gestes du quotidien."""

    def setUp(self):
        from django.contrib.auth.models import User

        translation.activate("fr")
        self.addCleanup(translation.activate, "fr")
        self.user = User.objects.create_superuser("riri", "riri@example.com", "un-mot-de-passe-solide")
        self.client.force_login(self.user)

    def test_dashboard_help_and_lists_answer(self):
        for url in (
            "/fr/admin/", "/fr/admin/aide/", "/fr/admin/core/siteimage/", "/fr/admin/core/sitetext/",
            "/fr/admin/core/project/", "/fr/admin/core/project/add/", "/fr/admin/core/quoterequest/",
            "/fr/admin/auth/user/",
        ):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_dashboard_links_to_the_four_sections(self):
        response = self.client.get("/fr/admin/")
        for label in ("Images du site", "Textes du site", "Portfolio", "Demandes de devis", "Besoin d'aide"):
            self.assertContains(response, label)

    def test_help_page_requires_a_staff_account(self):
        self.client.logout()
        self.assertEqual(self.client.get("/fr/admin/aide/").status_code, 302)

    def test_text_list_creates_rows_and_saving_one_changes_the_site(self):
        self.client.get("/fr/admin/core/sitetext/")
        row = SiteText.objects.get(key="home.hero_title")
        response = self.client.post(
            reverse("admin:core_sitetext_change", args=[row.pk]),
            {"text_fr": "Titre depuis le back-office", "text_de": ""},
        )
        self.assertEqual(response.status_code, 302)
        self.assertContains(self.client.get("/fr/"), "Titre depuis le back-office")


def fake_translate(text, source, target):
    return "[%s] %s" % (target, text)


@override_settings(MEDIA_ROOT=MEDIA, AUTO_TRANSLATE=True)
@mock.patch("core.translate.translate", side_effect=fake_translate)
class AutoTranslationTests(TestCase):
    """Une langue saisie, l'autre générée — sans jamais écraser une saisie manuelle."""

    def test_missing_german_is_generated_from_french(self, translate):
        text = SiteText.objects.create(key="home.hero_title", text_fr="Bonjour")
        self.assertEqual(text.text_de, "[de] Bonjour")
        self.assertEqual(text.machine_translations, {"text_de": True})
        translate.assert_called_once_with("Bonjour", "fr", "de")

    def test_missing_french_is_generated_from_german(self, translate):
        text = SiteText.objects.create(key="home.hero_title", text_de="Hallo")
        self.assertEqual(text.text_fr, "[fr] Hallo")
        self.assertEqual(text.machine_translations, {"text_fr": True})

    def test_both_languages_given_means_no_call(self, translate):
        SiteText.objects.create(key="home.hero_title", text_fr="Bonjour", text_de="Hallo")
        translate.assert_not_called()

    def test_machine_translation_follows_later_french_edits(self, translate):
        text = SiteText.objects.create(key="home.hero_title", text_fr="Bonjour")
        text = SiteText.objects.get(pk=text.pk)
        text.text_fr = "Bonsoir"
        text.save()
        self.assertEqual(text.text_de, "[de] Bonsoir")

    def test_hand_written_german_is_never_overwritten(self, translate):
        text = SiteText.objects.create(key="home.hero_title", text_fr="Bonjour", text_de="Guten Tag")
        text = SiteText.objects.get(pk=text.pk)
        text.text_fr = "Bonsoir"
        text.save()
        self.assertEqual(text.text_de, "Guten Tag")
        translate.assert_not_called()

    def test_editing_the_generated_german_makes_it_manual(self, translate):
        text = SiteText.objects.create(key="home.hero_title", text_fr="Bonjour")
        text = SiteText.objects.get(pk=text.pk)
        text.text_de = "Guten Abend"
        text.save()
        self.assertEqual(text.machine_translations, {})
        text = SiteText.objects.get(pk=text.pk)
        text.text_fr = "Bonsoir"
        text.save()
        self.assertEqual(text.text_de, "Guten Abend")

    def test_clearing_the_source_clears_its_generated_translation(self, translate):
        text = SiteText.objects.create(key="home.hero_title", text_fr="Bonjour")
        text = SiteText.objects.get(pk=text.pk)
        text.text_fr = ""
        text.save()
        self.assertEqual(text.text_de, "")
        self.assertFalse(text.is_custom)

    def test_api_failure_never_blocks_saving(self, translate):
        translate.side_effect = lambda *a: None
        text = SiteText.objects.create(key="home.hero_title", text_fr="Bonjour")
        self.assertEqual(text.text_de, "")
        self.assertEqual(SiteText.objects.count(), 1)

    def test_projects_and_inline_content_are_covered(self, translate):
        project = Project.objects.create(slug="p", title_fr="Titre", story_fr="Un.\n\nDeux.", cover=a_png("c.png"))
        self.assertEqual(project.title_de, "[de] Titre")
        self.assertEqual(project.story_de, "[de] Un.\n\nDeux.")
        color = PaletteColor.objects.create(project=project, hex_code="#000000", name="Corail")
        self.assertEqual(color.name_de, "[de] Corail")
        image = ProjectImage.objects.create(project=project, image=a_png("g.png"), caption_de="Bühne")
        self.assertEqual(image.caption_fr, "[fr] Bühne")

    def test_disabled_setting_skips_translation(self, translate):
        with self.settings(AUTO_TRANSLATE=False):
            text = SiteText.objects.create(key="home.hero_title", text_fr="Bonjour")
        self.assertEqual(text.text_de, "")
        translate.assert_not_called()
