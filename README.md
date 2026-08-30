# Maison Riri Design — site web

Site vitrine bilingue (français / allemand) pour **Maison Riri Design**, design
événementiel et décoration sur mesure — Freiburg im Breisgau, Alsace, Bâle.

Construit avec **Python + Django 4.2**, sans dépendance front-end : HTML, CSS et
un fichier JavaScript de 60 lignes.

---

## Ce que contient le site

| Page | URL (FR / DE) | Contenu |
| --- | --- | --- |
| Accueil | `/fr/` · `/de/` | Visuel plein écran, promesse, aperçu des prestations, projets mis en avant, différenciateurs, processus |
| À propos | `/fr/a-propos/` · `/de/ueber-mich/` | Parcours entre Madagascar, l'Allemagne et la France ; façon de travailler |
| Prestations | `/fr/prestations/` · `/de/leistungen/` | Les trois familles de prestations en détail |
| Portfolio | `/fr/portfolio/` · `/de/portfolio/` | Grille filtrable « Réalisation » / « Concept créatif » |
| Détail projet | `/fr/portfolio/<slug>/` | Récit, palette, galerie regroupée par étape (moodboard → détails → installation → résultat) |
| Devis | `/fr/contact/` · `/de/kontakt/` | Formulaire complet avec téléversement de photos d'inspiration |
| Mentions légales / Protection des données | `/fr/mentions-legales/`, `/fr/confidentialite/` | Modèles à compléter avant mise en ligne |

Également disponibles : `/robots.txt`, `/sitemap.xml`, administration Django sur
`/fr/admin/`.

---

## Démarrage

```bash
pip install -r requirements.txt
```

```bash
python manage.py migrate
```

```bash
python manage.py seed_content && python manage.py seed_site_images
```

```bash
python manage.py createsuperuser
```

```bash
python manage.py runserver
```

Le site est alors sur <http://127.0.0.1:8000/> (redirection automatique vers
`/fr/`) et l'administration sur <http://127.0.0.1:8000/fr/admin/>.

### Tests

```bash
python manage.py test core.tests
```

---

## Le formulaire de devis

Le formulaire reprend **question pour question** le Google Form déjà utilisé par
Maison Riri Design, dans la mise en forme du site plutôt que dans celle de
Google. À l'envoi, chaque demande :

1. est **enregistrée en base** et consultable dans l'administration (avec un
   statut : nouvelle, en cours, devis envoyé, confirmée, classée) ;
2. est **recopiée dans le Google Form**, afin que la feuille de calcul existante
   continue d'être alimentée ;
3. déclenche une **notification par e-mail** si `MRD_NOTIFY_EMAILS` est
   configuré.

Les identifiants de champs Google (`entry.794662135`, …) sont rassemblés dans
[`core/choices.py`](core/choices.py). Si le formulaire Google est modifié, ce
sont ces valeurs — et elles seules — qu'il faut mettre à jour.

Points de vigilance :

- **Les photos d'inspiration ne sont pas transmises à Google** : Google Forms
  exigerait que le visiteur se connecte à un compte Google. Elles sont stockées
  par le site et visibles dans l'administration, sur la fiche de la demande.
- Le **téléphone est facultatif** sur le site alors qu'il est obligatoire côté
  Google : lorsqu'il est vide, la mention « Non communiqué » / « Nicht
  angegeben » est transmise à sa place.
- Si Google est injoignable, **la demande n'est jamais perdue** : elle reste
  enregistrée, l'erreur est consignée, et l'action « Renvoyer vers le Google
  Form » de l'administration permet de réessayer.
- Un champ leurre invisible bloque les robots les plus simples.

Pour désactiver complètement la recopie vers Google :
`MRD_GOOGLE_FORM_ENABLED=0`.

---

## Contenu éditorial

- **Les projets du portfolio** se gèrent dans l'administration : titre, récit,
  palette, galerie par étape, et le type « Réalisation » ou « Concept créatif »
  qui affiche l'étiquette correspondante sur le site.
- Chaque champ éditorial existe en français et en allemand (`titre (FR)` /
  `titre (DE)`). Si la version allemande est vide, la version française est
  affichée à la place.
- **Les images du site** — logo, grande image de l'accueil, portrait et
  ambiance de la page « À propos », image de partage sur les réseaux sociaux —
  se remplacent dans l'administration, rubrique **Images du site**. Voir plus
  bas.
- **Les textes de pages** (accueil, à propos, prestations, processus) vivent
  dans les gabarits et se traduisent dans `locale/de/LC_MESSAGES/django.po`.

Après modification d'un texte de gabarit :

```bash
python manage.py makemessages -l de --ignore=staticfiles && python manage.py compilemessages -l de
```

### Les images du site

Aucune image n'est figée dans le code : les cinq visuels présents sur toutes les
pages se changent depuis `/fr/admin/core/siteimage/`, sans redéploiement ni
intervention technique.

| Emplacement | Où il apparaît | Format conseillé |
| --- | --- | --- |
| Logo | En-tête, pied de page, accueil, favicon | Carré, ~600 × 600 px |
| Grande image de l'accueil | Bandeau plein écran de la page d'accueil | Paysage, ~2000 × 1300 px |
| Portrait — page À propos | Colonne de gauche de « Mon histoire » | Portrait 4/5, ~1200 × 1500 px |
| Ambiance — page À propos | Encadré « Ma façon de travailler » | Paysage, ~1600 × 1100 px |
| Image de partage | Vignette affichée par WhatsApp, Facebook, LinkedIn… | Paysage 1200 × 630 px |

Marche à suivre : ouvrir l'emplacement, envoyer le nouveau fichier, enregistrer.
Le changement est visible immédiatement sur le site public. Le **texte
alternatif** (FR et DE) décrit l'image pour les lecteurs d'écran et les moteurs
de recherche ; laissé vide, un texte par défaut est utilisé.

Un emplacement **supprimé** n'est pas un problème : le site retombe alors sur le
visuel d'origine livré dans `static/img/`. Pour tout remettre en place :

```bash
python manage.py seed_site_images --reset
```

Les images des projets (couverture et galerie) se gèrent, elles, sur la fiche du
projet concerné, avec un aperçu de chaque photo.

### Portfolio de départ

`python manage.py seed_content` charge deux projets à partir des visuels fournis
(`core/assets/`) :

- **Dreamland** — remise de diplômes, arche de ballons et lettres lumineuses
  (réalisation, 7 photos) ;
- **Thirty & Fabulous — Red Wine** — étude de concept pour un 30ᵉ anniversaire,
  reprise du dossier PDF (concept créatif, 2 moodboards, palette burgundy).

`--reset` remplace les projets existants portant les mêmes identifiants.

---

## À compléter avant la mise en ligne

1. **Les mentions légales et la page de protection des données** : les deux
   pages sont des modèles et affichent un encadré le rappelant. Forme juridique,
   adresse, numéro d'identification, hébergeur et durée de conservation doivent
   être renseignés et relus juridiquement.
2. **Les coordonnées** : `MRD_EMAIL`, `MRD_PHONE`, `MRD_INSTAGRAM`,
   `MRD_FACEBOOK` (voir `.env.example`). Sans téléphone renseigné, la ligne
   correspondante n'est simplement pas affichée.
3. **L'envoi d'e-mails** : le réglage par défaut écrit les messages dans la
   console. Renseigner les variables `DJANGO_EMAIL_*` pour un vrai serveur SMTP.

---

## Mise en production

```bash
export DJANGO_DEBUG=0 DJANGO_SECRET_KEY="…" DJANGO_ALLOWED_HOSTS="maison-riri.com"
```

```bash
python manage.py collectstatic --noinput && python manage.py migrate
```

```bash
gunicorn config.wsgi:application
```

Points d'attention :

- Les variables d'environnement sont listées dans `.env.example`.
- Hors mode développement, le site force HTTPS, active HSTS et sécurise les
  cookies ; les fichiers statiques sont servis par WhiteNoise avec empreinte de
  version.
- `MEDIA_ROOT` (`media/`) contient **toutes les images administrables** — celles
  du portfolio, celles du site (logo, hero, portrait…) et les photos
  d'inspiration envoyées par les visiteurs. Ce dossier doit être **sauvegardé**
  au même titre que la base de données. Il est servi par WhiteNoise depuis
  `config/wsgi.py`, sans configuration supplémentaire ; un serveur frontal qui
  sert déjà `/media/` prend simplement la main avant.
- Le fichier `db.sqlite3` convient au volume attendu ; pour passer à PostgreSQL,
  seul le bloc `DATABASES` de `config/settings.py` est à modifier.
- `DJANGO_DATA_DIR` déplace **d'un seul réglage** la base et le dossier `media/`
  ailleurs que dans le code. Laissé vide, rien ne change. C'est indispensable
  sur un hébergeur à conteneurs, où le disque est remis à zéro à chaque
  déploiement (voir ci-dessous).

### Déploiement sur Railway

Le disque d'un conteneur Railway est **éphémère** : sans volume, chaque
déploiement effacerait la base (portfolio, demandes de devis, comptes admin) et
toutes les images envoyées depuis l'administration.

1. **Créer un volume** sur le service, point de montage `/app/data`.
2. **Variables d'environnement** du service :

   ```
   DJANGO_DATA_DIR=/app/data
   DJANGO_DEBUG=0
   DJANGO_SECRET_KEY=<clé aléatoire>
   DJANGO_ALLOWED_HOSTS=maison-riri.com,www.maison-riri.com,<sous-domaine>.up.railway.app
   DJANGO_CSRF_TRUSTED_ORIGINS=https://maison-riri.com,https://www.maison-riri.com
   ```

3. **Commande de démarrage** — les migrations doivent tourner sur le volume
   fraîchement monté, et `seed_site_images` (sans `--reset`, donc sans effet si
   les images sont déjà définies) donne ses visuels à une installation neuve :

   ```bash
   python manage.py migrate && python manage.py seed_site_images && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
   ```

Railway terminant le TLS en amont, `SECURE_PROXY_SSL_HEADER` est réglé pour que
`SECURE_SSL_REDIRECT` ne boucle pas — c'est déjà fait dans `config/settings.py`.

Le domaine doit figurer dans `DJANGO_ALLOWED_HOSTS`, faute de quoi Django
répond `DisallowedHost` sur toutes les pages.

---

## Organisation du code

```
config/          réglages, URL, WSGI/ASGI
core/
  models.py      Projet, image de projet, palette, image du site, demande de devis, photo d'inspiration
  forms.py       formulaire de devis (téléversement multiple, contrôles, leurre anti-robot)
  choices.py     listes de choix et identifiants des champs du Google Form
  google_form.py recopie des demandes vers Google, tolérante aux pannes
  views.py       pages publiques
  admin.py       back-office
  assets/        visuels d'origine utilisés par seed_content
  tests.py       23 tests (formulaire, passerelle Google, pages, bilinguisme, images du site)
templates/       gabarits, partagés via partials/
static/          css/site.css, js/site.js, images de marque
locale/de/       traduction allemande
```
