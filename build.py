#!/usr/bin/env python3
"""Script de build pour générer l'exécutable PC Cleanup Tool."""

import subprocess
import sys


def build():
    """Génère le .exe avec PyInstaller (mode GUI)."""
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("Installation de PyInstaller...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "pyinstaller"]
        )

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",                    # Un seul fichier .exe
        "--windowed",                   # Pas de console (fenêtre GUI uniquement)
        "--name", "PC-Cleanup",         # Nom de l'exécutable
        "--clean",                      # Nettoyer le cache avant le build
        "--add-data", "pc_cleanup:pc_cleanup",
        "main.py",
    ]

    print("=" * 50)
    print("  PC Cleanup Tool — Build GUI .exe")
    print("=" * 50)
    print(f"\nCommande: {' '.join(cmd)}\n")
    subprocess.check_call(cmd)
    print("\n" + "=" * 50)
    print("  Build terminé !")
    print("  → dist/PC-Cleanup.exe")
    print("=" * 50)


def build_cli():
    """Génère le .exe en mode console (CLI)."""
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("Installation de PyInstaller...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "pyinstaller"]
        )

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--console",
        "--name", "pc-cleanup-cli",
        "--clean",
        "--add-data", "pc_cleanup:pc_cleanup",
        "main.py",
    ]

    print("Build CLI en cours...")
    subprocess.check_call(cmd)
    print("\nBuild terminé → dist/pc-cleanup-cli.exe")


if __name__ == "__main__":
    if "--cli" in sys.argv:
        build_cli()
    else:
        build()
