"""Module d'analyse de l'espace disque, fichiers volumineux et doublons."""

import os
import hashlib
import datetime
from pathlib import Path
from collections import defaultdict


def get_disk_usage():
    """Récupère l'utilisation des disques/partitions."""
    import shutil
    partitions = []

    if os.name == "nt":
        # Windows: scanner les lettres de lecteur
        import string
        for letter in string.ascii_uppercase:
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                try:
                    usage = shutil.disk_usage(drive)
                    partitions.append({
                        "mount": drive,
                        "total_gb": round(usage.total / (1024**3), 2),
                        "used_gb": round(usage.used / (1024**3), 2),
                        "free_gb": round(usage.free / (1024**3), 2),
                        "percent_used": round(usage.used / usage.total * 100, 1),
                    })
                except OSError:
                    continue
    else:
        # Linux/macOS
        for mount in ["/", "/home", "/tmp", "/var"]:
            if os.path.ismount(mount) or mount == "/":
                try:
                    usage = shutil.disk_usage(mount)
                    partitions.append({
                        "mount": mount,
                        "total_gb": round(usage.total / (1024**3), 2),
                        "used_gb": round(usage.used / (1024**3), 2),
                        "free_gb": round(usage.free / (1024**3), 2),
                        "percent_used": round(usage.used / usage.total * 100, 1),
                    })
                except OSError:
                    continue

    return partitions


def find_large_files(directory, min_size_mb=100, max_results=50):
    """Trouve les fichiers les plus volumineux dans un répertoire."""
    large_files = []
    min_size_bytes = min_size_mb * 1024 * 1024
    directory = Path(directory)

    try:
        for filepath in directory.rglob("*"):
            if not filepath.is_file():
                continue
            try:
                size = filepath.stat().st_size
                if size >= min_size_bytes:
                    mtime = datetime.datetime.fromtimestamp(filepath.stat().st_mtime)
                    atime = datetime.datetime.fromtimestamp(filepath.stat().st_atime)
                    large_files.append({
                        "path": str(filepath),
                        "size_mb": round(size / (1024 * 1024), 2),
                        "last_modified": mtime.strftime("%Y-%m-%d %H:%M"),
                        "last_accessed": atime.strftime("%Y-%m-%d %H:%M"),
                        "extension": filepath.suffix.lower(),
                    })
            except (OSError, PermissionError):
                continue
    except PermissionError:
        pass

    large_files.sort(key=lambda x: x["size_mb"], reverse=True)
    return large_files[:max_results]


def find_duplicate_files(directory, min_size_kb=1):
    """Trouve les fichiers en double en comparant leurs hash."""
    directory = Path(directory)
    min_size_bytes = min_size_kb * 1024

    # Étape 1: Grouper par taille
    size_map = defaultdict(list)
    try:
        for filepath in directory.rglob("*"):
            if not filepath.is_file():
                continue
            try:
                size = filepath.stat().st_size
                if size >= min_size_bytes:
                    size_map[size].append(filepath)
            except (OSError, PermissionError):
                continue
    except PermissionError:
        pass

    # Étape 2: Pour les fichiers de même taille, comparer les hash
    duplicates = []
    for size, files in size_map.items():
        if len(files) < 2:
            continue
        hash_map = defaultdict(list)
        for filepath in files:
            file_hash = _hash_file(filepath)
            if file_hash:
                hash_map[file_hash].append(filepath)

        for file_hash, dup_files in hash_map.items():
            if len(dup_files) >= 2:
                total_wasted = size * (len(dup_files) - 1)
                duplicates.append({
                    "hash": file_hash[:16],
                    "size_mb": round(size / (1024 * 1024), 2),
                    "count": len(dup_files),
                    "wasted_mb": round(total_wasted / (1024 * 1024), 2),
                    "files": [str(f) for f in dup_files],
                })

    duplicates.sort(key=lambda x: x["wasted_mb"], reverse=True)
    return duplicates


def _hash_file(filepath, block_size=65536):
    """Calcule le hash SHA256 d'un fichier."""
    hasher = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            # Lire d'abord les premiers blocs pour un pré-filtrage rapide
            buf = f.read(block_size)
            while buf:
                hasher.update(buf)
                buf = f.read(block_size)
        return hasher.hexdigest()
    except (OSError, PermissionError):
        return None


def find_old_files(directory, days_threshold=365, max_results=100):
    """Trouve les fichiers non accédés depuis N jours."""
    old_files = []
    cutoff = datetime.datetime.now() - datetime.timedelta(days=days_threshold)
    directory = Path(directory)

    try:
        for filepath in directory.rglob("*"):
            if not filepath.is_file():
                continue
            try:
                atime = datetime.datetime.fromtimestamp(filepath.stat().st_atime)
                if atime < cutoff:
                    size = filepath.stat().st_size
                    old_files.append({
                        "path": str(filepath),
                        "size_mb": round(size / (1024 * 1024), 2),
                        "last_accessed": atime.strftime("%Y-%m-%d"),
                        "days_since_access": (datetime.datetime.now() - atime).days,
                    })
            except (OSError, PermissionError):
                continue
    except PermissionError:
        pass

    old_files.sort(key=lambda x: x["days_since_access"], reverse=True)
    return old_files[:max_results]


def get_directory_sizes(directory, depth=1):
    """Calcule la taille des sous-répertoires."""
    directory = Path(directory)
    dir_sizes = []

    try:
        for entry in directory.iterdir():
            if not entry.is_dir():
                continue
            try:
                total_size = sum(
                    f.stat().st_size
                    for f in entry.rglob("*")
                    if f.is_file()
                )
                dir_sizes.append({
                    "path": str(entry),
                    "name": entry.name,
                    "size_mb": round(total_size / (1024 * 1024), 2),
                    "size_gb": round(total_size / (1024**3), 2),
                })
            except (OSError, PermissionError):
                continue
    except PermissionError:
        pass

    dir_sizes.sort(key=lambda x: x["size_mb"], reverse=True)
    return dir_sizes
