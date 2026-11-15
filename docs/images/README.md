# Captures publiques du README

Les deux PNG sont des captures réelles de la zone de travail de l’application,
produites le 15 novembre 2026 sur macOS 27.0. Elles ne montrent pas la barre
d’outils native macOS. Aucun pixel d’interface n’a été inventé ou retouché.

| Image | État montré |
|---|---|
| `figure-sans-alternative.png` | Page 2 du document fictif, occurrence PDF/UA-1 7.3-1 sélectionnée, une zone d’image. |
| `lien-sans-description.png` | Même page, occurrence 7.18.5-2 sélectionnée, rectangle de l’annotation du lien. |

Le document pédagogique est créé par le [script de génération](../../scripts/captures-demo.py).
Les textes et données du graphique sont fictifs ; le lien utilise le domaine
réservé `example.invalid`. Aucun PDF, rapport ou capture utilisateur n’est utilisé.
Les erreurs sont les résultats réels d’une validation veraPDF, sans rapport simulé.

## Reproduction

Avec les dépendances Python, veraPDF CLI et les outils Swift disponibles :

```bash
python3.12 -B scripts/captures-demo.py
```

Le script génère un PDF et un paquet de diagnostic dans un répertoire temporaire,
compile les vues et le moteur du projet, puis sélectionne les occurrences
programmatiquement. Une copie temporaire du point d’entrée adapte seulement
la sélection initiale et le dossier de rapports ; les vues ne sont pas réécrites.
Le générateur crée une session POSIX dédiée à chaque capture. Dans la copie
temporaire du moteur uniquement, le détachement vers une autre session est
désactivé : l’application, le moteur et veraPDF sont ainsi arrêtés ensemble,
y compris en cas de délai dépassé. Les chemins accentués sont encodés en UTF-8 dans les
sources générées. Le répertoire temporaire propre au compilateur Swift reste
`/tmp/` pour éviter un arrêt du pilote local avec un `TMPDIR` accentué.
L’application installée et ses rapports privés ne sont pas modifiés.

Les métadonnées de contrôle imposent la page 2 et la présence d’un cadre avant
la copie des PNG. Le PDF, les XML et le paquet temporaires sont ensuite supprimés.
Les PNG ont été ouverts et inspectés avant leur inclusion dans le README.

Ces deux images de 1 400 × 900 pixels, d’environ 160 Kio chacune, constituent
les seuls éléments binaires ajoutés pour illustrer le parcours utilisateur.
Les sources du générateur permettent de les refaire sans conserver un PDF.
