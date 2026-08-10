"""
main.py
School / College Management System (Desktop)
Entry point - builds the main window, sidebar navigation, and wires up
all the feature pages.

Run with:  python main.py
Requires only the Python standard library (tkinter + sqlite3).
"""

import tkinter as tk
from tkinter import ttk

from database import init_db, get_setting
from ui_helpers import configure_styles, COLOR_SIDEBAR, COLOR_SIDEBAR_ACTIVE, COLOR_SIDEBAR_TEXT

from pages.dashboard import DashboardPage
from pages.students import StudentsPage
from pages.teachers import TeachersPage
from pages.classes import ClassesPage
from pages.subjects import SubjectsPage
from pages.attendance import AttendancePage
from pages.fees import FeesPage
from pages.exams import ExamsPage
from pages.results import ResultsPage
from pages.reports import ReportsPage
from pages.settings import SettingsPage


MENU_ITEMS = [
    ("Dashboard", "🏠"),
    ("Students", "🧑‍🎓"),
    ("Teachers", "🧑‍🏫"),
    ("Classes", "🏫"),
    ("Subjects", "📚"),
    ("Attendance", "🗓️"),
    ("Fee Management", "💵"),
    ("Examinations", "📝"),
    ("Results", "🏆"),
    ("Reports", "📊"),
    ("Settings", "⚙️"),
]


class SchoolManagementApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("School / College Management System")
        self.geometry("1200x750")
        self.minsize(1000, 650)

        configure_styles(self)

        self.container = ttk.Frame(self)
        self.container.pack(fill="both", expand=True)

        self.sidebar = tk.Frame(self.container, bg=COLOR_SIDEBAR, width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.content_area = ttk.Frame(self.container, style="TFrame")
        self.content_area.pack(side="left", fill="both", expand=True)

        self.pages = {}
        self.page_classes = {
            "Dashboard": DashboardPage,
            "Students": StudentsPage,
            "Teachers": TeachersPage,
            "Classes": ClassesPage,
            "Subjects": SubjectsPage,
            "Attendance": AttendancePage,
            "Fee Management": FeesPage,
            "Examinations": ExamsPage,
            "Results": ResultsPage,
            "Reports": ReportsPage,
            "Settings": SettingsPage,
        }
        self.sidebar_buttons = {}

        self.build_sidebar()
        self.show_page("Dashboard")

    def build_sidebar(self):
        school_name = get_setting("school_name", "My School")
        header = tk.Frame(self.sidebar, bg=COLOR_SIDEBAR)
        header.pack(fill="x", pady=(20, 10), padx=15)
        tk.Label(
            header, text=school_name, bg=COLOR_SIDEBAR, fg="#ffffff",
            font=("Segoe UI", 13, "bold"), wraplength=190, justify="left"
        ).pack(anchor="w")
        tk.Label(
            header, text="College Management System", bg=COLOR_SIDEBAR, fg="#9ca3af",
            font=("Segoe UI", 9)
        ).pack(anchor="w")

        sep = tk.Frame(self.sidebar, bg="#374151", height=1)
        sep.pack(fill="x", padx=15, pady=(5, 15))

        for name, icon in MENU_ITEMS:
            btn = tk.Button(
                self.sidebar,
                text=f"  {icon}   {name}",
                anchor="w",
                bg=COLOR_SIDEBAR,
                fg=COLOR_SIDEBAR_TEXT,
                activebackground=COLOR_SIDEBAR_ACTIVE,
                activeforeground="#ffffff",
                bd=0,
                font=("Segoe UI", 11),
                relief="flat",
                cursor="hand2",
                padx=10,
                pady=10,
                command=lambda n=name: self.show_page(n),
            )
            btn.pack(fill="x", padx=8, pady=1)
            self.sidebar_buttons[name] = btn

    def show_page(self, name):
        # Highlight active button
        for n, btn in self.sidebar_buttons.items():
            btn.configure(bg=COLOR_SIDEBAR_ACTIVE if n == name else COLOR_SIDEBAR)

        # Hide all pages
        for page in self.pages.values():
            page.pack_forget()

        if name not in self.pages:
            page_class = self.page_classes[name]
            page = page_class(self.content_area, self)
            self.pages[name] = page
        else:
            page = self.pages[name]
            if hasattr(page, "refresh"):
                page.refresh()

        page.pack(fill="both", expand=True)


def main():
    init_db()
    app = SchoolManagementApp()
    app.mainloop()


if __name__ == "__main__":
    main()
