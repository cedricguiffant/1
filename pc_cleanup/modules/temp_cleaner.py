"""Module de nettoyage des fichiers temporaires et caches."""

import os
import platform
import shutil
import datetime
from pathlib import Path


# Répertoires temporaires connus par OS
TEMP_DIRS = {
    "Windows": [
        "{TEMP}",
        "{LOCALAPPDATA}\\Temp",
        "C:\\Windows\\Temp",
        "C:\\Windows\\Prefetch",
        "{LOCALAPPDATA}\\Microsoft\\Windows\\INetCache",
        "{LOCALAPPDATA}\\Microsoft\\Windows\\Explorer",
    ],
    "Linux": [
        "/tmp",
        "/var/tmp",
        "~/.cache",
        "~/.local/share/Trash",
    ],
    "Darwin": [
        "/tmp",
        "/private/var/tmp",
        "~/Library/Caches",
        "~/.Trash",
    ],
}

# Extensions de fichiers temporaires courants
TEMP_EXTENSIONS = {
    ".tmp", ".temp", ".bak", ".old", ".swp", ".swo",
    ".log", ".dmp", ".crash", ".thumbs.db",
}

# Répertoires de cache de navigateurs
BROWSER_CACHE_DIRS = {
    "Windows": {
        "Chrome": "{LOCALAPPDATA}\\Google\\Chrome\\User Data\\Default\\Cache",
        "Firefox": "{LOCALAPPDATA}\\Mozilla\\Firefox\\Profiles",
        "Edge": "{LOCALAPPDATA}\\Microsoft\\Edge\\User Data\\Default\\Cache",
    },
    "Linux": {
        "Chrome": "~/.cache/google-chrome",
        "Firefox": "~/.cache/mozilla/firefox",
        "Chromium": "~/.cache/chromium",
    },
    "Darwin": {
        "Chrome": "~/Library/Caches/Google/Chrome",
        "Firefox": "~/Library/Caches/Firefox",
        "Safari": "~/Library/Caches/com.apple.Safari",
    },
}


def _expand_path(path_str):
    """Résout les variables d'environnement et le ~ dans un chemin."""
    path_str = path_str.replace("~", str(Path.home()))
    if "{" in path_str:
        for var in ["TEMP", "LOCALAPPDATA", "APPDATA", "USERPROFILE"]:
            value = os.environ.get(var, "")
            path_str = path_str.replace(f"{{{var}}}", value)
    return Path(path_str)


def scan_temp_files():
    """Scanne tous les répertoires temporaires et retourne un rapport."""
    system = platform.system()
    temp_dirs = TEMP_DIRS.get(system, [])
    report = {
        "total_size_mb": 0,
        "total_files": 0,
        "directories": [],
    }

    for dir_template in temp_dirs:
        dir_path = _expand_path(dir_template)
        if not dir_path.exists():
            continue
        dir_info = _scan_directory(dir_path)
        if dir_info["file_count"] > 0:
            report["directories"].append(dir_info)
            report["total_size_mb"] += dir_info["size_mb"]
            report["total_files"] += dir_info["file_count"]

    return report


def scan_browser_caches():
    """Scanne les caches de navigateurs."""
    system = platform.system()
    browser_dirs = BROWSER_CACHE_DIRS.get(system, {})
    report = {
        "total_size_mb": 0,
        "browsers": [],
    }

    for browser, dir_template in browser_dirs.items():
        dir_path = _expand_path(dir_template)
        if not dir_path.exists():
            continue
        dir_info = _scan_directory(dir_path)
        dir_info["browser"] = browser
        if dir_info["size_mb"] > 0:
            report["browsers"].append(dir_info)
            report["total_size_mb"] += dir_info["size_mb"]

    return report


def _scan_directory(dir_path):
    """Scanne un répertoire et retourne ses statistiques."""
    total_size = 0
    file_count = 0
    oldest_file = None

    try:
        for filepath in dir_path.rglob("*"):
            if filepath.is_file():
                try:
                    size = filepath.stat().st_size
                    mtime = filepath.stat().st_mtime
                    total_size += size
                    file_count += 1
                    if oldest_file is None or mtime < oldest_file:
                        oldest_file = mtime
                except (OSError, PermissionError):
                    continue
    except PermissionError:
        pass

    return {
        "path": str(dir_path),
        "size_mb": round(total_size / (1024 * 1024), 2),
        "file_count": file_count,
        "oldest_file": (
            datetime.datetime.fromtimestamp(oldest_file).strftime("%Y-%m-%d")
            if oldest_file else None
        ),
    }


def clean_temp_directory(dir_path, dry_run=True):
    """Nettoie un répertoire temporaire.

    Args:
        dir_path: Chemin du répertoire à nettoyer.
        dry_run: Si True, simule le nettoyage sans supprimer.

    Returns:
        Dictionnaire avec les résultats du nettoyage.
    """
    dir_path = Path(dir_path)
    results = {
        "deleted_files": 0,
        "deleted_size_mb": 0,
        "errors": [],
        "dry_run": dry_run,
    }

    if not dir_path.exists():
        results["errors"].append(f"Répertoire introuvable: {dir_path}")
        return results

    try:
        for filepath in dir_path.rglob("*"):
            if not filepath.is_file():
                continue
            try:
                size = filepath.stat().st_size
                if not dry_run:
                    filepath.unlink()
                results["deleted_files"] += 1
                results["deleted_size_mb"] += size / (1024 * 1024)
            except (OSError, PermissionError) as e:
                results["errors"].append(f"{filepath}: {e}")
    except PermissionError as e:
        results["errors"].append(f"Accès refusé: {dir_path}: {e}")

    results["deleted_size_mb"] = round(results["deleted_size_mb"], 2)
    return results


def clean_browser_cache(browser_name, dry_run=True):
    """Nettoie le cache d'un navigateur spécifique."""
    system = platform.system()
    browser_dirs = BROWSER_CACHE_DIRS.get(system, {})

    if browser_name not in browser_dirs:
        return {"error": f"Navigateur non supporté: {browser_name}"}

    dir_path = _expand_path(browser_dirs[browser_name])
    return clean_temp_directory(dir_path, dry_run=dry_run)


def find_temp_files_in_directory(directory):
    """Trouve les fichiers temporaires dans un répertoire utilisateur."""
    directory = Path(directory)
    temp_files = []

    try:
        for filepath in directory.rglob("*"):
            if not filepath.is_file():
                continue
            if filepath.suffix.lower() in TEMP_EXTENSIONS:
                try:
                    size = filepath.stat().st_size
                    temp_files.append({
                        "path": str(filepath),
                        "size_mb": round(size / (1024 * 1024), 2),
                        "extension": filepath.suffix.lower(),
                    })
                except (OSError, PermissionError):
                    continue
    except PermissionError:
        pass

    temp_files.sort(key=lambda x: x["size_mb"], reverse=True)
    return temp_files


def empty_recycle_bin(dry_run=True):
    """Vide la corbeille."""
    system = platform.system()
    results = {"deleted_size_mb": 0, "dry_run": dry_run, "errors": []}

    if system == "Windows":
        if not dry_run:
            try:
                import ctypes
                ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 0x07)
                return results
            except Exception as e:
                results["errors"].append(str(e))
    elif system == "Linux":
        trash_path = Path.home() / ".local/share/Trash"
        if trash_path.exists():
            return clean_temp_directory(trash_path, dry_run=dry_run)
    elif system == "Darwin":
        trash_path = Path.home() / ".Trash"
        if trash_path.exists():
            return clean_temp_directory(trash_path, dry_run=dry_run)

    return results
