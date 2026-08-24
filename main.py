import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import customtkinter as ctk
from tkinter import messagebox

import database
from ui.theme import BG_DEEP

# ── App Bootstrap ─────────────────────────────────────────────────────────────
app = ctk.CTk()
app.title("Face Attendance System  |  Enterprise")
app.geometry("1600x900")
app.minsize(1280, 720)
app.configure(fg_color=BG_DEEP)

if database.employees is None:
    messagebox.showerror("DB Error", "MongoDB connection failed.")
    exit()

# ── Page Router ───────────────────────────────────────────────────────────────
def _clear():
    for w in app.winfo_children():
        w.destroy()

def show_landing():
    _clear()
    from ui.landing import LandingPage
    LandingPage(app, on_admin=show_admin, on_employee=show_employee)

def show_admin():
    _clear()
    from ui.admin_panel import AdminPanel
    AdminPanel(app, on_back=show_landing)

def show_employee():
    _clear()
    from ui.employee_panel import EmployeePanel
    EmployeePanel(app, on_back=show_landing)

# ── Start ─────────────────────────────────────────────────────────────────────
show_landing()
app.mainloop()