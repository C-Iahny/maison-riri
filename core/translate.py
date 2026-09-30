"""Traduction automatique français ↔ allemand des contenus saisis en admin.

Quand l'administratrice renseigne un texte dans une langue et laisse l'autre
vide, la version manquante est générée à l'enregistrement via l'API Claude.
Une traduction écrite à la main n'est jamais écrasée (voir ``AutoTranslated``
dans ``models.py``). En cas d'erreur réseau ou d'absence de clé, rien ne
bloque : le texte est enregistré tel quel et l'incident est consigné.

Réglages : ``ANTHROPIC_API_KEY`` (variable d'environnement lue par le SDK) et
``MRD_AUTO_TRANSLATE`` (``0`` pour désactiver).
"""
import logging
import os

from django.conf import settings

logger = logging.getLogger(__name__)

MODEL = "claude-opus-5"

LANGUAGE_NAMES = {"fr": "French", "de": "German"}

SYSTEM_PROMPT = """You translate website copy for Maison Riri Design, an event design and decoration studio based in Freiburg im Breisgau that works in Germany, Alsace and Basel. The site is bilingual: French and German.

Rules:
- Translate faithfully, keeping the warm, elegant and personal tone of the original. The founder speaks in the first person ("je" / "ich").
- In German, address the reader formally with "Sie". In French, use "vous".
- Keep the structure exactly: same number of paragraphs (separated by blank lines) and same line breaks. One line in, one line out.
- Keep brand names, proper nouns, product names, emoji, prices and formatting characters (·, —, «», ✨) as they are. Keep "Maison Riri Design" unchanged. Keep English expressions that are used as-is on the site (e.g. "Candy Bar", "Moodboard", "Backdrop", "Designed with intention.").
- Use the place names customary in the target language (Fribourg-en-Brisgau ↔ Freiburg im Breisgau, Bâle ↔ Basel, Alsace ↔ Elsass, Forêt-Noire ↔ Schwarzwald).
- Output only the translation: no quotes, no explanations, no notes, no preamble."""


def is_enabled():
    return bool(getattr(settings, "AUTO_TRANSLATE", False))


def _request(text, source, target):
    """Appel brut à l'API ; lève l'exception du SDK en cas d'échec."""
    import anthropic

    prompt = "Translate the following text from %s to %s.\n\n<text>\n%s\n</text>" % (
        LANGUAGE_NAMES[source], LANGUAGE_NAMES[target], text
    )
    client = anthropic.Anthropic(timeout=45.0, max_retries=1)
    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        output_config={"effort": "low"},
        messages=[{"role": "user", "content": prompt}],
    )
    if response.stop_reason == "refusal":
        raise RuntimeError("demande refusée par le modèle")
    output = "".join(block.text for block in response.content if block.type == "text").strip()
    if not output:
        raise RuntimeError("réponse vide")
    return output


def has_credentials():
    return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"))


def translate(text, source, target):
    """Traduit ``text`` de ``source`` vers ``target`` (``"fr"`` / ``"de"``).

    Renvoie la traduction, ou ``None`` si elle n'a pas pu être obtenue.
    """
    text = (text or "").strip()
    if not text or source == target:
        return None
    try:
        return _request(text, source, target)
    except Exception as exc:  # noqa: BLE001 — la traduction ne doit jamais bloquer l'enregistrement
        logger.warning("Traduction automatique impossible : %s", describe_error(exc))
        return None


def describe_error(exc):
    """Message lisible pour un échec d'appel à l'API."""
    try:
        import anthropic
    except ImportError:  # pragma: no cover
        return str(exc)
    if isinstance(exc, TypeError) and "authentication" in str(exc).lower():
        return "aucune clé API trouvée (variable ANTHROPIC_API_KEY absente)"
    if isinstance(exc, anthropic.AuthenticationError):
        return "clé API refusée par Anthropic (vérifiez ANTHROPIC_API_KEY)"
    if isinstance(exc, anthropic.PermissionDeniedError):
        return "clé API sans autorisation pour ce modèle : %s" % exc.message
    if isinstance(exc, anthropic.NotFoundError):
        return "modèle introuvable (%s) : %s" % (MODEL, exc.message)
    if isinstance(exc, anthropic.RateLimitError):
        return "limite de débit ou crédit épuisé chez Anthropic : %s" % exc.message
    if isinstance(exc, anthropic.APIStatusError):
        return "erreur API %s : %s" % (exc.status_code, exc.message)
    if isinstance(exc, anthropic.APIConnectionError):
        return "API Claude injoignable depuis le serveur"
    return "%s : %s" % (type(exc).__name__, exc)


def diagnose():
    """Essai réel, pour la page d'aide : ``(ok, message)``."""
    if not is_enabled():
        return False, "La traduction automatique est désactivée (MRD_AUTO_TRANSLATE=0)."
    if not has_credentials():
        return False, "Aucune clé API trouvée : la variable ANTHROPIC_API_KEY n'est pas visible par le site."
    try:
        output = _request("Bonjour, je suis Rina, fondatrice de Maison Riri Design.", "fr", "de")
    except Exception as exc:  # noqa: BLE001
        return False, "L'appel à l'API a échoué : %s" % describe_error(exc)
    return True, "La traduction fonctionne. Essai : « %s »" % output
