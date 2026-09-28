"""Balise ``{% site_text "clé" %}`` : texte de page, personnalisable en admin.

Le texte saisi dans l'administration (``SiteText``) a priorité ; sinon la
valeur par défaut du registre ``core/content.py`` est affichée, traduite dans
la langue active. Les formes « paragraphes » et « liste » sont rendues en
``<p>`` et ``<li>``, le reste en texte simple échappé.
"""
from django import template
from django.utils.html import format_html_join
from django.utils.translation import get_language

from .. import content

register = template.Library()


def resolve(key, custom_texts):
    """Renvoie ``(spec, liste d'éléments)`` pour la langue active."""
    spec = content.REGISTRY[key]
    obj = (custom_texts or {}).get(key)
    if obj is not None:
        lang = (get_language() or "fr").split("-")[0]
        value = obj.text_de if lang == "de" and obj.text_de else (obj.text_fr or obj.text_de)
        if value:
            return spec, content.split_items(value, spec.kind)
    return spec, spec.default_items() if spec.kind != "text" else [str(spec.default)]


@register.simple_tag(takes_context=True)
def site_text(context, key):
    spec, items = resolve(key, context.get("site_texts"))
    if spec.kind == "paragraphs":
        return format_html_join("\n", "<p>{}</p>", ((item,) for item in items))
    if spec.kind == "lines":
        return format_html_join("\n", "<li>{}</li>", ((item,) for item in items))
    return items[0] if items else ""
