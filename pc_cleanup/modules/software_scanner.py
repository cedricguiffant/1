"""Module de scan des logiciels installés et détection des logiciels inutilisés."""

import platform
import subprocess
import datetime
import json
from pathlib import Path


def get_installed_software():
    """Récupère la liste des logiciels installés selon l'OS."""
    system = platform.system()

    if system == "Windows":
        return _get_windows_software()
    elif system == "Linux":
        return _get_linux_software()
    elif system == "Darwin":
        return _get_macos_software()
    else:
        return []


def _get_windows_software():
    """Récupère les logiciels installés sur Windows via le registre."""
    software_list = []
    try:
        import winreg
        registry_paths = [
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
        ]
        for reg_path in registry_paths:
            for hive in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
                try:
                    key = winreg.OpenKey(hive, reg_path)
                except OSError:
                    continue
                for i in range(winreg.QueryInfoKey(key)[0]):
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        subkey = winreg.OpenKey(key, subkey_name)
                        name = _reg_value(subkey, "DisplayName")
                        if not name:
                            continue
                        install_date = _reg_value(subkey, "InstallDate")
                        install_location = _reg_value(subkey, "InstallLocation")
                        uninstall_string = _reg_value(subkey, "UninstallString")
                        size = _reg_value(subkey, "EstimatedSize")
                        software_list.append({
                            "name": name,
                            "install_date": _parse_date(install_date),
                            "install_location": install_location or "",
                            "uninstall_command": uninstall_string or "",
                            "size_kb": size if isinstance(size, int) else 0,
                            "last_used": _estimate_last_used_windows(install_location),
                        })
                        winreg.CloseKey(subkey)
                    except OSError:
                        continue
                winreg.CloseKey(key)
    except ImportError:
        pass
    return software_list


def _reg_value(key, name):
    """Lit une valeur du registre Windows."""
    try:
        import winreg
        value, _ = winreg.QueryValueEx(key, name)
        return value
    except OSError:
        return None


def _parse_date(date_str):
    """Parse une date au format YYYYMMDD."""
    if not date_str or not isinstance(date_str, str):
        return None
    try:
        return datetime.datetime.strptime(date_str, "%Y%m%d").strftime("%Y-%m-%d")
    except ValueError:
        return None


def _estimate_last_used_windows(install_location):
    """Estime la dernière utilisation en regardant les fichiers .exe modifiés."""
    if not install_location:
        return None
    path = Path(install_location)
    if not path.exists():
        return None
    latest = None
    try:
        for exe in path.rglob("*.exe"):
            try:
                mtime = datetime.datetime.fromtimestamp(exe.stat().st_mtime)
                if latest is None or mtime > latest:
                    latest = mtime
            except OSError:
                continue
    except PermissionError:
        pass
    return latest.strftime("%Y-%m-%d") if latest else None


def _get_linux_software():
    """Récupère les logiciels installés sur Linux."""
    software_list = []

    # Essai avec dpkg (Debian/Ubuntu)
    try:
        result = subprocess.run(
            ["dpkg-query", "-W", "-f",
             "${Package}\t${Installed-Size}\t${Status}\n"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                parts = line.split("\t")
                if len(parts) >= 3 and "installed" in parts[2].lower():
                    name = parts[0]
                    size_kb = int(parts[1]) if parts[1].isdigit() else 0
                    last_used = _estimate_last_used_linux(name)
                    software_list.append({
                        "name": name,
                        "install_date": None,
                        "install_location": "",
                        "uninstall_command": f"sudo apt remove {name}",
                        "size_kb": size_kb,
                        "last_used": last_used,
                    })
            return software_list
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Essai avec rpm (Fedora/CentOS)
    try:
        result = subprocess.run(
            ["rpm", "-qa", "--queryformat",
             "%{NAME}\t%{SIZE}\t%{INSTALLTIME}\n"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                parts = line.split("\t")
                if len(parts) >= 3:
                    name = parts[0]
                    size_kb = int(parts[1]) // 1024 if parts[1].isdigit() else 0
                    install_ts = int(parts[2]) if parts[2].isdigit() else 0
                    install_date = (
                        datetime.datetime.fromtimestamp(install_ts).strftime("%Y-%m-%d")
                        if install_ts else None
                    )
                    software_list.append({
                        "name": name,
                        "install_date": install_date,
                        "install_location": "",
                        "uninstall_command": f"sudo dnf remove {name}",
                        "size_kb": size_kb,
                        "last_used": _estimate_last_used_linux(name),
                    })
            return software_list
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Essai avec pacman (Arch)
    try:
        result = subprocess.run(
            ["pacman", "-Q"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                parts = line.split()
                if parts:
                    name = parts[0]
                    software_list.append({
                        "name": name,
                        "install_date": None,
                        "install_location": "",
                        "uninstall_command": f"sudo pacman -R {name}",
                        "size_kb": 0,
                        "last_used": _estimate_last_used_linux(name),
                    })
            return software_list
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return software_list


def _estimate_last_used_linux(package_name):
    """Estime la dernière utilisation d'un paquet Linux via /usr/bin."""
    bin_paths = [Path("/usr/bin"), Path("/usr/local/bin")]
    latest = None
    for bin_path in bin_paths:
        candidate = bin_path / package_name
        if candidate.exists():
            try:
                atime = datetime.datetime.fromtimestamp(candidate.stat().st_atime)
                if latest is None or atime > latest:
                    latest = atime
            except OSError:
                continue
    return latest.strftime("%Y-%m-%d") if latest else None


def _get_macos_software():
    """Récupère les applications installées sur macOS."""
    software_list = []
    apps_dir = Path("/Applications")
    if not apps_dir.exists():
        return software_list
    for app in apps_dir.iterdir():
        if app.suffix == ".app":
            name = app.stem
            try:
                size = sum(f.stat().st_size for f in app.rglob("*") if f.is_file())
                size_kb = size // 1024
            except (OSError, PermissionError):
                size_kb = 0
            try:
                last_access = datetime.datetime.fromtimestamp(app.stat().st_atime)
                last_used = last_access.strftime("%Y-%m-%d")
            except OSError:
                last_used = None
            software_list.append({
                "name": name,
                "install_date": None,
                "install_location": str(app),
                "uninstall_command": "",
                "size_kb": size_kb,
                "last_used": last_used,
            })
    return software_list


def find_unused_software(days_threshold=90):
    """Identifie les logiciels non utilisés depuis N jours."""
    software = get_installed_software()
    cutoff = datetime.datetime.now() - datetime.timedelta(days=days_threshold)
    cutoff_str = cutoff.strftime("%Y-%m-%d")

    unused = []
    unknown = []
    for sw in software:
        if sw["last_used"] is None:
            unknown.append(sw)
        elif sw["last_used"] < cutoff_str:
            sw["days_unused"] = (
                datetime.datetime.now()
                - datetime.datetime.strptime(sw["last_used"], "%Y-%m-%d")
            ).days
            unused.append(sw)

    unused.sort(key=lambda x: x.get("days_unused", 0), reverse=True)
    return unused, unknown


def uninstall_software(uninstall_command):
    """Exécute la commande de désinstallation d'un logiciel."""
    if not uninstall_command:
        return False, "Aucune commande de désinstallation disponible."
    system = platform.system()
    try:
        if system == "Windows":
            result = subprocess.run(
                uninstall_command, shell=True,
                capture_output=True, text=True, timeout=120
            )
        else:
            result = subprocess.run(
                uninstall_command.split(),
                capture_output=True, text=True, timeout=120
            )
        if result.returncode == 0:
            return True, "Désinstallation réussie."
        return False, f"Erreur: {result.stderr}"
    except subprocess.TimeoutExpired:
        return False, "Timeout lors de la désinstallation."
    except Exception as e:
        return False, f"Erreur: {e}"
