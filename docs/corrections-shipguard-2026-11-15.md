# Corrections ShipGuard — version 0.2.1

L’audit du commit `77d2ffa` a relevé douze défauts distincts : un de sévérité
haute, sept moyens et quatre faibles. Les corroborations de l’analyse logique
portaient sur les mêmes défauts ; elles ne constituent pas cinq erreurs de plus.
Le rapport initial reste un état historique, conservé localement avec ses preuves.

## Corrections et vérifications

| Référence | Défaut corrigé | Vérification |
|---|---|---|
| r1-z02-001 | Un descendant refusant SIGTERM survivait si ses sorties étaient fermées. Le groupe est maintenant arrêté avant de libérer le processus du traitement annulé. | Contre-exemple Swift en échec avant correction, réussi après ; rejeu indépendant du harnais d’audit. |
| r1-z01-001 | Un XML déclarant zéro échec mais une règle échouée pouvait sembler complet. Les compteurs contradictoires sont refusés et la complétude inclut les règles. | Test Python de rejet ; XML réels et cas tronqués conservés dans la suite. |
| r1-z02-002 | Ajuster ne rétablissait pas la page après un zoom natif si le modèle valait déjà 1. Une demande explicite déclenche désormais l’ajustement PDFKit. | Ancienne action reproduite en échec ; nouvelle action vérifiée sur une vraie vue SwiftUI/PDFKit. |
| r1-z03-001 | Le minimum du binaire différait du plist. Une cible commune explicite est appliquée et contrôlée après compilation. | Construction : `minos 14.0` et plist `14.0`. |
| r1-z03-002 | Un nom de Python sans chemin devenait un chemin inexistant dans le paquet. Il est résolu avant la construction. | Construction avec `PYTHON_BIN=python3.12`, chemin absolu exécutable dans le plist. |
| r1-z03-003 | Le même nom court empêchait le harnais Swift de démarrer Python. Les tests partagent la résolution utilisée par la construction. | Suite complète lancée avec `PYTHON_BIN=python3.12`. |
| r1-z03-004 | Un répertoire temporaire accentué produisait des littéraux Swift invalides. Les chemins générés passent par UTF-8/base64. | Génération réelle des deux captures avec un `TMPDIR` accentué. |
| r1-z03-005 | Un délai de capture pouvait laisser le moteur et veraPDF vivants. Une session dédiée réunit les processus de chaque capture et son nettoyage utilise TERM puis KILL. | Tests de nettoyage, dont refus de SIGTERM ; captures réelles terminées et contre-vérification des groupes. |
| r1-z01-002 | Le PDF choisi était haché à répétition face à plusieurs jobs étrangers. Les empreintes sont mémorisées pendant la lecture du rapport. | Dix jobs étrangers, au plus un calcul pour le PDF choisi ; empreinte fraîche réutilisée. |
| r1-z01-003 | Le cache de texte retenait aussi les octets des images. L’extraction et le cache sont limités aux blocs de texte. | PDF avec image et texte : cadres de police conservés, aucun bloc d’image dans le cache. |
| r1-z02-003 | Le PDF initial n’était pas affiché lorsque le moteur manquait. Le repli est commun aux sorties en erreur. | Moteur absent et PDF réel de deux pages ; variante d’annulation tardive également ajoutée au harnais. |
| r1-z02-004 | Le bouton d’accueil pouvait ouvrir un deuxième sélecteur pendant une analyse. Le bouton est désactivé et l’action vérifie aussi l’état occupé. | Sélecteur intercepté uniquement dans le processus de test : aucun dialogue demandé pendant le traitement. |

Les trois nouveaux tests Python du moteur ont d’abord échoué sur les sources
initiales, puis réussi après correction. Les harnais natifs ont également
reproduit les défauts de processus, de repli initial, d’ouverture et de zoom
avant correction. Deux tests supplémentaires couvrent le générateur de captures.

## Rejouer

Depuis la racine du dépôt, avec les dépendances installées :

```bash
PYTHON_BIN=python3.12 bash scripts/test.sh
PYTHON_BIN=python3.12 bash scripts/build.sh
codesign --verify --deep --strict 'build/veraPDF Mac Inspecteur.app'
```

Résultat local : **38 tests Python et trois harnais Swift réussis**. Les
captures publiques proviennent toujours d’un PDF fictif, validé réellement
par veraPDF. Aucun document ou rapport privé n’est ajouté au dépôt.
Le document de recette de 21 pages conserve ses 75 échecs sur cinq règles,
avec toutes les occurrences chargées et la même empreinte avant et après.

## Limites

Ces vérifications ciblent les contre-exemples de l’audit et les régressions
couvertes par la suite. Elles ne constituent pas un nouvel audit exhaustif
ShipGuard ni une certification d’accessibilité. Les actions SwiftUI/PDFKit
sont exercées dans un harnais natif ; le parcours humain complet au clavier,
les dialogues système et VoiceOver restent à qualifier.

La compilation cible macOS 14.0, mais l’exécution locale est vérifiée seulement
sur macOS 27.0 Apple Silicon. Les versions antérieures et Intel restent à tester.
