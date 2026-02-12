#!/usr/bin/env python3
"""PC Cleanup Tool - Interface graphique moderne."""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import platform
import sys

from pc_cleanup.modules import disk_analyzer, temp_cleaner, file_organizer, software_scanner

# ─── Couleurs du thème ──────────────────────────────────────────────────────
COLORS = {
    "bg_dark":       "#0f0f1a",
    "bg_sidebar":    "#141425",
    "bg_card":       "#1a1a2e",
    "bg_card_hover": "#222240",
    "bg_input":      "#12122a",
    "accent":        "#6c5ce7",
    "accent_light":  "#a29bfe",
    "accent_dark":   "#5a4bd1",
    "success":       "#00cec9",
    "warning":       "#fdcb6e",
    "danger":        "#ff7675",
    "text":          "#e8e8f0",
    "text_dim":      "#8888aa",
    "text_muted":    "#555577",
    "border":        "#2a2a45",
    "progress_bg":   "#1e1e35",
    "white":         "#ffffff",
}

# ─── Icônes Unicode ─────────────────────────────────────────────────────────
ICONS = {
    "dashboard":  "\u2302",   # ⌂
    "software":   "\u2699",   # ⚙
    "disk":       "\u25C9",   # ◉
    "large":      "\u25B2",   # ▲
    "duplicates": "\u2687",   # ⚇
    "temp":       "\u2672",   # ♲
    "organize":   "\u2630",   # ☰
    "quick":      "\u26A1",   # ⚡
    "folder":     "\u25A3",   # ▣
    "file":       "\u25A1",   # □
    "check":      "\u2714",   # ✔
    "cross":      "\u2718",   # ✘
    "arrow":      "\u25B6",   # ▶
    "refresh":    "\u27F3",   # ⟳
    "trash":      "\u2716",   # ✖
    "info":       "\u24D8",   # ⓘ
    "warning":    "\u26A0",   # ⚠
}


def format_size(size_mb):
    """Formate une taille en Mo ou Go."""
    if size_mb >= 1024:
        return f"{size_mb / 1024:.1f} Go"
    return f"{size_mb:.1f} Mo"


def format_size_gb(size_gb):
    """Formate une taille en Go ou To."""
    if size_gb >= 1024:
        return f"{size_gb / 1024:.1f} To"
    return f"{size_gb:.1f} Go"


# ─── Widget: Carte avec statistique ─────────────────────────────────────────
class StatCard(tk.Frame):
    """Carte affichant une statistique avec titre et icône."""

    def __init__(self, parent, title, value, icon="", color=None, **kwargs):
        super().__init__(parent, bg=COLORS["bg_card"], **kwargs)
        self.config(highlightbackground=COLORS["border"], highlightthickness=1)

        color = color or COLORS["accent"]
        pad = 18

        icon_label = tk.Label(
            self, text=icon, font=("Segoe UI", 24), fg=color,
            bg=COLORS["bg_card"],
        )
        icon_label.pack(anchor="w", padx=pad, pady=(pad, 4))

        val_label = tk.Label(
            self, text=str(value), font=("Segoe UI Semibold", 22),
            fg=COLORS["white"], bg=COLORS["bg_card"],
        )
        val_label.pack(anchor="w", padx=pad)
        self._val_label = val_label

        title_label = tk.Label(
            self, text=title, font=("Segoe UI", 10),
            fg=COLORS["text_dim"], bg=COLORS["bg_card"],
        )
        title_label.pack(anchor="w", padx=pad, pady=(2, pad))

    def set_value(self, value):
        self._val_label.config(text=str(value))


# ─── Widget: Barre de progression circulaire simulée ────────────────────────
class ProgressRing(tk.Canvas):
    """Cercle de progression en pourcentage."""

    def __init__(self, parent, size=120, width=10, **kwargs):
        super().__init__(
            parent, width=size, height=size,
            bg=COLORS["bg_card"], highlightthickness=0, **kwargs,
        )
        self._size = size
        self._width = width
        self._percent = 0
        self._text_id = None
        self._arc_bg = None
        self._arc_fg = None
        self._draw()

    def _draw(self):
        s = self._size
        w = self._width
        pad = w + 4
        self._arc_bg = self.create_arc(
            pad, pad, s - pad, s - pad,
            start=90, extent=-360, style="arc",
            outline=COLORS["progress_bg"], width=w,
        )
        self._arc_fg = self.create_arc(
            pad, pad, s - pad, s - pad,
            start=90, extent=0, style="arc",
            outline=COLORS["accent"], width=w,
        )
        self._text_id = self.create_text(
            s // 2, s // 2, text="0%",
            font=("Segoe UI Semibold", 16), fill=COLORS["white"],
        )

    def set_percent(self, percent, color=None):
        self._percent = percent
        extent = -3.6 * percent
        self.itemconfig(self._arc_fg, extent=extent)
        if color:
            self.itemconfig(self._arc_fg, outline=color)
        self.itemconfig(self._text_id, text=f"{percent:.0f}%")


# ─── Widget: Bouton stylisé ─────────────────────────────────────────────────
class StyledButton(tk.Frame):
    """Bouton avec style moderne arrondi."""

    def __init__(self, parent, text, command=None, color=None,
                 icon="", width=None, **kwargs):
        super().__init__(parent, bg=parent["bg"], **kwargs)
        color = color or COLORS["accent"]

        label_text = f"{icon}  {text}" if icon else text
        self._btn = tk.Label(
            self, text=label_text, font=("Segoe UI Semibold", 10),
            fg=COLORS["white"], bg=color,
            padx=20, pady=8, cursor="hand2",
        )
        if width:
            self._btn.config(width=width)
        self._btn.pack(fill="x")

        self._color = color
        self._command = command

        self._btn.bind("<Enter>", self._on_enter)
        self._btn.bind("<Leave>", self._on_leave)
        self._btn.bind("<Button-1>", self._on_click)

    def _on_enter(self, _):
        # Lighten the color
        self._btn.config(bg=COLORS.get("accent_light", self._color))

    def _on_leave(self, _):
        self._btn.config(bg=self._color)

    def _on_click(self, _):
        if self._command:
            self._command()

    def set_enabled(self, enabled):
        if enabled:
            self._btn.config(fg=COLORS["white"], cursor="hand2")
            self._btn.bind("<Button-1>", self._on_click)
        else:
            self._btn.config(fg=COLORS["text_muted"], cursor="")
            self._btn.unbind("<Button-1>")


# ─── Widget: Barre de progression plate ─────────────────────────────────────
class FlatProgressBar(tk.Canvas):
    """Barre de progression plate et animée."""

    def __init__(self, parent, height=6, **kwargs):
        super().__init__(
            parent, height=height, bg=COLORS["progress_bg"],
            highlightthickness=0, **kwargs,
        )
        self._rect = None
        self._height = height
        self.bind("<Configure>", self._on_resize)

    def _on_resize(self, event):
        self.set_progress(getattr(self, "_last_pct", 0))

    def set_progress(self, percent, color=None):
        self._last_pct = percent
        self.delete("all")
        w = self.winfo_width()
        h = self._height
        color = color or COLORS["accent"]
        if percent > 0:
            fill_w = max(1, int(w * percent / 100))
            self.create_rectangle(0, 0, fill_w, h, fill=color, outline="")


# ─── Page de base ───────────────────────────────────────────────────────────
class Page(tk.Frame):
    """Classe de base pour les pages de l'application."""

    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS["bg_dark"])
        self.app = app

    def on_show(self):
        """Appelé quand la page devient visible."""
        pass

    def run_threaded(self, target, callback=None):
        """Exécute une fonction dans un thread séparé."""
        def wrapper():
            try:
                result = target()
                if callback:
                    self.after(0, lambda: callback(result))
            except Exception as e:
                self.after(0, lambda: self._show_error(str(e)))
        t = threading.Thread(target=wrapper, daemon=True)
        t.start()

    def _show_error(self, msg):
        messagebox.showerror("Erreur", msg)

    def create_title(self, text, icon=""):
        """Crée un titre de page."""
        frame = tk.Frame(self, bg=COLORS["bg_dark"])
        frame.pack(fill="x", padx=30, pady=(25, 5))
        label = tk.Label(
            frame, text=f"{icon}  {text}" if icon else text,
            font=("Segoe UI Semibold", 20), fg=COLORS["white"],
            bg=COLORS["bg_dark"], anchor="w",
        )
        label.pack(side="left")
        return frame

    def create_subtitle(self, text):
        """Crée un sous-titre."""
        label = tk.Label(
            self, text=text, font=("Segoe UI", 10),
            fg=COLORS["text_dim"], bg=COLORS["bg_dark"], anchor="w",
        )
        label.pack(fill="x", padx=30, pady=(0, 15))
        return label

    def create_card(self, parent=None):
        """Crée un conteneur carte."""
        parent = parent or self
        card = tk.Frame(
            parent, bg=COLORS["bg_card"],
            highlightbackground=COLORS["border"], highlightthickness=1,
        )
        return card

    def create_scrollable(self, parent=None):
        """Crée un conteneur scrollable."""
        parent = parent or self
        container = tk.Frame(parent, bg=COLORS["bg_dark"])

        canvas = tk.Canvas(container, bg=COLORS["bg_dark"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=COLORS["bg_dark"])

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Molette de souris
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _on_linux_scroll_up(event):
            canvas.yview_scroll(-3, "units")

        def _on_linux_scroll_down(event):
            canvas.yview_scroll(3, "units")

        canvas.bind("<MouseWheel>", _on_mousewheel)
        canvas.bind("<Button-4>", _on_linux_scroll_up)
        canvas.bind("<Button-5>", _on_linux_scroll_down)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self._scroll_canvas = canvas
        self._scroll_frame = scroll_frame
        return container, scroll_frame


# ─── Page: Tableau de bord ──────────────────────────────────────────────────
class DashboardPage(Page):

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.create_title("Tableau de bord", ICONS["dashboard"])
        self.create_subtitle("Vue d'ensemble de votre système")

        # Conteneur scrollable
        container, self.scroll = self.create_scrollable()
        container.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        # Cartes statistiques
        self.cards_frame = tk.Frame(self.scroll, bg=COLORS["bg_dark"])
        self.cards_frame.pack(fill="x", pady=(0, 20))

        self.card_os = StatCard(
            self.cards_frame, "Système", platform.system(),
            ICONS["info"], COLORS["accent"],
        )
        self.card_os.pack(side="left", fill="both", expand=True, padx=(0, 10))

        self.card_disks = StatCard(
            self.cards_frame, "Partitions", "...",
            ICONS["disk"], COLORS["success"],
        )
        self.card_disks.pack(side="left", fill="both", expand=True, padx=(0, 10))

        self.card_temp = StatCard(
            self.cards_frame, "Fichiers temporaires", "...",
            ICONS["temp"], COLORS["warning"],
        )
        self.card_temp.pack(side="left", fill="both", expand=True, padx=(0, 10))

        self.card_recover = StatCard(
            self.cards_frame, "Espace récupérable", "...",
            ICONS["trash"], COLORS["danger"],
        )
        self.card_recover.pack(side="left", fill="both", expand=True)

        # Section disques
        self.disk_section = tk.Frame(self.scroll, bg=COLORS["bg_dark"])
        self.disk_section.pack(fill="x", pady=(0, 15))

        disk_header = tk.Label(
            self.disk_section,
            text=f"{ICONS['disk']}  Utilisation des disques",
            font=("Segoe UI Semibold", 13), fg=COLORS["white"],
            bg=COLORS["bg_dark"], anchor="w",
        )
        disk_header.pack(fill="x", pady=(0, 10))

        self.disk_bars_frame = tk.Frame(self.disk_section, bg=COLORS["bg_dark"])
        self.disk_bars_frame.pack(fill="x")

        # Section scan rapide
        actions_card = self.create_card(self.scroll)
        actions_card.pack(fill="x", pady=(0, 15))

        actions_title = tk.Label(
            actions_card,
            text=f"{ICONS['quick']}  Actions rapides",
            font=("Segoe UI Semibold", 13), fg=COLORS["white"],
            bg=COLORS["bg_card"], anchor="w",
        )
        actions_title.pack(fill="x", padx=18, pady=(18, 10))

        btn_frame = tk.Frame(actions_card, bg=COLORS["bg_card"])
        btn_frame.pack(fill="x", padx=18, pady=(0, 18))

        StyledButton(
            btn_frame, "Scanner les fichiers temporaires",
            command=lambda: app.show_page("temp"), icon=ICONS["temp"],
        ).pack(side="left", padx=(0, 10))

        StyledButton(
            btn_frame, "Organiser les fichiers",
            command=lambda: app.show_page("organize"), icon=ICONS["organize"],
        ).pack(side="left", padx=(0, 10))

        StyledButton(
            btn_frame, "Trouver les gros fichiers",
            command=lambda: app.show_page("large"), icon=ICONS["large"],
            color=COLORS["warning"],
        ).pack(side="left")

        # Chargement
        self.loading_label = tk.Label(
            self.scroll, text="Chargement des données...",
            font=("Segoe UI", 10), fg=COLORS["text_dim"],
            bg=COLORS["bg_dark"],
        )
        self.loading_label.pack(pady=10)

    def on_show(self):
        self.loading_label.config(text="Chargement des données...")
        self.run_threaded(self._load_data, self._update_ui)

    def _load_data(self):
        disks = disk_analyzer.get_disk_usage()
        temp_data = temp_cleaner.scan_temp_files()
        cache_data = temp_cleaner.scan_browser_caches()
        return disks, temp_data, cache_data

    def _update_ui(self, data):
        disks, temp_data, cache_data = data
        self.loading_label.config(text="")

        # Mise à jour cartes
        self.card_disks.set_value(str(len(disks)))

        temp_total = temp_data.get("total_size_mb", 0)
        cache_total = cache_data.get("total_size_mb", 0)
        self.card_temp.set_value(format_size(temp_total))
        self.card_recover.set_value(format_size(temp_total + cache_total))

        # Barres disques
        for w in self.disk_bars_frame.winfo_children():
            w.destroy()

        for d in disks:
            row = tk.Frame(self.disk_bars_frame, bg=COLORS["bg_card"],
                           highlightbackground=COLORS["border"],
                           highlightthickness=1)
            row.pack(fill="x", pady=(0, 8))

            info_frame = tk.Frame(row, bg=COLORS["bg_card"])
            info_frame.pack(fill="x", padx=15, pady=(12, 4))

            tk.Label(
                info_frame, text=d["mount"],
                font=("Segoe UI Semibold", 11), fg=COLORS["white"],
                bg=COLORS["bg_card"],
            ).pack(side="left")

            tk.Label(
                info_frame,
                text=f"{format_size_gb(d['used_gb'])} / {format_size_gb(d['total_gb'])}",
                font=("Segoe UI", 10), fg=COLORS["text_dim"],
                bg=COLORS["bg_card"],
            ).pack(side="right")

            bar = FlatProgressBar(row, height=8)
            bar.pack(fill="x", padx=15, pady=(0, 12))

            pct = d["percent_used"]
            color = COLORS["success"] if pct < 70 else (
                COLORS["warning"] if pct < 90 else COLORS["danger"]
            )
            self.after(100, lambda b=bar, p=pct, c=color: b.set_progress(p, c))


# ─── Page: Logiciels ────────────────────────────────────────────────────────
class SoftwarePage(Page):

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.create_title("Logiciels installés", ICONS["software"])
        self.create_subtitle("Scannez et gérez les logiciels de votre système")

        # Toolbar
        toolbar = tk.Frame(self, bg=COLORS["bg_dark"])
        toolbar.pack(fill="x", padx=30, pady=(0, 10))

        StyledButton(
            toolbar, "Scanner", command=self._scan,
            icon=ICONS["refresh"],
        ).pack(side="left", padx=(0, 10))

        StyledButton(
            toolbar, "Logiciels non utilisés (90j)",
            command=self._scan_unused, icon=ICONS["warning"],
            color=COLORS["warning"],
        ).pack(side="left")

        self.status = tk.Label(
            toolbar, text="", font=("Segoe UI", 10),
            fg=COLORS["text_dim"], bg=COLORS["bg_dark"],
        )
        self.status.pack(side="right")

        # Tableau
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Dark.Treeview",
            background=COLORS["bg_card"],
            foreground=COLORS["text"],
            fieldbackground=COLORS["bg_card"],
            borderwidth=0,
            font=("Segoe UI", 10),
            rowheight=32,
        )
        style.configure(
            "Dark.Treeview.Heading",
            background=COLORS["bg_sidebar"],
            foreground=COLORS["text_dim"],
            font=("Segoe UI Semibold", 10),
            borderwidth=0,
        )
        style.map("Dark.Treeview", background=[("selected", COLORS["accent_dark"])])

        tree_frame = tk.Frame(self, bg=COLORS["bg_dark"])
        tree_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        columns = ("name", "size", "install_date", "last_used")
        self.tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings",
            style="Dark.Treeview",
        )
        self.tree.heading("name", text="Nom")
        self.tree.heading("size", text="Taille")
        self.tree.heading("install_date", text="Installé le")
        self.tree.heading("last_used", text="Dernière utilisation")

        self.tree.column("name", width=300)
        self.tree.column("size", width=100, anchor="e")
        self.tree.column("install_date", width=120, anchor="center")
        self.tree.column("last_used", width=140, anchor="center")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical",
                                  command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _scan(self):
        self.status.config(text="Scan en cours...")
        for row in self.tree.get_children():
            self.tree.delete(row)
        self.run_threaded(software_scanner.get_installed_software, self._show_results)

    def _scan_unused(self):
        self.status.config(text="Recherche des logiciels non utilisés...")
        for row in self.tree.get_children():
            self.tree.delete(row)

        def task():
            return software_scanner.find_unused_software(90)

        self.run_threaded(task, self._show_unused_results)

    def _show_results(self, software_list):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for s in sorted(software_list, key=lambda x: x.get("name", "")):
            size = s.get("size_kb", 0)
            size_str = format_size(size / 1024) if size else "—"
            self.tree.insert("", "end", values=(
                s.get("name", "Inconnu"),
                size_str,
                s.get("install_date", "—") or "—",
                s.get("last_used", "—") or "—",
            ))
        self.status.config(text=f"{len(software_list)} logiciels trouvés")

    def _show_unused_results(self, result):
        unused, unknown = result
        for row in self.tree.get_children():
            self.tree.delete(row)
        for s in unused:
            size = s.get("size_kb", 0)
            size_str = format_size(size / 1024) if size else "—"
            days = s.get("days_unused", "?")
            self.tree.insert("", "end", values=(
                s.get("name", "Inconnu"),
                size_str,
                s.get("install_date", "—") or "—",
                f"Non utilisé ({days}j)",
            ))
        self.status.config(
            text=f"{len(unused)} non utilisés, {len(unknown)} date inconnue"
        )


# ─── Page: Analyse disque ───────────────────────────────────────────────────
class DiskPage(Page):

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.create_title("Analyse de l'espace disque", ICONS["disk"])
        self.create_subtitle("Visualisez l'utilisation par dossier")

        toolbar = tk.Frame(self, bg=COLORS["bg_dark"])
        toolbar.pack(fill="x", padx=30, pady=(0, 10))

        tk.Label(
            toolbar, text="Dossier :", font=("Segoe UI", 10),
            fg=COLORS["text_dim"], bg=COLORS["bg_dark"],
        ).pack(side="left")

        self.path_var = tk.StringVar(value=os.path.expanduser("~"))
        entry = tk.Entry(
            toolbar, textvariable=self.path_var,
            font=("Segoe UI", 10), bg=COLORS["bg_input"],
            fg=COLORS["text"], insertbackground=COLORS["text"],
            relief="flat", highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        entry.pack(side="left", fill="x", expand=True, padx=10, ipady=6)

        StyledButton(
            toolbar, "Parcourir", command=self._browse,
            icon=ICONS["folder"],
        ).pack(side="left", padx=(0, 10))

        StyledButton(
            toolbar, "Analyser", command=self._analyze,
            icon=ICONS["arrow"], color=COLORS["success"],
        ).pack(side="left")

        self.status = tk.Label(
            self, text="", font=("Segoe UI", 10),
            fg=COLORS["text_dim"], bg=COLORS["bg_dark"],
        )
        self.status.pack(fill="x", padx=30)

        # Résultats
        container, self.scroll = self.create_scrollable()
        container.pack(fill="both", expand=True, padx=30, pady=(10, 20))

    def _browse(self):
        path = filedialog.askdirectory()
        if path:
            self.path_var.set(path)

    def _analyze(self):
        path = self.path_var.get()
        if not os.path.isdir(path):
            messagebox.showwarning("Attention", "Dossier invalide.")
            return
        self.status.config(text="Analyse en cours...")
        for w in self.scroll.winfo_children():
            w.destroy()

        def task():
            return disk_analyzer.get_directory_sizes(path, depth=1)

        self.run_threaded(task, self._show_results)

    def _show_results(self, dirs):
        self.status.config(text=f"{len(dirs)} dossiers analysés")
        if not dirs:
            tk.Label(
                self.scroll, text="Aucun sous-dossier trouvé.",
                font=("Segoe UI", 11), fg=COLORS["text_dim"],
                bg=COLORS["bg_dark"],
            ).pack(pady=20)
            return

        max_size = max(d["size_mb"] for d in dirs) if dirs else 1

        for d in dirs[:30]:
            row = tk.Frame(self.scroll, bg=COLORS["bg_card"],
                           highlightbackground=COLORS["border"],
                           highlightthickness=1)
            row.pack(fill="x", pady=(0, 4))

            info = tk.Frame(row, bg=COLORS["bg_card"])
            info.pack(fill="x", padx=12, pady=(8, 2))

            tk.Label(
                info, text=d["name"], font=("Segoe UI", 10),
                fg=COLORS["text"], bg=COLORS["bg_card"],
            ).pack(side="left")

            tk.Label(
                info, text=format_size(d["size_mb"]),
                font=("Segoe UI Semibold", 10),
                fg=COLORS["accent_light"], bg=COLORS["bg_card"],
            ).pack(side="right")

            bar = FlatProgressBar(row, height=4)
            bar.pack(fill="x", padx=12, pady=(0, 8))
            pct = (d["size_mb"] / max_size * 100) if max_size > 0 else 0
            self.after(50, lambda b=bar, p=pct: b.set_progress(p, COLORS["accent"]))


# ─── Page: Gros fichiers ────────────────────────────────────────────────────
class LargeFilesPage(Page):

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.create_title("Gros fichiers", ICONS["large"])
        self.create_subtitle("Trouvez les fichiers les plus volumineux")

        toolbar = tk.Frame(self, bg=COLORS["bg_dark"])
        toolbar.pack(fill="x", padx=30, pady=(0, 10))

        tk.Label(
            toolbar, text="Dossier :", font=("Segoe UI", 10),
            fg=COLORS["text_dim"], bg=COLORS["bg_dark"],
        ).pack(side="left")

        self.path_var = tk.StringVar(value=os.path.expanduser("~"))
        tk.Entry(
            toolbar, textvariable=self.path_var,
            font=("Segoe UI", 10), bg=COLORS["bg_input"],
            fg=COLORS["text"], insertbackground=COLORS["text"],
            relief="flat", highlightbackground=COLORS["border"],
            highlightthickness=1,
        ).pack(side="left", fill="x", expand=True, padx=10, ipady=6)

        StyledButton(
            toolbar, "Parcourir", command=self._browse,
            icon=ICONS["folder"],
        ).pack(side="left", padx=(0, 10))

        # Taille minimum
        tk.Label(
            toolbar, text="Min :", font=("Segoe UI", 10),
            fg=COLORS["text_dim"], bg=COLORS["bg_dark"],
        ).pack(side="left")

        self.min_size_var = tk.StringVar(value="50")
        tk.Entry(
            toolbar, textvariable=self.min_size_var, width=6,
            font=("Segoe UI", 10), bg=COLORS["bg_input"],
            fg=COLORS["text"], insertbackground=COLORS["text"],
            relief="flat", highlightbackground=COLORS["border"],
            highlightthickness=1,
        ).pack(side="left", padx=(5, 2), ipady=6)

        tk.Label(
            toolbar, text="Mo", font=("Segoe UI", 10),
            fg=COLORS["text_dim"], bg=COLORS["bg_dark"],
        ).pack(side="left", padx=(0, 10))

        StyledButton(
            toolbar, "Chercher", command=self._search,
            icon=ICONS["arrow"], color=COLORS["warning"],
        ).pack(side="left")

        self.status = tk.Label(
            self, text="", font=("Segoe UI", 10),
            fg=COLORS["text_dim"], bg=COLORS["bg_dark"],
        )
        self.status.pack(fill="x", padx=30)

        # Tableau
        tree_frame = tk.Frame(self, bg=COLORS["bg_dark"])
        tree_frame.pack(fill="both", expand=True, padx=30, pady=(10, 20))

        columns = ("path", "size", "modified", "ext")
        self.tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings",
            style="Dark.Treeview",
        )
        self.tree.heading("path", text="Fichier")
        self.tree.heading("size", text="Taille")
        self.tree.heading("modified", text="Modifié le")
        self.tree.heading("ext", text="Type")

        self.tree.column("path", width=400)
        self.tree.column("size", width=100, anchor="e")
        self.tree.column("modified", width=120, anchor="center")
        self.tree.column("ext", width=80, anchor="center")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical",
                                  command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _browse(self):
        path = filedialog.askdirectory()
        if path:
            self.path_var.set(path)

    def _search(self):
        path = self.path_var.get()
        if not os.path.isdir(path):
            messagebox.showwarning("Attention", "Dossier invalide.")
            return
        try:
            min_size = int(self.min_size_var.get())
        except ValueError:
            min_size = 50

        self.status.config(text="Recherche en cours...")
        for row in self.tree.get_children():
            self.tree.delete(row)

        def task():
            return disk_analyzer.find_large_files(path, min_size_mb=min_size)

        self.run_threaded(task, self._show_results)

    def _show_results(self, files):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for f in files:
            name = os.path.basename(f["path"])
            self.tree.insert("", "end", values=(
                name,
                format_size(f["size_mb"]),
                f.get("last_modified", "—"),
                f.get("extension", "—"),
            ))
        total = sum(f["size_mb"] for f in files)
        self.status.config(
            text=f"{len(files)} fichiers trouvés — Total : {format_size(total)}"
        )


# ─── Page: Doublons ─────────────────────────────────────────────────────────
class DuplicatesPage(Page):

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.create_title("Fichiers en double", ICONS["duplicates"])
        self.create_subtitle("Détectez les doublons par empreinte SHA-256")

        toolbar = tk.Frame(self, bg=COLORS["bg_dark"])
        toolbar.pack(fill="x", padx=30, pady=(0, 10))

        tk.Label(
            toolbar, text="Dossier :", font=("Segoe UI", 10),
            fg=COLORS["text_dim"], bg=COLORS["bg_dark"],
        ).pack(side="left")

        self.path_var = tk.StringVar(value=os.path.expanduser("~"))
        tk.Entry(
            toolbar, textvariable=self.path_var,
            font=("Segoe UI", 10), bg=COLORS["bg_input"],
            fg=COLORS["text"], insertbackground=COLORS["text"],
            relief="flat", highlightbackground=COLORS["border"],
            highlightthickness=1,
        ).pack(side="left", fill="x", expand=True, padx=10, ipady=6)

        StyledButton(
            toolbar, "Parcourir", command=self._browse,
            icon=ICONS["folder"],
        ).pack(side="left", padx=(0, 10))

        StyledButton(
            toolbar, "Scanner", command=self._scan,
            icon=ICONS["arrow"], color=COLORS["danger"],
        ).pack(side="left")

        self.status = tk.Label(
            self, text="", font=("Segoe UI", 10),
            fg=COLORS["text_dim"], bg=COLORS["bg_dark"],
        )
        self.status.pack(fill="x", padx=30)

        # Résultats
        container, self.scroll = self.create_scrollable()
        container.pack(fill="both", expand=True, padx=30, pady=(10, 20))

    def _browse(self):
        path = filedialog.askdirectory()
        if path:
            self.path_var.set(path)

    def _scan(self):
        path = self.path_var.get()
        if not os.path.isdir(path):
            messagebox.showwarning("Attention", "Dossier invalide.")
            return
        self.status.config(text="Analyse en cours (peut être long)...")
        for w in self.scroll.winfo_children():
            w.destroy()

        def task():
            return disk_analyzer.find_duplicate_files(path)

        self.run_threaded(task, self._show_results)

    def _show_results(self, groups):
        self.status.config(text="")
        for w in self.scroll.winfo_children():
            w.destroy()

        if not groups:
            tk.Label(
                self.scroll, text=f"{ICONS['check']}  Aucun doublon trouvé !",
                font=("Segoe UI", 13), fg=COLORS["success"],
                bg=COLORS["bg_dark"],
            ).pack(pady=30)
            return

        total_wasted = sum(g["wasted_mb"] for g in groups)
        summary = tk.Label(
            self.scroll,
            text=(f"{len(groups)} groupes de doublons — "
                  f"Espace gaspillé : {format_size(total_wasted)}"),
            font=("Segoe UI Semibold", 12), fg=COLORS["warning"],
            bg=COLORS["bg_dark"],
        )
        summary.pack(pady=(0, 15))

        for g in groups[:50]:
            card = self.create_card(self.scroll)
            card.pack(fill="x", pady=(0, 8))

            header = tk.Frame(card, bg=COLORS["bg_card"])
            header.pack(fill="x", padx=15, pady=(12, 6))

            tk.Label(
                header,
                text=f"{g['count']} copies — {format_size(g['size_mb'])} chacun",
                font=("Segoe UI Semibold", 11), fg=COLORS["accent_light"],
                bg=COLORS["bg_card"],
            ).pack(side="left")

            tk.Label(
                header,
                text=f"Gaspillé : {format_size(g['wasted_mb'])}",
                font=("Segoe UI", 10), fg=COLORS["danger"],
                bg=COLORS["bg_card"],
            ).pack(side="right")

            for filepath in g["files"]:
                tk.Label(
                    card, text=f"  {ICONS['file']}  {filepath}",
                    font=("Consolas", 9), fg=COLORS["text_dim"],
                    bg=COLORS["bg_card"], anchor="w",
                ).pack(fill="x", padx=15, pady=1)

            tk.Frame(card, bg=COLORS["bg_card"], height=8).pack(fill="x")


# ─── Page: Fichiers temporaires ─────────────────────────────────────────────
class TempPage(Page):

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.create_title("Nettoyage des temporaires", ICONS["temp"])
        self.create_subtitle("Supprimez les fichiers temporaires et caches navigateurs")

        toolbar = tk.Frame(self, bg=COLORS["bg_dark"])
        toolbar.pack(fill="x", padx=30, pady=(0, 10))

        StyledButton(
            toolbar, "Scanner", command=self._scan,
            icon=ICONS["refresh"],
        ).pack(side="left", padx=(0, 10))

        self.clean_btn = StyledButton(
            toolbar, "Nettoyer (simulation)", command=self._clean_dry,
            icon=ICONS["trash"], color=COLORS["warning"],
        )
        self.clean_btn.pack(side="left", padx=(0, 10))

        self.clean_real_btn = StyledButton(
            toolbar, "Nettoyer pour de vrai", command=self._clean_real,
            icon=ICONS["trash"], color=COLORS["danger"],
        )
        self.clean_real_btn.pack(side="left")

        self.status = tk.Label(
            self, text="", font=("Segoe UI", 10),
            fg=COLORS["text_dim"], bg=COLORS["bg_dark"],
        )
        self.status.pack(fill="x", padx=30)

        container, self.scroll = self.create_scrollable()
        container.pack(fill="both", expand=True, padx=30, pady=(10, 20))

        self._temp_data = None
        self._cache_data = None

    def _scan(self):
        self.status.config(text="Scan en cours...")
        for w in self.scroll.winfo_children():
            w.destroy()

        def task():
            return temp_cleaner.scan_temp_files(), temp_cleaner.scan_browser_caches()

        self.run_threaded(task, self._show_results)

    def _show_results(self, data):
        self._temp_data, self._cache_data = data
        for w in self.scroll.winfo_children():
            w.destroy()

        temp = self._temp_data
        cache = self._cache_data

        total = temp.get("total_size_mb", 0) + cache.get("total_size_mb", 0)
        self.status.config(
            text=f"Total récupérable : {format_size(total)}"
        )

        # Section fichiers temp
        if temp.get("directories"):
            tk.Label(
                self.scroll,
                text=f"{ICONS['folder']}  Dossiers temporaires",
                font=("Segoe UI Semibold", 12), fg=COLORS["white"],
                bg=COLORS["bg_dark"], anchor="w",
            ).pack(fill="x", pady=(0, 8))

            for d in temp["directories"]:
                card = self.create_card(self.scroll)
                card.pack(fill="x", pady=(0, 6))

                row = tk.Frame(card, bg=COLORS["bg_card"])
                row.pack(fill="x", padx=15, pady=10)

                tk.Label(
                    row, text=d["path"], font=("Consolas", 9),
                    fg=COLORS["text"], bg=COLORS["bg_card"],
                ).pack(side="left")

                tk.Label(
                    row,
                    text=f"{format_size(d['size_mb'])} — {d['file_count']} fichiers",
                    font=("Segoe UI", 10), fg=COLORS["accent_light"],
                    bg=COLORS["bg_card"],
                ).pack(side="right")

        # Section caches navigateurs
        browsers = cache.get("browsers", [])
        if browsers:
            tk.Label(
                self.scroll,
                text=f"\n{ICONS['info']}  Caches navigateurs",
                font=("Segoe UI Semibold", 12), fg=COLORS["white"],
                bg=COLORS["bg_dark"], anchor="w",
            ).pack(fill="x", pady=(10, 8))

            for b in browsers:
                card = self.create_card(self.scroll)
                card.pack(fill="x", pady=(0, 6))

                row = tk.Frame(card, bg=COLORS["bg_card"])
                row.pack(fill="x", padx=15, pady=10)

                tk.Label(
                    row, text=b["browser"], font=("Segoe UI Semibold", 10),
                    fg=COLORS["text"], bg=COLORS["bg_card"],
                ).pack(side="left")

                tk.Label(
                    row,
                    text=f"{format_size(b['size_mb'])} — {b['file_count']} fichiers",
                    font=("Segoe UI", 10), fg=COLORS["warning"],
                    bg=COLORS["bg_card"],
                ).pack(side="right")

    def _clean_dry(self):
        self._do_clean(dry_run=True)

    def _clean_real(self):
        if not messagebox.askyesno(
            "Confirmation",
            "Voulez-vous vraiment supprimer les fichiers temporaires ?\n"
            "Cette action est irréversible.",
        ):
            return
        self._do_clean(dry_run=False)

    def _do_clean(self, dry_run):
        label = "Simulation" if dry_run else "Nettoyage"
        self.status.config(text=f"{label} en cours...")

        def task():
            results = []
            if self._temp_data:
                for d in self._temp_data.get("directories", []):
                    r = temp_cleaner.clean_temp_directory(d["path"], dry_run=dry_run)
                    results.append(r)
            if self._cache_data:
                for b in self._cache_data.get("browsers", []):
                    r = temp_cleaner.clean_browser_cache(
                        b["browser"], dry_run=dry_run
                    )
                    results.append(r)
            return results, dry_run

        self.run_threaded(task, self._show_clean_results)

    def _show_clean_results(self, data):
        results, dry_run = data
        total_deleted = sum(r.get("deleted_files", 0) for r in results)
        total_size = sum(r.get("deleted_size_mb", 0) for r in results)
        mode = "Simulation" if dry_run else "Nettoyage terminé"
        self.status.config(
            text=f"{mode} : {total_deleted} fichiers — {format_size(total_size)} libérés"
        )


# ─── Page: Organiser ────────────────────────────────────────────────────────
class OrganizePage(Page):

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.create_title("Organiser les fichiers", ICONS["organize"])
        self.create_subtitle(
            "Triez automatiquement vos fichiers par catégorie ou par date"
        )

        toolbar = tk.Frame(self, bg=COLORS["bg_dark"])
        toolbar.pack(fill="x", padx=30, pady=(0, 10))

        tk.Label(
            toolbar, text="Dossier :", font=("Segoe UI", 10),
            fg=COLORS["text_dim"], bg=COLORS["bg_dark"],
        ).pack(side="left")

        self.path_var = tk.StringVar(value=os.path.expanduser("~"))
        tk.Entry(
            toolbar, textvariable=self.path_var,
            font=("Segoe UI", 10), bg=COLORS["bg_input"],
            fg=COLORS["text"], insertbackground=COLORS["text"],
            relief="flat", highlightbackground=COLORS["border"],
            highlightthickness=1,
        ).pack(side="left", fill="x", expand=True, padx=10, ipady=6)

        StyledButton(
            toolbar, "Parcourir", command=self._browse,
            icon=ICONS["folder"],
        ).pack(side="left")

        # Boutons d'action
        action_bar = tk.Frame(self, bg=COLORS["bg_dark"])
        action_bar.pack(fill="x", padx=30, pady=(0, 10))

        StyledButton(
            action_bar, "Aperçu par catégorie",
            command=self._preview_category, icon=ICONS["arrow"],
        ).pack(side="left", padx=(0, 10))

        StyledButton(
            action_bar, "Organiser par catégorie",
            command=self._organize_category, icon=ICONS["check"],
            color=COLORS["success"],
        ).pack(side="left", padx=(0, 10))

        StyledButton(
            action_bar, "Organiser par date",
            command=self._organize_date, icon=ICONS["check"],
            color=COLORS["warning"],
        ).pack(side="left")

        self.status = tk.Label(
            self, text="", font=("Segoe UI", 10),
            fg=COLORS["text_dim"], bg=COLORS["bg_dark"],
        )
        self.status.pack(fill="x", padx=30)

        container, self.scroll = self.create_scrollable()
        container.pack(fill="both", expand=True, padx=30, pady=(10, 20))

    def _browse(self):
        path = filedialog.askdirectory()
        if path:
            self.path_var.set(path)

    def _preview_category(self):
        path = self.path_var.get()
        if not os.path.isdir(path):
            messagebox.showwarning("Attention", "Dossier invalide.")
            return
        self.status.config(text="Analyse en cours...")
        for w in self.scroll.winfo_children():
            w.destroy()

        def task():
            return file_organizer.categorize_files(path)

        self.run_threaded(task, self._show_categories)

    def _show_categories(self, categories):
        for w in self.scroll.winfo_children():
            w.destroy()
        self.status.config(text="")

        total_files = sum(c["count"] for c in categories.values())
        total_size = sum(c["total_size_mb"] for c in categories.values())

        tk.Label(
            self.scroll,
            text=f"{total_files} fichiers — {format_size(total_size)} au total",
            font=("Segoe UI Semibold", 12), fg=COLORS["accent_light"],
            bg=COLORS["bg_dark"],
        ).pack(pady=(0, 15))

        for cat_name, cat_data in sorted(
            categories.items(), key=lambda x: -x[1]["total_size_mb"]
        ):
            if cat_data["count"] == 0:
                continue

            card = self.create_card(self.scroll)
            card.pack(fill="x", pady=(0, 6))

            header = tk.Frame(card, bg=COLORS["bg_card"])
            header.pack(fill="x", padx=15, pady=(12, 6))

            tk.Label(
                header, text=f"{ICONS['folder']}  {cat_name}",
                font=("Segoe UI Semibold", 11), fg=COLORS["white"],
                bg=COLORS["bg_card"],
            ).pack(side="left")

            tk.Label(
                header,
                text=f"{cat_data['count']} fichiers — {format_size(cat_data['total_size_mb'])}",
                font=("Segoe UI", 10), fg=COLORS["text_dim"],
                bg=COLORS["bg_card"],
            ).pack(side="right")

            # Afficher quelques fichiers
            for f in cat_data["files"][:5]:
                tk.Label(
                    card,
                    text=f"  {ICONS['file']}  {f['name']}  ({format_size(f['size_mb'])})",
                    font=("Consolas", 9), fg=COLORS["text_dim"],
                    bg=COLORS["bg_card"], anchor="w",
                ).pack(fill="x", padx=15, pady=1)

            remaining = cat_data["count"] - min(5, len(cat_data["files"]))
            if remaining > 0:
                tk.Label(
                    card,
                    text=f"  ... et {remaining} autres fichiers",
                    font=("Segoe UI", 9), fg=COLORS["text_muted"],
                    bg=COLORS["bg_card"], anchor="w",
                ).pack(fill="x", padx=15, pady=(1, 8))
            else:
                tk.Frame(card, bg=COLORS["bg_card"], height=8).pack(fill="x")

    def _organize_category(self):
        path = self.path_var.get()
        if not os.path.isdir(path):
            messagebox.showwarning("Attention", "Dossier invalide.")
            return
        if not messagebox.askyesno(
            "Confirmation",
            f"Organiser les fichiers de :\n{path}\n\n"
            "Les fichiers seront déplacés dans des sous-dossiers par catégorie.",
        ):
            return
        self.status.config(text="Organisation en cours...")

        def task():
            return file_organizer.organize_files(path, dry_run=False)

        self.run_threaded(task, self._show_organize_result)

    def _organize_date(self):
        path = self.path_var.get()
        if not os.path.isdir(path):
            messagebox.showwarning("Attention", "Dossier invalide.")
            return
        if not messagebox.askyesno(
            "Confirmation",
            f"Organiser les fichiers de :\n{path}\n\n"
            "Les fichiers seront déplacés dans des sous-dossiers par date (AAAA/AAAA-MM).",
        ):
            return
        self.status.config(text="Organisation en cours...")

        def task():
            return file_organizer.organize_by_date(path, dry_run=False)

        self.run_threaded(task, self._show_organize_result)

    def _show_organize_result(self, result):
        moved = result.get("moved_files", 0)
        errors = result.get("errors", [])
        self.status.config(
            text=f"{ICONS['check']}  {moved} fichiers déplacés"
            + (f" — {len(errors)} erreurs" if errors else "")
        )


# ─── Application principale ─────────────────────────────────────────────────
class PCCleanupApp:
    """Application principale PC Cleanup Tool."""

    PAGES = [
        ("dashboard",  "Tableau de bord",    ICONS["dashboard"],  DashboardPage),
        ("software",   "Logiciels",          ICONS["software"],   SoftwarePage),
        ("disk",       "Espace disque",      ICONS["disk"],       DiskPage),
        ("large",      "Gros fichiers",      ICONS["large"],      LargeFilesPage),
        ("duplicates", "Doublons",           ICONS["duplicates"], DuplicatesPage),
        ("temp",       "Temporaires",        ICONS["temp"],       TempPage),
        ("organize",   "Organiser",          ICONS["organize"],   OrganizePage),
    ]

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PC Cleanup Tool")
        self.root.geometry("1100x700")
        self.root.minsize(900, 550)
        self.root.configure(bg=COLORS["bg_dark"])

        # Icône de la fenêtre (optionnel)
        try:
            if platform.system() == "Windows":
                self.root.iconbitmap(default="")
        except Exception:
            pass

        self._build_ui()
        self.show_page("dashboard")

    def _build_ui(self):
        # Conteneur principal
        main = tk.Frame(self.root, bg=COLORS["bg_dark"])
        main.pack(fill="both", expand=True)

        # ── Sidebar ──
        self.sidebar = tk.Frame(main, bg=COLORS["bg_sidebar"], width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo / Titre
        logo_frame = tk.Frame(self.sidebar, bg=COLORS["bg_sidebar"])
        logo_frame.pack(fill="x", padx=15, pady=(20, 5))

        tk.Label(
            logo_frame, text=ICONS["quick"],
            font=("Segoe UI", 26), fg=COLORS["accent"],
            bg=COLORS["bg_sidebar"],
        ).pack(side="left")

        tk.Label(
            logo_frame, text=" PC Cleanup",
            font=("Segoe UI Semibold", 16), fg=COLORS["white"],
            bg=COLORS["bg_sidebar"],
        ).pack(side="left", padx=(5, 0))

        tk.Label(
            self.sidebar, text="v1.0.0",
            font=("Segoe UI", 9), fg=COLORS["text_muted"],
            bg=COLORS["bg_sidebar"],
        ).pack(padx=20, anchor="w")

        # Séparateur
        tk.Frame(
            self.sidebar, bg=COLORS["border"], height=1,
        ).pack(fill="x", padx=15, pady=15)

        # Boutons de navigation
        self._nav_buttons = {}
        for key, label, icon, _ in self.PAGES:
            btn = tk.Label(
                self.sidebar,
                text=f"  {icon}   {label}",
                font=("Segoe UI", 11),
                fg=COLORS["text_dim"],
                bg=COLORS["bg_sidebar"],
                anchor="w",
                padx=15, pady=10,
                cursor="hand2",
            )
            btn.pack(fill="x")
            btn.bind("<Button-1>", lambda e, k=key: self.show_page(k))
            btn.bind("<Enter>", lambda e, b=btn: self._nav_hover(b, True))
            btn.bind("<Leave>", lambda e, b=btn: self._nav_hover(b, False))
            self._nav_buttons[key] = btn

        # Info système en bas
        tk.Frame(self.sidebar, bg=COLORS["bg_sidebar"]).pack(fill="both", expand=True)

        info = tk.Frame(self.sidebar, bg=COLORS["bg_sidebar"])
        info.pack(fill="x", padx=15, pady=15)

        tk.Frame(info, bg=COLORS["border"], height=1).pack(fill="x", pady=(0, 10))

        tk.Label(
            info, text=f"{platform.system()} {platform.release()}",
            font=("Segoe UI", 9), fg=COLORS["text_muted"],
            bg=COLORS["bg_sidebar"], anchor="w",
        ).pack(fill="x")

        tk.Label(
            info, text=f"Python {platform.python_version()}",
            font=("Segoe UI", 9), fg=COLORS["text_muted"],
            bg=COLORS["bg_sidebar"], anchor="w",
        ).pack(fill="x")

        # ── Zone de contenu ──
        self.content = tk.Frame(main, bg=COLORS["bg_dark"])
        self.content.pack(side="left", fill="both", expand=True)

        # Créer toutes les pages
        self.pages = {}
        for key, _, _, PageClass in self.PAGES:
            page = PageClass(self.content, self)
            self.pages[key] = page

        self._current_page = None

    def _nav_hover(self, btn, entering):
        """Effet de survol sur les boutons de navigation."""
        key = None
        for k, b in self._nav_buttons.items():
            if b is btn:
                key = k
                break
        if key == self._current_page:
            return
        if entering:
            btn.config(bg=COLORS["bg_card_hover"], fg=COLORS["text"])
        else:
            btn.config(bg=COLORS["bg_sidebar"], fg=COLORS["text_dim"])

    def show_page(self, key):
        """Affiche une page et met à jour la navigation."""
        # Masquer la page courante
        if self._current_page and self._current_page in self.pages:
            self.pages[self._current_page].pack_forget()

        # Réinitialiser tous les boutons de nav
        for k, btn in self._nav_buttons.items():
            btn.config(
                bg=COLORS["bg_sidebar"],
                fg=COLORS["text_dim"],
                font=("Segoe UI", 11),
            )

        # Activer le bouton sélectionné
        if key in self._nav_buttons:
            self._nav_buttons[key].config(
                bg=COLORS["accent_dark"],
                fg=COLORS["white"],
                font=("Segoe UI Semibold", 11),
            )

        # Afficher la page
        self._current_page = key
        page = self.pages[key]
        page.pack(fill="both", expand=True)
        page.on_show()

    def run(self):
        """Lancer l'application."""
        self.root.mainloop()


def launch_gui():
    """Point d'entrée pour la GUI."""
    app = PCCleanupApp()
    app.run()


if __name__ == "__main__":
    launch_gui()
