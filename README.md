# PC Cleanup Tool

Outil en ligne de commande pour trier, organiser et nettoyer son PC. Fonctionne sur **Windows**, **Linux** et **macOS**.

## Fonctionnalités

| Fonction | Description |
|---|---|
| **Scanner les logiciels** | Liste les logiciels installés, détecte ceux non utilisés depuis longtemps, permet la désinstallation |
| **Analyser l'espace disque** | Affiche l'utilisation par partition et par répertoire |
| **Trouver les gros fichiers** | Recherche les fichiers volumineux avec possibilité de suppression |
| **Détecter les doublons** | Identifie les fichiers en double par comparaison de hash SHA-256 |
| **Nettoyer les temporaires** | Supprime les fichiers temporaires système et les caches navigateurs |
| **Organiser les fichiers** | Trie automatiquement les fichiers par catégorie (Images, Vidéos, Documents...) ou par date |
| **Nettoyage rapide** | Scan complet en un seul passage avec résumé et nettoyage automatique |

## Installation

```bash
# Cloner le dépôt
git clone <url-du-repo>
cd pc-cleanup-tool

# Installer
pip install .
```

## Utilisation

```bash
# Méthode 1 : script direct
python main.py

# Méthode 2 : module Python
python -m pc_cleanup

# Méthode 3 : après installation
pc-cleanup
```

## Structure du projet

```
pc_cleanup/
├── __init__.py              # Package principal
├── __main__.py              # Exécution via python -m
├── cli.py                   # Interface CLI interactive
└── modules/
    ├── __init__.py
    ├── software_scanner.py  # Scan et désinstallation de logiciels
    ├── disk_analyzer.py     # Analyse disque, gros fichiers, doublons
    ├── temp_cleaner.py      # Nettoyage fichiers temporaires et caches
    └── file_organizer.py    # Organisation des fichiers par catégorie/date
```

## Compatibilité

- **Windows** : Lecture du registre, gestionnaire de paquets natif
- **Linux** : Support dpkg (Debian/Ubuntu), rpm (Fedora/CentOS), pacman (Arch)
- **macOS** : Scan du dossier /Applications

## Prérequis

- Python 3.8+
- Aucune dépendance externe (uniquement la bibliothèque standard Python)

## Avertissement

Certaines opérations (désinstallation, suppression) sont irréversibles. L'outil propose toujours une confirmation avant toute action destructive. Un mode simulation (dry run) est disponible pour prévisualiser les changements.
