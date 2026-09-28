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

from django.conf import settings

logger = logging.getLogger(__name__)

MODEL = "claude-opus-5"

LANGUAGE_NAMES = {"fr": "French", "de": "German"}

SYSTEM_PROMPT = """You translate website copy for Maison Riri Design, an event design and decoration studio based in Freiburg im Breisgau that works in Germany, Alsace and Basel. The site is bilingual: French and German.

Rules:
- Translate faithfully, keeping the warm, elegant and personal tone of the original. The founder speaks in the first person ("je" / "ich").
- In German, address the reader formally with "Sie". In French, use "vous".
- Keep the structure exactly: same number of paragraphs (separated by blank lines) and same line breaks. One line in, one line out.
- Keep brand names, proper nouns, product names, emoji, prices and formatting characters (·, —, «», ✨) as they are. Keep "Maison Riri Design" unchanged. Keep English expressions that are used as-is on the site (e.g. "Sweet Table", "Moodboard", "Backdrop", "Designed with intention.").
- Use the place names customary in the target language (Fribourg-en-Brisgau ↔ Freiburg im Breisgau, Bâle ↔ Basel, Alsace ↔ Elsass, Forêt-Noire ↔ Schwarzwald).
- Output only the translation: no quotes, no explanations, no notes, no preamble."""


def is_enabled():
    return bool(getattr(settings, "AUTO_TRANSLATE", False))


def translate(text, source, target):
    """Traduit ``text`` de ``source`` vers ``target`` (``"fr"`` / ``"de"``).

    Renvoie la traduction, ou ``None`` si elle n'a pas pu être obtenue.
    """
    text = (text or "").strip()
    if not text or source == target:
        return None
    try:
        import anthropic
    except ImportError:  # pragma: no cover — dépendance listée dans requirements.txt
        logger.warning("Traduction automatique impossible : le paquet « anthropic » est absent.")
        return None

    prompt = "Translate the following text from %s to %s.\n\n<text>\n%s\n</text>" % (
        LANGUAGE_NAMES[source], LANGUAGE_NAMES[target], text
    )
    try:
        client = anthropic.Anthropic(timeout=45.0, max_retries=1)
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            output_config={"effort": "low"},
            messages=[{"role": "user", "content": prompt}],
        )
    except (anthropic.AuthenticationError, TypeError):
        # TypeError : le SDK n'a trouvé aucune clé (ni ANTHROPIC_API_KEY ni profil).
        logger.warning("Traduction automatique : clé API Claude absente ou invalide (ANTHROPIC_API_KEY).")
        return None
    except anthropic.APIConnectionError:
        logger.warning("Traduction automatique : API Claude injoignable.")
        return None
    except anthropic.APIStatusError as exc:
        logger.warning("Traduction automatique : erreur API (%s) %s", exc.status_code, exc.message)
        return None
    except Exception:  # noqa: BLE001 — la traduction ne doit jamais bloquer l'enregistrement
        logger.exception("Traduction automatique : erreur inattendue.")
        return None

    if response.stop_reason == "refusal":
        logger.warning("Traduction automatique : demande refusée par le modèle.")
        return None
    output = "".join(block.text for block in response.content if block.type == "text").strip()
    return output or None
