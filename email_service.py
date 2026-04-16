"""
email_service.py — Servicio de notificaciones por correo electrónico.
Consultorio Odontológico Passera
"""
from __future__ import annotations
import json
import os
import smtplib
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Callable, Dict, Optional

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "email_config.json")

_DEFAULT_CONFIG: Dict = {
    "smtp_server":   "smtp.gmail.com",
    "smtp_port":     587,
    "use_tls":       True,
    "username":      "consultorioodontologicopassera@gmail.com",
    "password":      "wybr rokj etus suwv",
    "from_name":     "Consultorio Odontológico Passera",
    "from_address":  "consultorioodontologicopassera@gmail.com",
    "enabled":       False,
}


# ─────────────────────────────────────────────────────────────
# Configuración
# ─────────────────────────────────────────────────────────────

def load_config() -> Dict:
    """Carga la configuración SMTP desde disco. Retorna defaults si no existe."""
    if not os.path.exists(CONFIG_PATH):
        return dict(_DEFAULT_CONFIG)
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            stored = json.load(f)
        cfg = dict(_DEFAULT_CONFIG)
        cfg.update(stored)
        return cfg
    except Exception:
        return dict(_DEFAULT_CONFIG)


def save_config(cfg: Dict) -> None:
    """Persiste la configuración SMTP en disco."""
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


# ─────────────────────────────────────────────────────────────
# Envío de email
# ─────────────────────────────────────────────────────────────

def _build_message(cfg: Dict, to_address: str, to_name: str,
                   turno: Dict, paciente: Dict, odontologo: Dict) -> MIMEMultipart:
    """Arma el mensaje MIME con cuerpo HTML y texto plano."""
    fecha  = turno.get("fecha", "")
    hora   = turno.get("hora", "")
    motivo = turno.get("motivo", "") or "Consulta general"
    dur    = turno.get("duracion_min", 30)
    od_nombre = f"Dr./Dra. {odontologo.get('nombre','')} {odontologo.get('apellido','')}"

    subject = f"Turno confirmado — {fecha} {hora} | Consultorio Passera"

    html = f"""
    <html><body style="font-family:Arial,sans-serif;color:#333;max-width:600px;margin:auto">
      <div style="background:#2B6CB0;padding:20px 24px;border-radius:8px 8px 0 0">
        <h1 style="color:#fff;margin:0;font-size:20px">🦷 Consultorio Odontológico Passera</h1>
      </div>
      <div style="background:#f9f9f9;padding:24px;border:1px solid #ddd;border-top:none;border-radius:0 0 8px 8px">
        <p style="font-size:16px">Estimado/a <strong>{to_name}</strong>,</p>
        <p>Le confirmamos que tiene un turno programado con los siguientes datos:</p>
        <table style="width:100%;border-collapse:collapse;margin:16px 0">
          <tr style="background:#EBF8FF">
            <td style="padding:10px 14px;font-weight:bold;border:1px solid #bee3f8">📅 Fecha</td>
            <td style="padding:10px 14px;border:1px solid #bee3f8">{fecha}</td>
          </tr>
          <tr>
            <td style="padding:10px 14px;font-weight:bold;border:1px solid #bee3f8">⏰ Hora</td>
            <td style="padding:10px 14px;border:1px solid #bee3f8">{hora} hs ({dur} min)</td>
          </tr>
          <tr style="background:#EBF8FF">
            <td style="padding:10px 14px;font-weight:bold;border:1px solid #bee3f8">👨‍⚕️ Profesional</td>
            <td style="padding:10px 14px;border:1px solid #bee3f8">{od_nombre}</td>
          </tr>
          <tr>
            <td style="padding:10px 14px;font-weight:bold;border:1px solid #bee3f8">📋 Motivo</td>
            <td style="padding:10px 14px;border:1px solid #bee3f8">{motivo}</td>
          </tr>
        </table>
        <p style="color:#555;font-size:14px">
          Si necesita cancelar o reprogramar su turno, comuníquese con nosotros
          con la mayor anticipación posible.
        </p>
        <hr style="border:none;border-top:1px solid #ddd;margin:20px 0">
        <p style="color:#888;font-size:12px;text-align:center">
          Consultorio Odontológico Passera — Córdoba, Argentina<br>
          Este es un mensaje automático, por favor no responda este correo.
        </p>
      </div>
    </body></html>
    """

    plain = (
        f"Estimado/a {to_name},\n\n"
        f"Su turno ha sido confirmado:\n"
        f"  Fecha:       {fecha}\n"
        f"  Hora:        {hora} hs ({dur} min)\n"
        f"  Profesional: {od_nombre}\n"
        f"  Motivo:      {motivo}\n\n"
        f"Consultorio Odontológico Passera — Córdoba\n"
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"{cfg['from_name']} <{cfg['from_address']}>"
    msg["To"]      = f"{to_name} <{to_address}>"
    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(html,  "html",  "utf-8"))
    return msg


def _send_smtp(cfg: Dict, msg: MIMEMultipart, to_address: str) -> None:
    """Realiza la conexión SMTP y envía el mensaje."""
    port = int(cfg["smtp_port"])
    if cfg["use_tls"]:
        server = smtplib.SMTP(cfg["smtp_server"], port, timeout=15)
        server.ehlo()
        server.starttls()
    else:
        server = smtplib.SMTP_SSL(cfg["smtp_server"], port, timeout=15)
    server.ehlo()
    if cfg["username"]:
        server.login(cfg["username"], cfg["password"])
    server.sendmail(cfg["from_address"], [to_address], msg.as_string())
    server.quit()


def send_turno_notification(
    turno: Dict,
    paciente: Dict,
    odontologo: Dict,
    on_success: Optional[Callable[[], None]] = None,
    on_error: Optional[Callable[[str], None]] = None,
) -> None:
    """
    Envía en un hilo secundario la notificación de turno al paciente.
    Si el email no está configurado o el paciente no tiene email, no hace nada.
    """
    cfg = load_config()
    if not cfg.get("enabled"):
        return
    if not cfg.get("smtp_server") or not cfg.get("from_address"):
        return

    to_address = (paciente.get("email") or "").strip()
    if not to_address:
        return

    to_name = f"{paciente.get('nombre','')} {paciente.get('apellido','')}".strip()

    def _worker():
        try:
            msg = _build_message(cfg, to_address, to_name, turno, paciente, odontologo)
            _send_smtp(cfg, msg, to_address)
            if on_success:
                on_success()
        except Exception as exc:
            if on_error:
                on_error(str(exc))

    threading.Thread(target=_worker, daemon=True).start()


def test_connection(cfg: Dict) -> str:
    """
    Intenta conectarse al servidor SMTP con la configuración dada.
    Retorna "" si todo OK, o el mensaje de error.
    """
    try:
        port = int(cfg["smtp_port"])
        if cfg["use_tls"]:
            server = smtplib.SMTP(cfg["smtp_server"], port, timeout=10)
            server.ehlo()
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(cfg["smtp_server"], port, timeout=10)
        server.ehlo()
        if cfg["username"]:
            server.login(cfg["username"], cfg["password"])
        server.quit()
        return ""
    except Exception as exc:
        return str(exc)
