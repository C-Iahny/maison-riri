"""Registre des textes du site modifiables depuis l'administration.

Chaque entrée décrit un texte de page : où il apparaît, comment il s'appelle
dans le back-office, et sa valeur par défaut. Tant que l'administratrice n'a
rien saisi, c'est la valeur par défaut qui s'affiche — traduite en allemand
via ``locale/`` comme n'importe quel texte du site. Dès qu'un texte est saisi
dans l'administration, il remplace le texte par défaut, sans redéploiement.

Trois formes de texte :

- ``text`` : une ligne (titre, accroche) ;
- ``paragraphs`` : plusieurs paragraphes, séparés par une ligne vide ;
- ``lines`` : une liste, un élément par ligne.
"""
from django.utils.translation import gettext_lazy as _

PAGES = [
    ("home", _("Accueil")),
    ("about", _("À propos")),
    ("services", _("Prestations")),
    ("contact", _("Contact")),
    ("shared", _("Toutes les pages")),
]

# (clé, page, libellé, forme, défaut, aide)
_ENTRIES = [
    # --- Accueil --------------------------------------------------------------
    ("home.hero_title", "home", _("Grand titre"), "text",
     _("Des événements qui racontent votre histoire."),
     _("La phrase affichée sur la grande image de l'accueil.")),
    ("home.hero_claim", "home", _("Sous-titre du bandeau"), "text",
     _("Design événementiel & décoration sur mesure"), ""),
    ("home.intro_statement", "home", _("Phrase d'introduction"), "text",
     _("Concevoir des atmosphères, pas seulement des décors."), ""),
    ("home.intro_lede", "home", _("Introduction — premier paragraphe"), "text",
     _("Maison Riri Design imagine, planifie et met en scène des concepts de décoration entièrement sur mesure pour les anniversaires, les cérémonies et fêtes privées, les événements d'entreprise et les mariages."),
     ""),
    ("home.intro_body", "home", _("Introduction — suite"), "paragraphs",
     [
         _("Du premier échange à l'installation le jour J, chaque projet part d'une histoire : la vôtre. Couleurs, matières, lumières et détails sont choisis pour composer un ensemble cohérent, chaleureux et profondément personnel."),
         _("Basée à Fribourg-en-Brisgau, j'interviens avant tout à Fribourg et dans ses environs — du Kaiserstuhl à la Forêt-Noire —, ainsi qu'en Alsace et dans la région de Bâle, en allemand comme en français."),
     ],
     _("Un paragraphe par bloc, séparés par une ligne vide.")),
    ("home.services_title", "home", _("Titre du bloc Prestations"), "text",
     _("Trois façons de vous accompagner"), ""),
    ("home.corporate_title", "home", _("Événements d'entreprise — titre"), "text",
     _("Une mise en scène à l'image de votre entreprise"), ""),
    ("home.corporate_body", "home", _("Événements d'entreprise — texte"), "paragraphs",
     [
         _("Fête d'équipe, soirée de fin d'année, lancement de produit, réception clients ou anniversaire d'entreprise : je conçois une décoration qui traduit votre identité et donne à vos invités le sentiment d'être attendus."),
         _("Pour les entreprises de Fribourg et de la région, un interlocuteur unique du concept jusqu'au démontage — avec des délais tenus et un rendu soigné jusque dans le détail."),
     ],
     ""),
    ("home.portfolio_title", "home", _("Titre du bloc Portfolio"), "text",
     _("Quelques univers créés sur mesure"), ""),

    # --- À propos -------------------------------------------------------------
    ("about.hero_title", "about", _("Titre de la page"), "text",
     _("Entre Madagascar, l'Allemagne et la France"), ""),
    ("about.hero_lede", "about", _("Accroche sous le titre"), "text",
     _("Maison Riri Design est née de l'envie de faire dialoguer plusieurs cultures dans un même espace — et d'en faire quelque chose de beau."),
     ""),
    ("about.story_title", "about", _("Mon histoire — titre"), "text",
     _("Créer des liens, entre les cultures et entre les gens"), ""),
    ("about.story_intro", "about", _("Mon histoire — première phrase"), "text",
     _("Bonjour, je suis Rina, fondatrice de Maison Riri Design. ✨"), ""),
    ("about.story", "about", _("Mon histoire — texte"), "paragraphs",
     [
         _("Il y a bientôt sept ans, mon chemin m'a menée de Madagascar à l'Allemagne. Cette nouvelle aventure a changé ma façon de voir les rencontres, les cultures et tous ces moments précieux qui nous rassemblent."),
         _("Depuis toujours, j'aime imaginer des anniversaires, des surprises et des moments uniques. Cette passion est devenue un métier : j'ai suivi et validé la formation certifiante en event design et décoration événementielle de la DCTE School, où j'ai approfondi la conception, l'harmonie des couleurs, la mise en scène des espaces et la création d'univers visuels."),
         _("De la rencontre entre mon histoire, ma créativité et ce savoir-faire est née Maison Riri Design. Aujourd'hui, j'imagine des concepts événementiels sur mesure, de la première idée jusqu'à l'univers final : couleurs, matières, décoration, ambiance et chaque petit détail qui donnera vie à votre événement."),
         _("Une chose est particulièrement importante pour moi :"),
         _("Un événement ne devrait pas ressembler à tous les autres. Il doit raconter quelque chose de vous."),
         _("Grâce à mes racines et à mon parcours entre différentes cultures, j'ai une sensibilité particulière pour les événements internationaux et multiculturels. J'aime réunir influences, traditions et histoires personnelles pour créer un univers moderne, élégant et profondément personnel — avec beaucoup d'attention aux détails, sans jamais perdre de vue l'harmonie de l'ensemble."),
         _("Bienvenue chez Maison Riri Design. ✨"),
     ],
     _("Un paragraphe par bloc, séparés par une ligne vide.")),
    ("about.work_title", "about", _("Ma façon de travailler — titre"), "text",
     _("Designed with intention."), ""),

    # --- Prestations ----------------------------------------------------------
    ("services.hero_title", "services", _("Titre de la page"), "text",
     _("Du concept à la dernière bougie allumée"), ""),
    ("services.hero_lede", "services", _("Accroche sous le titre"), "text",
     _("Trois familles de prestations, à combiner librement selon l'ampleur de votre événement et le rôle que vous souhaitez me confier."),
     ""),
    ("services.s1_title", "services", _("01 Design & concept — titre"), "text",
     _("Donner une direction claire à votre événement"), ""),
    ("services.s1_text", "services", _("01 Design & concept — texte"), "text",
     _("Tout commence par une intention. Nous définissons ensemble l'atmosphère recherchée, puis je la traduis en une direction artistique complète que vous pouvez visualiser avant même le premier achat."),
     ""),
    ("services.s2_title", "services", _("02 Décoration — titre"), "text",
     _("Composer l'espace, jusqu'au dernier détail"), ""),
    ("services.s2_text", "services", _("02 Décoration — texte"), "text",
     _("C'est le moment où le concept devient tangible. J'installe, j'ajuste et je vérifie chaque angle de vue afin que la salle soit parfaite à l'instant où vos invités poussent la porte — puis je démonte une fois la fête terminée."),
     ""),
    ("services.s3_title", "services", _("03 Planification — titre"), "text",
     _("Vous gardez la fête, je garde la logistique"), ""),
    ("services.s3_text", "services", _("03 Planification — texte"), "text",
     _("Un événement réussi tient autant aux personnes qui l'entourent qu'à sa décoration. Je vous accompagne dans le choix des prestataires et je coordonne les échanges jusqu'au jour J."),
     ""),
    ("services.closing", "services", _("Phrase de conclusion"), "text",
     _("Chaque événement est conçu individuellement. Je serais ravie de vous établir une proposition personnalisée."),
     ""),
    ("services.closing_note", "services", _("Note sous la conclusion (budget, zone)"), "text",
     _("Projets à partir de 1 000 €. Décoration et mise en scène pour les particuliers comme pour les entreprises, à Fribourg-en-Brisgau et ses environs, en Alsace et à Bâle."),
     _("Laissez vide pour ne rien afficher… ou écrivez un espace.")),

    # --- Contact --------------------------------------------------------------
    ("contact.hero_title", "contact", _("Titre de la page"), "text",
     _("Demander un devis pour votre événement"), ""),
    ("contact.hero_lede", "contact", _("Accroche sous le titre"), "text",
     _("Quelques questions pour bien comprendre votre projet. Comptez cinq minutes — et n'hésitez pas à joindre vos images d'inspiration."),
     ""),
    ("contact.reply_note", "contact", _("Note sous le bouton d'envoi"), "text",
     _("Réponse en règle générale sous 2 jours ouvrés. Champs marqués d'une étoile obligatoires."),
     ""),
    ("contact.good_to_know", "contact", _("Encadré « Bon à savoir »"), "lines",
     [
         _("Le devis est gratuit et sans engagement."),
         _("Projets à partir de 1 000 €."),
         _("Conseil en allemand, en français ou en malgache."),
         _("Fribourg-en-Brisgau et ses environs, Alsace, Bâle — et au-delà sur demande."),
         _("Vos photos d'inspiration sont les bienvenues."),
     ],
     _("Un point par ligne.")),
    ("contact.success_text", "contact", _("Message après envoi du formulaire"), "text",
     _("Je reviens vers vous en règle générale sous 2 jours ouvrés avec une première proposition et, si besoin, quelques questions complémentaires."),
     ""),

    # --- Partagé --------------------------------------------------------------
    ("shared.callout_title", "shared", _("Bandeau « Parlons de votre événement » — titre"), "text",
     _("Chaque événement est conçu individuellement"), ""),
    ("shared.callout_text", "shared", _("Bandeau « Parlons de votre événement » — texte"), "text",
     _("Je serais ravie de vous établir une proposition personnalisée, adaptée à votre occasion, à votre lieu et à votre budget."),
     ""),
    ("shared.footer_claim", "shared", _("Devise du pied de page"), "text",
     _("where details create memories."), ""),
]


class Spec:
    __slots__ = ("key", "page", "label", "kind", "default", "help", "position")

    def __init__(self, position, key, page, label, kind, default, help_text):
        self.position = position
        self.key = key
        self.page = page
        self.label = label
        self.kind = kind
        self.default = default
        self.help = help_text

    @property
    def page_label(self):
        return dict(PAGES)[self.page]

    def default_text(self):
        """Valeur par défaut dans la langue active, sous forme de texte brut."""
        if self.kind == "paragraphs":
            return "\n\n".join(str(p) for p in self.default)
        if self.kind == "lines":
            return "\n".join(str(p) for p in self.default)
        return str(self.default)

    def default_items(self):
        return [str(p) for p in self.default]


REGISTRY = {
    entry[0]: Spec(position, *entry) for position, entry in enumerate(_ENTRIES)
}


def split_items(text, kind):
    """Découpe un texte saisi en admin selon sa forme."""
    if kind == "paragraphs":
        return [p.strip() for p in text.replace("\r\n", "\n").split("\n\n") if p.strip()]
    if kind == "lines":
        return [p.strip() for p in text.replace("\r\n", "\n").split("\n") if p.strip()]
    return [text.strip()]
