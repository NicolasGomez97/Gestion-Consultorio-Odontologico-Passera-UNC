"""
odontograma_ui.py — Odontograma interactivo con Canvas.

FDI notation:
  Permanentes superiores: 18-11 (derecha) | 21-28 (izquierda)
  Permanentes inferiores: 48-41 (derecha) | 31-38 (izquierda)
  Temporales superiores:  55-51 (derecha) | 61-65 (izquierda)
  Temporales inferiores:  85-81 (derecha) | 71-75 (izquierda)

Cada diente se dibuja como un cuadrado con 5 triángulos/zonas:
  V (vestibular) = arriba, L (lingual) = abajo,
  M (mesial) = izquierda, D (distal) = derecha, O (oclusal) = centro
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Optional, Dict, Tuple
import models
from ui.theme import COLORS, FONTS
from ui.app import app_state

# ── Tamaño de cada casilla de diente ──────────────────────────────────────────
TS = 38          # tooth size in pixels
GAP = 3          # gap between teeth
STEP = TS + GAP  # total step per tooth

# ── Colores por estado ─────────────────────────────────────────────────────────
STATE_COLORS = {
    "Sano":       "#FFFFFF",
    "Caries":     "#E53E3E",
    "Obturacion": "#3182CE",
    "Fractura":   "#718096",
    "Pendiente":  "#BEE3F8",
}
STATE_CYCLE = ["Sano", "Caries", "Obturacion", "Fractura", "Pendiente"]

# ── Colores de condición del diente completo ───────────────────────────────────
CONDICION_COLORS = {
    "sano":              None,
    "ausente":           "#2D3748",    # negro (X roja encima)
    "implante":          "#9F7AEA",
    "corona":            "#F6E05E",
    "endodoncia":        "#FC8181",
    "protesis_fija":     "#FBD38D",
    "protesis_removible":"#FED7D7",
    "sellante":          "#C6F6D5",
}
CONDICIONES = list(CONDICION_COLORS.keys())

# ── Disposición de dientes ────────────────────────────────────────────────────
# Cada fila: list of FDI numbers from left to right as drawn on canvas
PERM_UPPER  = [18, 17, 16, 15, 14, 13, 12, 11, 21, 22, 23, 24, 25, 26, 27, 28]
PERM_LOWER  = [48, 47, 46, 45, 44, 43, 42, 41, 31, 32, 33, 34, 35, 36, 37, 38]
TEMP_UPPER  = [None, None, None, 55, 54, 53, 52, 51, 61, 62, 63, 64, 65, None, None, None]
TEMP_LOWER  = [None, None, None, 85, 84, 83, 82, 81, 71, 72, 73, 74, 75, None, None, None]


def tooth_polygons(x0: int, y0: int) -> Dict[str, list]:
    """
    Devuelve los 5 polígonos de superficies para un diente en (x0, y0).
    """
    s = TS
    q = s // 4  # quarter
    return {
        "V": [x0,    y0,    x0+s,  y0,    x0+s-q, y0+q,  x0+q,   y0+q],
        "L": [x0+q,  y0+s-q,x0+s-q,y0+s-q,x0+s,  y0+s,  x0,     y0+s],
        "M": [x0,    y0,    x0+q,  y0+q,  x0+q,   y0+s-q,x0,     y0+s],
        "D": [x0+s-q,y0+q,  x0+s,  y0,    x0+s,   y0+s,  x0+s-q, y0+s-q],
        "O": [x0+q,  y0+q,  x0+s-q,y0+q,  x0+s-q, y0+s-q,x0+q,  y0+s-q],
    }


class OdontogramaFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["bg"])
        self._pac_id: Optional[int] = None
        self._data: Dict = {}          # {fdi: {condicion, notas, superficies: {surf: estado}}}
        self._tooth_items: Dict = {}   # {(fdi, surf): canvas_item_id}
        self._tooth_centers: Dict = {} # {fdi: (cx, cy)}
        self._build()
        app_state.register("patient_changed", lambda **kw: self._on_patient_change(**kw))

    # ── Construcción de la UI ─────────────────────────────────────────────────

    def _build(self):
        hdr = tk.Frame(self, bg=COLORS["header_bg"], pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text="🦷  Odontograma",
                 font=FONTS["title"], bg=COLORS["header_bg"], fg=COLORS["white"]).pack(padx=20, anchor="w")
        self._lbl_pac = tk.Label(hdr, text="Sin paciente seleccionado",
                                  font=FONTS["body"], bg=COLORS["header_bg"], fg="#BEE3F8")
        self._lbl_pac.pack(padx=20, anchor="w")

        # Barra de herramientas
        toolbar = tk.Frame(self, bg=COLORS["bg"], pady=6, padx=16)
        toolbar.pack(fill="x")

        tk.Label(toolbar, text="Paciente:", font=FONTS["body"],
                 bg=COLORS["bg"]).pack(side="left")
        self._pac_var = tk.StringVar()
        self._pac_combo = ttk.Combobox(toolbar, textvariable=self._pac_var, width=34)
        self._pac_combo.pack(side="left", padx=6)
        ttk.Button(toolbar, text="Cargar", command=self._cargar_combo).pack(side="left")

        # Leyenda
        leg_frame = tk.Frame(toolbar, bg=COLORS["bg"])
        leg_frame.pack(side="right", padx=12)
        tk.Label(leg_frame, text="Leyenda:", font=FONTS["small"],
                 bg=COLORS["bg"]).pack(side="left")
        for estado, color in STATE_COLORS.items():
            if estado == "sano":
                continue
            fr = tk.Frame(leg_frame, bg=color, width=16, height=16, relief="solid", bd=1)
            fr.pack(side="left", padx=2)
            tk.Label(leg_frame, text=estado.capitalize(), font=FONTS["small"],
                     bg=COLORS["bg"], fg=COLORS["text"]).pack(side="left", padx=(0, 6))

        # Canvas con scrollbar
        canvas_frame = tk.Frame(self, bg=COLORS["bg"])
        canvas_frame.pack(fill="both", expand=True, padx=8, pady=4)

        canvas_width  = STEP * 16 + 80
        canvas_height = STEP * 6 + 120

        self._canvas = tk.Canvas(canvas_frame, bg="#F0F4F8",
                                  width=canvas_width, height=canvas_height,
                                  scrollregion=(0, 0, canvas_width, canvas_height))
        hscroll = ttk.Scrollbar(canvas_frame, orient="horizontal",
                                 command=self._canvas.xview)
        vscroll = ttk.Scrollbar(canvas_frame, orient="vertical",
                                 command=self._canvas.yview)
        self._canvas.configure(xscrollcommand=hscroll.set, yscrollcommand=vscroll.set)
        hscroll.pack(side="bottom", fill="x")
        vscroll.pack(side="right", fill="y")
        self._canvas.pack(fill="both", expand=True)

        self._canvas.bind("<Button-1>", self._on_left_click)
        self._canvas.bind("<Button-3>", self._on_right_click)

        # Panel de notas del diente seleccionado
        self._notes_frame = tk.Frame(self, bg=COLORS["bg"], padx=16, pady=4)
        self._notes_frame.pack(fill="x")
        tk.Label(self._notes_frame, text="Notas del diente seleccionado:",
                 font=FONTS["body"], bg=COLORS["bg"]).pack(side="left")
        self._notes_var = tk.StringVar()
        ttk.Entry(self._notes_frame, textvariable=self._notes_var, width=40
                  ).pack(side="left", padx=6)
        ttk.Button(self._notes_frame, text="💾 Guardar nota",
                   command=self._save_note).pack(side="left")
        self._selected_fdi: Optional[int] = None
        self._lbl_sel = tk.Label(self._notes_frame, text="", font=FONTS["small"],
                                  bg=COLORS["bg"], fg=COLORS["accent"])
        self._lbl_sel.pack(side="left", padx=8)

        ttk.Button(self._notes_frame, text="🔄 Recargar",
                   command=self._draw).pack(side="right")
        ttk.Button(self._notes_frame, text="🗑️ Limpiar diente",
                   command=self._clear_tooth).pack(side="right", padx=4)

        self._refresh_pacientes()
        self._draw_empty()

    # ── Datos ─────────────────────────────────────────────────────────────────

    def _refresh_pacientes(self):
        self._pacientes = models.get_pacientes()
        names = [f"{p['apellido']}, {p['nombre']} ({p.get('dni','')})"
                 for p in self._pacientes]
        self._pac_combo["values"] = names

    def _on_patient_change(self, paciente_id=None, **kw):
        if paciente_id:
            for p in self._pacientes:
                if p["id"] == paciente_id:
                    self._pac_var.set(f"{p['apellido']}, {p['nombre']} ({p.get('dni','')})")
                    self._load_patient(paciente_id)
                    break

    def _cargar_combo(self):
        val = self._pac_var.get()
        for p in self._pacientes:
            if val.startswith(f"{p['apellido']}, {p['nombre']}"):
                app_state.set_paciente(p["id"])
                self._load_patient(p["id"])
                return

    def _load_patient(self, pac_id: int):
        self._pac_id = pac_id
        pac = models.get_paciente(pac_id)
        if pac:
            self._lbl_pac.configure(
                text=f"Paciente: {pac['apellido']}, {pac['nombre']} — DNI: {pac.get('dni','')}"
            )
        self._data = models.get_odontograma(pac_id)
        self._draw()

    # ── Dibujo ────────────────────────────────────────────────────────────────

    def _draw_empty(self):
        c = self._canvas
        c.delete("all")
        c.create_text(400, 200, text="Seleccione un paciente para ver el odontograma",
                      font=FONTS["subtitle"], fill=COLORS["text_light"])

    def _draw(self):
        if not self._pac_id:
            self._draw_empty()
            return
        c = self._canvas
        c.delete("all")
        self._tooth_items.clear()
        self._tooth_centers.clear()

        margin_x = 30
        margin_y = 20

        # Filas: upper-perm, upper-temp, --- línea central ---, lower-temp, lower-perm
        rows = [
            (PERM_UPPER, margin_y,                          "Permanentes superiores"),
            (TEMP_UPPER, margin_y + STEP + 8,               "Temporales superiores"),
            (TEMP_LOWER, margin_y + STEP*2 + 30,            "Temporales inferiores"),
            (PERM_LOWER, margin_y + STEP*3 + 38,            "Permanentes inferiores"),
        ]

        # Línea central
        cy_line = margin_y + STEP*2 + 16
        c.create_line(margin_x, cy_line, margin_x + STEP*16 + 10, cy_line,
                      fill=COLORS["border"], dash=(4, 4))
        c.create_text(margin_x + STEP*16 + 30, cy_line, text="—", fill=COLORS["text_light"])

        for row_fdis, y0, row_label in rows:
            # Etiqueta de fila
            c.create_text(margin_x - 8, y0 + TS//2, text=row_label[:3],
                          font=FONTS["small"], fill=COLORS["text_light"], anchor="e")
            for col, fdi in enumerate(row_fdis):
                if fdi is None:
                    continue
                x0 = margin_x + col * STEP

                # Dibujar el diente
                self._draw_tooth(fdi, x0, y0)

                # Número FDI encima
                cx = x0 + TS // 2
                c.create_text(cx, y0 - 8, text=str(fdi),
                               font=FONTS["small"], fill=COLORS["text"])
                self._tooth_centers[fdi] = (cx, y0 + TS // 2)

            # Separador entre cuadrantes (entre columna 7 y 8)
            sep_x = margin_x + 8 * STEP - GAP // 2
            c.create_line(sep_x, y0 - 4, sep_x, y0 + TS + 4,
                          fill=COLORS["text_light"], width=2)

    def _draw_tooth(self, fdi: int, x0: int, y0: int):
        c = self._canvas
        tooth_data = self._data.get(fdi, {})
        condicion = tooth_data.get("condicion", "sano")
        superficies = tooth_data.get("superficies", {})

        polys = tooth_polygons(x0, y0)
        # Determinar si hay color de fondo por condición
        cond_color = CONDICION_COLORS.get(condicion)

        for surf, pts in polys.items():
            if condicion == "ausente":
                fill = "#E2E8F0"
            elif cond_color and surf == "O":
                fill = cond_color
            else:
                estado = superficies.get(surf, "sano")
                fill = STATE_COLORS.get(estado, "#FFFFFF")
            item = c.create_polygon(pts, fill=fill,
                                     outline=COLORS["tooth_border"], width=1,
                                     tags=(f"tooth_{fdi}", f"surf_{fdi}_{surf}", "surface"))
            self._tooth_items[(fdi, surf)] = item

        # Símbolo especial según condición
        cx, cy = x0 + TS // 2, y0 + TS // 2
        if condicion == "ausente":
            c.create_line(x0+4, y0+4, x0+TS-4, y0+TS-4, fill="#E53E3E", width=2,
                           tags=(f"tooth_{fdi}", "cond_sym"))
            c.create_line(x0+TS-4, y0+4, x0+4, y0+TS-4, fill="#E53E3E", width=2,
                           tags=(f"tooth_{fdi}", "cond_sym"))
        elif condicion == "implante":
            c.create_text(cx, cy, text="I", font=("Segoe UI", 8, "bold"),
                           fill="#FFFFFF", tags=(f"tooth_{fdi}", "cond_sym"))
        elif condicion == "corona":
            c.create_text(cx, cy, text="C", font=("Segoe UI", 8, "bold"),
                           fill="#2D3748", tags=(f"tooth_{fdi}", "cond_sym"))
        elif condicion == "endodoncia":
            c.create_oval(cx-4, cy-4, cx+4, cy+4, fill="#E53E3E", outline="",
                           tags=(f"tooth_{fdi}", "cond_sym"))
        elif condicion == "protesis_fija":
            c.create_text(cx, cy, text="PF", font=("Segoe UI", 7, "bold"),
                           fill="#2D3748", tags=(f"tooth_{fdi}", "cond_sym"))
        elif condicion == "sellante":
            c.create_text(cx, cy, text="S", font=("Segoe UI", 8, "bold"),
                           fill="#2D3748", tags=(f"tooth_{fdi}", "cond_sym"))

    # ── Interacción ───────────────────────────────────────────────────────────

    def _find_tooth_surf(self, event) -> Tuple[Optional[int], Optional[str]]:
        """Devuelve (fdi, superficie) bajo el cursor."""
        cx, cy = self._canvas.canvasx(event.x), self._canvas.canvasy(event.y)
        items = self._canvas.find_overlapping(cx-1, cy-1, cx+1, cy+1)
        for item in reversed(items):
            tags = self._canvas.gettags(item)
            for tag in tags:
                if tag.startswith("surf_"):
                    parts = tag.split("_")
                    return int(parts[1]), parts[2]
        return None, None

    def _on_left_click(self, event):
        if not self._pac_id:
            return
        fdi, surf = self._find_tooth_surf(event)
        if fdi is None:
            return
        self._selected_fdi = fdi
        self._lbl_sel.configure(
            text=f"Diente: {fdi} | Superficie: {surf or ''}"
        )
        tooth_data = self._data.get(fdi, {})
        self._notes_var.set(tooth_data.get("notas", "") or "")

        if surf:
            # Ciclar estado de superficie
            current = self._data.get(fdi, {}).get("superficies", {}).get(surf, "sano")
            idx = STATE_CYCLE.index(current) if current in STATE_CYCLE else 0
            next_state = STATE_CYCLE[(idx + 1) % len(STATE_CYCLE)]

            if fdi not in self._data:
                self._data[fdi] = {"condicion": "sano", "notas": "", "superficies": {}}
            self._data[fdi]["superficies"][surf] = next_state

            # Guardar en BD
            models.upsert_odontograma_superficie(self._pac_id, fdi, surf, next_state)
            # Actualizar color del canvas
            item = self._tooth_items.get((fdi, surf))
            if item:
                self._canvas.itemconfig(item, fill=STATE_COLORS.get(next_state, "#FFFFFF"))

    def _on_right_click(self, event):
        if not self._pac_id:
            return
        fdi, surf = self._find_tooth_surf(event)
        if fdi is None:
            return
        self._selected_fdi = fdi
        self._lbl_sel.configure(text=f"Diente: {fdi}")

        # Menú contextual
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label=f"── Diente {fdi} ──", state="disabled")
        menu.add_separator()

        if surf:
            menu.add_command(label=f"Superficie: {surf}", state="disabled")
            menu.add_separator()
            for estado in STATE_CYCLE:
                color = STATE_COLORS[estado]
                menu.add_command(
                    label=f"  {'● ' if self._data.get(fdi,{}).get('superficies',{}).get(surf,'sano')==estado else '  '}{estado.capitalize()}",
                    command=lambda s=surf, e=estado: self._set_surface_state(fdi, s, e)
                )
            menu.add_separator()

        menu.add_command(label="Condición del diente:", state="disabled")
        for cond in CONDICIONES:
            menu.add_command(
                label=f"  {'● ' if self._data.get(fdi,{}).get('condicion','sano')==cond else '  '}{cond.replace('_',' ').capitalize()}",
                command=lambda c=cond: self._set_condicion(fdi, c)
            )
        menu.add_separator()
        menu.add_command(label="📝 Editar notas", command=lambda: self._edit_notes(fdi))
        menu.add_separator()
        menu.add_command(label="💊 Registrar prestación",
                         command=lambda: self._registrar_prestacion(fdi, surf))

        menu.tk_popup(event.x_root, event.y_root)

    def _set_surface_state(self, fdi: int, surf: str, estado: str):
        if fdi not in self._data:
            self._data[fdi] = {"condicion": "sano", "notas": "", "superficies": {}}
        self._data[fdi]["superficies"][surf] = estado
        models.upsert_odontograma_superficie(self._pac_id, fdi, surf, estado)
        item = self._tooth_items.get((fdi, surf))
        if item:
            self._canvas.itemconfig(item, fill=STATE_COLORS.get(estado, "#FFFFFF"))

    def _set_condicion(self, fdi: int, condicion: str):
        if fdi not in self._data:
            self._data[fdi] = {"condicion": "sano", "notas": "", "superficies": {}}
        self._data[fdi]["condicion"] = condicion
        models.upsert_odontograma_diente(self._pac_id, fdi, condicion,
                                          self._data[fdi].get("notas",""))
        # Redibujar ese diente
        self._redraw_tooth(fdi)

    def _edit_notes(self, fdi: int):
        current = self._data.get(fdi, {}).get("notas", "") or ""
        nota = simpledialog.askstring("Notas", f"Notas para diente {fdi}:",
                                       initialvalue=current, parent=self)
        if nota is not None:
            if fdi not in self._data:
                self._data[fdi] = {"condicion": "sano", "notas": "", "superficies": {}}
            self._data[fdi]["notas"] = nota
            condicion = self._data[fdi].get("condicion", "sano")
            models.upsert_odontograma_diente(self._pac_id, fdi, condicion, nota)
            self._notes_var.set(nota)

    def _save_note(self):
        if not self._pac_id or not self._selected_fdi:
            return
        nota = self._notes_var.get().strip()
        fdi = self._selected_fdi
        if fdi not in self._data:
            self._data[fdi] = {"condicion": "sano", "notas": "", "superficies": {}}
        self._data[fdi]["notas"] = nota
        condicion = self._data[fdi].get("condicion", "sano")
        models.upsert_odontograma_diente(self._pac_id, fdi, condicion, nota)

    def _clear_tooth(self):
        if not self._pac_id or not self._selected_fdi:
            return
        fdi = self._selected_fdi
        if messagebox.askyesno("Confirmar", f"¿Limpiar todos los datos del diente {fdi}?"):
            self._data.pop(fdi, None)
            models.upsert_odontograma_diente(self._pac_id, fdi, "sano", "")
            for surf in ("V","L","M","D","O"):
                models.upsert_odontograma_superficie(self._pac_id, fdi, surf, "sano")
            self._redraw_tooth(fdi)

    def _redraw_tooth(self, fdi: int):
        """Redibuja únicamente el diente indicado."""
        # Eliminar items del canvas de ese diente
        self._canvas.delete(f"tooth_{fdi}")
        # Encontrar su posición
        if fdi in self._tooth_centers:
            # Recalcular x0, y0 desde el centro guardado
            cx, cy = self._tooth_centers[fdi]
            x0 = cx - TS // 2
            y0 = cy - TS // 2
            self._draw_tooth(fdi, x0, y0)

    def _registrar_prestacion(self, fdi: Optional[int], surf: Optional[str]):
        app_state.emit("nueva_prestacion", fdi=fdi, superficie=surf)
        self.winfo_toplevel().show_page("prestaciones")

    def on_show(self):
        self._refresh_pacientes()
        pid = app_state.paciente_id
        if pid and pid != self._pac_id:
            self._load_patient(pid)
