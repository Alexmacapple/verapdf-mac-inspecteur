# veraPDF Mac Inspecteur

Application macOS autonome pour lire un PDF à côté des erreurs de son contrôle
PDF/UA-1. Aucun document modifié, aucun serveur et aucun envoi du PDF.

## Utilisation

Ouvrir `build/veraPDF Mac Inspecteur.app`, puis **Ouvrir un PDF**. Une validation
veraPDF fraîche démarre ; choisir une occurrence à gauche pour afficher son
diagnostic et sa page. Le bouton **Importer un XML** lit un rapport existant
compatible. **Enregistrer le XML** conserve le rapport de contrôle.

Les annotations ont leur rectangle PDF ; les images directement associées à
un MCID de page ont leur cadre calculé depuis les opérateurs PDF. Les textes
des polices sont repérés par leur nom sur la page. Une balise peut avoir une
page connue sans rectangle précis : cet état reste visible. Les erreurs de
métadonnées sont globales. Aucune localisation arbitraire n’est produite.
Une balise mêlant plusieurs types de contenu affiche « Localisation partielle »
si seuls certains cadres sont établis, y compris en présence d’images intégrées
au flux ou d’objets référencés non localisés. Les images réellement rognées, les
découpes indéterminées et les MCID ambigus ne reçoivent aucun cadre approximatif.
Une découpe rectangulaire qui contient l’image conserve son cadre. Une page portée uniquement par un ancêtre
de la balise n’est pas empruntée.

## Dépendances et construction

macOS 14 ou ultérieur, outils de compilation Swift, Python 3.12 avec `pikepdf`
et `PyMuPDF`, et veraPDF déjà installé dans `/opt/homebrew/bin/verapdf`.
Le script ne les télécharge pas. `PYTHON_BIN` choisit un autre interpréteur.

```bash
bash scripts/build.sh
bash scripts/test.sh
open 'build/veraPDF Mac Inspecteur.app'
```

Le paquet reste dépendant du Python local : ce n’est pas une distribution
notarisée autonome. Aucun dépôt GitHub distant n’est créé par cette livraison.

## Localisation et confiance

Un rapport importé indique un chemin et une taille, pas une empreinte au moment
du contrôle. L’interface le dit ; pour une preuve fraîche, utiliser **Analyser**.
Les empreintes du PDF sont comparées avant et après le traitement. Les rapports
produits sont conservés sous `~/Library/Application Support/Inspecteur veraPDF/Rapports/`.

Les formulaires, balises couvrant plusieurs flux, images dans des Form XObjects,
graphismes vectoriels et textes de figures ne reçoivent pas nécessairement de
rectangle. Les rectangles de police concernent les fragments du même nom sur
la page ; plusieurs objets homonymes rendent l’attribution ambiguë et masquent
les cadres. Les dimensions sont des coordonnées PDF, converties par PDFKit.

Limites : PDF de 256 Mio, rapport XML de 64 Mio, 2 000 échecs affichés au maximum,
validation de 120 secondes et traitement global de 180 secondes, avec secours
d’arrêt après deux secondes. **Annuler** arrête aussi les descendants du moteur.
Le compteur total reste celui du rapport. L’absence
de détail ou de zone n’est pas une réussite. Les explications françaises ciblent
les règles courantes ; sans traduction, l’exigence originale est visible dans la
liste et dans le détail, avec la mention « traduction indisponible ».

veraPDF reçoit explicitement un plafond de 2 000 détails par règle. Le plafond
local reste de 2 000 occurrences au total. Si le XML ou ce plafond tronque les
détails, un avertissement visible indique le nombre chargé et les règles
incomplètes. Le pied de page distingue les occurrences visibles après filtrage,
les occurrences chargées et le total des échecs.

La navigation interne à l’aperçu met à jour le compteur de page. Les rectangles
ne sont dessinés que sur leur page, y compris pendant un changement de page.

Ce logiciel n’est pas un produit officiel veraPDF. Une validation technique ne
remplace ni le jugement humain, ni un essai avec lecteur d’écran.

Un contrôle refusé ou annulé conserve le résultat précédent. Un PDF déplacé
peut être relié à son rapport par nom et taille, avec provenance déclarative
explicite. Après chaque analyse réussie, les rapports générés au-delà de 50
fichiers ou de 30 jours rejoignent la Corbeille ; le rapport affiché et les XML
importés ou exportés ailleurs sont préservés. Le menu **Rapports** permet aussi
ce nettoyage manuellement.

## Installer les dépendances Python dans un environnement dédié

Les chemins par défaut ciblent une installation Homebrew Apple Silicon.
Avec Python 3.12 et veraPDF déjà disponibles :

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
PYTHON_BIN="$PWD/.venv/bin/python" bash scripts/build.sh
PYTHON_BIN="$PWD/.venv/bin/python" bash scripts/test.sh
```

Le paquet mémorise le chemin de Python ; conserver cet environnement ou
reconstruire l’application après déplacement. `VERAPDF_COMMAND` permet de
choisir un autre validateur dans l’environnement de lancement du moteur.

## Documentation du projet

La [documentation](docs/README.md) contient la [genèse](docs/genese.md), les
[moyens et sources](docs/moyens-et-sources.md), les
[spécifications fonctionnelles a posteriori](docs/specifications-fonctionnelles.md),
les [spécifications techniques](docs/specifications-techniques.md) et la
[recette](docs/recette.md). Les rapports de revue gardent les anciens noms comme
témoignage de la construction.
