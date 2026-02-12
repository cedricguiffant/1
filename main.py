#!/usr/bin/env python3
"""PC Cleanup Tool - Point d'entrée principal."""

import sys


def main():
    """Lance l'application en mode GUI par défaut, ou CLI avec --cli."""
    if "--cli" in sys.argv:
        from pc_cleanup.cli import run
        run()
    else:
        from pc_cleanup.gui import launch_gui
        launch_gui()


if __name__ == "__main__":
    main()
