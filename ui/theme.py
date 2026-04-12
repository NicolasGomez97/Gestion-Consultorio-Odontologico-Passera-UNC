"""
theme.py — Paleta de colores y estilos ttk para la aplicación.
"""
import tkinter as tk
from tkinter import ttk

# ── Paleta ──────────────────────────────────────────────────────────────────
COLORS = {
    "bg":           "#F5F7FA",   # fondo general
    "sidebar_bg":   "#1A2940",   # azul oscuro sidebar
    "sidebar_fg":   "#FFFFFF",
    "sidebar_sel":  "#2E4A70",
    "header_bg":    "#2C5282",   # encabezado de secciones
    "header_fg":    "#FFFFFF",
    "accent":       "#3182CE",   # azul principal
    "accent_hover": "#2B6CB0",
    "success":      "#38A169",
    "warning":      "#D69E2E",
    "danger":       "#E53E3E",
    "text":         "#2D3748",
    "text_light":   "#718096",
    "border":       "#CBD5E0",
    "white":        "#FFFFFF",
    "row_even":     "#FFFFFF",
    "row_odd":      "#EBF4FF",
    # odontograma
    "tooth_sano":       "#FFFFFF",
    "tooth_caries":     "#E53E3E",
    "tooth_obturacion": "#3182CE",
    "tooth_fractura":   "#718096",
    "tooth_pendiente":  "#BEE3F8",
    "tooth_ausente_x":  "#E53E3E",
    "tooth_border":     "#2D3748",
    "tooth_corona":     "#F6E05E",
    "tooth_implante":   "#9F7AEA",
    "tooth_endo":       "#FC8181",
    # periodontal
    "perio_ok":     "#C6F6D5",
    "perio_warn":   "#FEFCBF",
    "perio_alert":  "#FED7D7",
}

FONTS = {
    "title":    ("Segoe UI", 16, "bold"),
    "subtitle": ("Segoe UI", 12, "bold"),
    "body":     ("Segoe UI", 10),
    "small":    ("Segoe UI", 9),
    "mono":     ("Courier New", 9),
    "sidebar":  ("Segoe UI", 11),
}


def apply_theme(root: tk.Tk):
    """Aplica el tema global a la ventana raíz."""
    root.configure(bg=COLORS["bg"])
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    # ── Frames y Labels ──────────────────────────────────────────────────────
    style.configure("TFrame",       background=COLORS["bg"])
    style.configure("TLabel",       background=COLORS["bg"], foreground=COLORS["text"],
                    font=FONTS["body"])
    style.configure("Header.TLabel",background=COLORS["bg"], foreground=COLORS["text"],
                    font=FONTS["title"])
    style.configure("Sub.TLabel",   background=COLORS["bg"], foreground=COLORS["text"],
                    font=FONTS["subtitle"])
    style.configure("Sidebar.TFrame", background=COLORS["sidebar_bg"])
    style.configure("Sidebar.TLabel", background=COLORS["sidebar_bg"],
                    foreground=COLORS["sidebar_fg"], font=FONTS["sidebar"])
    style.configure("SideTitle.TLabel", background=COLORS["sidebar_bg"],
                    foreground=COLORS["sidebar_fg"], font=("Segoe UI", 13, "bold"))

    # ── Botones ──────────────────────────────────────────────────────────────
    style.configure("TButton", font=FONTS["small"], padding=(5, 2))
    style.configure("Accent.TButton", background=COLORS["accent"],
                    foreground=COLORS["white"], font=FONTS["small"], padding=(5, 2))
    style.map("Accent.TButton",
              background=[("active", COLORS["accent_hover"]),
                          ("disabled", COLORS["border"])])
    style.configure("Danger.TButton", background=COLORS["danger"],
                    foreground=COLORS["white"], font=FONTS["small"], padding=(5, 2))
    style.configure("Success.TButton", background=COLORS["success"],
                    foreground=COLORS["white"], font=FONTS["small"], padding=(5, 2))
    style.configure("Sidebar.TButton", background=COLORS["sidebar_bg"],
                    foreground=COLORS["sidebar_fg"],
                    font=FONTS["sidebar"], padding=(16, 10), anchor="w",
                    relief="flat", borderwidth=0)
    style.map("Sidebar.TButton",
              background=[("active", COLORS["sidebar_sel"]),
                          ("pressed", COLORS["sidebar_sel"])])

    # ── Entradas ─────────────────────────────────────────────────────────────
    style.configure("TEntry", padding=4, font=FONTS["body"])
    style.configure("TCombobox", padding=4, font=FONTS["body"])
    style.configure("TSpinbox", padding=4, font=FONTS["body"])

    # ── Treeview ─────────────────────────────────────────────────────────────
    style.configure("Treeview",
                    background=COLORS["white"],
                    fieldbackground=COLORS["white"],
                    foreground=COLORS["text"],
                    font=FONTS["body"],
                    rowheight=28)
    style.configure("Treeview.Heading",
                    background=COLORS["header_bg"],
                    foreground=COLORS["header_fg"],
                    font=FONTS["subtitle"],
                    padding=8)
    style.map("Treeview",
              background=[("selected", COLORS["accent"])],
              foreground=[("selected", COLORS["white"])])

    # ── Notebook ─────────────────────────────────────────────────────────────
    style.configure("TNotebook",        background=COLORS["bg"])
    style.configure("TNotebook.Tab",    background=COLORS["border"],
                    foreground=COLORS["text"], padding=(12, 6), font=FONTS["body"])
    style.map("TNotebook.Tab",
              background=[("selected", COLORS["accent"])],
              foreground=[("selected", COLORS["white"])])

    # ── LabelFrame ───────────────────────────────────────────────────────────
    style.configure("TLabelframe",      background=COLORS["bg"],
                    foreground=COLORS["text"], font=FONTS["body"])
    style.configure("TLabelframe.Label",background=COLORS["bg"],
                    foreground=COLORS["accent"], font=FONTS["subtitle"])

    # ── Scrollbar ────────────────────────────────────────────────────────────
    style.configure("TScrollbar", background=COLORS["border"], troughcolor=COLORS["bg"])

    # ── Separator ────────────────────────────────────────────────────────────
    style.configure("TSeparator", background=COLORS["border"])


def card_frame(parent, **kwargs) -> ttk.Frame:
    """Frame con aspecto de tarjeta (borde y fondo blanco)."""
    f = ttk.Frame(parent, relief="solid", borderwidth=1, style="TFrame", **kwargs)
    f.configure(style="TFrame")
    return f
