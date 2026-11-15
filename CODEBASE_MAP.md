# Carte du code

| Entrée | Rôle |
|---|---|
| `Sources/App.swift` | Cycle de vie, commandes, sélection des fichiers et état. |
| `Sources/Views.swift` | Liste des erreurs et panneau de diagnostic. |
| `Sources/PDFCanvas.swift` | Lecture PDFKit et contours sans mutation du PDF. |
| `Sources/Models.swift` | Diagnostic, sélection et conservation de l’état après erreur. |
| `Sources/WorkerTask.swift` | Processus, annulation du groupe et délai global. |
| `Sources/ReportCache.swift` | Rétention réversible des rapports générés. |
| `worker/analyzer.py` | Validation fraîche, XML, empreintes et JSON pour l’UI. |
| `worker/locations.py` | Résolution des pages, annotations, images et polices. |
| `tests/` | Cas synthétiques du rapport et des localisations. |
| `scripts/build.sh` | Compilation locale et assemblage du paquet macOS. |
| `docs/README.md` | Entrée de la genèse, des moyens et des spécifications a posteriori. |

Le worker ne reçoit que des chemins de fichiers choisis ; ses résultats sont
structurés et les références XML ne sont jamais exécutées.
