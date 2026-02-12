"""Permet l'exécution via `python -m pc_cleanup`."""

import sys


def main():
    if "--cli" in sys.argv:
        from pc_cleanup.cli import run
        run()
    else:
        from pc_cleanup.gui import launch_gui
        launch_gui()


if __name__ == "__main__":
    main()
