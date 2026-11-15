# Compatibilité et chemins des dépendances

État vérifié le 15 novembre 2026 sur le poste de création. Cette page décrit
les limites présentes ; elle n’annonce pas une compatibilité universelle.

## Quel Mac peut utiliser le binaire construit ?

| Élément | Constat vérifié | Conséquence |
|---|---|---|
| Architecture du binaire local | `arm64` uniquement | Cible Apple Silicon ; le binaire ne convient pas aux Mac Intel. |
| Minimum inscrit dans le binaire Mach-O | `LC_BUILD_VERSION`, `minos 27.0` | Binaire compilé pour macOS 27.0 minimum ; compatibilité avec les versions antérieures non validée. |
| SDK de compilation | `27.2` | Version des outils utilisés, à distinguer du minimum `minos`. |
| Minimum déclaré dans `Info.plist` | `LSMinimumSystemVersion = 14.0` | Déclaration incohérente avec le binaire ; elle ne prouve pas une compatibilité macOS 14. |
| Poste d’exécution contrôlé | macOS 27.0, Apple Silicon | Recette locale uniquement, pas une campagne de tests sur tous les Mac. |

Le [script de construction](../scripts/build.sh) ne fixe actuellement ni cible
de déploiement explicite, ni construction universelle Intel + Apple Silicon.
Une reconstruction sur un autre poste peut donc produire d’autres métadonnées.
La compatibilité des sources avec macOS 14 n’est pas démontrée par le plist.

**À corriger dans un chantier de compatibilité :** aligner la cible de
compilation et le plist, puis tester chaque combinaison annoncée. Cette
documentation ne modifie pas la compilation et ne résout pas cette incohérence.

## Ce qui doit être installé

| Dépendance | Nécessaire pour… | Comment son chemin est choisi |
|---|---|---|
| Python 3.12 | Le moteur, y compris l’import de rapports XML | Chemin mémorisé lors de la construction du paquet. |
| pikepdf 10.6.0 et PyMuPDF 1.27.2.2 | Lecture des objets PDF et localisation | Paquets installés dans le Python choisi, selon [requirements.txt](../requirements.txt). |
| veraPDF CLI | Produire une nouvelle validation PDF/UA-1 | `VERAPDF_COMMAND`, sinon `/opt/homebrew/bin/verapdf`. |
| Environnement Java de veraPDF | Exécuter le validateur CLI | Doit être correctement configuré par l’installation de veraPDF. |
| Outils Swift et macOS (`xcrun swiftc`, `codesign`) | Construire et vérifier le paquet | Outils de développement du poste ; pas requis pour chaque contrôle une fois le paquet construit. |

Les bibliothèques Python doivent être compatibles avec l’interpréteur et
l’architecture du poste. Aucun de ces composants externes n’est téléchargé
ou installé automatiquement par l’application.

Un import XML n’exécute pas veraPDF : Python et ses deux bibliothèques restent
nécessaires. L’ouverture d’un PDF lance toutefois d’abord une analyse ; si le
validateur manque, elle échoue, puis un rapport existant peut être importé.

## Comment l’application trouve veraPDF

Le [moteur](../worker/analyzer.py) applique exactement cet ordre :

1. Si `VERAPDF_COMMAND` est défini, utiliser sa valeur comme chemin de fichier.
2. Sinon, utiliser `/opt/homebrew/bin/verapdf`.
3. Si ce fichier n’existe pas, afficher une erreur. Un fichier inexécutable
   ou une installation Java défaillante peut également empêcher le contrôle.

Il n’y a **ni recherche dans le `PATH`, ni exploration des installations
Homebrew, ni champ de réglage du chemin dans l’interface**. Par exemple,
`/usr/local/bin/verapdf` n’est pas essayé automatiquement. Le simple fait
que `verapdf` fonctionne dans votre Terminal ne suffit donc pas.

Pour connaître le chemin visible depuis votre Terminal :

```bash
command -v verapdf
```

Cette commande sert au diagnostic manuel ; l’application ne l’exécute pas.
Choisissez le fichier de lancement **CLI**, pas l’application graphique.

## Fournir un autre chemin pour un lancement

Après construction, depuis la racine du projet, adaptez le chemin absolu :

```bash
VERAPDF_COMMAND="/chemin/absolu/vers/verapdf" \
  './build/veraPDF Mac Inspecteur.app/Contents/MacOS/InspecteurVeraPDF'
```

Le lancement direct de l’exécutable transmet cette variable au moteur Python.
Le Terminal reste attaché à l’application jusqu’à sa fermeture. Cet exemple
ne crée pas un réglage permanent ; il vaut pour ce lancement seulement.

Un double-clic dans le Finder ou un clic dans le Dock ne reprend pas
nécessairement les variables de votre Terminal. Définir `VERAPDF_COMMAND`
dans un profil de shell, puis lancer l’application par le Dock, n’est donc
pas une configuration garantie. Le chemin doit parvenir au processus de
l’application ; il n’est pas enregistré dans ses préférences.

## Chemin de Python et déplacement du paquet

La variable `PYTHON_BIN` du [script de construction](../scripts/build.sh)
choisit Python. Sa valeur par défaut est
`/opt/homebrew/opt/python@3.12/bin/python3.12`. Le chemin absolu choisi est
inscrit sous `PythonExecutable` dans le plist du paquet.

Le programme ne recherche pas automatiquement un autre Python si ce chemin
disparaît. Copier seulement le `.app` vers un autre Mac ne copie ni Python,
ni les paquets, ni veraPDF. Après déplacement d’un environnement `.venv`,
reconstruisez le paquet avec son nouveau chemin : voir [Installation](installation.md).

## Vérifier les métadonnées sur son propre paquet

Depuis la racine du projet :

```bash
file 'build/veraPDF Mac Inspecteur.app/Contents/MacOS/InspecteurVeraPDF'
otool -l 'build/veraPDF Mac Inspecteur.app/Contents/MacOS/InspecteurVeraPDF'
/usr/libexec/PlistBuddy -c 'Print :LSMinimumSystemVersion' \
  'build/veraPDF Mac Inspecteur.app/Contents/Info.plist'
```

Dans la sortie d’`otool`, repérez `LC_BUILD_VERSION` et `minos` ; ne déduisez
pas le minimum réel de la seule valeur du plist. Les résultats indiqués en
haut de cette page décrivent le binaire local observé, pas une garantie pour
toutes les futures constructions.
