"""Interface CLI interactive pour PC Cleanup Tool."""

import os
import sys
import platform
from pathlib import Path

from pc_cleanup.modules import software_scanner, disk_analyzer, temp_cleaner, file_organizer


# -- Utilitaires d'affichage --------------------------------------------------

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def print_header(title):
    width = 60
    print()
    print("=" * width)
    print(f"  {title}".center(width))
    print("=" * width)
    print()


def print_separator():
    print("-" * 60)


def format_size(size_mb):
    if size_mb >= 1024:
        return f"{size_mb / 1024:.2f} Go"
    return f"{size_mb:.2f} Mo"


def progress_bar(percent, width=30):
    filled = int(width * percent / 100)
    bar = "#" * filled + "-" * (width - filled)
    return f"[{bar}] {percent:.1f}%"


def prompt_choice(prompt, max_val, allow_back=True):
    """Demande un choix numérique à l'utilisateur."""
    while True:
        extra = " (0: retour)" if allow_back else ""
        choice = input(f"\n{prompt}{extra}: ").strip()
        if choice == "0" and allow_back:
            return 0
        try:
            val = int(choice)
            if 1 <= val <= max_val:
                return val
        except ValueError:
            pass
        print(f"  Choix invalide. Entrez un nombre entre {'0' if allow_back else '1'} et {max_val}.")


def confirm(prompt):
    """Demande une confirmation oui/non."""
    while True:
        answer = input(f"{prompt} (o/n): ").strip().lower()
        if answer in ("o", "oui", "y", "yes"):
            return True
        if answer in ("n", "non", "no"):
            return False


# -- Menus principaux ---------------------------------------------------------

def main_menu():
    """Affiche le menu principal et retourne le choix."""
    clear_screen()
    print_header("PC CLEANUP TOOL v1.0")
    print(f"  Systeme: {platform.system()} {platform.release()}")
    print(f"  Machine: {platform.node()}")
    print()
    print_separator()
    print()
    print("  1. Logiciels installes - Scanner et desinstaller")
    print("  2. Espace disque      - Analyser l'utilisation")
    print("  3. Fichiers volumineux - Trouver les gros fichiers")
    print("  4. Fichiers doublons   - Detecter les duplicatas")
    print("  5. Fichiers temporaires - Scanner et nettoyer")
    print("  6. Organiser fichiers  - Trier par categorie")
    print("  7. Nettoyage rapide    - Tout scanner d'un coup")
    print("  8. Quitter")
    print()
    return prompt_choice("Votre choix", 8, allow_back=False)


# -- 1. Gestion des logiciels --------------------------------------------------

def software_menu():
    """Menu de gestion des logiciels installés."""
    clear_screen()
    print_header("LOGICIELS INSTALLES")
    print("  Scan en cours...")

    software = software_scanner.get_installed_software()

    if not software:
        print("  Aucun logiciel detecte (methode non supportee sur ce systeme).")
        input("\n  Appuyez sur Entree pour continuer...")
        return

    print(f"  {len(software)} logiciels detectes.")
    print()
    print("  1. Voir tous les logiciels")
    print("  2. Logiciels non utilises (> 90 jours)")
    print("  3. Logiciels non utilises (> 180 jours)")
    print("  4. Trier par taille (plus gros en premier)")
    print("  5. Desinstaller un logiciel")
    print()

    choice = prompt_choice("Votre choix", 5)
    if choice == 0:
        return

    if choice == 1:
        _display_software_list(software)
    elif choice == 2:
        _display_unused_software(90)
    elif choice == 3:
        _display_unused_software(180)
    elif choice == 4:
        software.sort(key=lambda x: x.get("size_kb", 0), reverse=True)
        _display_software_list(software)
    elif choice == 5:
        _uninstall_software_interactive(software)


def _display_software_list(software):
    """Affiche une liste de logiciels."""
    clear_screen()
    print_header("LISTE DES LOGICIELS")
    print(f"  {'Nom':<35} {'Taille':>10} {'Derniere utilisation':>20}")
    print_separator()
    for sw in software:
        name = sw["name"][:34]
        size = format_size(sw.get("size_kb", 0) / 1024)
        last_used = sw.get("last_used", "Inconnu") or "Inconnu"
        print(f"  {name:<35} {size:>10} {last_used:>20}")

    print()
    print(f"  Total: {len(software)} logiciels")
    input("\n  Appuyez sur Entree pour continuer...")


def _display_unused_software(days):
    """Affiche les logiciels non utilisés."""
    clear_screen()
    print_header(f"LOGICIELS NON UTILISES (> {days} JOURS)")

    unused, unknown = software_scanner.find_unused_software(days)

    if not unused:
        print(f"  Aucun logiciel detecte comme inutilise depuis {days} jours.")
    else:
        total_size = sum(sw.get("size_kb", 0) for sw in unused) / 1024
        print(f"  {len(unused)} logiciels non utilises - {format_size(total_size)} recuperables")
        print()
        print(f"  {'#':<4} {'Nom':<30} {'Taille':>10} {'Jours':>8}")
        print_separator()
        for i, sw in enumerate(unused, 1):
            name = sw["name"][:29]
            size = format_size(sw.get("size_kb", 0) / 1024)
            days_unused = sw.get("days_unused", "?")
            print(f"  {i:<4} {name:<30} {size:>10} {days_unused:>8}")

    if unknown:
        print(f"\n  + {len(unknown)} logiciels avec date d'utilisation inconnue.")

    input("\n  Appuyez sur Entree pour continuer...")


def _uninstall_software_interactive(software):
    """Interface interactive de désinstallation."""
    clear_screen()
    print_header("DESINSTALLER UN LOGICIEL")

    for i, sw in enumerate(software[:30], 1):
        print(f"  {i:>3}. {sw['name'][:45]}")

    print()
    choice = prompt_choice("Numero du logiciel a desinstaller", min(30, len(software)))
    if choice == 0:
        return

    sw = software[choice - 1]
    print(f"\n  Logiciel: {sw['name']}")
    print(f"  Commande: {sw.get('uninstall_command', 'N/A')}")

    if not sw.get("uninstall_command"):
        print("  Pas de commande de desinstallation disponible.")
        input("\n  Appuyez sur Entree pour continuer...")
        return

    if confirm(f"  Confirmer la desinstallation de '{sw['name']}'?"):
        print("  Desinstallation en cours...")
        success, msg = software_scanner.uninstall_software(sw["uninstall_command"])
        print(f"  Resultat: {msg}")

    input("\n  Appuyez sur Entree pour continuer...")


# -- 2. Analyse disque --------------------------------------------------------

def disk_analysis_menu():
    """Menu d'analyse de l'espace disque."""
    clear_screen()
    print_header("ANALYSE DE L'ESPACE DISQUE")

    partitions = disk_analyzer.get_disk_usage()

    if not partitions:
        print("  Impossible de lire les informations disque.")
        input("\n  Appuyez sur Entree pour continuer...")
        return

    for p in partitions:
        print(f"  {p['mount']}")
        print(f"    {progress_bar(p['percent_used'])}")
        print(f"    Utilise: {p['used_gb']:.1f} Go / {p['total_gb']:.1f} Go  "
              f"(Libre: {p['free_gb']:.1f} Go)")
        print()

    print_separator()
    print()
    print("  1. Analyser les tailles des sous-repertoires")
    print("  2. Retour")
    print()

    choice = prompt_choice("Votre choix", 2)
    if choice == 1:
        _analyze_directory_sizes()


def _analyze_directory_sizes():
    """Analyse les tailles des sous-répertoires."""
    default_dir = str(Path.home())
    dir_input = input(f"\n  Repertoire a analyser [{default_dir}]: ").strip()
    directory = dir_input if dir_input else default_dir

    print(f"\n  Analyse de {directory} en cours...")
    dir_sizes = disk_analyzer.get_directory_sizes(directory)

    if not dir_sizes:
        print("  Aucun sous-repertoire trouve.")
    else:
        clear_screen()
        print_header(f"TAILLE DES SOUS-REPERTOIRES: {directory}")
        print(f"  {'Repertoire':<40} {'Taille':>15}")
        print_separator()
        for d in dir_sizes[:20]:
            name = d["name"][:39]
            size = format_size(d["size_mb"])
            print(f"  {name:<40} {size:>15}")

    input("\n  Appuyez sur Entree pour continuer...")


# -- 3. Fichiers volumineux ---------------------------------------------------

def large_files_menu():
    """Menu de recherche de fichiers volumineux."""
    clear_screen()
    print_header("FICHIERS VOLUMINEUX")

    default_dir = str(Path.home())
    dir_input = input(f"  Repertoire a scanner [{default_dir}]: ").strip()
    directory = dir_input if dir_input else default_dir

    size_input = input("  Taille minimum en Mo [100]: ").strip()
    min_size = int(size_input) if size_input.isdigit() else 100

    print(f"\n  Recherche des fichiers > {min_size} Mo dans {directory}...")
    large_files = disk_analyzer.find_large_files(directory, min_size_mb=min_size)

    if not large_files:
        print(f"  Aucun fichier superieur a {min_size} Mo trouve.")
    else:
        clear_screen()
        print_header(f"FICHIERS > {min_size} Mo")
        total_size = sum(f["size_mb"] for f in large_files)
        print(f"  {len(large_files)} fichiers trouves - Total: {format_size(total_size)}")
        print()
        print(f"  {'#':>3} {'Taille':>10} {'Dernier acces':>14} {'Chemin'}")
        print_separator()
        for i, f in enumerate(large_files, 1):
            size = format_size(f["size_mb"])
            print(f"  {i:>3} {size:>10} {f['last_accessed']:>14} {f['path'][:60]}")

        print()
        if confirm("  Voulez-vous supprimer certains fichiers?"):
            _delete_files_interactive(large_files)

    input("\n  Appuyez sur Entree pour continuer...")


def _delete_files_interactive(files):
    """Suppression interactive de fichiers."""
    nums = input("  Numeros des fichiers a supprimer (ex: 1,3,5): ").strip()
    try:
        indices = [int(n.strip()) - 1 for n in nums.split(",")]
    except ValueError:
        print("  Format invalide.")
        return

    to_delete = [files[i] for i in indices if 0 <= i < len(files)]

    if not to_delete:
        print("  Aucun fichier selectionne.")
        return

    print(f"\n  {len(to_delete)} fichiers a supprimer:")
    for f in to_delete:
        print(f"    - {f['path']} ({format_size(f['size_mb'])})")

    if confirm("\n  Confirmer la suppression?"):
        for f in to_delete:
            try:
                Path(f["path"]).unlink()
                print(f"    Supprime: {f['path']}")
            except OSError as e:
                print(f"    Erreur: {f['path']}: {e}")


# -- 4. Fichiers doublons -----------------------------------------------------

def duplicates_menu():
    """Menu de détection des fichiers doublons."""
    clear_screen()
    print_header("DETECTION DES DOUBLONS")

    default_dir = str(Path.home())
    dir_input = input(f"  Repertoire a scanner [{default_dir}]: ").strip()
    directory = dir_input if dir_input else default_dir

    print(f"\n  Recherche des doublons dans {directory}...")
    print("  (Cela peut prendre du temps selon la taille du repertoire)")
    duplicates = disk_analyzer.find_duplicate_files(directory)

    if not duplicates:
        print("  Aucun doublon detecte.")
    else:
        total_wasted = sum(d["wasted_mb"] for d in duplicates)
        clear_screen()
        print_header("DOUBLONS DETECTES")
        print(f"  {len(duplicates)} groupes de doublons - {format_size(total_wasted)} gaspilles")
        print()
        for i, dup in enumerate(duplicates[:20], 1):
            print(f"  Groupe {i} - {dup['count']} copies - "
                  f"{format_size(dup['size_mb'])} chacun "
                  f"({format_size(dup['wasted_mb'])} gaspilles)")
            for f in dup["files"]:
                print(f"    -> {f}")
            print()

    input("\n  Appuyez sur Entree pour continuer...")


# -- 5. Fichiers temporaires --------------------------------------------------

def temp_files_menu():
    """Menu de gestion des fichiers temporaires."""
    clear_screen()
    print_header("FICHIERS TEMPORAIRES")

    print("  Scan des fichiers temporaires...")
    temp_report = temp_cleaner.scan_temp_files()
    browser_report = temp_cleaner.scan_browser_caches()

    print(f"\n  Fichiers temporaires: {format_size(temp_report['total_size_mb'])} "
          f"({temp_report['total_files']} fichiers)")

    if temp_report["directories"]:
        for d in temp_report["directories"]:
            print(f"    {d['path']}: {format_size(d['size_mb'])} ({d['file_count']} fichiers)")

    print(f"\n  Caches navigateurs: {format_size(browser_report['total_size_mb'])}")
    if browser_report["browsers"]:
        for b in browser_report["browsers"]:
            print(f"    {b['browser']}: {format_size(b['size_mb'])}")

    total = temp_report["total_size_mb"] + browser_report["total_size_mb"]
    print(f"\n  Total recuperable: {format_size(total)}")

    print()
    print("  1. Nettoyer les fichiers temporaires")
    print("  2. Nettoyer les caches navigateurs")
    print("  3. Tout nettoyer")
    print("  4. Vider la corbeille")
    print()

    choice = prompt_choice("Votre choix", 4)
    if choice == 0:
        return

    if choice in (1, 3):
        if confirm("  Supprimer les fichiers temporaires?"):
            for d in temp_report["directories"]:
                result = temp_cleaner.clean_temp_directory(d["path"], dry_run=False)
                print(f"    {d['path']}: {result['deleted_files']} fichiers supprimes "
                      f"({format_size(result['deleted_size_mb'])})")

    if choice in (2, 3):
        if confirm("  Supprimer les caches navigateurs?"):
            for b in browser_report["browsers"]:
                result = temp_cleaner.clean_browser_cache(b["browser"], dry_run=False)
                print(f"    {b['browser']}: {result.get('deleted_files', 0)} fichiers supprimes")

    if choice == 4:
        if confirm("  Vider la corbeille?"):
            result = temp_cleaner.empty_recycle_bin(dry_run=False)
            print(f"    Corbeille videe: {format_size(result.get('deleted_size_mb', 0))}")

    input("\n  Appuyez sur Entree pour continuer...")


# -- 6. Organisation des fichiers ---------------------------------------------

def organize_menu():
    """Menu d'organisation des fichiers."""
    clear_screen()
    print_header("ORGANISER LES FICHIERS")

    default_dir = str(Path.home() / "Downloads") if (Path.home() / "Downloads").exists() else str(Path.home())
    dir_input = input(f"  Repertoire a organiser [{default_dir}]: ").strip()
    directory = dir_input if dir_input else default_dir

    print(f"\n  Analyse de {directory}...")
    categories = file_organizer.categorize_files(directory)

    if not categories:
        print("  Aucun fichier trouve.")
        input("\n  Appuyez sur Entree pour continuer...")
        return

    print(f"\n  {'Categorie':<20} {'Fichiers':>10} {'Taille':>15}")
    print_separator()
    for cat, info in sorted(categories.items(), key=lambda x: x[1]["total_size_mb"], reverse=True):
        print(f"  {cat:<20} {info['count']:>10} {format_size(info['total_size_mb']):>15}")

    print()
    print("  1. Organiser par categorie (Images, Videos, Documents...)")
    print("  2. Organiser par date (Annee/Mois)")
    print("  3. Simuler l'organisation (apercu sans deplacer)")
    print()

    choice = prompt_choice("Votre choix", 3)
    if choice == 0:
        return

    if choice == 1:
        if confirm(f"  Organiser {directory} par categorie?"):
            result = file_organizer.organize_files(directory, dry_run=False)
            print(f"\n  {result['moved_files']} fichiers deplaces.")
            if result["errors"]:
                print(f"  {len(result['errors'])} erreurs.")
    elif choice == 2:
        if confirm(f"  Organiser {directory} par date?"):
            result = file_organizer.organize_by_date(directory, dry_run=False)
            print(f"\n  {result['moved_files']} fichiers deplaces.")
            if result["errors"]:
                print(f"  {len(result['errors'])} erreurs.")
    elif choice == 3:
        print("\n  --- Simulation par categorie ---")
        result = file_organizer.organize_files(directory, dry_run=True)
        print(f"  {result['moved_files']} fichiers seraient deplaces:")
        for move in result["moves"][:15]:
            print(f"    {Path(move['from']).name} -> {move['category']}/")
        if len(result["moves"]) > 15:
            print(f"    ... et {len(result['moves']) - 15} autres")

    input("\n  Appuyez sur Entree pour continuer...")


# -- 7. Nettoyage rapide ------------------------------------------------------

def quick_cleanup():
    """Nettoyage rapide : scan complet en un seul passage."""
    clear_screen()
    print_header("NETTOYAGE RAPIDE - SCAN COMPLET")

    # 1. Espace disque
    print("  [1/5] Analyse de l'espace disque...")
    partitions = disk_analyzer.get_disk_usage()
    for p in partitions:
        print(f"    {p['mount']}: {progress_bar(p['percent_used'])} "
              f"({p['free_gb']:.1f} Go libre)")

    # 2. Fichiers temporaires
    print("\n  [2/5] Scan des fichiers temporaires...")
    temp_report = temp_cleaner.scan_temp_files()
    print(f"    {format_size(temp_report['total_size_mb'])} de fichiers temporaires")

    # 3. Caches navigateurs
    print("\n  [3/5] Scan des caches navigateurs...")
    browser_report = temp_cleaner.scan_browser_caches()
    print(f"    {format_size(browser_report['total_size_mb'])} de caches navigateurs")

    # 4. Logiciels inutilisés
    print("\n  [4/5] Scan des logiciels non utilises...")
    unused, _ = software_scanner.find_unused_software(90)
    if unused:
        total_sw_size = sum(sw.get("size_kb", 0) for sw in unused) / 1024
        print(f"    {len(unused)} logiciels non utilises ({format_size(total_sw_size)})")
    else:
        print("    Aucun logiciel inutilise detecte")

    # 5. Gros fichiers dans le dossier utilisateur
    print("\n  [5/5] Recherche de gros fichiers...")
    large_files = disk_analyzer.find_large_files(str(Path.home()), min_size_mb=500, max_results=10)
    if large_files:
        total_large = sum(f["size_mb"] for f in large_files)
        print(f"    {len(large_files)} fichiers > 500 Mo ({format_size(total_large)})")
    else:
        print("    Aucun fichier volumineux detecte")

    # Résumé
    total_recoverable = temp_report["total_size_mb"] + browser_report["total_size_mb"]
    print()
    print_separator()
    print(f"\n  RESUME: {format_size(total_recoverable)} facilement recuperables")
    print(f"    - Fichiers temporaires: {format_size(temp_report['total_size_mb'])}")
    print(f"    - Caches navigateurs:   {format_size(browser_report['total_size_mb'])}")

    if total_recoverable > 0 and confirm("\n  Lancer le nettoyage automatique?"):
        print("\n  Nettoyage en cours...")
        for d in temp_report["directories"]:
            temp_cleaner.clean_temp_directory(d["path"], dry_run=False)
        for b in browser_report["browsers"]:
            temp_cleaner.clean_browser_cache(b["browser"], dry_run=False)
        print(f"  Nettoyage termine. ~{format_size(total_recoverable)} recuperes.")

    input("\n  Appuyez sur Entree pour continuer...")


# -- Point d'entrée -----------------------------------------------------------

def run():
    """Point d'entrée principal de l'application CLI."""
    try:
        while True:
            choice = main_menu()

            if choice == 1:
                software_menu()
            elif choice == 2:
                disk_analysis_menu()
            elif choice == 3:
                large_files_menu()
            elif choice == 4:
                duplicates_menu()
            elif choice == 5:
                temp_files_menu()
            elif choice == 6:
                organize_menu()
            elif choice == 7:
                quick_cleanup()
            elif choice == 8:
                clear_screen()
                print("\n  Merci d'avoir utilise PC Cleanup Tool!")
                print("  Au revoir.\n")
                sys.exit(0)

    except KeyboardInterrupt:
        print("\n\n  Programme interrompu. Au revoir.")
        sys.exit(0)
