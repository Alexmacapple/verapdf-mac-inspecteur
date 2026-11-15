# Genèse du projet

Reconstitution du 15 novembre 2026 à partir des demandes d’Alex dans la session,
du code livré et des rapports conservés. Le dépôt n’avait pas encore de commit
lors de cette rédaction : la chronologie ne provient donc pas d’un historique Git.

Marqueurs : **[FA]** fourni par Alex ; **[IC]** confirmé par les sources locales ;
**[INC]** information non conservée ou non vérifiable. Les paroles d’Alex
rapportées ici viennent de la conversation de création, non d’un fichier audio.

## Pourquoi une application supplémentaire ? [FA]

Le point de départ était un travail sur l’accessibilité des PDF avec PAC et
veraPDF sur Mac. Alex voulait comprendre les profils, les rapports et les
possibilités de remédiation, puis disposer d’une fiche pratique.

Un rapport veraPDF consulté signalait 75 échecs sur un PDF de présentation :
69 figures sans alternative, trois polices non incorporées, une identification
PDF/UA absente et deux contrôles concernant la description d’une annotation
de lien. Cela représente cinq règles en échec, pas 75 règles différentes.

Le diagnostic machine était disponible, mais sa traduction en travail concret
restait difficile : quelle figure, quelle page, quelle zone et quelle correction
préparer ? Alex l’a formulé ainsi : « ça me semblerait très pertinent d’avoir
un visualiseur pour mieux situer les corrections à faire ».

La finalité retenue est donc de rapprocher l’erreur de la page et de son contexte,
en donnant une explication exploitable. L’application prépare une correction
à effectuer ailleurs ; elle ne répare pas elle-même le PDF.

## Pourquoi à ce moment-là ? [FA, IC]

L’exploration des dépôts veraPDF a mis en évidence des briques de visualisation
et d’analyse, documentées dans les ressources de travail. En parallèle,
veraPDF était déjà installé localement et pouvait produire un rapport XML
PDF/UA-1 exploitable. Un vrai document fournissait immédiatement un cas de recette.

Cette combinaison — besoin exprimé, validateur disponible, document réel et
briques locales de lecture PDF — a permis un outil ciblé. Aucun changement
réglementaire déclencheur n’a été identifié dans les sources **[INC]**.

## Les décisions qui ont formé le projet

| Décision | Origine et raison |
|---|---|
| Application distincte de PAC Mac | **[FA]** Alex a proposé un outil séparé et validé cette direction. Cela permet un cycle d’évolution indépendant. |
| Dépôt autonome dans `git-hors-workflow/` | **[FA]** Alex a écarté l’emplacement initial dans les projets actifs et nommé ce répertoire. |
| PDF/UA-1 comme cible de cette version | **[FA, IC]** La discussion a conservé ce cadre ; le moteur lance `--flavour ua1` et refuse les autres profils. |
| Interface native SwiftUI, AppKit et PDFKit | **[IC]** L’implémentation réutilise l’affichage PDF du système et évite un serveur ou une application React à lancer. Ce choix technique a été réalisé pendant la construction. |
| Moteur Python séparé | **[IC]** Il relie XML, objets PDF et géométrie sans réimplémenter le validateur Java. |
| Lecture seule et traitement local | **[IC]** Aucun enregistrement du PDF, serveur ou envoi réseau n’est présent dans le parcours. |
| Localisation prudente | **[IC]** Une page connue sans rectangle et une zone partielle doivent rester explicites ; aucun cadre ne remplace une preuve manquante. |
| Nouveau nom | **[FA]** Alex a proposé `verapdf-mac-inspecteur`, puis validé « veraPDF Mac Inspecteur » pour le nom affiché. |
| Dépôt GitHub public | **[FA]** Alex a choisi explicitement la visibilité publique pour `Alexmacapple/verapdf-mac-inspecteur`. |

## Construction, confrontation et corrections [IC]

La première version a réuni une liste d’occurrences, un aperçu PDF et un panneau
de diagnostic. Les annotations ont fourni leurs rectangles ; certaines figures
ont été reliées à des images par les MCID ; le texte a servi au repérage des polices.
Les métadonnées globales sont restées sans page arbitraire.

Après un premier essai jugé fonctionnel par Alex, celui-ci a demandé une
contre-revue indépendante avec Claude Fable. Le relecteur a exécuté ses propres
cas synthétiques et un harnais PDFKit, sans modifier le code évalué.

Quatre défauts importants ont changé l’implémentation : la limite implicite de
100 détails par règle, des zones partielles présentées comme complètes, des
surlignages conservés sur la mauvaise page et des exigences non traduites trop
cachées. Les corrections ont ajouté un suivi de complétude, des motifs de
localisation, une synchronisation PDFKit et l’exigence originale toujours visible
quand aucune explication française spécifique n’existe.

Les nouvelles vérifications ont aussi révélé les images intégrées, les références
d’objets et les découpes. Masquer toute image après un opérateur de découpe
supprimait inutilement les 22 localisations du document réel : le traitement
a été affiné pour reconnaître une découpe rectangulaire contenante.

Alex a ensuite demandé de solder les améliorations mineures : annulation,
délais, rétention des rapports, imports, états d’erreur et coordonnées de police.
La [recette](recette.md) conserve la distinction entre corrections et limites de qualification.

## Ce que ce projet n’emprunte pas à PAC [IC]

PAC Mac appartient au contexte du besoin, mais ce projet ne décompile pas PAC,
ne réutilise pas son code et ne prétend pas à sa parité. La décompilation avec
ILSpy évoquée dans les échanges concernait un autre chantier. Le validateur
appelé ici est veraPDF ; les localisations sont produites par notre propre adaptateur.

## Sources et limites de cette reconstitution

- Demandes d’Alex dans la conversation : besoin, séparation, emplacement, nom et visibilité.
- [Produit](../PRODUCT.md), [carte du code](../CODEBASE_MAP.md), [moyens](moyens-et-sources.md).
- [Première revue](contre-revue-fable-2026-11-15.md), [vérifications](verification-corrections-fable-2026-11-15.md), [recette](recette.md).
- Les heures exactes de chaque décision et une transcription complète indépendante de la conversation ne sont pas conservées **[INC]**.
