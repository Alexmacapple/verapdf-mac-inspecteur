# veraPDF Mac Inspecteur

Application macOS autonome et locale, en lecture seule : PDF et rapport XML,
erreurs navigables, zones sourcées et limites de localisation visibles.

- Lire `README.md`, `PRODUCT.md` et `CODEBASE_MAP.md` avant modification.
- `Sources/` : interface native ; `worker/` : validation et localisation.
- Aucun PDF utilisateur, rapport privé ou capture dans Git.
- Aucun accès réseau, action PDF, correction ou déclaration de conformité.
- Un rapport importé reste une association déclarative ; seule une validation
  fraîche encadrée par les empreintes porte sur les octets contrôlés.
- Distinguer page connue, rectangle établi et localisation inconnue.
- Tests : `bash scripts/test.sh`.
- Construction : `bash scripts/build.sh` ; application dans `build/`.
- Garder les dépendances Python explicites, sans installation automatique.
- Recette : vrai PDF, import XML, fichier incompatible, navigation et original
  intact ; nommer les vérifications d’interface réellement exécutées.
