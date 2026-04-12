"""
database.py — Conexión SQLite e inicialización del esquema completo.
Consultorio Odontológico Passera — Sistema de Gestión
"""
import sqlite3
import os
import hashlib

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "clinica.db")


def get_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_db():
    with get_connection() as conn:
        conn.executescript("""
        -- ===== OBRAS SOCIALES =====
        CREATE TABLE IF NOT EXISTS obras_sociales (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre      TEXT NOT NULL UNIQUE,
            codigo      TEXT,
            activo      INTEGER NOT NULL DEFAULT 1
        );

        -- ===== ODONTÓLOGOS =====
        CREATE TABLE IF NOT EXISTS odontologos (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre          TEXT NOT NULL,
            apellido        TEXT NOT NULL,
            especialidad    TEXT,
            matricula       TEXT NOT NULL UNIQUE,
            circulo         TEXT,
            telefono        TEXT,
            email           TEXT,
            activo          INTEGER NOT NULL DEFAULT 1
        );

        -- ===== PACIENTES =====
        CREATE TABLE IF NOT EXISTS pacientes (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre              TEXT NOT NULL,
            apellido            TEXT NOT NULL,
            dni                 TEXT,
            fecha_nacimiento    TEXT,
            sexo                TEXT CHECK(sexo IN ('M','F','X')),
            estado_civil        TEXT,
            direccion           TEXT,
            telefono            TEXT,
            email               TEXT,
            obra_social_id      INTEGER REFERENCES obras_sociales(id),
            num_afiliado        TEXT,
            titular             TEXT,
            grupo_familiar      TEXT,
            lugar_trabajo       TEXT,
            jerarquia           TEXT,
            alergias            TEXT,
            enfermedades        TEXT,
            medico_clinico      TEXT,
            observaciones       TEXT,
            activo              INTEGER NOT NULL DEFAULT 1,
            created_at          TEXT NOT NULL DEFAULT (datetime('now','localtime')),
            updated_at          TEXT NOT NULL DEFAULT (datetime('now','localtime'))
        );

        -- ===== TURNOS =====
        CREATE TABLE IF NOT EXISTS turnos (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id     INTEGER NOT NULL REFERENCES pacientes(id),
            odontologo_id   INTEGER NOT NULL REFERENCES odontologos(id),
            fecha           TEXT NOT NULL,
            hora            TEXT NOT NULL,
            duracion_min    INTEGER NOT NULL DEFAULT 30,
            motivo          TEXT,
            estado          TEXT NOT NULL DEFAULT 'Pendiente'
                                CHECK(estado IN ('Pendiente','Confirmado','Presente',
                                                 'Ausente','Cancelado','Reprogramado')),
            notas           TEXT,
            created_at      TEXT NOT NULL DEFAULT (datetime('now','localtime'))
        );
        CREATE INDEX IF NOT EXISTS idx_turnos_fecha     ON turnos(fecha);
        CREATE INDEX IF NOT EXISTS idx_turnos_odontologo ON turnos(odontologo_id);

        -- ===== HISTORIAL CLÍNICO =====
        CREATE TABLE IF NOT EXISTS historial_clinico (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id     INTEGER NOT NULL REFERENCES pacientes(id),
            odontologo_id   INTEGER NOT NULL REFERENCES odontologos(id),
            fecha           TEXT NOT NULL DEFAULT (date('now','localtime')),
            diagnostico     TEXT,
            tratamiento     TEXT,
            notas           TEXT,
            radiografias    INTEGER NOT NULL DEFAULT 0,
            informes_ext    TEXT,
            created_at      TEXT NOT NULL DEFAULT (datetime('now','localtime'))
        );
        CREATE INDEX IF NOT EXISTS idx_historial_paciente ON historial_clinico(paciente_id);

        -- ===== ODONTOGRAMA (diente y superficies) =====
        CREATE TABLE IF NOT EXISTS odontograma_diente (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id INTEGER NOT NULL REFERENCES pacientes(id),
            numero_fdi  INTEGER NOT NULL,
            condicion   TEXT NOT NULL DEFAULT 'sano'
                            CHECK(condicion IN ('sano','Ausente','implante','corona',
                                                'endodoncia','protesis_fija',
                                                'protesis_removible','sellante')),
            notas       TEXT,
            updated_at  TEXT NOT NULL DEFAULT (datetime('now','localtime')),
            UNIQUE(paciente_id, numero_fdi)
        );

        CREATE TABLE IF NOT EXISTS odontograma_superficie (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id INTEGER NOT NULL REFERENCES pacientes(id),
            numero_fdi  INTEGER NOT NULL,
            superficie  TEXT NOT NULL CHECK(superficie IN ('V','L','M','D','O')),
            estado      TEXT NOT NULL DEFAULT 'sano'
                            CHECK(estado IN ('sano','caries','obturacion',
                                             'fractura','pendiente')),
            updated_at  TEXT NOT NULL DEFAULT (datetime('now','localtime')),
            UNIQUE(paciente_id, numero_fdi, superficie)
        );

        -- ===== FICHA PERIODONTAL =====
        CREATE TABLE IF NOT EXISTS ficha_periodontal (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id     INTEGER NOT NULL REFERENCES pacientes(id),
            odontologo_id   INTEGER NOT NULL REFERENCES odontologos(id),
            fecha           TEXT NOT NULL DEFAULT (date('now','localtime')),
            estado_encias   TEXT,
            indice_placa    REAL,
            indice_sangrado REAL,
            notas           TEXT,
            created_at      TEXT NOT NULL DEFAULT (datetime('now','localtime'))
        );

        -- Mediciones por diente y cara (6 sitios: MB,B,DB,ML,L,DL)
        CREATE TABLE IF NOT EXISTS periodontal_medicion (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            ficha_id        INTEGER NOT NULL REFERENCES ficha_periodontal(id) ON DELETE CASCADE,
            numero_fdi      INTEGER NOT NULL,
            -- profundidad de bolsa (6 valores separados por coma, en mm)
            prof_bolsa      TEXT DEFAULT '0,0,0,0,0,0',
            -- margen gingival (6 valores, negativo=recesión)
            margen_gingival TEXT DEFAULT '0,0,0,0,0,0',
            -- sangrado (6 bits: 0/1)
            sangrado        TEXT DEFAULT '0,0,0,0,0,0',
            -- placa (6 bits: 0/1)
            placa           TEXT DEFAULT '0,0,0,0,0,0',
            furcacion       INTEGER DEFAULT 0 CHECK(furcacion BETWEEN 0 AND 3),
            UNIQUE(ficha_id, numero_fdi)
        );

        -- ===== NOMENCLADOR (catálogo de prestaciones) =====
        CREATE TABLE IF NOT EXISTS nomenclador (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo      TEXT NOT NULL UNIQUE,
            descripcion TEXT NOT NULL,
            categoria   TEXT,
            costo_base  REAL NOT NULL DEFAULT 0
        );

        -- ===== USUARIOS DEL SISTEMA =====
        CREATE TABLE IF NOT EXISTS usuarios (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            username        TEXT NOT NULL UNIQUE,
            password_hash   TEXT NOT NULL,
            nombre          TEXT NOT NULL,
            apellido        TEXT NOT NULL,
            rol             TEXT NOT NULL DEFAULT 'operador'
                                CHECK(rol IN ('admin','operador')),
            activo          INTEGER NOT NULL DEFAULT 1,
            created_at      TEXT NOT NULL DEFAULT (datetime('now','localtime'))
        );

        -- ===== REGISTRO DE PRESTACIONES =====
        CREATE TABLE IF NOT EXISTS registro_prestaciones (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id         INTEGER NOT NULL REFERENCES pacientes(id),
            odontologo_id       INTEGER NOT NULL REFERENCES odontologos(id),
            nomenclador_id      INTEGER NOT NULL REFERENCES nomenclador(id),
            fecha               TEXT NOT NULL DEFAULT (date('now','localtime')),
            numero_fdi          INTEGER,
            superficies         TEXT,
            monto               REAL NOT NULL DEFAULT 0,
            obra_social_id      INTEGER REFERENCES obras_sociales(id),
            num_afiliado        TEXT,
            enviado_federacion  INTEGER NOT NULL DEFAULT 0,
            fecha_envio_fed     TEXT,
            historial_id        INTEGER REFERENCES historial_clinico(id),
            notas               TEXT,
            created_at          TEXT NOT NULL DEFAULT (datetime('now','localtime'))
        );
        CREATE INDEX IF NOT EXISTS idx_prestaciones_paciente ON registro_prestaciones(paciente_id);
        CREATE INDEX IF NOT EXISTS idx_prestaciones_fecha    ON registro_prestaciones(fecha);
        """)

        # ─── Seed usuario admin ────────────────────────────────────────────────
        if not conn.execute("SELECT 1 FROM usuarios LIMIT 1").fetchone():
            admin_hash = hashlib.sha256("admin123".encode()).hexdigest()
            conn.execute(
                "INSERT INTO usuarios (username, password_hash, nombre, apellido, rol) "
                "VALUES (?, ?, ?, ?, ?)",
                ("admin", admin_hash, "Administrador", "Sistema", "admin"),
            )

        # ─── Seed obras sociales ───────────────────────────────────────────────
        if not conn.execute("SELECT 1 FROM obras_sociales LIMIT 1").fetchone():
            conn.executemany(
                "INSERT INTO obras_sociales (nombre, codigo) VALUES (?, ?)",
                [
                    ("APROSS",          "AP"),
                    ("OSDE",            "OS"),
                    ("Swiss Medical",   "SM"),
                    ("Galeno",          "GA"),
                    ("PAMI",            "PA"),
                    ("IOMA",            "IO"),
                    ("Medicus",         "MD"),
                    ("Federada",        "FE"),
                    ("IOSFA",           "IF"),
                    ("Sancor Salud",    "SS"),
                    ("Particular",      "PART"),
                ],
            )

        # ─── Seed odontólogos ──────────────────────────────────────────────────
        if not conn.execute("SELECT 1 FROM odontologos LIMIT 1").fetchone():
            conn.executemany(
                "INSERT INTO odontologos (nombre, apellido, especialidad, matricula, circulo) "
                "VALUES (?, ?, ?, ?, ?)",
                [
                    ("Cristina",    "Passero",  "Directora / Odontología General",    "MP-1234", "Córdoba"),
                    ("Carla Inés",  "Macías",   "Periodoncia / Odontopediatría",       "MP-5678", "Córdoba"),
                    ("Carlos",      "García",   "Cirugía Oral / Endodoncia",            "MP-9012", "Córdoba"),
                    ("Laura",       "Soria",    "Ortodoncia",                           "MP-3456", "Córdoba"),
                    ("Diego",       "Fernández","Prótesis Dental",                      "MP-7890", "Córdoba"),
                ],
            )

        # ─── Seed nomenclador FOC ──────────────────────────────────────────────
        if not conn.execute("SELECT 1 FROM nomenclador LIMIT 1").fetchone():
            conn.executemany(
                "INSERT INTO nomenclador (codigo, descripcion, categoria, costo_base) VALUES (?, ?, ?, ?)",
                [
                    ("0101", "Consulta / Examen General",                      "Diagnóstico",   3000),
                    ("0102", "Diagnóstico Integral",                           "Diagnóstico",   4500),
                    ("0201", "Radiografía Periapical",                         "Radiología",    2000),
                    ("0202", "Radiografía Panorámica",                         "Radiología",    6000),
                    ("0203", "Radiografía Bitewing",                           "Radiología",    2500),
                    ("0301", "Tartrectomía / Profilaxis",                      "Periodoncia",   6000),
                    ("0302", "Raspado y Alisado Radicular (por cuadrante)",    "Periodoncia",  14000),
                    ("0401", "Restauración Simple (1 cara)",                   "Operatoria",    5000),
                    ("0402", "Restauración Compuesta (2+ caras)",              "Operatoria",    8000),
                    ("0501", "Extracción Simple",                              "Cirugía",       6000),
                    ("0502", "Extracción Quirúrgica",                          "Cirugía",      15000),
                    ("0503", "Extracción de Muela del Juicio",                 "Cirugía",      25000),
                    ("0601", "Tratamiento de Conductos - Unirradicular",       "Endodoncia",   18000),
                    ("0602", "Tratamiento de Conductos - Birradicular",        "Endodoncia",   24000),
                    ("0603", "Tratamiento de Conductos - Multirradicular",     "Endodoncia",   30000),
                    ("0701", "Corona de Porcelana",                            "Prótesis",     50000),
                    ("0702", "Corona Metálica",                                "Prótesis",     35000),
                    ("0703", "Perno Colado",                                   "Prótesis",     20000),
                    ("0801", "Prótesis Removible Parcial (Cromo)",             "Prótesis",     70000),
                    ("0802", "Prótesis Removible Total (por arcada)",          "Prótesis",     90000),
                    ("0803", "Prótesis Fija (por pilar)",                      "Prótesis",     55000),
                    ("0901", "Ortodoncia - Colocación de Aparatos",            "Ortodoncia",  100000),
                    ("0902", "Ortodoncia - Control Mensual",                   "Ortodoncia",   10000),
                    ("1001", "Implante Dental (colocación)",                   "Implantología",180000),
                    ("1101", "Blanqueamiento Dental",                          "Estética",     30000),
                    ("1201", "Sellante de Fosas y Fisuras (por diente)",       "Prevención",    3500),
                    ("1301", "Consulta Odontopediátrica",                      "Odontopediatría",3000),
                    ("1401", "Dolor Orofacial - Diagnóstico",                  "Medicina Bucal", 4500),
                    ("1501", "Ferulización (por diente)",                      "Periodoncia",    5000),
                ],
            )
