# sociograma_data.py
# (v1.4 - "alumno" a "miembro", "Escuela" a "Institución", "genero" a "sexo")

import collections
import datetime

# --- Estructuras de Datos Globales ---
schools_data = collections.OrderedDict() # Esta estructura almacena INSTITUCIONES
classes_data = collections.OrderedDict() # Claves son nombres de institución, valores son listas de grupos
members_data = collections.OrderedDict()  # Claves: inst, grupo; valor: lista de MIEMBROS (con clave "sexo") # CAMBIO
questionnaire_responses_data = collections.OrderedDict()
question_definitions = collections.OrderedDict() # Claves: (institucion, grupo)

relationship_types_map = collections.OrderedDict()
sociogram_relation_options_map = collections.OrderedDict()

# --- FUNCIONES HELPER LOCALES (para iniciales) ---
def _parse_nombre_apellido_local(nombre_completo_str_titulo):
    partes = nombre_completo_str_titulo.strip().split()
    if not partes: return "", ""
    if len(partes) == 1: return partes[0], ""
    nombre = " ".join(partes[:-1])
    apellido = partes[-1]
    return nombre, apellido

def _generar_iniciales_local(nombre_str, apellido_str):
    iniciales = []
    if nombre_str:
        for parte_n in nombre_str.strip().split():
            if parte_n: iniciales.append(parte_n[0].upper())
            if len(iniciales) >= 2: break
    if apellido_str:
        for parte_a in apellido_str.strip().split():
            if parte_a: iniciales.append(parte_a[0].upper())
            if len(iniciales) >= 4: break
    final_str_iniciales = "".join(iniciales)
    if not final_str_iniciales: return "N/A"
    if len(final_str_iniciales) > 4: final_str_iniciales = final_str_iniciales[:4]
    while len(final_str_iniciales) < 3: final_str_iniciales += "X"
    return final_str_iniciales

def get_class_question_definitions(institution_name, group_name):
    class_key = (institution_name, group_name)
    if class_key not in question_definitions:
        question_definitions[class_key] = collections.OrderedDict()
    return question_definitions[class_key]

def regenerate_relationship_maps_for_class(institution_name, group_name):
    global relationship_types_map, sociogram_relation_options_map
    relationship_types_map.clear()
    sociogram_relation_options_map.clear()
    sociogram_relation_options_map["all"] = "Todos los Tipos de Relación"
    current_class_questions = get_class_question_definitions(institution_name, group_name)
    if not isinstance(current_class_questions, collections.OrderedDict) or not current_class_questions:
        return
    try:
        sorted_q_items = sorted(current_class_questions.items(), key=lambda item: (item[1].get('order', 999), item[0]))
        for q_id, q_def in sorted_q_items:
            data_key = q_def.get('data_key', q_id)
            q_type_desc = q_def.get('type', 'General')
            polarity_char = "Pos" if q_def.get('polarity') == 'positive' else "Neg" if q_def.get('polarity') == 'negative' else "Neu"
            label_for_map_and_checkbox = f"({polarity_char}) {q_type_desc}"
            polarity_desc_full = "Aceptación" if q_def.get('polarity') == 'positive' else "Rechazo" if q_def.get('polarity') == 'negative' else "Neutral"
            relationship_types_map[data_key] = f"{polarity_desc_full} - {q_type_desc}"
            sociogram_relation_options_map[data_key] = label_for_map_and_checkbox
    except Exception as e:
        print(f"ERROR (sociograma_data.regenerate_relationship_maps): Al regenerar mapas para {institution_name}/{group_name}: {e}")

def initialize_data():
    global schools_data, classes_data, members_data, questionnaire_responses_data, question_definitions # CAMBIO
    global relationship_types_map, sociogram_relation_options_map

    institucion1_nombre_es = "Colegio \"Miguel de Cervantes\""
    institucion2_nombre_es = "Instituto \"Benito Juárez\""

    schools_data.clear()
    schools_data.update({
        institucion1_nombre_es: "Anotaciones para el Colegio Cervantes. Grupo piloto.",
        institucion2_nombre_es: "Notas: Instituto con enfoque en ciencias sociales."
    })

    classes_data.clear()
    classes_data.update({
        institucion1_nombre_es: [
            {"name": "4to Grado A", "coordinator": "Diana Batista", "ins2": "Cristina Reyes", "ins3": "", "sostegno": "Marcos Neri", "annotations": "Grupo piloto. Activo."},
            {"name": "4to Grado B", "coordinator": "Mario Romero", "ins2": "", "ins3": "", "sostegno": "", "annotations": "Grupo más tranquilo."}
        ],
        institucion2_nombre_es: [
            {"name": "1er Año A (Secundaria)", "coordinator": "Prof. Elena Rivas", "ins2": "Prof. Luis Bravo", "ins3": "", "sostegno": "", "annotations": "Primer grupo del ciclo básico."},
            {"name": "2do Año A (Secundaria)", "coordinator": "Prof. Juan Herrera", "ins2": "", "ins3": "", "sostegno": "", "annotations": ""}
        ]
    })
    for inst_name_init_classes in list(schools_data.keys()):
        if inst_name_init_classes not in classes_data:
            classes_data[inst_name_init_classes] = []

    members_data.clear() # CAMBIO
    members_data.update({ # CAMBIO
        institucion1_nombre_es: collections.OrderedDict({
            "4to Grado A": [
                {"cognome": "AGUILAR", "nome": "Ángela", "iniz": _generar_iniciales_local("Ángela", "Aguilar"), "sexo": "Femenino", "fecha_nac": "15/03/2015", "annotations": "Miembro participativa."},
                {"cognome": "BENÍTEZ", "nome": "Daniela", "iniz": _generar_iniciales_local("Daniela", "Benítez"), "sexo": "Femenino", "fecha_nac": "10/07/2015", "annotations": ""},
                {"cognome": "BLANCO", "nome": "Mateo", "iniz": _generar_iniciales_local("Mateo", "Blanco"), "sexo": "Masculino", "fecha_nac": "02/11/2014", "annotations": "Líder natural."},
                {"cognome": "BERNAL", "nome": "Alicia", "iniz": _generar_iniciales_local("Alicia", "Bernal"), "sexo": "Femenino", "fecha_nac": "20/01/2015", "annotations": ""},
                {"cognome": "CASTILLO", "nome": "Marcos", "iniz": _generar_iniciales_local("Marcos", "Castillo"), "sexo": "Masculino", "fecha_nac": "05/09/2015", "annotations": ""},
                {"cognome": "FLORES", "nome": "Jéssica", "iniz": _generar_iniciales_local("Jéssica", "Flores"), "sexo": "Femenino", "fecha_nac": "12/04/2015", "annotations": ""},
                {"cognome": "GÓMEZ", "nome": "Óscar", "iniz": _generar_iniciales_local("Óscar", "Gómez"), "sexo": "Masculino", "fecha_nac": "30/06/2015", "annotations": ""},
                {"cognome": "GUTIÉRREZ", "nome": "Martina", "iniz": _generar_iniciales_local("Martina", "Gutiérrez"), "sexo": "Femenino", "fecha_nac": "08/12/2014", "annotations": ""},
                {"cognome": "MARTÍNEZ", "nome": "Adela", "iniz": _generar_iniciales_local("Adela", "Martínez"), "sexo": "Femenino", "fecha_nac": "25/05/2015", "annotations": ""},
                {"cognome": "NAVARRO", "nome": "Manuel", "iniz": _generar_iniciales_local("Manuel", "Navarro"), "sexo": "Masculino", "fecha_nac": "18/08/2015", "annotations": "Miembro nuevo este año."},
                {"cognome": "RAMÍREZ", "nome": "Luisa", "iniz": _generar_iniciales_local("Luisa", "Ramírez"), "sexo": "Femenino", "fecha_nac": "03/02/2015", "annotations": ""},
                {"cognome": "ROJAS", "nome": "Alejandro", "iniz": _generar_iniciales_local("Alejandro", "Rojas"), "sexo": "Masculino", "fecha_nac": "14/10/2014", "annotations": ""},
                {"cognome": "VARGAS", "nome": "Carmen", "iniz": _generar_iniciales_local("Carmen", "Vargas"), "sexo": "Femenino", "fecha_nac": "22/07/2015", "annotations": ""},
                {"cognome": "VELÁZQUEZ", "nome": "Nicolás", "iniz": _generar_iniciales_local("Nicolás", "Velázquez"), "sexo": "Masculino", "fecha_nac": "09/04/2015", "annotations": "Necesita apoyo en socialización."},
                {"cognome": "VIDAL", "nome": "Matías", "iniz": _generar_iniciales_local("Matías", "Vidal"), "sexo": "Masculino", "fecha_nac": "01/06/2015", "annotations": ""},
                {"cognome": "BRAVO", "nome": "Esteban", "iniz": _generar_iniciales_local("Esteban", "Bravo"), "sexo": "Masculino", "fecha_nac": "10/10/2014", "annotations": ""}
            ],
             "4to Grado B": [
                {"cognome": "ROMERO", "nome": "Mario", "iniz": _generar_iniciales_local("Mario", "Romero"), "sexo": "Masculino", "fecha_nac": "05/05/2015", "annotations": ""},
                {"cognome": "BELTRÁN", "nome": "Laura", "iniz": _generar_iniciales_local("Laura", "Beltrán"), "sexo": "Femenino", "fecha_nac": "12/08/2015", "annotations": ""}
             ]
        }),
        institucion2_nombre_es: collections.OrderedDict({
            "1er Año A (Secundaria)": [
                {"cognome": "RÍOS", "nome": "Julia", "iniz": _generar_iniciales_local("Julia", "Ríos"), "sexo": "Femenino", "fecha_nac": "10/02/2011", "annotations": ""},
                {"cognome": "CAMPOS", "nome": "Marco", "iniz": _generar_iniciales_local("Marco", "Campos"), "sexo": "Masculino", "fecha_nac": "20/09/2010", "annotations": ""}
            ],
            "2do Año A (Secundaria)": []
        })
    })
    # Asegurar que cada par institución/grupo tenga una entrada en members_data (antes students_data)
    for inst_name_memb_init, groups_list_memb_init in classes_data.items(): # CAMBIO
        if inst_name_memb_init not in members_data: # CAMBIO
            members_data[inst_name_memb_init] = collections.OrderedDict() # CAMBIO
        for group_info_memb_init in groups_list_memb_init: # CAMBIO
             group_name_memb_init = group_info_memb_init['name'] # CAMBIO
             if group_name_memb_init not in members_data[inst_name_memb_init]: # CAMBIO
                 members_data[inst_name_memb_init][group_name_memb_init] = [] # CAMBIO

    question_definitions.clear()
    for inst_name_q_def, group_list_q_def in classes_data.items():
        for group_info_q_def in group_list_q_def:
            group_name_q_def = group_info_q_def['name']
            class_key_q_def_init = (inst_name_q_def, group_name_q_def)
            default_questions_for_this_group = collections.OrderedDict()
            default_questions_for_this_group["q_asiento_pos"] = {"text": "Si pudieras elegir, ¿a quién querrías como compañero de asiento?", "type": "Asiento", "polarity": "positive", "order": 1, "data_key": "q_asiento_pos", "max_selections": 2, "allow_self_selection": False}
            default_questions_for_this_group["q_trabajo_pos"] = {"text": "Indica los nombres de dos compañeros con quienes crees que te iría bien trabajando en grupo para realizar una tarea escolar.", "type": "Tarea Escolar", "polarity": "positive", "order": 2, "data_key": "q_trabajo_pos", "max_selections": 2, "allow_self_selection": True}
            default_questions_for_this_group["q_juego_pos"] = {"text": "Si tuvieras que organizar un picnic, ¿a qué compañeros invitarías?", "type": "Picnic/Juego", "polarity": "positive", "order": 3, "data_key": "q_juego_pos", "max_selections": 2, "allow_self_selection": True}
            default_questions_for_this_group["q_asiento_neg"] = {"text": "Si pudieras elegir, ¿a quién evitarías totalmente como compañero de asiento?", "type": "Asiento", "polarity": "negative", "order": 4, "data_key": "q_asiento_neg", "max_selections": 2, "allow_self_selection": False}
            default_questions_for_this_group["q_trabajo_neg"] = {"text": "Indica los nombres de dos compañeros con quienes no querrías trabajar en absoluto para realizar una tarea escolar.", "type": "Tarea Escolar", "polarity": "negative", "order": 5, "data_key": "q_trabajo_neg", "max_selections": 2, "allow_self_selection": False}
            default_questions_for_this_group["q_juego_neg"] = {"text": "Indica los nombres de dos compañeros a quienes preferirías no invitar al picnic.", "type": "Picnic/Juego", "polarity": "negative", "order": 6, "data_key": "q_juego_neg", "max_selections": 2, "allow_self_selection": False}
            question_definitions[class_key_q_def_init] = default_questions_for_this_group

    questionnaire_responses_data.clear()
    # Las claves de las respuestas usan (nombre_institucion, nombre_grupo, nombre_miembro)
    questionnaire_responses_data.update({
        (institucion1_nombre_es, "4to Grado A", "Ángela Aguilar"): {
            "q_asiento_pos": ["Luisa Ramírez", "Adela Martínez"], "q_trabajo_pos": ["Adela Martínez", "Alicia Bernal"],
            "q_juego_pos": ["Luisa Ramírez", "Adela Martínez"], "q_asiento_neg": ["Alejandro Rojas", "Manuel Navarro"],
            "q_trabajo_neg": ["Alejandro Rojas", "Manuel Navarro"], "q_juego_neg": ["Manuel Navarro", "Alejandro Rojas"]
        },
        (institucion1_nombre_es, "4to Grado A", "Daniela Benítez"): { "q_asiento_pos": ["Martina Gutiérrez", "Jéssica Flores"], "q_trabajo_pos": ["Ángela Aguilar", "Alicia Bernal"], "q_juego_pos": ["Adela Martínez", "Martina Gutiérrez"], "q_asiento_neg": ["Nicolás Velázquez", "Alejandro Rojas"], "q_trabajo_neg": ["Matías Vidal", "Nicolás Velázquez"], "q_juego_neg": ["Nicolás Velázquez", "Alejandro Rojas"] },
        (institucion1_nombre_es, "4to Grado A", "Mateo Blanco"): { "q_asiento_pos": ["Marcos Castillo", "Óscar Gómez"], "q_trabajo_pos": ["Marcos Castillo", "Óscar Gómez"], "q_juego_pos": ["Marcos Castillo", "Óscar Gómez"], "q_asiento_neg": ["Alejandro Rojas", "Nicolás Velázquez"], "q_trabajo_neg": ["Alejandro Rojas", "Nicolás Velázquez"], "q_juego_neg": ["Alejandro Rojas", "Nicolás Velázquez"] },
        (institucion1_nombre_es, "4to Grado A", "Alicia Bernal"): { "q_asiento_pos": ["Martina Gutiérrez", "Luisa Ramírez"], "q_trabajo_pos": ["Ángela Aguilar", "Martina Gutiérrez"], "q_juego_pos": ["Luisa Ramírez", "Carmen Vargas"], "q_asiento_neg": ["Nicolás Velázquez", "Manuel Navarro"], "q_trabajo_neg": ["Nicolás Velázquez", "Alejandro Rojas"], "q_juego_neg": ["Esteban Bravo", "Jéssica Flores"] },
        (institucion1_nombre_es, "4to Grado A", "Marcos Castillo"): { "q_asiento_pos": ["Óscar Gómez", "Mateo Blanco"], "q_trabajo_pos": ["Óscar Gómez", "Mateo Blanco"], "q_juego_pos": ["Óscar Gómez", "Mateo Blanco"], "q_asiento_neg": ["Nicolás Velázquez", "Alejandro Rojas"], "q_trabajo_neg": ["Nicolás Velázquez", "Alejandro Rojas"], "q_juego_neg": ["Nicolás Velázquez", "Alejandro Rojas"] },
        (institucion1_nombre_es, "4to Grado A", "Jéssica Flores"): { "q_asiento_pos": ["Martina Gutiérrez", "Luisa Ramírez"], "q_trabajo_pos": ["Adela Martínez", "Martina Gutiérrez"], "q_juego_pos": ["Ángela Aguilar", "Martina Gutiérrez"], "q_asiento_neg": ["Nicolás Velázquez", "Esteban Bravo"], "q_trabajo_neg": ["Alejandro Rojas", "Mateo Blanco"], "q_juego_neg": ["Nicolás Velázquez", "Alejandro Rojas"] },
        (institucion1_nombre_es, "4to Grado A", "Óscar Gómez"): { "q_asiento_pos": ["Mateo Blanco", "Martina Gutiérrez"], "q_trabajo_pos": ["Ángela Aguilar", "Carmen Vargas"], "q_juego_pos": ["Marcos Castillo", "Alejandro Rojas"], "q_asiento_neg": ["Marcos Castillo", "Mateo Blanco"], "q_trabajo_neg": ["Nicolás Velázquez", "Matías Vidal"], "q_juego_neg": ["Matías Vidal", "Nicolás Velázquez"] },
        (institucion1_nombre_es, "4to Grado A", "Martina Gutiérrez"): { "q_asiento_pos": ["Luisa Ramírez", "Ángela Aguilar"], "q_trabajo_pos": ["Alicia Bernal", "Adela Martínez"], "q_juego_pos": ["Carmen Vargas", "Luisa Ramírez"], "q_asiento_neg": ["Esteban Bravo", "Alejandro Rojas"], "q_trabajo_neg": ["Matías Vidal", "Alejandro Rojas"], "q_juego_neg": ["Nicolás Velázquez", "Alejandro Rojas"] },
        (institucion1_nombre_es, "4to Grado A", "Adela Martínez"): { "q_asiento_pos": ["Luisa Ramírez", "Martina Gutiérrez"], "q_trabajo_pos": ["Luisa Ramírez", "Martina Gutiérrez"], "q_juego_pos": ["Luisa Ramírez", "Martina Gutiérrez"], "q_asiento_neg": ["Nicolás Velázquez", "Manuel Navarro"], "q_trabajo_neg": [], "q_juego_neg": [] },
        (institucion1_nombre_es, "4to Grado A", "Manuel Navarro"): { "q_asiento_pos": ["Marcos Castillo", "Óscar Gómez"], "q_trabajo_pos": ["Marcos Castillo", "Óscar Gómez"], "q_juego_pos": ["Marcos Castillo", "Óscar Gómez"], "q_asiento_neg": ["Nicolás Velázquez", "Alejandro Rojas"], "q_trabajo_neg": ["Alejandro Rojas", "Nicolás Velázquez"], "q_juego_neg": ["Alejandro Rojas", "Nicolás Velázquez"] },
        (institucion1_nombre_es, "4to Grado A", "Luisa Ramírez"): { "q_asiento_pos": ["Martina Gutiérrez", "Ángela Aguilar"], "q_trabajo_pos": ["Alicia Bernal", "Adela Martínez"], "q_juego_pos": ["Martina Gutiérrez", "Adela Martínez"], "q_asiento_neg": ["Manuel Navarro", "Nicolás Velázquez"], "q_trabajo_neg": ["Nicolás Velázquez", "Esteban Bravo"], "q_juego_neg": ["Matías Vidal", "Alejandro Rojas"] },
        (institucion1_nombre_es, "4to Grado A", "Alejandro Rojas"): { "q_asiento_pos": ["Marcos Castillo", "Esteban Bravo"], "q_trabajo_pos": ["Marcos Castillo", "Esteban Bravo"], "q_juego_pos": ["Adela Martínez", "Esteban Bravo"], "q_asiento_neg": ["Manuel Navarro", "Nicolás Velázquez"], "q_trabajo_neg": ["Manuel Navarro", "Nicolás Velázquez"], "q_juego_neg": ["Nicolás Velázquez", "Manuel Navarro"] },
        (institucion1_nombre_es, "4to Grado A", "Carmen Vargas"): { "q_asiento_pos": ["Ángela Aguilar", "Adela Martínez"], "q_trabajo_pos": ["Ángela Aguilar", "Martina Gutiérrez"], "q_juego_pos": ["Alicia Bernal", "Ángela Aguilar"], "q_asiento_neg": ["Alejandro Rojas", "Esteban Bravo"], "q_trabajo_neg": ["Esteban Bravo", "Nicolás Velázquez"], "q_juego_neg": ["Esteban Bravo", "Alejandro Rojas"] },
        (institucion1_nombre_es, "4to Grado A", "Nicolás Velázquez"): { "q_asiento_pos": ["Marcos Castillo", "Mateo Blanco"], "q_trabajo_pos": ["Marcos Castillo", "Mateo Blanco"], "q_juego_pos": ["Marcos Castillo", "Manuel Navarro"], "q_asiento_neg": ["Esteban Bravo", "Mateo Blanco"], "q_trabajo_neg": ["Alicia Bernal", "Daniela Benítez"], "q_juego_neg": ["Alicia Bernal", "Daniela Benítez"] },
        (institucion1_nombre_es, "4to Grado A", "Matías Vidal"): { "q_asiento_pos": ["Marcos Castillo", "Mateo Blanco"], "q_trabajo_pos": ["Marcos Castillo", "Mateo Blanco"], "q_juego_pos": ["Mateo Blanco", "Marcos Castillo"], "q_asiento_neg": ["Alejandro Rojas", "Esteban Bravo"], "q_trabajo_neg": ["Nicolás Velázquez", "Alejandro Rojas"], "q_juego_neg": ["Nicolás Velázquez", "Esteban Bravo"] },
        (institucion1_nombre_es, "4to Grado A", "Esteban Bravo"): { "q_asiento_pos": ["Marcos Castillo", "Mateo Blanco"], "q_trabajo_pos": ["Mateo Blanco", "Ángela Aguilar"], "q_juego_pos": ["Marcos Castillo", "Luisa Ramírez"], "q_asiento_neg": ["Carmen Vargas", "Alicia Bernal"], "q_trabajo_neg": ["Matías Vidal", "Carmen Vargas"], "q_juego_neg": ["Alicia Bernal", "Carmen Vargas"] },
        (institucion2_nombre_es, "1er Año A (Secundaria)", "Julia Ríos"): { "q_asiento_pos": ["Marco Campos"], "q_trabajo_pos": ["Marco Campos"], "q_juego_pos": ["Marco Campos"] },
        (institucion2_nombre_es, "1er Año A (Secundaria)", "Marco Campos"): { "q_asiento_pos": ["Julia Ríos"], "q_trabajo_pos": ["Julia Ríos"], "q_juego_neg": ["Julia Ríos"] }
    })

    relationship_types_map.clear()
    sociogram_relation_options_map.clear()
    initial_context_institution = None
    initial_context_group = None
    if schools_data:
        first_institution_init = list(schools_data.keys())[0]
        if first_institution_init in classes_data and classes_data[first_institution_init]:
            first_group_info_init = classes_data[first_institution_init][0]
            if 'name' in first_group_info_init:
                initial_context_institution = first_institution_init
                initial_context_group = first_group_info_init['name']
    if initial_context_institution and initial_context_group:
        regenerate_relationship_maps_for_class(initial_context_institution, initial_context_group)