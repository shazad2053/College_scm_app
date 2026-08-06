# School / College Management System (Desktop App)

A complete desktop application built with **Python** (Tkinter + SQLite —
both included in the standard Python installation, no extra packages
required) implementing every module from your plan.

## Modules included

1. **Dashboard** — totals for students/teachers/classes, today's attendance,
   pending fee, fee collected this month, upcoming exams, recent activity.
2. **Student Management** — add/edit/delete/view profile, all fields from
   your plan (roll no, registration no, CNIC/B-Form, photo, etc.).
3. **Teacher Management** — full CRUD with salary, qualification, status.
4. **Class Management** — session, class, section, class teacher.
5. **Subject Management** — subject name/code linked to class & teacher.
6. **Attendance** — student & teacher daily marking (double-click to cycle
   Present/Absent/Leave) plus monthly reports.
7. **Fee Management** — fee structure per class, fee collection (with
   discount/fine) and printable receipts, challan generation/printing.
8. **Examinations** — Monthly Test / Mid-Term / Final-Term records.
9. **Marks Management** — enter/edit marks per exam & subject.
10. **Result Management** — result cards, position list, merit list, printing.
11. **Reports** — student, attendance, fee, examination, and teacher reports.
12. **Settings** — school info, academic session, users & roles, backup &
    restore of the database.

## How to run

1. Make sure Python 3.8+ is installed (Tkinter ships with the standard
   installer on Windows/macOS; on Linux you may need
   `sudo apt install python3-tk`).
2. Open a terminal in this folder.
3. Run:
   ```
   python main.py
   ```
   (use `python3 main.py` on macOS/Linux if `python` points to Python 2)

That's it — no `pip install` needed. On first run the app automatically
creates a local database file called `school.db` in this folder, along with
a default login:

- **Username:** admin
- **Password:** admin123

(You can add more users under Settings → Users & Roles.)

## Data storage

All data is stored locally in `school.db` (SQLite). Use
**Settings → Backup & Restore** to copy this file somewhere safe or restore
from a previous backup. If you move the app folder, the database moves
with it since it always sits next to `main.py`.

## Suggested first steps

1. Go to **Settings** and set your school name, address, and session.
2. Go to **Classes** and create your classes/sections.
3. Go to **Teachers** and add your teaching staff.
4. Go to **Subjects** and link subjects to classes and teachers.
5. Go to **Students** and start admitting students.
6. Use **Fee Management → Fee Structure** to set fee amounts per class.
7. Start marking **Attendance**, collecting fees, running **Examinations**,
   and generating **Results** and **Reports** as the term progresses.

## Project structure

```
school_app/
├── main.py                # Entry point — run this
├── database.py            # SQLite schema & connection helpers
├── ui_helpers.py           # Shared styling & small reusable widgets
├── pages/
│   ├── dashboard.py
│   ├── students.py
│   ├── teachers.py
│   ├── classes.py
│   ├── subjects.py
│   ├── attendance.py
│   ├── fees.py
│   ├── exams.py
│   ├── results.py
│   ├── reports.py
│   └── settings.py
└── school.db               # created automatically on first run
```

## Notes / possible next steps

- Receipts, challans, and merit lists currently save as plain `.txt` files
  (or open a preview window) so they can be printed from any text editor.
  If you'd like proper PDF output or a print dialog, that can be added.
- Photos you attach to a student profile are copied into a
  `student_photos/` folder next to the app.
- This is a single-computer app (SQLite file on disk). If you eventually
  need multiple people using it over a network at the same time, the
  database layer would need to move to a client-server database
  (e.g. PostgreSQL/MySQL) — happy to help with that migration if needed.
