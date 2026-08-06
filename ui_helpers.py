"""
ui_helpers.py
Shared style constants and small reusable widgets used across every page.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

# ---------------- Color / Style Palette ----------------
COLOR_SIDEBAR = "#1f2937"
COLOR_SIDEBAR_ACTIVE = "#374151"
COLOR_SIDEBAR_TEXT = "#e5e7eb"
COLOR_BG = "#f3f4f6"
COLOR_CARD = "#ffffff"
COLOR_ACCENT = "#2563eb"
COLOR_ACCENT_DARK = "#1d4ed8"
COLOR_DANGER = "#dc2626"
COLOR_SUCCESS = "#16a34a"
COLOR_TEXT = "#111827"
COLOR_MUTED = "#6b7280"

FONT_TITLE = ("Segoe UI", 18, "bold")
FONT_SUBTITLE = ("Segoe UI", 12, "bold")
FONT_NORMAL = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_CARD_NUM = ("Segoe UI", 22, "bold")


def configure_styles(root):
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure("TFrame", background=COLOR_BG)
    style.configure("Card.TFrame", background=COLOR_CARD)
    style.configure("Sidebar.TFrame", background=COLOR_SIDEBAR)

    style.configure("TLabel", background=COLOR_BG, foreground=COLOR_TEXT, font=FONT_NORMAL)
    style.configure("Card.TLabel", background=COLOR_CARD, foreground=COLOR_TEXT, font=FONT_NORMAL)
    style.configure("Title.TLabel", background=COLOR_BG, foreground=COLOR_TEXT, font=FONT_TITLE)
    style.configure("Subtitle.TLabel", background=COLOR_BG, foreground=COLOR_TEXT, font=FONT_SUBTITLE)
    style.configure("CardNum.TLabel", background=COLOR_CARD, foreground=COLOR_ACCENT, font=FONT_CARD_NUM)
    style.configure("Muted.TLabel", background=COLOR_CARD, foreground=COLOR_MUTED, font=FONT_NORMAL)

    style.configure("Sidebar.TLabel", background=COLOR_SIDEBAR, foreground=COLOR_SIDEBAR_TEXT, font=FONT_NORMAL)
    style.configure("SidebarTitle.TLabel", background=COLOR_SIDEBAR, foreground="#ffffff",
                    font=("Segoe UI", 13, "bold"))

    style.configure("Accent.TButton", font=FONT_BOLD, padding=8)
    style.map("Accent.TButton",
              background=[("!disabled", COLOR_ACCENT), ("active", COLOR_ACCENT_DARK)],
              foreground=[("!disabled", "#ffffff")])

    style.configure("Danger.TButton", font=FONT_BOLD, padding=8)
    style.map("Danger.TButton",
              background=[("!disabled", COLOR_DANGER), ("active", COLOR_DANGER)],
              foreground=[("!disabled", "#ffffff")])

    style.configure("Secondary.TButton", font=FONT_BOLD, padding=8,
                    background="#f3f4f6", foreground=COLOR_TEXT)
    style.map("Secondary.TButton",
              background=[("!disabled", "#f3f4f6"), ("active", "#e5e7eb")],
              foreground=[("!disabled", COLOR_TEXT)])

    style.configure("TButton", font=FONT_NORMAL, padding=6)
    style.configure("Search.TEntry", fieldbackground="#ffffff", background="#ffffff",
                    bordercolor="#d1d5db", lightcolor="#d1d5db", darkcolor="#d1d5db",
                    padding=6)

    style.configure("Treeview", font=FONT_NORMAL, rowheight=26, background="#ffffff",
                    fieldbackground="#ffffff")
    style.configure("Treeview.Heading", font=FONT_BOLD, background="#e5e7eb")
    style.map("Treeview", background=[("selected", COLOR_ACCENT)], foreground=[("selected", "#ffffff")])

    style.configure("TNotebook", background=COLOR_BG)
    style.configure("TNotebook.Tab", font=FONT_BOLD, padding=(12, 6))


def today_str():
    return datetime.now().strftime("%Y-%m-%d")


def make_stat_card(parent, title, value, row, col):
    """A small dashboard KPI card."""
    card = ttk.Frame(parent, style="Card.TFrame", padding=16)
    card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
    ttk.Label(card, text=str(value), style="CardNum.TLabel").pack(anchor="w")
    ttk.Label(card, text=title, style="Muted.TLabel").pack(anchor="w", pady=(4, 0))
    return card


class ScrollableFrame(ttk.Frame):
    """A frame with a vertical scrollbar, useful for long forms."""

    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        canvas = tk.Canvas(self, background=COLOR_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")


def labeled_entry(parent, label_text, row, col=0, width=28, show=None):
    """Creates a label + entry pair, returns the Entry widget."""
    ttk.Label(parent, text=label_text, style="Card.TLabel").grid(
        row=row, column=col * 2, sticky="w", padx=(0, 8), pady=6
    )
    entry = ttk.Entry(parent, width=width, show=show)
    entry.grid(row=row, column=col * 2 + 1, sticky="w", pady=6)
    return entry


def labeled_combo(parent, label_text, values, row, col=0, width=25):
    ttk.Label(parent, text=label_text, style="Card.TLabel").grid(
        row=row, column=col * 2, sticky="w", padx=(0, 8), pady=6
    )
    combo = ttk.Combobox(parent, values=values, width=width - 2, state="readonly")
    combo.grid(row=row, column=col * 2 + 1, sticky="w", pady=6)
    return combo


def confirm_delete(item_name="this record"):
    return messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {item_name}?")


def info(msg, title="Success"):
    messagebox.showinfo(title, msg)


def warn(msg, title="Warning"):
    messagebox.showwarning(title, msg)


def error(msg, title="Error"):
    messagebox.showerror(title, msg)
