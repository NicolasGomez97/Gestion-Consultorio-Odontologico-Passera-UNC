"""
historial_fields.py — Definición de los campos extendidos de la Historia Clínica
General (según formulario en papel), organizados por sección.

Esta lista es la fuente única de verdad: se usa para generar las columnas de la
tabla `historial_clinico` (database.py), el formulario de carga (ui/historial_ui.py)
y la exportación a PDF (pdf_export.py).

Tipos de campo:
    "bool"        -> Sí / No (se guarda como INTEGER 1/0/NULL)
    "text"        -> línea de texto simple (TEXT)
    "area"        -> texto multilínea (TEXT)
    "choice"      -> combobox de una sola opción fija (TEXT), 4ta posición = lista de opciones
    "multichoice" -> casillas de selección múltiple (TEXT, opciones separadas por ", "),
                     4ta posición = lista de opciones
"""

SECTIONS = [
    ("datos", "Datos de la Consulta", [
        ("lugar", "text", "Lugar"),
    ]),

    ("af", "Antecedentes Familiares", [
        ("af_padre_vivo",           "bool", "¿Padre con vida?"),
        ("af_padre_enfermedad",     "text", "Enfermedad que padece o padeció (padre)"),
        ("af_madre_viva",           "bool", "¿Madre con vida?"),
        ("af_madre_enfermedad",     "text", "Enfermedad que padece o padeció (madre)"),
        ("af_hermanos",             "bool", "¿Tiene hermanos?"),
        ("af_hermanos_sanos",       "text", "¿Están sanos? / Detalle"),
    ]),

    ("ap", "Antecedentes Personales y Salud", [
        ("ap_enfermedad_actual",          "bool",   "¿Sufre alguna enfermedad?"),
        ("ap_enfermedad_actual_cual",     "text",   "¿De qué?"),
        ("ap_tratamiento_medico",         "bool",   "¿Hace algún tratamiento médico?"),
        ("ap_tratamiento_medico_cual",    "text",   "¿Cuál?"),
        ("ap_medicamentos_habituales",    "area",   "Medicamentos que consume habitualmente"),
        ("ap_medicamentos_5anios",        "area",   "Medicamentos consumidos en los últimos 5 años"),
        ("ap_deporte",                    "bool",   "¿Realiza algún deporte?"),
        ("ap_deporte_malestar",           "bool",   "¿Nota algún malestar al realizarlo?"),
        ("ap_alergico_droga",             "bool",   "¿Es alérgico a alguna droga?"),
        ("ap_alergia_anestesia",          "bool",   "Alergia a la anestesia"),
        ("ap_alergia_penicilina",         "bool",   "Alergia a la penicilina"),
        ("ap_alergia_otros",              "text",   "Otras alergias"),
        ("ap_cicatriza_bien",             "bool",   "¿Cicatriza bien al sacar una muela o lastimarse?"),
        ("ap_sangra_mucho",               "text",   "¿Sangra mucho? Detalle"),
        ("ap_colageno",                   "bool",   "¿Problema de colágeno (hiperlaxitud)?"),
        ("ap_fiebre_reumatica",           "bool",   "¿Antecedentes de fiebre reumática?"),
        ("ap_fiebre_reumatica_medicacion","text",   "¿Se protege con alguna medicación?"),
        ("ap_diabetico",                  "bool",   "¿Es diabético?"),
        ("ap_diabetico_controlado",       "text",   "¿Está controlado? ¿Con qué?"),
        ("ap_cardiaco",                   "bool",   "¿Tiene algún problema cardíaco?"),
        ("ap_cardiaco_cual",              "text",   "¿Cuál?"),
        ("ap_anticoagulante",             "bool",   "¿Toma seguido aspirina y/o anticoagulante?"),
        ("ap_anticoagulante_frecuencia",  "text",   "¿Con qué frecuencia?"),
        ("ap_presion_alta",               "bool",   "¿Tiene presión alta?"),
        ("ap_chagas",                     "bool",   "¿Chagas?"),
        ("ap_chagas_tratamiento",         "text",   "¿Está en tratamiento?"),
        ("ap_renal",                      "bool",   "¿Tiene problemas renales?"),
        ("ap_ulcera_gastrica",            "bool",   "¿Úlcera gástrica?"),
        ("ap_hepatitis",                  "bool",   "¿Tuvo hepatitis?"),
        ("ap_hepatitis_tipo",             "choice", "¿De qué tipo?", ["A", "B", "C"]),
        ("ap_hepatico",                   "bool",   "¿Tiene algún problema hepático?"),
        ("ap_hepatico_cual",              "text",   "¿Cuál?"),
        ("ap_convulsiones",               "bool",   "¿Tuvo convulsiones?"),
        ("ap_epileptico",                 "bool",   "¿Es epiléptico?"),
        ("ap_epileptico_medicacion",      "text",   "Medicación que toma"),
        ("ap_sifilis_gonorrea",           "bool",   "¿Ha tenido Sífilis o Gonorrea?"),
        ("ap_otra_infecto_contagiosa",    "bool",   "¿Otra enfermedad infecto-contagiosa?"),
        ("ap_transfusiones",              "bool",   "¿Tuvo transfusiones?"),
        ("ap_operado",                    "bool",   "¿Fue operado alguna vez?"),
        ("ap_operado_que",                "text",   "¿De qué?"),
        ("ap_operado_cuando",             "text",   "¿Cuándo?"),
        ("ap_respiratorio",               "bool",   "¿Tiene algún problema respiratorio?"),
        ("ap_respiratorio_cual",          "text",   "¿Cuál?"),
        ("ap_fuma",                       "bool",   "¿Fuma?"),
        ("ap_embarazada",                 "bool",   "¿Está embarazada?"),
        ("ap_embarazada_meses",           "text",   "¿De cuántos meses?"),
        ("ap_otra_enfermedad",            "bool",   "¿Otra enfermedad o recomendación de su médico?"),
        ("ap_otra_enfermedad_cual",       "text",   "¿Cuál?"),
        ("ap_tratamiento_alternativo",    "text",   "Homeopatía, Acupuntura, otros"),
        ("ap_clinica_derivacion",         "text",   "Clínica/Hospital en caso de hacer falta derivación"),
    ]),

    ("co", "Consulta Odontológica", [
        ("co_motivo_consulta",       "area", "¿Por qué asistió a la consulta?"),
        ("co_consulto_antes",        "bool", "¿Consultó antes con algún otro profesional?"),
        ("co_tomo_medicamento",      "bool", "¿Tomó algún medicamento?"),
        ("co_medicamento_nombre",    "text", "Nombre de los medicamentos"),
        ("co_medicamento_desde",     "text", "¿Desde cuándo?"),
        ("co_medicamento_resultado", "bool", "¿Obtuvo resultados?"),
        ("co_dolor",                 "bool", "¿Ha tenido dolor?"),
        ("co_dolor_tipo",            "multichoice", "Tipo de dolor", [
            "Suave", "Moderado", "Intenso", "Temporario", "Intermitente",
            "Continuo", "Espontáneo", "Provocado", "Al frío", "Al calor",
        ]),
        ("co_dolor_localizado",      "text", "Localizado, ¿dónde?"),
        ("co_dolor_irradiado",       "text", "Irradiado, ¿hacia dónde?"),
        ("co_dolor_calma",           "text", "¿Puede calmarlo con algo?"),
        ("co_golpe_dientes",         "bool", "¿Sufrió algún golpe en los dientes?"),
        ("co_golpe_cuando",          "text", "¿Cuándo?"),
        ("co_golpe_como",            "text", "¿Cómo se produjo?"),
        ("co_fractura_diente",       "bool", "¿Se le fracturó algún diente?"),
        ("co_fractura_cual",         "text", "¿Cuál?"),
        ("co_fractura_tratamiento",  "text", "¿Recibió algún tratamiento?"),
        ("co_dif_hablar",            "text", "Dificultad para hablar"),
        ("co_dif_masticar",          "text", "Dificultad para masticar"),
        ("co_dif_abrir_boca",        "text", "Dificultad para abrir la boca"),
        ("co_dif_tragar",            "text", "Dificultad para tragar los alimentos"),
    ]),

    ("eb", "Examen Bucal e Higiene", [
        ("eb_anormal_labios",         "text",   "Anormalidad en labios"),
        ("eb_anormal_lengua",         "text",   "Anormalidad en lengua"),
        ("eb_anormal_paladar",        "text",   "Anormalidad en paladar"),
        ("eb_anormal_piso_boca",      "text",   "Anormalidad en piso de boca"),
        ("eb_anormal_carrillos",      "text",   "Anormalidad en carrillos"),
        ("eb_anormal_rebordes",       "text",   "Anormalidad en rebordes"),
        ("eb_anormal_trigono",        "text",   "Anormalidad en trígono"),
        ("eb_anormal_retromolar",     "text",   "Anormalidad retromolar"),
        ("eb_lesion_manchas",         "bool",   "Manchas"),
        ("eb_lesion_abultamiento",    "bool",   "Abultamiento de los tejidos"),
        ("eb_lesion_ulceraciones",    "bool",   "Ulceraciones"),
        ("eb_lesion_ampollas",        "bool",   "Ampollas"),
        ("eb_lesion_otros",           "text",   "Otras lesiones"),
        ("eb_sangrado_encias",        "bool",   "¿Le sangran las encías?"),
        ("eb_sangrado_encias_cuando", "text",   "¿Cuándo?"),
        ("eb_pus",                    "bool",   "¿Sale pus de algún lugar de su boca?"),
        ("eb_pus_donde",              "text",   "¿De dónde?"),
        ("eb_movilidad_dientes",      "bool",   "¿Tiene movilidad en sus dientes?"),
        ("eb_altos_al_morder",        "text",   "¿Al morder siente altos los dientes?"),
        ("eb_cara_hinchada",          "bool",   "¿Ha tenido la cara hinchada?"),
        ("eb_cara_hinchada_trato",    "text",   "¿Se puso hielo, calor, otros?"),
        ("eb_momentos_azucar",        "text",   "Momentos de azúcar diario"),
        ("eb_indice_placa",           "text",   "Índice de placa"),
        ("eb_higiene_bucal",          "choice", "Estado de la higiene bucal",
            ["Muy bueno", "Bueno", "Deficiente", "Malo"]),
        ("eb_sarro",                  "bool",   "Presencia de sarro"),
        ("eb_enfermedad_periodontal", "bool",   "Enfermedad Periodontal"),
    ]),

    ("consent", "Consentimiento Informado", [
        ("consent_acepta", "bool", "El paciente (o tutor) otorga su consentimiento informado"),
        ("consent_dni",    "text", "DNI de quien suscribe (paciente o tutor)"),
    ]),
]


def all_fields():
    """Devuelve la lista plana de todas las tuplas de campo de todas las secciones."""
    fields = []
    for _key, _title, section_fields in SECTIONS:
        fields.extend(section_fields)
    return fields


def all_keys():
    """Devuelve la lista de nombres de columna (para SELECT/INSERT)."""
    return [f[0] for f in all_fields()]


def bool_keys():
    """Devuelve el subconjunto de claves cuyo tipo es 'bool'."""
    return [f[0] for f in all_fields() if f[1] == "bool"]
