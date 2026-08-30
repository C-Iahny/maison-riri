"""Passerelle vers le Google Form de Maison Riri Design.

Le site enregistre chaque demande en base, puis la recopie dans le formulaire
Google déjà en place afin que la feuille de calcul du client reste alimentée.
La transmission est volontairement « best effort » : si Google est
indisponible, la demande reste enregistrée et l'erreur est consignée sur
l'objet, sans jamais faire échouer l'envoi côté visiteur.

Le téléversement de photos d'inspiration n'est pas relayé : Google Forms
imposerait une connexion à un compte Google au visiteur. Ces fichiers sont
donc stockés par le site et consultables depuis l'administration.
"""
import logging
from urllib import error, parse, request

from django.conf import settings

from . import choices

logger = logging.getLogger(__name__)

_USER_AGENT = "Mozilla/5.0 (compatible; MaisonRiriDesign/1.0; +https://maison-riri.com)"


def build_payload(quote):
    """Construit les couples ``entry.X`` attendus par le Google Form."""
    german = quote.submitted_language.startswith("de")
    # Le téléphone est facultatif sur le site mais obligatoire côté Google :
    # on transmet une valeur explicite plutôt que de faire rejeter l'envoi.
    phone = quote.phone or ("Nicht angegeben" if german else "Non communiqué")

    pairs = [
        (choices.ENTRY_FULL_NAME, quote.full_name),
        (choices.ENTRY_EMAIL, quote.email),
        (choices.ENTRY_PHONE, phone),
        (choices.ENTRY_LANGUAGE, quote.preferred_language),
        (choices.ENTRY_EVENT_LOCATION, quote.event_location),
        (choices.ENTRY_GUESTS, quote.guest_count),
        (choices.ENTRY_THEME, quote.theme),
        (choices.ENTRY_BUDGET, quote.budget),
        (choices.ENTRY_MESSAGE, quote.message),
    ]
    if quote.event_type:
        pairs.append((choices.ENTRY_EVENT_TYPE, quote.event_type))
    if quote.referral:
        pairs.append((choices.ENTRY_REFERRAL, quote.referral))

    # Une question « cases à cocher » se transmet en répétant la même clé.
    for service in quote.service_list:
        pairs.append((choices.ENTRY_SERVICES, service))

    if quote.event_date:
        pairs += [
            ("%s_year" % choices.ENTRY_EVENT_DATE, str(quote.event_date.year)),
            ("%s_month" % choices.ENTRY_EVENT_DATE, str(quote.event_date.month)),
            ("%s_day" % choices.ENTRY_EVENT_DATE, str(quote.event_date.day)),
        ]

    if quote.consent:
        pairs.append((choices.ENTRY_CONSENT, choices.CONSENT_DE if german else choices.CONSENT_FR))

    pairs += [("fvv", "1"), ("pageHistory", "0,1,2,3"), ("submit", "Submit")]
    return [(key, value) for key, value in pairs if value not in (None, "")]


def forward(quote):
    """Transmet la demande à Google. Renvoie ``True`` en cas de succès."""
    if not settings.GOOGLE_FORM_ENABLED or not settings.GOOGLE_FORM_ACTION:
        return False

    body = parse.urlencode(build_payload(quote)).encode("utf-8")
    req = request.Request(
        settings.GOOGLE_FORM_ACTION,
        data=body,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": _USER_AGENT,
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=settings.GOOGLE_FORM_TIMEOUT) as response:
            ok = 200 <= response.status < 400
        if not ok:
            raise error.HTTPError(settings.GOOGLE_FORM_ACTION, response.status, "réponse inattendue", None, None)
    except Exception as exc:  # noqa: BLE001 — aucune erreur réseau ne doit gêner le visiteur
        logger.warning("Transmission Google Form impossible pour la demande #%s : %s", quote.pk, exc)
        quote.forwarded_to_google = False
        quote.forward_error = str(exc)[:1000]
    else:
        quote.forwarded_to_google = True
        quote.forward_error = ""
    quote.save(update_fields=["forwarded_to_google", "forward_error"])
    return quote.forwarded_to_google
