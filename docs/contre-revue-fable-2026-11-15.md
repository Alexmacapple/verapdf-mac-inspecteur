Revue demandée par Alex le 15 novembre 2026.

- Relecteur indépendant : `claude-fable-5-2`.
- Session Claude : `f137a0ac-76c9-4cb9-a1cd-ff7e4453df3e` ; terminal distinct du processus Codex.
- Périmètre : lecture seule, preuves et cas adverses sous `/tmp/verapdf-contre-revue-fable.Qi0IEt`.
- Intégrité après revue : les 14 fichiers empreintés sont inchangés.
- Le texte ci-dessous est le verdict du relecteur, conservé sans réécriture.

---

# Contre-revue — Inspecteur veraPDF

**Aucun problème bloquant trouvé** dans ce que j'ai exécuté : pas de PDF modifié, pas de faux résultat vert, pas de rapport importé présenté comme frais. En revanche, quatre constats importants touchent la promesse centrale (rectangle sourcé, liste complète, bonne page) : **utilisable pour essais, corrections nécessaires avant confiance**.

## Bloquant

Aucun. Ce n'est pas une garantie : les essais portent sur des PDF synthétiques et l'interface n'a pas été manipulée.

## Important

**I1. Liste tronquée à 100 occurrences par règle, sans explication**
- Où : `worker/analyzer.py:95` (appel veraPDF sans `--maxfailuresdisplayed`), `analyzer.py:71-79`, `Sources/Views.swift:27` et `:53`, `README.md:46`.
- Scénario : PDF de 151 figures sans alternative, validation fraîche par veraPDF 1.30.4.
- Preuve vérifiée : le XML déclare `failedChecks=151` pour la règle 7.3-1 et ne contient que 100 `<check>`. Le worker rend 105 occurrences pour 156 échecs.
- Impact : 51 défauts ne sont ni listés ni localisables. Seul le pied de page « 105 occurrences affichées / 156 échecs » le laisse deviner ; le README annonce un plafond de 2 000.
- Correction : passer `--maxfailuresdisplayed` à la valeur du plafond, et afficher par règle « n affichées sur m » quand les deux diffèrent.

**I2. Zones partielles ou héritées étiquetées « Image directe dans le contenu balisé ciblé »**
- Où : `worker/locations.py:104-130` (collecte), `:125-126` (abandon silencieux des `/Stm`), `:132-144` (page héritée d'un ancêtre), `:85-92`, `:145-147`.
- Preuves vérifiées, toutes rendues avec `precision: image` :
  - Balise mêlant texte et image : seule l'icône de 10 × 10 est encadrée, le titre est ignoré.
  - Figure composée d'une petite image de page et d'une grande image dans un Form XObject : seule la petite est encadrée.
  - Figure sans `/Pg` avec un MCID : elle reçoit le rectangle d'une image de la page de son ancêtre, qui appartient à une autre balise.
  - Image de 300 × 300 rognée à 20 × 20 par un chemin de découpe : le rectangle couvre 300 × 300.
- Impact : « 1 zone(s) repérée(s) » annonce une couverture précise alors qu'elle est incomplète ou empruntée. Les limites de profondeur (80) et de nœuds (10 000) tronquent aussi sans le dire (lecture du code).
- Correction : marquer « zone partielle » dès qu'un MCID sans image, un `/Stm` ou une limite est rencontré ; ne pas hériter la page au-delà de la balise elle-même.

**I3. Rectangle dessiné sur une autre page que celle affichée**
- Où : `Sources/PDFCanvas.swift:70-72` (la notification de changement de page ne fait que redessiner), `:81`, `:87-91`, `:32-35`.
- Preuve vérifiée (harnais hors écran avec les vraies classes) : après `goToNextPage`, la zone de la page 1 reste dessinée au même endroit et recouvre la page 2.
- Inférence : un défilement ou une touche de page dans `PDFView` produit ce même changement interne. Le modèle n'en est pas informé, donc « Page N / M » resterait faux aussi.
- Impact : rectangle sur la mauvaise page, exactement ce que le produit exclut.
- Correction : remonter `PDFViewPageChanged` vers `model.page`, ou ne dessiner que si `pdf.currentPage` est la page du rectangle.

**I4. Explications françaises limitées aux cinq règles du document de recette**
- Où : `worker/analyzer.py:24-33`, `Sources/Views.swift:64-67` et `:134`.
- Preuve vérifiée : sur le PDF synthétique, 7.18.5-1 et 7.1-8 s'affichent « Exigence PDF/UA 7.x, test n ». L'exigence, en anglais, est repliée par défaut.
- Impact : pour toutes les autres règles, les lignes de la liste ne se distinguent que par la page et le numéro d'occurrence.
- Correction : afficher la description veraPDF dans la ligne et le détail quand aucune traduction n'existe.

## Mineur

- **Polices sur page tournée avec CropBox décalée** (`locations.py:177`) : rectangle décalé de l'origine du CropBox, soit (20, 354) au lieu de (50, 394) dans mon cas. Rotation seule ou CropBox seule sont correctes. Vérifié.
- **Page prise sur un ancêtre** (`locations.py:132-143`) : une Figure vide sans `/Pg` est annoncée « Page 3 » parce que sa section porte ce `/Pg`. Vérifié.
- **Polices de même nom** (`locations.py:168-176`) : deux objets police homonymes sont tous deux encadrés. Vérifié, et annoncé par le libellé.
- **`/Rect` inversé** (`locations.py:14`) : une annotation au rectangle non normalisé, pourtant légal, retombe sur « page seule ». Vérifié, honnête mais perdant.
- **Chemin Python versionné** (`scripts/build.sh:18`) : l'`Info.plist` pointe sur `Cellar/python@3.12/3.12.14/…`. Vérifié ; inférence : une mise à jour Homebrew casse l'application jusqu'à reconstruction.
- **Attente sans borne ni annulation** (`Models.swift:66`, `:96-97`) : seul veraPDF est limité à 120 s (`analyzer.py:96`) ; le repérage ne l'est pas et relit le texte de la page à chaque occurrence de police (`locations.py:173`). Lecture du code ; délai non exercé.
- **Messages bruts en anglais** (`analyzer.py:39`, `:60`, `:136-137`) : XML vide, mal formé ou taille non numérique rendent par exemple « no element found: line 1, column 0 ». Vérifié.
- **Filtre DOCTYPE contournable en UTF-16** (`analyzer.py:37`) : une entité interne passe. Vérifié, mais expat 2.7.4 bloque l'amplification et l'entité externe.
- **Import à la fois strict et lâche** (`analyzer.py:45-60`) : un PDF déplacé est refusé même identique ; un rapport sans `size`, sans `jobEndStatus`, ou dont le profil contient seulement « PDF/UA-1 » est accepté. Vérifié. Un import refusé efface aussi le résultat précédent (`Models.swift:67-69`, lecture).
- **États d'interface** : « Page 1 / 0 » et flèches inactives quand l'analyse échoue alors que le PDF est affiché (`Views.swift:87-91`, lecture). La provenance d'un import n'apparaît qu'en légende de pied de page.
- **Résidus** : chaque analyse ajoute un XML dans `Application Support` sans purge (`analyzer.py:100-104`, six fichiers présents) ; l'option `--capture` reste dans le binaire livré (`App.swift:30-48`).

## Ce qui tient, vérifié

- PDF modifié à taille égale après le rapport : accepté, mais l'interface dit « sans preuve des octets », conforme à la documentation.
- Empreinte du PDF inchangée après validation et repérage ; `fresh` vrai seulement pour une validation fraîche.
- Faux PDF, PDF endommagé, rapport interrompu : erreur explicite, sortie JSON pure, aucun résultat vert.
- Contenu mal formé, page hors bornes, annotation d'une autre page : jamais de rectangle.
- Les coordonnées des rectangles correspondent à l'espace de page PDFKit, avec ou sans rotation et CropBox (hors le cas de police ci-dessus).
- Paquet : signature valide, worker identique aux sources, aucun `__pycache__` dedans, fonctionnement avec un `PATH` réduit type Finder.
- Les titres français de 7.3-1, 7.18.1-2, 7.18.5-2 et 7.21.4.1-1 correspondent aux exigences de veraPDF 1.30.4 ; 5-1 n'a pas été déclenchée.

## Interface : ce que la capture établit

- Établi : trois colonnes, rectangle orange autour du texte du lien en page 10, statut textuel « 1 zone(s) repérée(s) », provenance en pied de page.
- La capture ne montre aucune ligne de liste : le champ de filtre contient « lan » et la liste est vide. Le détail reste pourtant affiché et le pied de page annonce « 75 occurrences affichées ».
- À essayer humainement : rendu et sélection de la liste, défilement et touches dans l'aperçu (I3), clic sur un lien du PDF, barre d'outils, dialogues, clavier, VoiceOver. Mon clic simulé sur un lien n'a déclenché aucune ouverture, mais rien ne prouve qu'il ait été traité comme un vrai clic : non conclusif.

## Vérifications effectuées et limites

- `bash scripts/test.sh` avec Python 3.12.14 : 11 tests, exit 0. Aucun test ne couvre Swift, la troncature ni l'héritage de page.
- Cas adverses de localisation, de rapport XML et chaîne réelle worker → veraPDF, sur PDF synthétiques uniquement.
- Harnais Swift compilé dans le dossier temporaire avec `Sources/PDFCanvas.swift` en lecture.
- Intégrité : les 14 empreintes de `empreintes-avant.json` sont inchangées ; les `__pycache__` de `worker/` et `tests/` datent de 16:08, avant ma session.
- Non fait : le PDF réel de 21 pages et les chiffres de `docs/recette.md` (75 échecs, 22/3/2/47) ne sont pas rejoués ; l'application n'a pas été lancée ; le délai de 120 s n'a pas été exercé.

Scripts et sorties sont dans `/tmp/verapdf-contre-revue-fable.Qi0IEt/cas/` (`*.out`) et `/tmp/verapdf-contre-revue-fable.Qi0IEt/swift/harnais.out`.
