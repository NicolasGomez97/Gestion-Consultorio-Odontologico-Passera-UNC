"""
models.py — Todas las operaciones CRUD sobre la base de datos.
Consultorio Odontológico Passera
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
import json
import hashlib
from database import get_connection

# ─────────────────────────────────────────────────────────────
# OBRAS SOCIALES
# ─────────────────────────────────────────────────────────────

def get_obras_sociales() -> List[Dict]:
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM obras_sociales WHERE activo=1 ORDER BY nombre"
        ).fetchall()]


def get_obra_social_map() -> Dict[int, str]:
    """Devuelve {id: nombre} para combos."""
    return {r["id"]: r["nombre"] for r in get_obras_sociales()}


def save_obra_social(data: Dict) -> int:
    with get_connection() as conn:
        if data.get("id"):
            conn.execute(
                "UPDATE obras_sociales SET nombre=?, codigo=?, activo=? WHERE id=?",
                (data["nombre"], data.get("codigo",""), data.get("activo",1), data["id"]),
            )
            return data["id"]
        cur = conn.execute(
            "INSERT INTO obras_sociales (nombre, codigo) VALUES (?, ?)",
            (data["nombre"], data.get("codigo","")),
        )
        return cur.lastrowid


# ─────────────────────────────────────────────────────────────
# ODONTÓLOGOS
# ─────────────────────────────────────────────────────────────

def get_odontologos(solo_activos: bool = True) -> List[Dict]:
    where = "WHERE activo=1" if solo_activos else ""
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(
            f"SELECT * FROM odontologos {where} ORDER BY apellido, nombre"
        ).fetchall()]


def get_odontologo(id_: int) -> Optional[Dict]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM odontologos WHERE id=?", (id_,)).fetchone()
        return dict(row) if row else None


def get_odontologo_map() -> Dict[int, str]:
    return {r["id"]: f"{r['apellido']}, {r['nombre']}" for r in get_odontologos()}


def save_odontologo(data: Dict) -> int:
    cols = ["nombre", "apellido", "especialidad", "matricula", "circulo", "telefono", "email", "activo"]
    vals = [data.get(c, "") for c in cols[:-1]] + [data.get("activo", 1)]
    with get_connection() as conn:
        if data.get("id"):
            sets = ", ".join(f"{c}=?" for c in cols)
            conn.execute(f"UPDATE odontologos SET {sets} WHERE id=?", vals + [data["id"]])
            return data["id"]
        placeholders = ", ".join("?" for _ in cols)
        cur = conn.execute(
            f"INSERT INTO odontologos ({', '.join(cols)}) VALUES ({placeholders})", vals
        )
        return cur.lastrowid


def delete_odontologo(id_: int):
    with get_connection() as conn:
        conn.execute("UPDATE odontologos SET activo=0 WHERE id=?", (id_,))


# ─────────────────────────────────────────────────────────────
# PACIENTES
# ─────────────────────────────────────────────────────────────

_PACIENTE_COLS = [
    "nombre", "apellido", "dni", "fecha_nacimiento", "sexo", "estado_civil",
    "direccion", "telefono", "email", "obra_social_id", "num_afiliado",
    "titular", "grupo_familiar", "lugar_trabajo", "jerarquia",
    "alergias", "enfermedades", "medico_clinico", "observaciones", "activo",
]


def get_pacientes(solo_activos: bool = True) -> List[Dict]:
    where = "WHERE p.activo=1" if solo_activos else ""
    with get_connection() as conn:
        rows = conn.execute(f"""
            SELECT p.*, os.nombre AS obra_social_nombre
            FROM pacientes p
            LEFT JOIN obras_sociales os ON os.id = p.obra_social_id
            {where}
            ORDER BY p.apellido, p.nombre
        """).fetchall()
        return [dict(r) for r in rows]


def get_paciente(id_: int) -> Optional[Dict]:
    with get_connection() as conn:
        row = conn.execute("""
            SELECT p.*, os.nombre AS obra_social_nombre
            FROM pacientes p
            LEFT JOIN obras_sociales os ON os.id = p.obra_social_id
            WHERE p.id=?
        """, (id_,)).fetchone()
        return dict(row) if row else None


def save_paciente(data: Dict) -> int:
    vals = [data.get(c) for c in _PACIENTE_COLS]
    with get_connection() as conn:
        if data.get("id"):
            sets = ", ".join(f"{c}=?" for c in _PACIENTE_COLS)
            conn.execute(
                f"UPDATE pacientes SET {sets}, updated_at=datetime('now','localtime') WHERE id=?",
                vals + [data["id"]],
            )
            return data["id"]
        cols_str = ", ".join(_PACIENTE_COLS)
        ph = ", ".join("?" for _ in _PACIENTE_COLS)
        cur = conn.execute(f"INSERT INTO pacientes ({cols_str}) VALUES ({ph})", vals)
        return cur.lastrowid


def delete_paciente(id_: int):
    with get_connection() as conn:
        conn.execute("UPDATE pacientes SET activo=0, updated_at=datetime('now','localtime') WHERE id=?", (id_,))


def search_pacientes(criterios: Dict) -> List[Dict]:
    """
    Búsqueda avanzada multi-criterio.
    criterios puede tener: nombre, apellido, dni, obra_social_id,
    num_afiliado, estado_civil, odontologo_id, enfermedades,
    fecha_nacimiento_desde, fecha_nacimiento_hasta, edad_min, edad_max
    """
    clauses = ["p.activo = 1"]
    params: List[Any] = []

    def like(campo, valor):
        clauses.append(f"LOWER(p.{campo}) LIKE LOWER(?)")
        params.append(f"%{valor}%")

    if criterios.get("nombre"):      like("nombre", criterios["nombre"])
    if criterios.get("apellido"):    like("apellido", criterios["apellido"])
    if criterios.get("dni"):         like("dni", criterios["dni"])
    if criterios.get("num_afiliado"):like("num_afiliado", criterios["num_afiliado"])
    if criterios.get("enfermedades"):like("enfermedades", criterios["enfermedades"])
    if criterios.get("observaciones"):like("observaciones", criterios["observaciones"])
    if criterios.get("estado_civil"):
        clauses.append("p.estado_civil = ?")
        params.append(criterios["estado_civil"])
    if criterios.get("obra_social_id"):
        clauses.append("p.obra_social_id = ?")
        params.append(criterios["obra_social_id"])
    if criterios.get("fecha_nacimiento_desde"):
        clauses.append("p.fecha_nacimiento >= ?")
        params.append(criterios["fecha_nacimiento_desde"])
    if criterios.get("fecha_nacimiento_hasta"):
        clauses.append("p.fecha_nacimiento <= ?")
        params.append(criterios["fecha_nacimiento_hasta"])
    if criterios.get("edad_min"):
        clauses.append("CAST((julianday('now') - julianday(p.fecha_nacimiento)) / 365.25 AS INTEGER) >= ?")
        params.append(int(criterios["edad_min"]))
    if criterios.get("edad_max"):
        clauses.append("CAST((julianday('now') - julianday(p.fecha_nacimiento)) / 365.25 AS INTEGER) <= ?")
        params.append(int(criterios["edad_max"]))

    # Filtro por odontólogo: paciente tuvo al menos un turno o prestación con ese odontólogo
    if criterios.get("odontologo_id"):
        clauses.append("""
            EXISTS (SELECT 1 FROM turnos t WHERE t.paciente_id = p.id
                    AND t.odontologo_id = ?)
        """)
        params.append(criterios["odontologo_id"])

    # Filtro por profundidad de sonda
    if criterios.get("profundidad_min"):
        clauses.append("""
            EXISTS (
                SELECT 1 FROM ficha_periodontal fp
                JOIN periodontal_medicion pm ON pm.ficha_id = fp.id
                WHERE fp.paciente_id = p.id
                AND (
                    CAST(SUBSTR(pm.prof_bolsa, 1, 1) AS INTEGER) >= ?
                )
            )
        """)
        params.append(int(criterios["profundidad_min"]))

    where = " AND ".join(clauses)
    with get_connection() as conn:
        rows = conn.execute(f"""
            SELECT p.*, os.nombre AS obra_social_nombre
            FROM pacientes p
            LEFT JOIN obras_sociales os ON os.id = p.obra_social_id
            WHERE {where}
            ORDER BY p.apellido, p.nombre
            LIMIT 500
        """, params).fetchall()
        return [dict(r) for r in rows]


# ─────────────────────────────────────────────────────────────
# TURNOS
# ─────────────────────────────────────────────────────────────

def get_turnos(fecha: Optional[str] = None, odontologo_id: Optional[int] = None,
               paciente_id: Optional[int] = None) -> List[Dict]:
    clauses = []
    params = []
    if fecha:
        clauses.append("t.fecha = ?")
        params.append(fecha)
    if odontologo_id:
        clauses.append("t.odontologo_id = ?")
        params.append(odontologo_id)
    if paciente_id:
        clauses.append("t.paciente_id = ?")
        params.append(paciente_id)
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    with get_connection() as conn:
        rows = conn.execute(f"""
            SELECT t.*,
                   p.nombre || ' ' || p.apellido AS paciente_nombre,
                   o.nombre || ' ' || o.apellido AS odontologo_nombre
            FROM turnos t
            JOIN pacientes p ON p.id = t.paciente_id
            JOIN odontologos o ON o.id = t.odontologo_id
            {where}
            ORDER BY t.fecha, t.hora
        """, params).fetchall()
        return [dict(r) for r in rows]


def get_turnos_semana(fecha_inicio: str, fecha_fin: str) -> List[Dict]:
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT t.*,
                   p.nombre || ' ' || p.apellido AS paciente_nombre,
                   o.nombre || ' ' || o.apellido AS odontologo_nombre,
                   o.especialidad
            FROM turnos t
            JOIN pacientes p ON p.id = t.paciente_id
            JOIN odontologos o ON o.id = t.odontologo_id
            WHERE t.fecha BETWEEN ? AND ?
            ORDER BY t.fecha, t.hora
        """, (fecha_inicio, fecha_fin)).fetchall()
        return [dict(r) for r in rows]


def save_turno(data: Dict) -> int:
    cols = ["paciente_id", "odontologo_id", "fecha", "hora",
            "duracion_min", "motivo", "estado", "notas"]
    vals = [data.get(c) for c in cols]
    with get_connection() as conn:
        if data.get("id"):
            sets = ", ".join(f"{c}=?" for c in cols)
            conn.execute(f"UPDATE turnos SET {sets} WHERE id=?", vals + [data["id"]])
            return data["id"]
        ph = ", ".join("?" for _ in cols)
        cur = conn.execute(f"INSERT INTO turnos ({', '.join(cols)}) VALUES ({ph})", vals)
        return cur.lastrowid


def delete_turno(id_: int):
    with get_connection() as conn:
        conn.execute("UPDATE turnos SET estado='cancelado' WHERE id=?", (id_,))


def get_turno(id_: int) -> Optional[Dict]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM turnos WHERE id=?", (id_,)).fetchone()
        return dict(row) if row else None


# ─────────────────────────────────────────────────────────────
# HISTORIAL CLÍNICO
# ─────────────────────────────────────────────────────────────

def get_historial(paciente_id: int) -> List[Dict]:
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT h.*,
                   o.nombre || ' ' || o.apellido AS odontologo_nombre
            FROM historial_clinico h
            JOIN odontologos o ON o.id = h.odontologo_id
            WHERE h.paciente_id = ?
            ORDER BY h.fecha DESC, h.created_at DESC
        """, (paciente_id,)).fetchall()
        return [dict(r) for r in rows]


def get_historial_entry(id_: int) -> Optional[Dict]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM historial_clinico WHERE id=?", (id_,)).fetchone()
        return dict(row) if row else None


def save_historial(data: Dict) -> int:
    cols = ["paciente_id", "odontologo_id", "fecha", "diagnostico",
            "tratamiento", "notas", "radiografias", "informes_ext"]
    vals = [data.get(c) for c in cols]
    with get_connection() as conn:
        if data.get("id"):
            sets = ", ".join(f"{c}=?" for c in cols)
            conn.execute(f"UPDATE historial_clinico SET {sets} WHERE id=?", vals + [data["id"]])
            return data["id"]
        ph = ", ".join("?" for _ in cols)
        cur = conn.execute(f"INSERT INTO historial_clinico ({', '.join(cols)}) VALUES ({ph})", vals)
        return cur.lastrowid


def delete_historial(id_: int):
    with get_connection() as conn:
        conn.execute("DELETE FROM historial_clinico WHERE id=?", (id_,))


# ─────────────────────────────────────────────────────────────
# ODONTOGRAMA
# ─────────────────────────────────────────────────────────────

def get_odontograma(paciente_id: int) -> Dict:
    """
    Devuelve el estado del odontograma como dict:
    {
      fdi: {
        "condicion": "sano",
        "notas": "",
        "superficies": {"V": "sano", "L": "caries", ...}
      }
    }
    """
    result: Dict[int, Dict] = {}
    with get_connection() as conn:
        # Dientes
        for row in conn.execute(
            "SELECT numero_fdi, condicion, notas FROM odontograma_diente WHERE paciente_id=?",
            (paciente_id,)
        ).fetchall():
            fdi = row["numero_fdi"]
            result[fdi] = {"condicion": row["condicion"], "notas": row["notas"] or "", "superficies": {}}

        # Superficies
        for row in conn.execute(
            "SELECT numero_fdi, superficie, estado FROM odontograma_superficie WHERE paciente_id=?",
            (paciente_id,)
        ).fetchall():
            fdi = row["numero_fdi"]
            if fdi not in result:
                result[fdi] = {"condicion": "sano", "notas": "", "superficies": {}}
            result[fdi]["superficies"][row["superficie"]] = row["estado"]
    return result


def upsert_odontograma_diente(paciente_id: int, numero_fdi: int, condicion: str, notas: str = ""):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO odontograma_diente (paciente_id, numero_fdi, condicion, notas, updated_at)
            VALUES (?, ?, ?, ?, datetime('now','localtime'))
            ON CONFLICT(paciente_id, numero_fdi) DO UPDATE SET
                condicion=excluded.condicion,
                notas=excluded.notas,
                updated_at=excluded.updated_at
        """, (paciente_id, numero_fdi, condicion, notas))


def upsert_odontograma_superficie(paciente_id: int, numero_fdi: int, superficie: str, estado: str):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO odontograma_superficie (paciente_id, numero_fdi, superficie, estado, updated_at)
            VALUES (?, ?, ?, ?, datetime('now','localtime'))
            ON CONFLICT(paciente_id, numero_fdi, superficie) DO UPDATE SET
                estado=excluded.estado,
                updated_at=excluded.updated_at
        """, (paciente_id, numero_fdi, superficie, estado))


# ─────────────────────────────────────────────────────────────
# FICHA PERIODONTAL
# ─────────────────────────────────────────────────────────────

def get_fichas_periodontales(paciente_id: int) -> List[Dict]:
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT fp.*, o.nombre || ' ' || o.apellido AS odontologo_nombre
            FROM ficha_periodontal fp
            JOIN odontologos o ON o.id = fp.odontologo_id
            WHERE fp.paciente_id = ?
            ORDER BY fp.fecha DESC
        """, (paciente_id,)).fetchall()
        return [dict(r) for r in rows]


def get_ficha_periodontal(id_: int) -> Optional[Dict]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM ficha_periodontal WHERE id=?", (id_,)).fetchone()
        if not row:
            return None
        ficha = dict(row)
        mediciones = conn.execute(
            "SELECT * FROM periodontal_medicion WHERE ficha_id=? ORDER BY numero_fdi",
            (id_,)
        ).fetchall()
        ficha["mediciones"] = {m["numero_fdi"]: dict(m) for m in mediciones}
        return ficha


def save_ficha_periodontal(data: Dict) -> int:
    cols = ["paciente_id", "odontologo_id", "fecha", "estado_encias",
            "indice_placa", "indice_sangrado", "notas"]
    vals = [data.get(c) for c in cols]
    with get_connection() as conn:
        if data.get("id"):
            sets = ", ".join(f"{c}=?" for c in cols)
            conn.execute(f"UPDATE ficha_periodontal SET {sets} WHERE id=?", vals + [data["id"]])
            ficha_id = data["id"]
        else:
            ph = ", ".join("?" for _ in cols)
            cur = conn.execute(f"INSERT INTO ficha_periodontal ({', '.join(cols)}) VALUES ({ph})", vals)
            ficha_id = cur.lastrowid

        # Guardar mediciones
        if "mediciones" in data:
            for fdi, m in data["mediciones"].items():
                conn.execute("""
                    INSERT INTO periodontal_medicion
                        (ficha_id, numero_fdi, prof_bolsa, margen_gingival, sangrado, placa, furcacion)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(ficha_id, numero_fdi) DO UPDATE SET
                        prof_bolsa=excluded.prof_bolsa,
                        margen_gingival=excluded.margen_gingival,
                        sangrado=excluded.sangrado,
                        placa=excluded.placa,
                        furcacion=excluded.furcacion
                """, (ficha_id, fdi, m.get("prof_bolsa","0,0,0,0,0,0"),
                      m.get("margen_gingival","0,0,0,0,0,0"),
                      m.get("sangrado","0,0,0,0,0,0"),
                      m.get("placa","0,0,0,0,0,0"),
                      m.get("furcacion", 0)))
    return ficha_id


# ─────────────────────────────────────────────────────────────
# NOMENCLADOR
# ─────────────────────────────────────────────────────────────

def get_nomenclador(categoria: Optional[str] = None) -> List[Dict]:
    where = "WHERE categoria=?" if categoria else ""
    params = [categoria] if categoria else []
    with get_connection() as conn:
        rows = conn.execute(
            f"SELECT * FROM nomenclador {where} ORDER BY codigo", params
        ).fetchall()
        return [dict(r) for r in rows]


def get_nomenclador_map() -> Dict[int, str]:
    return {r["id"]: f"{r['codigo']} - {r['descripcion']}" for r in get_nomenclador()}


def get_categorias_nomenclador() -> List[str]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT categoria FROM nomenclador ORDER BY categoria"
        ).fetchall()
        return [r["categoria"] for r in rows if r["categoria"]]


# ─────────────────────────────────────────────────────────────
# REGISTRO DE PRESTACIONES
# ─────────────────────────────────────────────────────────────

def get_prestaciones(paciente_id: Optional[int] = None,
                     desde: Optional[str] = None,
                     hasta: Optional[str] = None,
                     pendiente_federacion: bool = False) -> List[Dict]:
    clauses = []
    params = []
    if paciente_id:
        clauses.append("rp.paciente_id = ?")
        params.append(paciente_id)
    if desde:
        clauses.append("rp.fecha >= ?")
        params.append(desde)
    if hasta:
        clauses.append("rp.fecha <= ?")
        params.append(hasta)
    if pendiente_federacion:
        clauses.append("rp.enviado_federacion = 0")
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    with get_connection() as conn:
        rows = conn.execute(f"""
            SELECT rp.*,
                   p.nombre || ' ' || p.apellido AS paciente_nombre,
                   o.nombre || ' ' || o.apellido AS odontologo_nombre,
                   n.codigo AS nom_codigo, n.descripcion AS nom_descripcion,
                   os.nombre AS obra_social_nombre
            FROM registro_prestaciones rp
            JOIN pacientes p ON p.id = rp.paciente_id
            JOIN odontologos o ON o.id = rp.odontologo_id
            JOIN nomenclador n ON n.id = rp.nomenclador_id
            LEFT JOIN obras_sociales os ON os.id = rp.obra_social_id
            {where}
            ORDER BY rp.fecha DESC, rp.created_at DESC
        """, params).fetchall()
        return [dict(r) for r in rows]


def save_prestacion(data: Dict) -> int:
    cols = ["paciente_id", "odontologo_id", "nomenclador_id", "fecha",
            "numero_fdi", "superficies", "monto", "obra_social_id",
            "num_afiliado", "enviado_federacion", "fecha_envio_fed",
            "historial_id", "notas"]
    vals = [data.get(c) for c in cols]
    with get_connection() as conn:
        if data.get("id"):
            sets = ", ".join(f"{c}=?" for c in cols)
            conn.execute(f"UPDATE registro_prestaciones SET {sets} WHERE id=?", vals + [data["id"]])
            return data["id"]
        ph = ", ".join("?" for _ in cols)
        cur = conn.execute(
            f"INSERT INTO registro_prestaciones ({', '.join(cols)}) VALUES ({ph})", vals
        )
        return cur.lastrowid


def delete_prestacion(id_: int):
    with get_connection() as conn:
        conn.execute("DELETE FROM registro_prestaciones WHERE id=?", (id_,))


def marcar_enviado_federacion(ids: List[int]):
    with get_connection() as conn:
        for id_ in ids:
            conn.execute("""
                UPDATE registro_prestaciones
                SET enviado_federacion=1, fecha_envio_fed=date('now','localtime')
                WHERE id=?
            """, (id_,))


# ─────────────────────────────────────────────────────────────
# ESTADÍSTICAS (dashboard)
# ─────────────────────────────────────────────────────────────

def get_stats() -> Dict:
    with get_connection() as conn:
        stats = {}
        stats["total_pacientes"] = conn.execute(
            "SELECT COUNT(*) FROM pacientes WHERE activo=1"
        ).fetchone()[0]
        stats["turnos_hoy"] = conn.execute(
            "SELECT COUNT(*) FROM turnos WHERE fecha=date('now','localtime')"
        ).fetchone()[0]
        stats["turnos_pendientes"] = conn.execute(
            "SELECT COUNT(*) FROM turnos WHERE estado='Pendiente' AND fecha >= date('now','localtime')"
        ).fetchone()[0]
        stats["prestaciones_mes"] = conn.execute(
            "SELECT COUNT(*), COALESCE(SUM(monto),0) FROM registro_prestaciones "
            "WHERE strftime('%Y-%m', fecha) = strftime('%Y-%m', 'now','localtime')"
        ).fetchone()
        stats["prestaciones_pendientes_fed"] = conn.execute(
            "SELECT COUNT(*) FROM registro_prestaciones WHERE enviado_federacion=0"
        ).fetchone()[0]
        return stats


# ─────────────────────────────────────────────────────────────
# USUARIOS
# ─────────────────────────────────────────────────────────────

def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """Retorna el dict del usuario si las credenciales son válidas, sino None."""
    h = _hash_password(password)
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM usuarios WHERE username=? AND password_hash=? AND activo=1",
            (username, h),
        ).fetchone()
        return dict(row) if row else None


def get_usuarios(solo_activos: bool = False) -> List[Dict]:
    where = "WHERE activo=1" if solo_activos else ""
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(
            f"SELECT id, username, nombre, apellido, rol, activo, created_at "
            f"FROM usuarios {where} ORDER BY apellido, nombre"
        ).fetchall()]


def get_usuario(id_: int) -> Optional[Dict]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, username, nombre, apellido, rol, activo FROM usuarios WHERE id=?",
            (id_,),
        ).fetchone()
        return dict(row) if row else None


def save_usuario(data: Dict) -> int:
    """Crea o actualiza un usuario. Si data contiene 'password' (no vacío), actualiza el hash."""
    with get_connection() as conn:
        if data.get("id"):
            if data.get("password"):
                conn.execute(
                    "UPDATE usuarios SET username=?, password_hash=?, nombre=?, apellido=?, "
                    "rol=?, activo=? WHERE id=?",
                    (data["username"], _hash_password(data["password"]),
                     data["nombre"], data["apellido"], data["rol"],
                     data.get("activo", 1), data["id"]),
                )
            else:
                conn.execute(
                    "UPDATE usuarios SET username=?, nombre=?, apellido=?, rol=?, activo=? "
                    "WHERE id=?",
                    (data["username"], data["nombre"], data["apellido"],
                     data["rol"], data.get("activo", 1), data["id"]),
                )
            return data["id"]
        cur = conn.execute(
            "INSERT INTO usuarios (username, password_hash, nombre, apellido, rol) "
            "VALUES (?, ?, ?, ?, ?)",
            (data["username"], _hash_password(data["password"]),
             data["nombre"], data["apellido"], data.get("rol", "operador")),
        )
        return cur.lastrowid


def delete_usuario(id_: int):
    """Baja lógica."""
    with get_connection() as conn:
        conn.execute("UPDATE usuarios SET activo=0 WHERE id=?", (id_,))
