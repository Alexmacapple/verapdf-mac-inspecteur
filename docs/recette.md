# Recette locale du 15 novembre 2026

- Dépôt Git autonome vérifié : `git-hors-workflow/verapdf-mac-inspecteur`.
- Construction native Swift et signature locale terminées sans erreur.
- Trente-trois tests Python déterministes réussis : XML avec entités refusé, profil incorrect,
  fichier incompatible, taille différente, jobs ambigus, échecs sans détails,
  original intact, rectangle d’annotation, image balisée, transformation tournée,
  contenu mal formé et localisation globale ou absente ; troncature par règle,
  plafond transmis au validateur, règle sans traduction, images avec texte ou
  Form XObject, découpe, page non empruntée à l’ancêtre, MCID absent, flux externe,
  limite de parcours, déclaration XML en UTF-16, image intégrée, référence
  d’objet, découpe rectangulaire non rognante, découpe non rectangulaire,
  chemin prolongé après W et découpe par texte hors de la balise.
- Harnais Swift exécuté sur les vraies classes PDFKit : navigation interne vers
  la deuxième page, synchronisation du modèle et suppression immédiate des
  anciens cadres ; une mise à jour programmée ne republie pas l’état SwiftUI.
- Validation réelle PDF/UA-1 : document de 21 pages, cinq règles et 75 échecs.
  Les mêmes 75 occurrences sont lues depuis le rapport XML importé.
- Soixante-quatorze occurrences ont une page connue : 18 avec cadres d’images,
  quatre avec localisation partielle explicitement signalée, deux avec fragments
  de polices, deux avec le rectangle d’un même lien et 48 sans zone précise.
  Les 22 anciennes localisations d’images sont conservées : les découpes
  rectangulaires du document contiennent les images. Une occurrence est globale.
- Le cas adverse réel de Fable produit désormais 156 occurrences chargées sur
  156 échecs, dont les 151 figures sans alternative (100 seulement avant correction).
  Le contrôle de complétude est vrai, par règle et au total.
- Empreinte du PDF inchangée avant et après la validation et la localisation.
- Démarrage du paquet vérifié, chargement du document et sélection initiale
  de l’annotation en page 10 observés dans l’état du modèle de l’application.
- Capture interne après reconstruction : liste visible et compteur 75 visibles,
  75 chargées sur 75 échecs. Un ancien XML tronqué affiche bien l’avertissement
  105/156 et le détail de la règle 7.3-1 à 100/151 ; la description originale
  de la règle 7.18.5-1 est visible directement dans la liste.
- Lanceur du Bureau : lien vers le paquet construit dans `build/`.

## Corrections issues de la contre-revue

Les quatre constats importants de la revue indépendante sont traités : plafond
veraPDF explicite et avertissement de troncature, zones partielles signalées et
cadres incertains masqués, navigation PDFKit synchronisée et exigence originale
visible pour les règles sans traduction. Le chemin Python du paquet conserve
le lien stable Homebrew. Les DTD sont refusées par le parseur quelle que soit
l’encodage, et les erreurs XML de syntaxe sont présentées en français.

La contre-vérification Fable a confirmé I1, I3 au niveau du harnais et I4, puis
trouvé deux variantes de I2 (image intégrée et référence OBJR) ainsi qu’un
masquage excessif des cadres par découpe pleine page. Ces trois points ont été
corrigés dans une seconde passe et ajoutés aux tests. La conservation d’une
image à la frontière de sa découpe tolère seulement 0,0001 point d’arrondi ;
le cadre final est intersecté avec la découpe pour ne pas la dépasser.
La vérification finale de Fable conclut « I2 : corrigé », avec une réserve
mineure sur le prolongement du chemin après W. Cette réserve et la découpe par
texte ont ensuite été corrigées ; 29 cas indépendants produits par Fable ont
été rejoués par Codex avec assertions, sans changer les localisations du PDF réel.
Le dernier ajustement n’a pas fait l’objet d’un nouveau passage du modèle Fable.

## Améliorations mineures réalisées en 0.2.0

| Constat historique | Réponse réalisée | Vérification |
|---|---|---|
| Attente du repérage non bornée | Délai global de 180 s, bouton Annuler, arrêt du groupe de processus et secours SIGKILL après 2 s. | Harnais Swift, y compris descendant qui refuse SIGTERM. |
| Extraction répétée du texte | Cache en mémoire par page, limité à la durée du contrôle. | Test de deux résolutions avec une seule extraction. |
| Police sur page tournée et CropBox décalée | Conversion par l’origine et la hauteur non tournée de la CropBox. | Même rectangle sur rotations 0, 90, 180 et 270°. |
| Polices homonymes | Aucun cadre si plusieurs objets correspondent au nom normalisé. | PDF synthétique à deux objets ; une localisation réelle auparavant trop large est masquée. |
| Rectangle d’annotation inversé | Normalisation réservée aux annotations ; une intersection vide de découpe reste vide. | Test d’annotation et rejeu des cas de découpes. |
| Python versionné | Lien stable Homebrew mémorisé par le paquet. | Lecture du plist et construction. |
| Import trop strict ou trop lâche | Fichier déplacé accepté par nom et taille si l’ancien chemin est absent ; état normal, profil exact, taille et compteurs exigés. | Tests de déplacement et d’attributs manquants ou invalides. |
| Résultat perdu après refus | Diagnostic, sélection, page et PDF précédents préservés jusqu’à une nouvelle réussite. | Harnais de vrais états `Inspector`. |
| Page 1/0 après erreur | Nombre réel de pages du PDF initial même si le contrôle échoue ; aucune page annoncée si le PDF n’est pas lisible. | PDF témoin de deux pages dans le harnais Swift. |
| Provenance importée trop discrète | Bandeau dédié et provenance conservée dans le pied de page. | Source SwiftUI ; parcours humain complet non qualifié. |
| XML accumulés | 50 rapports générés récents ou 30 jours ; déplacement à la Corbeille, rapport affiché protégé ; nettoyage manuel disponible. | Sélection de fichiers testée avec Corbeille simulée, sans toucher aux rapports privés. |
| Messages de parsing bruts | Erreurs XML, nombres invalides, fichiers absents et délai présentés en français. | Tests Python ; réponse invalide traitée en français par Swift. |
| Capture de diagnostic dans le binaire livré | Code compilé seulement avec `DIAGNOSTICS=1`. | Construction normale et contrôle de l’absence de l’option de capture. |

Les 33 tests Python et les deux harnais Swift passent via `bash scripts/test.sh`.
Le PDF réel reste à 75 occurrences chargées sur 75, avec SHA-256 inchangé.
Ces derniers ajustements ont été contrôlés par Codex, sans nouvelle revue Fable.
Le nouveau nom affiché est « veraPDF Mac Inspecteur » ; les identifiants et le
dossier interne de rapports restent stables pour conserver les données existantes.

## Limites de la recette

Le contrôle du binaire a révélé `arm64`, `LC_BUILD_VERSION minos 27.0` et SDK
`27.2`, sur un poste macOS 27.0. Le plist déclare pourtant `14.0` : cette
incohérence de compilation reste à corriger et invalide l’ancienne annonce
de compatibilité macOS 14. Aucun essai sur Mac Intel ou ancien macOS n’a été
réalisé. Les chemins par défaut sont locaux, sans découverte automatique :
voir [Compatibilité et dépendances](compatibilite.md).

La capture système est refusée à l’hôte REA par les permissions macOS.
Les captures internes de l’application ne couvrent pas les dialogues système.
Le parcours manuel complet des boutons, le clavier et VoiceOver ne sont pas
qualifiés par cette recette. Les cadres vectoriels, Form XObjects et zones
sans preuve restent hors localisation précise ; ils ne sont pas fabriqués.

Les rapports et captures du document réel restent hors du dépôt. Aucun dépôt
distant, publication, installateur portable ni notarisation n’a été créé.
