"""
pdf_export.py — Exportación de una entrada de Historia Clínica a PDF,
replicando las secciones del formulario "Historia Clínica General" en papel.

Requiere el paquete 'reportlab' (pip install reportlab).
"""
from __future__ import annotations
from typing import Dict, Optional
from xml.sax.saxutils import escape as _xml_escape

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Flowable

import historial_fields

_styles = getSampleStyleSheet()
_TITLE = ParagraphStyle("HCTitle", parent=_styles["Title"], fontSize=16, spaceAfter=2)
_SUBTITLE = ParagraphStyle("HCSubtitle", parent=_styles["Normal"], fontSize=10,
                            textColor=colors.HexColor("#4A5568"), spaceAfter=8)
_SECTION = ParagraphStyle("HCSection", parent=_styles["Heading2"], fontSize=12,
                           textColor=colors.HexColor("#2C5282"), spaceBefore=14, spaceAfter=6)
_BODY = ParagraphStyle("HCBody", parent=_styles["Normal"], fontSize=9.5, leading=13)
_LABEL = ParagraphStyle("HCLabel", parent=_styles["Normal"], fontSize=9.5,
                         leading=13, textColor=colors.HexColor("#4A5568"))

# ── Odontograma ──────────────────────────────────────────────────────────────
_ODO_PERM_UPPER = [18, 17, 16, 15, 14, 13, 12, 11, 21, 22, 23, 24, 25, 26, 27, 28]
_ODO_PERM_LOWER = [48, 47, 46, 45, 44, 43, 42, 41, 31, 32, 33, 34, 35, 36, 37, 38]
_ODO_TEMP_UPPER = [None, None, None, 55, 54, 53, 52, 51, 61, 62, 63, 64, 65, None, None, None]
_ODO_TEMP_LOWER = [None, None, None, 85, 84, 83, 82, 81, 71, 72, 73, 74, 75, None, None, None]

_ODO_STATE_COLORS = {
    "sano":       "#FFFFFF",
    "caries":     "#E53E3E",
    "obturacion": "#3182CE",
    "fractura":   "#718096",
    "pendiente":  "#BEE3F8",
}
_ODO_CONDICION_COLORS = {
    "sano":               None,
    "ausente":            "#2D3748",
    "implante":           "#9F7AEA",
    "corona":             "#F6E05E",
    "endodoncia":         "#FC8181",
    "protesis_fija":      "#FBD38D",
    "protesis_removible": "#FED7D7",
    "sellante":           "#C6F6D5",
}
_ODO_TS = 22      # tamaño de diente (pt)
_ODO_GAP = 4
_ODO_STEP = _ODO_TS + _ODO_GAP


def _odo_tooth_polygons(x0, y0):
    """Polígonos de las 5 superficies de un diente, en coordenadas de diseño
    (origen arriba-izquierda, Y crece hacia abajo, como en el canvas de la UI)."""
    s, q = _ODO_TS, _ODO_TS // 4
    return {
        "V": [(x0, y0), (x0 + s, y0), (x0 + s - q, y0 + q), (x0 + q, y0 + q)],
        "L": [(x0 + q, y0 + s - q), (x0 + s - q, y0 + s - q), (x0 + s, y0 + s), (x0, y0 + s)],
        "M": [(x0, y0), (x0 + q, y0 + q), (x0 + q, y0 + s - q), (x0, y0 + s)],
        "D": [(x0 + s - q, y0 + q), (x0 + s, y0), (x0 + s, y0 + s), (x0 + s - q, y0 + s - q)],
        "O": [(x0 + q, y0 + q), (x0 + s - q, y0 + q), (x0 + s - q, y0 + s - q), (x0 + q, y0 + s - q)],
    }


class _OdontogramaFlowable(Flowable):
    """Dibuja el odontograma completo (permanentes + temporales) replicando
    la grilla de la UI, usando primitivas de reportlab.canvas."""

    def __init__(self, data: Dict):
        Flowable.__init__(self)
        self.data = data or {}
        self._margin_x = 46
        self._margin_y = 14
        self._num_h = 9
        self._inner_gap = 12
        self._center_gap = 26
        self._legend_h = 20

        y_pu = self._margin_y
        y_tu = y_pu + _ODO_TS + self._inner_gap + self._num_h
        y_tl = y_tu + _ODO_TS + self._center_gap
        y_pl = y_tl + _ODO_TS + self._inner_gap + self._num_h
        self._rows = [
            (_ODO_PERM_UPPER, y_pu, "Per Sup"),
            (_ODO_TEMP_UPPER, y_tu, "Tem Sup"),
            (_ODO_TEMP_LOWER, y_tl, "Tem Inf"),
            (_ODO_PERM_LOWER, y_pl, "Per Inf"),
        ]
        self._cy_line = (y_tu + _ODO_TS + y_tl) / 2.0
        self.width = self._margin_x + _ODO_STEP * 16 + 10
        self.height = y_pl + _ODO_TS + self._margin_y + self._legend_h

    def wrap(self, availWidth, availHeight):
        return (self.width, self.height)

    def _y(self, y_local):
        """Convierte una coordenada de diseño (Y hacia abajo) a coordenada de canvas (Y hacia arriba)."""
        return self.height - self._legend_h - y_local

    def draw(self):
        c = self.canv

        c.setStrokeColor(colors.HexColor("#CBD5E0"))
        c.setDash(4, 3)
        c.line(self._margin_x, self._y(self._cy_line),
               self._margin_x + _ODO_STEP * 16 + 10, self._y(self._cy_line))
        c.setDash()

        for row_fdis, y0, row_label in self._rows:
            c.setFillColor(colors.HexColor("#718096"))
            c.setFont("Helvetica", 6.5)
            c.drawRightString(self._margin_x - 6, self._y(y0 + _ODO_TS / 2) - 2, row_label)

            for col, fdi in enumerate(row_fdis):
                if fdi is None:
                    continue
                x0 = self._margin_x + col * _ODO_STEP
                self._draw_tooth(fdi, x0, y0)
                cx = x0 + _ODO_TS / 2
                c.setFillColor(colors.HexColor("#2D3748"))
                c.setFont("Helvetica", 6)
                c.drawCentredString(cx, self._y(y0 - self._num_h / 2) - 2, str(fdi))

            sep_x = self._margin_x + 8 * _ODO_STEP - _ODO_GAP / 2
            c.setStrokeColor(colors.HexColor("#718096"))
            c.setLineWidth(1)
            c.line(sep_x, self._y(y0 - 6), sep_x, self._y(y0 + _ODO_TS + 6))

        self._draw_legend()

    def _draw_tooth(self, fdi, x0, y0):
        c = self.canv
        tooth = self.data.get(fdi) or self.data.get(str(fdi)) or {}
        condicion = tooth.get("condicion", "sano")
        superficies = tooth.get("superficies", {})
        cond_color = _ODO_CONDICION_COLORS.get(condicion)

        for surf, pts in _odo_tooth_polygons(x0, y0).items():
            if condicion == "ausente":
                fill = "#E2E8F0"
            elif cond_color and surf == "O":
                fill = cond_color
            else:
                estado = superficies.get(surf, "sano")
                fill = _ODO_STATE_COLORS.get(estado, "#FFFFFF")

            path = c.beginPath()
            for i, (px, py) in enumerate(pts):
                pcx, pcy = px, self._y(py)
                if i == 0:
                    path.moveTo(pcx, pcy)
                else:
                    path.lineTo(pcx, pcy)
            path.close()
            c.setFillColor(colors.HexColor(fill))
            c.setStrokeColor(colors.HexColor("#2D3748"))
            c.setLineWidth(0.4)
            c.drawPath(path, fill=1, stroke=1)

        cx, cy = x0 + _ODO_TS / 2, self._y(y0 + _ODO_TS / 2)
        if condicion == "ausente":
            c.setStrokeColor(colors.HexColor("#E53E3E"))
            c.setLineWidth(1.3)
            c.line(x0 + 3, self._y(y0 + 3), x0 + _ODO_TS - 3, self._y(y0 + _ODO_TS - 3))
            c.line(x0 + _ODO_TS - 3, self._y(y0 + 3), x0 + 3, self._y(y0 + _ODO_TS - 3))
        elif condicion == "implante":
            c.setFillColor(colors.white)
            c.setFont("Helvetica-Bold", 6)
            c.drawCentredString(cx, cy - 2, "I")
        elif condicion == "corona":
            c.setFillColor(colors.HexColor("#2D3748"))
            c.setFont("Helvetica-Bold", 6)
            c.drawCentredString(cx, cy - 2, "C")
        elif condicion == "endodoncia":
            c.setFillColor(colors.HexColor("#E53E3E"))
            c.circle(cx, cy, 2.4, fill=1, stroke=0)
        elif condicion == "protesis_fija":
            c.setFillColor(colors.HexColor("#2D3748"))
            c.setFont("Helvetica-Bold", 5)
            c.drawCentredString(cx, cy - 2, "PF")
        elif condicion == "sellante":
            c.setFillColor(colors.HexColor("#2D3748"))
            c.setFont("Helvetica-Bold", 6)
            c.drawCentredString(cx, cy - 2, "S")

    def _draw_legend(self):
        c = self.canv
        box = 8
        x = self._margin_x
        y = 5
        for estado in ("caries", "obturacion", "fractura", "pendiente"):
            color = _ODO_STATE_COLORS[estado]
            c.setFillColor(colors.HexColor(color))
            c.setStrokeColor(colors.HexColor("#2D3748"))
            c.setLineWidth(0.4)
            c.rect(x, y, box, box, fill=1, stroke=1)
            label = estado.capitalize()
            c.setFillColor(colors.HexColor("#2D3748"))
            c.setFont("Helvetica", 6.5)
            c.drawString(x + box + 3, y + 1, label)
            x += box + 3 + c.stringWidth(label, "Helvetica", 6.5) + 14


def _fmt_bool(value) -> str:
    if value == 1:
        return "Sí"
    if value == 0:
        return "No"
    return "—"


def _p_text(value) -> str:
    """Escapa el texto para insertarlo en un Paragraph y convierte saltos de línea."""
    text = str(value) if value not in (None, "") else "—"
    return _xml_escape(text).replace("\n", "<br/>")


def _section_rows(fields, entry: Dict):
    rows = []
    for field in fields:
        key, ftype, label = field[0], field[1], field[2]
        val = entry.get(key)
        display = _fmt_bool(val) if ftype == "bool" else _p_text(val)
        rows.append((_xml_escape(label), display))
    return rows


def _add_table(story, rows):
    if not rows:
        return
    data = [[Paragraph(lbl, _LABEL), Paragraph(val, _BODY)] for lbl, val in rows]
    tbl = Table(data, colWidths=[7.5 * cm, 8.5 * cm])
    tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#E2E8F0")),
    ]))
    story.append(tbl)


def generar_pdf_historial(path: str, entry: Dict, paciente: Dict, odontologo: Optional[Dict],
                           odontograma: Optional[Dict] = None):
    """Genera un PDF con toda la información de una entrada de Historia Clínica.

    Si se provee `odontograma` (ver models.get_odontograma), se agrega una
    sección con la grilla completa del odontograma del paciente.
    """
    doc = SimpleDocTemplate(
        path, pagesize=A4,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
    )
    story = []

    story.append(Paragraph("Historia Clínica General", _TITLE))
    story.append(Paragraph("Consultorio Odontológico Passera", _SUBTITLE))

    od_nombre = f"{odontologo.get('apellido','')}, {odontologo.get('nombre','')}" if odontologo else "—"
    header_data = [
        ["Paciente", f"{paciente.get('apellido','')}, {paciente.get('nombre','')}"],
        ["DNI", paciente.get("dni") or "—"],
        ["Fecha de nacimiento", paciente.get("fecha_nacimiento") or "—"],
        ["Odontólogo", od_nombre],
        ["Fecha de la consulta", entry.get("fecha") or "—"],
        ["Lugar", entry.get("lugar") or "—"],
    ]
    t = Table(header_data, colWidths=[4.5 * cm, 11.5 * cm])
    t.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#4A5568")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(t)

    for skey, title, fields in historial_fields.SECTIONS:
        if skey == "datos":
            continue
        story.append(Paragraph(_xml_escape(title), _SECTION))
        _add_table(story, _section_rows(fields, entry))

    if odontograma:
        story.append(Paragraph("Odontograma", _SECTION))
        story.append(_OdontogramaFlowable(odontograma))
        story.append(Paragraph(
            "Símbolos: I = Implante · C = Corona · ● = Endodoncia · "
            "PF = Prótesis fija · S = Sellante · X = Ausente",
            ParagraphStyle("HCPerioNote", parent=_BODY, fontSize=8, textColor=colors.HexColor("#718096")),
        ))
        story.append(Spacer(1, 6))

    story.append(Paragraph("Diagnóstico y Plan de Tratamiento", _SECTION))
    _add_table(story, [
        ("Diagnóstico presuntivo",     _p_text(entry.get("diagnostico"))),
        ("Plan de tratamiento",        _p_text(entry.get("tratamiento"))),
        ("Observaciones",              _p_text(entry.get("notas"))),
        ("Informes externos",          _p_text(entry.get("informes_ext"))),
        ("Radiografías adjuntas",      str(entry.get("radiografias") or 0)),
    ])

    story.append(Spacer(1, 22))
    story.append(Paragraph(
        "Declaro que he contestado todas las preguntas con honestidad y según mi conocimiento. "
        "Asimismo, he sido informado que los datos suministrados quedan reservados en la presente "
        "Historia Clínica y amparados en secreto profesional.",
        _BODY,
    ))
    story.append(Spacer(1, 30))
    firma_data = [["", "", ""], ["Firma del paciente o tutor", "Aclaración", "DNI N°"]]
    firma_tbl = Table(firma_data, colWidths=[6 * cm, 5 * cm, 5 * cm])
    firma_tbl.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.black),
        ("FONTSIZE", (0, 1), (-1, 1), 8.5),
        ("TEXTCOLOR", (0, 1), (-1, 1), colors.HexColor("#4A5568")),
        ("TOPPADDING", (0, 1), (-1, 1), 4),
    ]))
    story.append(firma_tbl)

    doc.build(story)
