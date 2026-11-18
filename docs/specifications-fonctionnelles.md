# Spécifications fonctionnelles a posteriori

**Version 0.2.1 du 15 novembre 2026.** Reconstitution du comportement
implémenté dans [l’interface](../Sources/Views.swift), le [modèle](../Sources/Models.swift)
et le [moteur](../worker/analyzer.py). Ce document décrit l’existant, pas une promesse
de couverture complète de l’accessibilité ni un cahier des charges initial.

## Utilisateur, besoin et périmètre

Une personne qui prépare la remédiation d’un PDF doit pouvoir passer d’un échec
veraPDF à une explication, une page et, lorsqu’elle est établie, une zone.
Le document est consulté en lecture seule. La correction s’effectue ensuite
dans la source ou dans un autre outil, puis le document peut être recontrôlé.

L’application est locale, native macOS et ciblée PDF/UA-1. Les erreurs recensées
sont celles du rapport reçu : une erreur du validateur n’équivaut pas à une
violation unique, et plusieurs règles peuvent concerner le même objet.

## Parcours nominal

1. Ouvrir un PDF : le contrôle PDF/UA-1 démarre automatiquement.
2. Examiner le nombre de règles et d’échecs, ainsi que l’éventuelle troncature.
3. Sélectionner une occurrence dans la liste de gauche.
4. Lire le diagnostic à droite ; consulter la page et les cadres disponibles au centre.
5. Naviguer, ajuster le zoom ou filtrer les occurrences.
6. Enregistrer le rapport XML si nécessaire ; préparer la correction dans un autre outil.
7. Utiliser **Analyser** pour produire un nouveau contrôle sur le PDF ouvert.

## Exigences réalisées

| Identifiant | Comportement requis et observé | Source / vérification |
|---|---|---|
| F01 | Le dialogue **Ouvrir un PDF** accepte les fichiers PDF et lance une analyse. | `App.swift`, `Models.swift` ; démarrage de recette. |
| F02 | **Analyser** appelle veraPDF avec le profil `ua1`. | `analyzer.py` ; commande contrôlée dans les tests. |
| F03 | **Importer un XML** est disponible avec un PDF ouvert ; il ne relance pas veraPDF. | `App.swift`, `analyzer.py` ; test d’import. |
| F04 | Un import exige un profil PDF/UA-1 reconnu, un état normal, une taille valide et un seul job associé. Si le XML annonce zéro échec tout en détaillant une règle échouée, l’import est refusé. | Tests de métadonnées, de jobs ambigus et de cohérence des compteurs. |
| F05 | Un fichier déplacé peut être associé par nom et taille si l’ancien chemin n’existe plus ; cet import reste déclaré sans preuve historique des octets. | Test de déplacement ; bandeau de provenance. |
| F06 | La liste distingue règle et occurrence, indique les pages connues et permet de sélectionner un échec. | `Views.swift`, test des compteurs. |
| F07 | Le filtre porte sur titre, clause, page, message et exigence originale. | `Inspector.filtered`. |
| F08 | La sélection conduit à la première page connue de l’occurrence ; plusieurs pages restent accessibles dans le détail. | `Inspector.select`, panneau de localisation. |
| F09 | Les flèches, la navigation PDFKit et le compteur de page restent cohérents ; les anciens cadres disparaissent immédiatement après un changement de page. | Harnais PDFKit. |
| F10 | Les boutons de zoom procèdent par pas de 0,25, entre 0,5 et 4. **Ajuster** réadapte la page à la fenêtre, y compris après un zoom natif de PDFKit. | Harnais d’actions Swift. |
| F11 | Les cinq règles expliquées en français ont un conseil spécifique. Les autres montrent directement leur exigence originale et « traduction indisponible » dans le détail. | Catalogue `explain`, tests et capture de revue. |
| F12 | Exigence, message et contexte techniques restent consultables dans un volet dépliable. | `Views.swift`. |
| F13 | Un rapport incomplet affiche un bandeau et les nombres chargés par règle. Le pied de page sépare occurrences visibles, chargées et échecs totaux. | Tests de troncature et capture indépendante. |
| F14 | **Enregistrer le XML** copie atomiquement le rapport courant vers une destination choisie. | `App.swift` ; dialogue manuel non qualifié intégralement. |
| F15 | **Annuler** interrompt le moteur et ses descendants. Un délai global borne aussi l’attente. Le diagnostic précédent est conservé. | Harnais d’exécution avec sous-processus témoin. |
| F16 | Un import refusé ou une nouvelle analyse en erreur conserve le PDF, la page et le diagnostic précédents. | Harnais d’états. |
| F17 | Si la première analyse échoue, même lorsque le moteur manque, le PDF lisible reste consultable avec son nombre de pages. | Harnais d’états sur deux pages. |
| F18 | Les anciens rapports générés sont déplacés à la Corbeille selon la rétention ; le menu **Rapports** permet leur nettoyage manuel. Le rapport courant et les fichiers importés ne sont pas visés. | `ReportCache.swift`, tests à Corbeille simulée. |

## Règles de localisation

| État | Présentation et signification |
|---|---|
| Document / inconnu | Aucune page établie : aucun cadre ni page inventée. |
| Page connue | Page reliée au rapport ou à la balise ; aucune zone précise démontrée. |
| Annotation | Rectangle de l’annotation référencée, vérifié sur la page ; coordonnées inversées normalisées. |
| Image | Cadre d’une image directe dans le MCID ciblé, avec géométrie connue et découpe compatible. |
| Localisation partielle | Certaines images sont localisées, mais du texte, un tracé, un Form, une image intégrée ou une référence reste non localisé. |
| Police | Fragments de texte correspondant au nom de police ; absence de cadre si plusieurs objets homonymes rendent l’attribution ambiguë. |

Le conseil de correction n’est pas une instruction exécutée. Une balise sans
alternative ne devient pas automatiquement décorative. L’identification PDF/UA
n’est pas ajoutée automatiquement et ne vaut pas correction des autres défauts.

## États et erreurs

Pendant un traitement, le bouton **Ouvrir un PDF** de l’accueil est désactivé.
L’ouverture d’un second sélecteur, la relance et l’import sont bloqués.
L’annulation reste disponible. Le résultat antérieur reste
consultable ; le résultat nouveau le remplace seulement après une réponse valide.

Un import présente un bandeau visible : chemin, nom et taille n’attestent pas
les octets au moment de la validation. Seule une analyse fraîche de cette
session porte le statut de validation fraîche, avec empreinte inchangée.

Aucun échec dans un rapport ne constitue pas une déclaration d’accessibilité.
La pertinence des alternatives, l’ordre de lecture et l’usage réel exigent
toujours une évaluation humaine.

## Hors périmètre et qualification

Cette version ne modifie ni balises, ni alternatives, ni polices, ni métadonnées
PDF. Elle ne traduit pas toute l’interface veraPDF, ne couvre pas PDF/UA-2 ou
WTPDF, n’offre pas de parité PAC et ne remplace pas un lecteur d’écran.

Le clavier et VoiceOver font partie des intentions de conception, mais leur
parcours humain complet n’est pas qualifié. La [recette](recette.md) distingue
tests exécutés, captures et limites. Les [spécifications techniques](specifications-techniques.md)
décrivent les plafonds et les limites géométriques.
