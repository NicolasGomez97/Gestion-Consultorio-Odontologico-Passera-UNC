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
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

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


def generar_pdf_historial(path: str, entry: Dict, paciente: Dict, odontologo: Optional[Dict]):
    """Genera un PDF con toda la información de una entrada de Historia Clínica."""
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
