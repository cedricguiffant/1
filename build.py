#!/usr/bin/env python3
"""Script de build pour générer l'exécutable PC Cleanup Tool."""

import subprocess
import sys


def build():
    """Génère le .exe avec PyInstaller."""
    # Vérifier que PyInstaller est installé
    try:
        import PyInstaller
    except ImportError:
        print("Installation de PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",                    # Un seul fichier .exe
        "--console",                    # Application console (pas de fenêtre GUI)
        "--name", "pc-cleanup",         # Nom de l'exécutable
        "--clean",                      # Nettoyer le cache avant le build
        "main.py",                      # Point d'entrée
    ]

    print("Build en cours...")
    print(f"Commande: {' '.join(cmd)}")
    subprocess.check_call(cmd)
    print("\nBuild terminé! L'exécutable se trouve dans le dossier dist/")


if __name__ == "__main__":
    build()
