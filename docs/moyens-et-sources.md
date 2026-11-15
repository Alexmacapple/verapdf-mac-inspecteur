# Moyens et sources utilisés

État reconstitué le 15 novembre 2026. Cette liste distingue les composants
effectivement intégrés des ressources étudiées pendant la conception.

## Composants exécutés par l’application

| Composant | Rôle concret | Pourquoi ce choix |
|---|---|---|
| Swift et SwiftUI | Fenêtre, liste, commandes, état observable | Interface native macOS et distribution sous forme de paquet `.app`. |
| AppKit | Dialogues de fichiers, activation, Corbeille | Intégration au poste et gestion réversible des anciens rapports. |
| PDFKit | Affichage et navigation PDF, conversion des rectangles | Réutiliser le moteur système et garder les surlignages sur la bonne page. |
| Python 3.12 | Processus séparé de validation et de localisation | Accès aux bibliothèques PDF déjà disponibles et isolation de l’interface. |
| veraPDF CLI | Validation PDF/UA-1 et rapport XML | Employer un moteur de règles existant plutôt que recréer les contrôles normatifs. |
| pikepdf 10.6.0 | Objets PDF, structure, annotations et opérateurs graphiques | Relier les références du rapport aux données du document. |
| PyMuPDF 1.27.2.2 | Extraction et géométrie du texte | Repérer les fragments d’une police et vérifier les coordonnées. |
| Bibliothèque standard Python | XML, SHA-256, processus, JSON, fichiers | Contrôler les entrées et fournir un contrat simple à Swift. |

Les versions Python de dépendances sont fixées dans [requirements.txt](../requirements.txt).
Le poste de création utilisait veraPDF 1.30.4 installé par Homebrew. Son
affichage de version applicative pouvait encore annoncer 1.30.0 : ce détail
observé ne doit pas servir à déduire la version d’une autre installation.

La GUI veraPDF n’est pas embarquée. L’application appelle le validateur CLI
installé sur le poste et dépend encore de Python et de ses paquets locaux.
Elle n’est pas un installateur autonome universel.

## Outils de construction et de contrôle

| Outil ou intervention | Usage observé |
|---|---|
| Codex | Analyse du besoin, code, tests, documentation et intégration locale. |
| Claude Fable `claude-fable-5-2` | Contre-revue indépendante, création de contre-exemples et vérification ciblée des corrections. |
| Terminal et shell Bash | Compilation, lancement des contrôles et exécution séparée de la revue Claude. |
| `xcrun swiftc` | Compilation native avec les frameworks système. |
| `codesign` | Signature locale ad hoc et contrôle d’intégrité du paquet ; aucune notarisation Apple. |
| `unittest` et harnais Swift | Cas synthétiques Python, vraie navigation PDFKit, annulation, délai et conservation de l’état. |
| Git et GitHub CLI | Versionnement autonome et publication demandée par Alex. |
| Homebrew | Installation locale préalable du validateur et de Python ; les scripts du projet n’installent rien automatiquement. |
| Captures internes de diagnostic | Vérification de la liste, des compteurs et des avertissements ; compilation dédiée nécessaire. |
| REA et automatisation de bureau | Tentatives d’observation système ; permissions indisponibles. Aucun résultat de parcours humain n’en est déduit. |

Les tests synthétiques du dépôt ne contiennent aucun PDF utilisateur. Un PDF réel
de 21 pages a servi à la recette locale ; ni ses octets, ni son rapport XML,
ni ses captures ne sont distribués dans ce dépôt.

## Ressources étudiées, sans intégration directe

| Ressource | Apport à la réflexion | Ce qui n’en est pas déduit |
|---|---|---|
| [Documentation GUI veraPDF](https://docs.verapdf.org/gui/) | Lecture des réglages et des rapports | La GUI d’origine n’a pas été traduite ou modifiée par ce projet. |
| [Documentation de validation](https://docs.verapdf.org/validation/) | Distinction des profils et lecture des résultats | La réussite technique ne remplace pas une évaluation humaine. |
| [Règles PDF/UA-1](https://github.com/veraPDF/veraPDF-validation-profiles/wiki/PDFUA-Part-1-rules) | Correspondance entre clause, test et exigence | Le moteur local ne recode pas ces règles ; il consomme le XML de veraPDF. |
| [Corpus PDF/UA-1](https://github.com/veraPDF/veraPDF-corpus/tree/staging/PDF_UA-1) | Source potentielle de témoins ciblés | Il n’est ni embarqué ni exécuté intégralement par la suite de tests actuelle. |
| [verapdf-js-viewer](https://github.com/veraPDF/verapdf-js-viewer) | Piste de visualisation et de surlignage | Aucun composant React, PDF.js ou paquet npm de ce projet n’est intégré. |
| [veraPDF-wcag-algs](https://github.com/veraPDF/veraPDF-wcag-algs) | Piste d’analyses complémentaires | Aucune bibliothèque Maven de ce dépôt n’est appelée par notre moteur. |

Les profils PDF/UA-2 et WTPDF ont été discutés en amont ; cette version reste
bornée à PDF/UA-1. Leur présence dans les ressources ne signifie pas leur prise en charge.

Les skills de création et remédiation PDF du poste ont constitué le contexte
de travail et utilisent aussi veraPDF. L’application n’appelle pas ces skills.
Le skill `readme-causal` a guidé la reconstitution de la genèse ; les sources
de vérité pour le comportement restent le code et les tests du dépôt.

## Reproductibilité et limites

Les scripts de [construction](../scripts/build.sh) et de [tests](../scripts/test.sh)
donnent les commandes effectivement utilisées. Les revues sont conservées dans
[docs](README.md), avec leurs limites. Les chemins temporaires cités dans les
anciens verdicts peuvent ne plus exister sur une autre machine.

Une dépendance présente dans cette liste n’est pas redistribuée avec le code.
Les licences et notices des composants doivent être consultées dans leurs
distributions respectives avant de préparer un paquet qui les embarque.
