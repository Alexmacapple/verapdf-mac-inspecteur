# Vérification des corrections par Claude Fable

Relecteur : `claude-fable-5-2`, session `20d24e3d-0eb9-494b-91af-65a7c52843a4`.

Les verdicts ci-dessous sont conservés sans réécriture. La recette décrit les deux ajustements mineurs réalisés après le dernier verdict et leurs vérifications par Codex.


## Première vérification

Deux constats sont corrigés sans réserve (I1, I4), I3 est corrigé au niveau du harnais, I2 reste partiel, et la correction de I2 supprime tous les cadres de figures sur le document réel.

## Verdict par constat

**I1 — liste tronquée : corrigé.**
- Validation fraîche du PDF de la revue : 156 occurrences chargées sur 156, règle 7.3-1 à 151/151, `complete: true`.
- Import de l'ancien XML tronqué : 105 chargées, 7.3-1 à 100/151, `complete: false`, et le bandeau « Diagnostic incomplet… Règle 7.3-1 : 100 / 151 » apparaît sur la capture.
- Plafond global (2 100 figures) : 2 000 chargées sur 2 105, et les deux règles évincées sont annoncées à 0/1.
- `/tmp/verapdf-inspecteur-151-figures.json` est identique au rejeu, occurrences et localisations.

**I2 — localisation honnête : partiel.**
- Les quatre contre-exemples d'origine ne se reproduisent plus : texte + image → « partial », image dans un Form → « partial », page d'ancêtre → aucune localisation, image rognée → cadre masqué.
- Deux cas neufs rendent encore `precision: image` avec « Image directe dans le contenu balisé ciblé » alors que la zone est incomplète :
  - **Image intégrée (BI/ID/EI)** à côté d'une image XObject : seule la petite image est encadrée. Le garde de `worker/locations.py:72` (`hasattr(instruction, 'operator')`) est toujours vrai avec pikepdf 10.6.0, donc la branche prévue ne s'exécute jamais.
  - **Référence d'objet (OBJR)** vers une annotation dans la même balise : ignorée sans avertissement (`locations.py:171-174`).

**I3 — page affichée : corrigé au niveau du harnais.**
- Le harnais du dépôt compile et passe (exit 0).
- Mon harnais héberge la vraie `PDFCanvas` dans SwiftUI, avec ses propres observateurs : 9 contrôles, exit 0.
- Après `goToNextPage`, aucun pixel orange n'est dessiné avant même la mise à jour SwiftUI, puis le modèle passe à 2.
- Saut par destination, rafale de changements et molette synthétique laissent le modèle égal à la page affichée.
- Non vérifié : geste humain réel (trackpad, clavier) dans l'application, et ce harnais n'a pas été rejoué contre l'ancien code.

**I4 — exigence visible : corrigé.**
- Sur la chaîne réelle, 7.1-8 et 7.18.5-1 sortent avec `translated: false` et l'exigence renseignée.
- La capture de l'application compilée depuis les sources actuelles montre l'exigence dans la ligne de liste et la section « Exigence originale · traduction indisponible » dans le détail.

## Nouvelle régression importante

Sur le document réel de 21 pages, les 69 figures sont maintenant en « page seule » : les 22 cadres d'avant ont disparu. Le rejeu est identique à `/tmp/verapdf-inspecteur-corrige.json`, et `docs/recette.md` l'annonce.

Ce que la recette ne dit pas : les 26 images balisées de ce document ont toutes une découpe rectangulaire qui ne rogne rien (tolérance 0,5 pt). Le masquage se déclenche sur tout opérateur `W`, sans comparer la découpe au cadre de l'image. Le résultat est honnête mais ne localise plus aucune figure sur ce document. Garder le cadre quand la découpe est un rectangle qui contient l'image corrigerait ce cas sans rouvrir I2.

## À savoir

- **Dépôt** : `docs/recette.md` a changé à 16:37:17 pendant ma session, par un autre processus ; mes commandes n'ont écrit dans aucun fichier du dépôt, et les 30 autres fichiers sont inchangés. La suite Python a tourné sans écrire de bytecode : 22 tests, exit 0.
- **Aperçu vide** : sur ma capture en validation fraîche, la page 1 apparaît blanche alors qu'elle porte 150 images. Délai de rendu ou vrai défaut, je n'ai pas tranché.
- **Fenêtre à l'écran** : les deux captures ont ouvert brièvement une fenêtre de l'application, lancée avec un dossier personnel factice sous `/tmp`.

Tout est dans `/tmp/verapdf-verification-corrections/` ; ouvrir `verdict.md` en premier, les sorties sont dans `out/`.

## Vérification ciblée finale de I2

**I2 : corrigé**, avec une réserve mineure sur des flux de contenu irréguliers.

## Ce qui est prouvé

- **N1 et N3** : l'image intégrée (BI/ID/EI) et la référence d'objet (OBJR) sortent maintenant en « partial », avec les raisons « Image intégrée au flux non localisée » et « Objet référencé par la balise non localisé ».
- **Cas d'origine** : les sorties de L1, L3, L8 et L9 sont identiques à celles de mon passage précédent (texte + image partiel, page d'ancêtre non empruntée, image rognée masquée, Form partiel).
- **Découpes rognantes** : sur 25 cas, restent masqués le rognage de 1 pt et de 0,001 pt, le triangle, le chemin à deux rectangles, le rectangle tourné de 30°, les découpes emboîtées dont une rogne, les découpes disjointes et une découpe inconnue suivie d'un rectangle large.
- **Découpes contenantes** : le cadre est conservé pour la pleine page, la découpe égale au cadre, les découpes emboîtées qui contiennent l'image et le rectangle à dimensions négatives.
- **Document réel** : 22 cadres reviennent, sur 69 figures (18 « image », 4 « partial », 47 « page »).
  - Mon inventaire indépendant, qui n'utilise pas les fonctions du worker, retrouve chacun des 22 cadres parmi les images à découpe contenante.
  - Aucun cadre ne déborde de la page, et aucune localisation « image » ne porte de texte, tracé ou Form dans son MCID.
  - Le rejeu est identique à `/tmp/verapdf-inspecteur-corrige-final.json`, et l'empreinte du PDF est inchangée.
- **Suite du dépôt** : 26 tests, exit 0.

## Réserve liée à ce changement

Si le chemin est prolongé après `W` ou `W*` avant l'opérateur de fin (`re W* re n`), la découpe réelle a un trou sur l'image. L'image est invisible (0 pixel au rendu MuPDF), mais elle reçoit un cadre étiqueté « image ». Deux cas le montrent : D8 (pair-impair) et D20 (sens inverse).

- **Cause** : `worker/locations.py:124-142`, où `clip_rect` n'est pas invalidé quand un opérateur de construction de chemin survient après `W`.
- **Portée** : cette écriture est irrégulière au regard d'ISO 32000 et absente du document réel. Je la classe mineure.
- **Correctif** : invalider `clip_rect` dans ce cas.

## Limites

- **Découpe par texte (mode `Tr 7`)** : elle n'est pas reconnue, donc l'image invisible reste encadrée, en « partial » à cause du texte. Ce cas ne vient pas de ce changement.
- **PDF synthétiques** : ils ne couvrent ni les découpes dans un Form XObject, ni les masques (`SMask`).
- **Document réel** : c'est un seul fichier, sans page tournée.
- **Dépôt** : `README.md` et `docs/recette.md` ont changé pendant ma session, par un autre processus. Je n'ai rien écrit dans le dépôt ; `worker/`, `tests/` et `Sources/` sont restés stables pendant les mesures.

Tout est dans `/tmp/verapdf-verification-finale/` ; ouvrir `verdict.md` en premier, les sorties sont dans `out/`.