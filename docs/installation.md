# Installation et maintenance

La version actuelle est distribuée sous forme de code source. Il n’y a pas
d’installateur autonome ni de paquet notarisé prêt à télécharger dans ce dépôt.
La préparation nécessite le Terminal et les outils de développement macOS.

Une fois l’application construite, son utilisation se fait dans son interface
graphique : voir le [guide utilisateur](../README.md).

## Prérequis

- macOS 14 ou ultérieur et les outils de compilation Swift (`xcrun swiftc`).
- Python 3.12 avec les dépendances de [requirements.txt](../requirements.txt).
- veraPDF installé localement ; le moteur attend par défaut `/opt/homebrew/bin/verapdf`.

Les chemins par défaut correspondent à une installation Homebrew Apple Silicon.
Les scripts du projet ne téléchargent ni Python, ni veraPDF, ni leurs dépendances.

## Construire l’application

Récupérez les sources, puis ouvrez le Terminal à la racine du projet,
dans le dossier qui contient `requirements.txt` et `scripts/`.

Avec Python 3.12 et veraPDF déjà disponibles :

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
PYTHON_BIN="$PWD/.venv/bin/python" bash scripts/build.sh
open 'build/veraPDF Mac Inspecteur.app'
```

Le script vérifie les imports Python, compile l’interface et signe localement
le paquet. Il produit **`build/veraPDF Mac Inspecteur.app`**.

Vous pouvez ensuite ouvrir cette application depuis le Finder et l’ajouter
au Dock. Conservez le dossier du projet et l’environnement Python : ils font
encore partie de l’installation. Un alias peut servir de raccourci vers le paquet.

Si les dépendances sont déjà présentes dans le Python Homebrew par défaut :

```bash
bash scripts/build.sh
open 'build/veraPDF Mac Inspecteur.app'
```

## Après un déplacement ou une mise à jour

Le paquet mémorise le chemin de Python au moment de sa construction. Si vous
déplacez le projet ou son environnement `.venv`, reconstruisez l’application
avec le bon `PYTHON_BIN`. Actualisez aussi vos alias s’ils pointent vers un ancien emplacement.

`VERAPDF_COMMAND` permet de choisir un autre exécutable veraPDF dans
l’environnement de lancement du moteur. Cette variable doit être transmise
au processus qui lance l’application ; un lancement depuis le Finder ne
reprend pas nécessairement les variables de votre Terminal.

## Vérifier l’installation

Depuis la racine du projet, avec le même Python que pour la construction :

```bash
PYTHON_BIN="$PWD/.venv/bin/python" bash scripts/test.sh
codesign --verify --deep --strict 'build/veraPDF Mac Inspecteur.app'
```

Si vous utilisez le Python Homebrew par défaut, `bash scripts/test.sh` suffit
pour la suite de tests. Les scripts compilent les harnais Swift : les outils
de développement restent nécessaires à cette vérification.

Ouvrez ensuite l’application et un PDF pour vérifier le parcours réel de
validation sur votre poste. La suite synthétique ne remplace pas ce contrôle.

## Où sont les rapports ?

Le menu **Rapports → Ouvrir le dossier des rapports** ouvre :

```text
~/Library/Application Support/Inspecteur veraPDF/Rapports/
```

Ce nom interne historique est conservé malgré le renommage de l’application.
Les rapports générés au-delà des 50 plus récents ou de 30 jours sont déplacés
à la Corbeille, avec protection du rapport affiché. Les copies enregistrées
ailleurs par **Enregistrer le XML** ne sont pas concernées.

## Pour le développement

La capture interne est exclue de la construction normale. Une construction
dédiée s’obtient avec `DIAGNOSTICS=1 bash scripts/build.sh` ; fournissez aussi
`PYTHON_BIN` si vous utilisez un environnement Python distinct.

La [recette](recette.md) décrit les contrôles réalisés et leurs limites.
Les [spécifications techniques](specifications-techniques.md) détaillent le
contrat du moteur, les plafonds et les règles de localisation.
