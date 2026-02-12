"""Module d'organisation et de tri des fichiers."""

import shutil
import datetime
from pathlib import Path
from collections import defaultdict


# Catégories de fichiers par extension
FILE_CATEGORIES = {
    "Images": {
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp",
        ".tiff", ".ico", ".raw", ".heic", ".heif",
    },
    "Videos": {
        ".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm",
        ".m4v", ".mpg", ".mpeg", ".3gp",
    },
    "Audio": {
        ".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a",
        ".opus", ".aiff",
    },
    "Documents": {
        ".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".xls",
        ".xlsx", ".ppt", ".pptx", ".csv", ".ods", ".odp",
    },
    "Archives": {
        ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz",
        ".iso", ".dmg",
    },
    "Code": {
        ".py", ".js", ".ts", ".java", ".c", ".cpp", ".h", ".cs",
        ".go", ".rs", ".rb", ".php", ".html", ".css", ".sql",
        ".sh", ".bat", ".ps1", ".json", ".xml", ".yaml", ".yml",
    },
    "Executables": {
        ".exe", ".msi", ".deb", ".rpm", ".appimage", ".app",
        ".dmg", ".bin", ".run",
    },
}


def categorize_files(directory):
    """Analyse et catégorise tous les fichiers d'un répertoire."""
    directory = Path(directory)
    categories = defaultdict(list)

    try:
        for filepath in directory.iterdir():
            if not filepath.is_file():
                continue
            ext = filepath.suffix.lower()
            category = _get_category(ext)
            try:
                size = filepath.stat().st_size
                mtime = datetime.datetime.fromtimestamp(filepath.stat().st_mtime)
                categories[category].append({
                    "name": filepath.name,
                    "path": str(filepath),
                    "size_mb": round(size / (1024 * 1024), 2),
                    "last_modified": mtime.strftime("%Y-%m-%d %H:%M"),
                    "extension": ext,
                })
            except (OSError, PermissionError):
                continue
    except PermissionError:
        pass

    # Convertir en dict normal avec statistiques
    result = {}
    for category, files in categories.items():
        total_size = sum(f["size_mb"] for f in files)
        result[category] = {
            "files": files,
            "count": len(files),
            "total_size_mb": round(total_size, 2),
        }

    return result


def _get_category(extension):
    """Détermine la catégorie d'un fichier par son extension."""
    for category, extensions in FILE_CATEGORIES.items():
        if extension in extensions:
            return category
    return "Autres"


def organize_files(directory, dry_run=True):
    """Organise les fichiers d'un répertoire en sous-dossiers par catégorie.

    Args:
        directory: Répertoire à organiser.
        dry_run: Si True, simule l'organisation sans déplacer.

    Returns:
        Dictionnaire avec les résultats de l'organisation.
    """
    directory = Path(directory)
    results = {
        "moved_files": 0,
        "created_dirs": [],
        "moves": [],
        "errors": [],
        "dry_run": dry_run,
    }

    try:
        for filepath in directory.iterdir():
            if not filepath.is_file():
                continue

            ext = filepath.suffix.lower()
            category = _get_category(ext)

            if category == "Autres":
                continue

            dest_dir = directory / category
            dest_file = dest_dir / filepath.name

            # Gérer les conflits de noms
            if dest_file.exists():
                stem = filepath.stem
                suffix = filepath.suffix
                counter = 1
                while dest_file.exists():
                    dest_file = dest_dir / f"{stem}_{counter}{suffix}"
                    counter += 1

            results["moves"].append({
                "from": str(filepath),
                "to": str(dest_file),
                "category": category,
            })

            if not dry_run:
                dest_dir.mkdir(exist_ok=True)
                if str(dest_dir) not in results["created_dirs"]:
                    results["created_dirs"].append(str(dest_dir))
                try:
                    shutil.move(str(filepath), str(dest_file))
                    results["moved_files"] += 1
                except (OSError, PermissionError) as e:
                    results["errors"].append(f"{filepath}: {e}")
            else:
                results["moved_files"] += 1

    except PermissionError as e:
        results["errors"].append(f"Accès refusé: {directory}: {e}")

    return results


def organize_by_date(directory, dry_run=True):
    """Organise les fichiers par date (année/mois).

    Args:
        directory: Répertoire à organiser.
        dry_run: Si True, simule l'organisation sans déplacer.

    Returns:
        Dictionnaire avec les résultats de l'organisation.
    """
    directory = Path(directory)
    results = {
        "moved_files": 0,
        "moves": [],
        "errors": [],
        "dry_run": dry_run,
    }

    try:
        for filepath in directory.iterdir():
            if not filepath.is_file():
                continue

            try:
                mtime = datetime.datetime.fromtimestamp(filepath.stat().st_mtime)
                year_month = mtime.strftime("%Y/%Y-%m")
                dest_dir = directory / year_month
                dest_file = dest_dir / filepath.name

                results["moves"].append({
                    "from": str(filepath),
                    "to": str(dest_file),
                })

                if not dry_run:
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(filepath), str(dest_file))
                    results["moved_files"] += 1
                else:
                    results["moved_files"] += 1

            except (OSError, PermissionError) as e:
                results["errors"].append(f"{filepath}: {e}")

    except PermissionError as e:
        results["errors"].append(f"Accès refusé: {directory}: {e}")

    return results
