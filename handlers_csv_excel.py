# handlers_csv_excel.py
# (v1.9.0 - Cambiado "Alumno" a "Miembro", "Genero" a "Sexo", Importación granular y validaciones de contexto)

# --- BLOQUE 0: IMPORTACIONES Y CONFIGURACIÓN INICIAL ---
import sys
import io
import re
import collections
import traceback
import base64
import datetime
import unicodedata
import csv
import os

from IPython.display import display, clear_output, HTML
from ipywidgets import widgets, VBox, HBox, Layout, Button, Checkbox, Output, HTML as IPHTMLWidget

import sociograma_data # Importar sociograma_data directamente (contendrá members_data)
import pdf_generator

NOMINATOR_ID_COLS_ORDERED = [
    "Marca temporal",
    "Dirección de correo electrónico",
    "Institucion",
    "Grupo",
    "Nombre y Apellido", # Esta es la columna para el nombre del miembro
    "Sexo",
    "Fecha De Nacimiento"
]

ESSENTIAL_NOMINATOR_COLS_IF_MEMBERS_OR_RESP = [ # CAMBIO
    "Institucion",
    "Grupo",
    "Nombre y Apellido", # Columna para el miembro
    "Sexo",
    "Fecha De Nacimiento"
]

_import_session_data = {}
DEBUG_NOMINADOR_TARGET = "daniel" # Puede ser un nombre de miembro para depurar
# --- FIN BLOQUE 0 ---

# --- BLOQUE 1: FUNCIONES HELPER DE PARSEO Y GENERACIÓN DE DATOS ---
def parse_nombre_apellido(nombre_completo_str):
    partes = nombre_completo_str.strip().split()
    apellido = ""
    nombre = ""
    if not partes:
        return nombre, apellido
    if len(partes) == 1:
        nombre = partes[0]
    else:
        apellido = partes[-1]
        nombre = " ".join(partes[:-1])
    return nombre.strip(), apellido.strip()

def generar_iniciales_desde_nombre_apellido(nombre_str, apellido_str):
    iniciales = []
    if nombre_str:
        for parte_n in nombre_str.strip().split():
            if parte_n:
                iniciales.append(parte_n[0].upper())
            if len(iniciales) >= 2:
                break
    if apellido_str:
        for parte_a in apellido_str.strip().split():
            if parte_a:
                iniciales.append(parte_a[0].upper())
            if len(iniciales) >= 4:
                break
    final_str_iniciales = "".join(iniciales)
    if not final_str_iniciales:
        return "N/A"
    if len(final_str_iniciales) > 4:
        final_str_iniciales = final_str_iniciales[:4]
    if final_str_iniciales != "N/A":
        while len(final_str_iniciales) < 3:
            final_str_iniciales += "X"
    return final_str_iniciales

def generar_data_key_desde_texto(texto_pregunta):
    if not texto_pregunta:
        return None
    s = texto_pregunta.lower().strip()
    s = re.sub(r'\s+', '_', s)
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    s = re.sub(r'[^a-z0-9_]', '', s)
    s = re.sub(r'__+', '_', s)
    s = s.strip('_')
    return f"q_{s[:50]}" if s else f"q_pregunta_{abs(hash(texto_pregunta))%10000}"

def normalizar_nombre_para_comparacion(nombre_str):
    if not isinstance(nombre_str, str):
        return ""
    s = nombre_str.lower().strip()
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    s = re.sub(r'[^a-z0-9\s]', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s
# --- FIN BLOQUE 1 ---
# --- BLOQUE 2: FUNCIONES HELPER PARA LA SESIÓN DE IMPORTACIÓN (LOGS, ERRORES) ---
def _reset_import_session_data(file_name=""):
    global _import_session_data
    _import_session_data = {
        'file_name_original': file_name,
        'import_mode': 'add_new_only',
        'import_mode_display_name': 'Importación Granular por Checkboxes',
        'default_allow_self_for_new_questions': False,

        'import_escuelas_selected': True,
        'import_grupos_selected': True,
        'import_miembros_selected': True, # CAMBIO
        'import_defs_preguntas_selected': True,
        'import_respuestas_selected': True,
        'prefill_mentioned_members_if_resp_selected': True, # CAMBIO
        'csv_excess_response_handling_mode': 'omit_extra',

        'newly_created_question_data_keys_this_session': set(),
        '_escuelas_nuevas_sesion': [],

        'csv_data_list': [],
        'parsed_questions_from_csv_headers': collections.defaultdict(list),

        'escuela_ref_for_polarity_confirm': None,
        'grupo_ref_for_polarity_confirm': None,
        'questions_needing_polarity_confirm': {},

        'escuela_seleccionada_en_ui_al_importar': None,
        'current_class_selected_in_ui_for_context': None,

        'contadores': collections.defaultdict(int),
        'errores_detalle': [],
        'advertencias_detalle': [],
        'log_proceso': [],
        
        'global_registro_output_ref': None
    }

def _configure_global_registro_output_for_session(registro_output_global):
    global _import_session_data
    if registro_output_global and isinstance(registro_output_global, widgets.Output):
        _import_session_data['global_registro_output_ref'] = registro_output_global
    else:
        _import_session_data['global_registro_output_ref'] = None

def _log_to_global_output(message):
    global _import_session_data
    ro_widget = _import_session_data.get('global_registro_output_ref')
    # if ro_widget:
      # with ro_widget:
          # print(f"[CSV Import]: {message}") # COMENTADO PARA UNA SALIDA LIMPIA

def _log_proceso_interno(msg):
    global _import_session_data
    timestamp = datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]
    full_log_msg = f"[{timestamp}] {msg}"
    _import_session_data['log_proceso'].append(full_log_msg)
    # _log_to_global_output(f"LOG: {msg}") # COMENTADO PARA UNA SALIDA LIMPIA

def _add_error_detalle(msg, log_to_global=True):
    global _import_session_data
    _import_session_data['errores_detalle'].append(msg)
    if log_to_global:
        pass # _log_to_global_output(f"ERROR DETALLE: {msg}") # COMENTADO PARA UNA SALIDA LIMPIA

def _add_advertencia_detalle(msg, log_to_global=True):
    global _import_session_data
    _import_session_data['advertencias_detalle'].append(msg)
    if log_to_global:
        pass # _log_to_global_output(f"ADVERTENCIA DETALLE: {msg}") # COMENTADO PARA UNA SALIDA LIMPIA
# --- FIN BLOQUE 2 ---
# --- BLOQUE 3: UI Y LÓGICA PARA CONFIRMACIÓN DE POLARIDAD DE PREGUNTAS ---
def _display_polarity_confirmation_ui_static(ui_main_institutions_dict_ref_dp,
                                             callback_finalize_import_dp,
                                             app_state_dp=None,
                                             institution_refresh_func_dp=None,
                                             registro_output_dp=None
                                             ):
    """
    Muestra dinámicamente una UI para que el usuario confirme la polaridad
    de las preguntas nuevas encontradas en el CSV.
    """
    global _import_session_data
    institution_ref_dp = _import_session_data.get('escuela_ref_for_polarity_confirm', 'N/A')
    group_ref_dp = _import_session_data.get('grupo_ref_for_polarity_confirm', 'N/A')
    preguntas_a_confirmar_dp = _import_session_data.get('questions_needing_polarity_confirm', {})
    
    confirm_polarity_output_widget_dp = ui_main_institutions_dict_ref_dp.get("confirm_polarity_output_csv")

    if not confirm_polarity_output_widget_dp:
        _add_error_detalle("Error crítico: Widget de confirmación de polaridad (confirm_polarity_output_csv) no encontrado.")
        # _log_proceso_interno("OMITIENDO confirmación de polaridad debido a widget de UI faltante.")
        callback_finalize_import_dp(
            {},
            ui_main_institutions_dict_ref_ff=ui_main_institutions_dict_ref_dp,
            app_state_ref_ff=app_state_dp,
            institution_refresh_func_ref_ff=institution_refresh_func_dp,
            registro_output_ref_ff=registro_output_dp
        )
        return

    with confirm_polarity_output_widget_dp:
        clear_output(wait=True)
        
        if not preguntas_a_confirmar_dp:
            # _log_proceso_interno("No hay preguntas nuevas que necesiten confirmación de polaridad.")
            callback_finalize_import_dp(
                {},
                ui_main_institutions_dict_ref_ff=ui_main_institutions_dict_ref_dp,
                app_state_ref_ff=app_state_dp,
                institution_refresh_func_ref_ff=institution_refresh_func_dp,
                registro_output_ref_ff=registro_output_dp
            )
            return

        html_intro_value_dp = (
            f"<h4>Definir Polaridad para Nuevas Preguntas en {institution_ref_dp} - {group_ref_dp}:</h4>"
            f"<p style='font-size:0.9em;'>Marcar la casilla = Pregunta Positiva.</p>"
            f"<p style='font-size:0.9em;'>Desmarcar la casilla = Pregunta Negativa.</p>"
            f"<p style='font-size:0.8em; color:grey;'><i>Preguntas del CSV no existentes en la institución/grupo.</i></p>"
        )
        html_intro_dp = widgets.HTML(value=html_intro_value_dp)
        
        widgets_polaridad_ui_list_dp = [html_intro_dp]
        pregunta_checkbox_map_local_dp = {}

        for pregunta_base_csv_dp, info_pregunta_dp in preguntas_a_confirmar_dp.items():
            data_key_propuesto_dp = info_pregunta_dp.get('data_key')
            if not data_key_propuesto_dp:
                data_key_propuesto_dp = generar_data_key_desde_texto(pregunta_base_csv_dp)

            default_polarity_is_positive_dp = True
            texto_pregunta_lower_dp = pregunta_base_csv_dp.lower()
            palabras_negativas_dp = ["no ", "evitar", "nunca", "jamás", "rechaz", "odia", "mal"]
            if any(palabra_neg_dp in texto_pregunta_lower_dp for palabra_neg_dp in palabras_negativas_dp):
                default_polarity_is_positive_dp = False
            
            checkbox_descripcion_dp = f"{pregunta_base_csv_dp[:70]}" + ("..." if len(pregunta_base_csv_dp) > 70 else "")
            
            cb_polaridad_actual_dp = widgets.Checkbox(
                value=default_polarity_is_positive_dp, description=checkbox_descripcion_dp,
                indent=False, layout=Layout(width='95%', margin_bottom='3px')
            )
            pregunta_checkbox_map_local_dp[data_key_propuesto_dp] = {
                'checkbox': cb_polaridad_actual_dp,
                'pregunta_base_csv': pregunta_base_csv_dp,
                'tipo_propuesto': info_pregunta_dp.get('tipo_propuesto', pregunta_base_csv_dp[:30])
            }
            widgets_polaridad_ui_list_dp.append(cb_polaridad_actual_dp)
        
        confirm_button_polaridad_dp = widgets.Button(
            description="Confirmar Polaridades y Continuar Importación",
            button_style='info', icon='check', layout=Layout(margin_top='10px', width='auto')
        )
        
        def _on_confirm_polarities_static_internal_handler_dp(b_ignored_dp):
            preguntas_confirmadas_final_dict_dp_handler = {}
            for data_key_handler_dp, widget_info_handler_dp in pregunta_checkbox_map_local_dp.items():
                preguntas_confirmadas_final_dict_dp_handler[data_key_handler_dp] = {
                    'polaridad': 'positive' if widget_info_handler_dp['checkbox'].value else 'negative',
                    'texto_pregunta_original_csv': widget_info_handler_dp['pregunta_base_csv'],
                    'tipo_propuesto': widget_info_handler_dp['tipo_propuesto']
                }
            
            # _log_proceso_interno(f"Polaridades confirmadas por usuario: {preguntas_confirmadas_final_dict_dp_handler}")
            
            with confirm_polarity_output_widget_dp:
                clear_output(wait=True)
                display(HTML("<i>Polaridades definidas. Continuando con la importación...</i>"))
            
            callback_finalize_import_dp(
                preguntas_confirmadas_final_dict_dp_handler,
                ui_main_institutions_dict_ref_ff=ui_main_institutions_dict_ref_dp,
                app_state_ref_ff=app_state_dp,
                institution_refresh_func_ref_ff=institution_refresh_func_dp,
                registro_output_ref_ff=registro_output_dp
            )

        confirm_button_polaridad_dp.on_click(_on_confirm_polarities_static_internal_handler_dp)
        widgets_polaridad_ui_list_dp.append(confirm_button_polaridad_dp)
        
        display(VBox(children=widgets_polaridad_ui_list_dp))
        # _log_proceso_interno("UI de confirmación de polaridad mostrada al usuario.")
# --- FIN BLOQUE 3 ---
# --- BLOQUE 4: FINALIZACIÓN DE IMPORTACIÓN (DEFINICIONES DE PREGUNTAS Y RESPUESTAS) ---
def _finalize_import_stages(preguntas_con_polaridad_confirmada,
                            ui_main_institutions_dict_ref_ff=None,
                            app_state_ref_ff=None,
                            institution_refresh_func_ref_ff=None,
                            registro_output_ref_ff=None
                           ):
    global _import_session_data
    
    # _log_proceso_interno(f"Iniciando EJECUCIÓN de importación (v2.5 - Atómico). Polaridades: {len(preguntas_con_polaridad_confirmada)}")

    # --- PASO 1: Crear entidades básicas (si fue seleccionado) ---
    if _import_session_data.get('import_escuelas_selected', False):
        # _log_proceso_interno("Ejecutando: Creación de Instituciones...")
        institutions_procesadas_set_inst_proc_p1 = set()
        if '_escuelas_nuevas_sesion' not in _import_session_data: _import_session_data['_escuelas_nuevas_sesion'] = []
        for row_inst_create_proc_p1 in _import_session_data['csv_data_list']:
            inst_csv_create_proc_p1 = str(row_inst_create_proc_p1.get("Institucion", "")).strip()
            if inst_csv_create_proc_p1 and inst_csv_create_proc_p1 not in institutions_procesadas_set_inst_proc_p1:
                if inst_csv_create_proc_p1 not in sociograma_data.schools_data:
                    sociograma_data.schools_data[inst_csv_create_proc_p1] = f"Importada CSV: {_import_session_data['file_name_original']}"
                    sociograma_data.classes_data.setdefault(inst_csv_create_proc_p1, [])
                    sociograma_data.members_data.setdefault(inst_csv_create_proc_p1, collections.OrderedDict())
                    _import_session_data['contadores']['escuelas_creadas'] += 1
                    _import_session_data['_escuelas_nuevas_sesion'].append(inst_csv_create_proc_p1)
                else:
                    _import_session_data['contadores']['escuelas_ya_existentes_omitidas'] += 1
                institutions_procesadas_set_inst_proc_p1.add(inst_csv_create_proc_p1)
    
    if _import_session_data.get('import_grupos_selected', False):
        # _log_proceso_interno("Ejecutando: Creación de Grupos...")
        groups_procesadas_set_grp_proc_p2 = set()
        for row_grp_create_proc_p2 in _import_session_data['csv_data_list']:
            inst_csv_grp_proc_p2 = str(row_grp_create_proc_p2.get("Institucion", "")).strip()
            grp_csv_proc_p2 = str(row_grp_create_proc_p2.get("Grupo", "")).strip()
            if not inst_csv_grp_proc_p2 or not grp_csv_proc_p2: continue
            institution_destino_para_grupo_proc_p2 = inst_csv_grp_proc_p2
            if inst_csv_grp_proc_p2 not in sociograma_data.schools_data:
                if not _import_session_data.get('import_escuelas_selected', False) and _import_session_data['escuela_seleccionada_en_ui_al_importar']:
                    institution_destino_para_grupo_proc_p2 = _import_session_data['escuela_seleccionada_en_ui_al_importar']
                else: continue
            if institution_destino_para_grupo_proc_p2 and (institution_destino_para_grupo_proc_p2, grp_csv_proc_p2) not in groups_procesadas_set_grp_proc_p2:
                if institution_destino_para_grupo_proc_p2 in sociograma_data.schools_data:
                    if not any(c.get('name') == grp_csv_proc_p2 for c in sociograma_data.classes_data.get(institution_destino_para_grupo_proc_p2, [])):
                        sociograma_data.classes_data[institution_destino_para_grupo_proc_p2].append({"name": grp_csv_proc_p2, "coordinator": "Importado CSV"})
                        sociograma_data.members_data.get(institution_destino_para_grupo_proc_p2, collections.OrderedDict()).setdefault(grp_csv_proc_p2, [])
                        sociograma_data.get_class_question_definitions(institution_destino_para_grupo_proc_p2, grp_csv_proc_p2)
                        _import_session_data['contadores']['grupos_creados'] += 1
                    else:
                        _import_session_data['contadores']['grupos_ya_existentes_omitidos'] +=1
                    groups_procesadas_set_grp_proc_p2.add((institution_destino_para_grupo_proc_p2, grp_csv_proc_p2))

    if _import_session_data.get('import_miembros_selected', False):
        # _log_proceso_interno("Ejecutando: Creación de miembros NOMINADORES...")
        for row_idx_nom_p3a, row_dict_nom_p3a in enumerate(_import_session_data['csv_data_list']):
            inst_nom_csv_p3a = str(row_dict_nom_p3a.get("Institucion", "")).strip()
            grp_nom_csv_p3a = str(row_dict_nom_p3a.get("Grupo", "")).strip()
            nom_ap_nom_csv_p3a = str(row_dict_nom_p3a.get("Nombre y Apellido", "")).strip()
            sexo_nom_csv_original_p3a = str(row_dict_nom_p3a.get("Sexo", "Desconocido")).strip()
            nac_nom_csv_p3a = str(row_dict_nom_p3a.get("Fecha De Nacimiento", "")).strip()

            if not all([inst_nom_csv_p3a, grp_nom_csv_p3a, nom_ap_nom_csv_p3a, nac_nom_csv_p3a]): continue

            nombre_p_nom_proc_parsed, apellido_p_nom_proc_parsed = parse_nombre_apellido(nom_ap_nom_csv_p3a)
            cognome_para_guardar_db = apellido_p_nom_proc_parsed.upper()
            nome_para_guardar_db = nombre_p_nom_proc_parsed.title()
            nombre_normalizado_nominador_csv = normalizar_nombre_para_comparacion(f"{cognome_para_guardar_db} {nome_para_guardar_db}")
            
            miembros_grupo_actual_p3a = sociograma_data.members_data.get(inst_nom_csv_p3a, {}).get(grp_nom_csv_p3a, [])
            miembro_existente_p3a_db = next((s_ex_db for s_ex_db in miembros_grupo_actual_p3a if normalizar_nombre_para_comparacion(f"{s_ex_db.get('cognome','')} {s_ex_db.get('nome','').strip()}") == nombre_normalizado_nominador_csv), None)

            if not miembro_existente_p3a_db:
                iniz_generadas_p3a_val = generar_iniciales_desde_nombre_apellido(nome_para_guardar_db, cognome_para_guardar_db)
                sexo_nom_csv_final_p3a = sexo_nom_csv_original_p3a
                if sexo_nom_csv_original_p3a.lower() not in ["masculino", "femenino", "desconocido"]:
                    sexo_nom_csv_final_p3a = "Desconocido"
                
                nuevo_miembro_data_p3a_val = {"cognome": cognome_para_guardar_db, "nome": nome_para_guardar_db, "iniz": iniz_generadas_p3a_val, "sexo": sexo_nom_csv_final_p3a, "fecha_nac": nac_nom_csv_p3a, "annotations": f"Importado CSV (Nominador): {_import_session_data['file_name_original']}"}
                
                if grp_nom_csv_p3a not in sociograma_data.members_data[inst_nom_csv_p3a]:
                    sociograma_data.members_data[inst_nom_csv_p3a][grp_nom_csv_p3a] = []
                sociograma_data.members_data[inst_nom_csv_p3a][grp_nom_csv_p3a].append(nuevo_miembro_data_p3a_val)
                _import_session_data['contadores']['miembros_creados'] += 1
            else:
                _import_session_data['contadores']['miembros_nomin_ya_existentes_omitidos'] += 1

    if _import_session_data.get('import_respuestas_selected', False) and _import_session_data.get('prefill_mentioned_members_if_resp_selected', False):
        # _log_proceso_interno("Ejecutando: Prellenado de miembros MENCIONADOS...")
        todos_los_mencionados_a_procesar_p3b_val = collections.defaultdict(lambda: collections.defaultdict(str))
        for row_menc_p3b_val in _import_session_data['csv_data_list']:
            inst_menc_csv_p3b_val = str(row_menc_p3b_val.get("Institucion", "")).strip()
            grp_menc_csv_p3b_val = str(row_menc_p3b_val.get("Grupo", "")).strip()
            if not (inst_menc_csv_p3b_val and grp_menc_csv_p3b_val): continue
            for preg_base_menc_p3b_val, cols_op_menc_p3b_val in _import_session_data['parsed_questions_from_csv_headers'].items():
                for op_info_menc_p3b_val in cols_op_menc_p3b_val:
                    elegido_orig_menc_p3b_val = str(row_menc_p3b_val.get(op_info_menc_p3b_val['col_header'], "")).strip()
                    if elegido_orig_menc_p3b_val:
                        nom_el_menc_p3b_v, ap_el_menc_p3b_v = parse_nombre_apellido(elegido_orig_menc_p3b_val)
                        nom_comp_sis_menc_p3b_v = f"{ap_el_menc_p3b_v.upper()} {nom_el_menc_p3b_v.title()}".strip()
                        nom_norm_el_menc_p3b_v = normalizar_nombre_para_comparacion(nom_comp_sis_menc_p3b_v)
                        if nom_norm_el_menc_p3b_v:
                            todos_los_mencionados_a_procesar_p3b_val[(inst_menc_csv_p3b_val, grp_menc_csv_p3b_val)][nom_norm_el_menc_p3b_v] = elegido_orig_menc_p3b_val
        for (inst_pref_menc_p3b, grp_pref_menc_p3b), miembros_norm_grupo_menc_p3b in todos_los_mencionados_a_procesar_p3b_val.items():
            miembros_exist_db_norm_menc_p3b_val = {normalizar_nombre_para_comparacion(f"{s.get('cognome','')} {s.get('nome','').strip()}") for s in sociograma_data.members_data.get(inst_pref_menc_p3b, {}).get(grp_pref_menc_p3b, [])}
            for nom_norm_el_pref_menc_p3b_v, elegido_orig_log_menc_p3b_v in miembros_norm_grupo_menc_p3b.items():
                if nom_norm_el_pref_menc_p3b_v not in miembros_exist_db_norm_menc_p3b_val:
                    nom_el_log_menc_p3b_v, ap_el_log_menc_p3b_v = parse_nombre_apellido(elegido_orig_log_menc_p3b_v)
                    cognome_g_pref_menc_p3b_v = ap_el_log_menc_p3b_v.upper(); nome_g_pref_menc_p3b_v = nom_el_log_menc_p3b_v.title()
                    iniciales_g_pref_menc_p3b_v = generar_iniciales_desde_nombre_apellido(nome_g_pref_menc_p3b_v, cognome_g_pref_menc_p3b_v)
                    miembro_prellenado_data_menc_p3b_val = {"cognome": cognome_g_pref_menc_p3b_v, "nome": nome_g_pref_menc_p3b_v, "iniz": iniciales_g_pref_menc_p3b_v, "sexo": "Desconocido", "fecha_nac": "", "annotations": f"Creado por mención en CSV: {_import_session_data['file_name_original']}"}
                    sociograma_data.members_data[inst_pref_menc_p3b][grp_pref_menc_p3b].append(miembro_prellenado_data_menc_p3b_val)
                    _import_session_data['contadores']['miembros_creados_por_mencion'] += 1
                    miembros_exist_db_norm_menc_p3b_val.add(nom_norm_el_pref_menc_p3b_v)
                else:
                    _import_session_data['contadores']['miembros_menc_ya_existentes_no_recreados'] +=1

    # --- FASE 2: Procesar Definiciones de Preguntas ---
    clases_afectadas_por_cambios_en_defs = set()
    should_process_question_defs = _import_session_data.get('import_defs_preguntas_selected', False) or \
                                   _import_session_data.get('force_create_defs_for_empty_group', False)

    if should_process_question_defs:
        # _log_proceso_interno("Ejecutando: Creación/Actualización de Definiciones de Preguntas...")
        is_add_only_mode = _import_session_data.get('add_new_questions_only_selected', False)
        clases_unicas_en_csv_f1 = set((str(r.get("Institucion", "")).strip(), str(r.get("Grupo", "")).strip()) for r in _import_session_data.get('csv_data_list', []) if r.get("Institucion") and r.get("Grupo"))
        
        for inst_destino_f1, grp_destino_f1 in clases_unicas_en_csv_f1:
            if not (inst_destino_f1 in sociograma_data.schools_data and any(c.get('name') == grp_destino_f1 for c in sociograma_data.classes_data.get(inst_destino_f1, []))): continue
            
            defs_grupo_actual_f1 = sociograma_data.get_class_question_definitions(inst_destino_f1, grp_destino_f1)
            defs_realmente_modificadas_este_grupo_f1 = False

            if not is_add_only_mode:
                defs_grupo_actual_f1.clear()
                # _log_proceso_interno(f"  Modo Sobrescribir: Limpiando definiciones existentes para el grupo '{grp_destino_f1}'.")

            for preg_base_csv_f1, opciones_cols_f1 in _import_session_data['parsed_questions_from_csv_headers'].items():
                data_key_f1 = generar_data_key_desde_texto(preg_base_csv_f1)
                
                if data_key_f1 not in defs_grupo_actual_f1:
                    num_miembros_grupo_f1 = len(sociograma_data.members_data.get(inst_destino_f1, {}).get(grp_destino_f1, []))
                    allow_self_global_para_nuevas_f1 = _import_session_data.get('default_allow_self_for_new_questions', False)
                    max_sel_sugerido_por_csv_f1 = len(opciones_cols_f1) if opciones_cols_f1 else 1
                    max_permitido_por_N_esta_preg_f1 = max(0, num_miembros_grupo_f1 if allow_self_global_para_nuevas_f1 else num_miembros_grupo_f1 - 1)
                    max_sel_final_calculado_f1 = min(max_sel_sugerido_por_csv_f1, max_permitido_por_N_esta_preg_f1)
                    polaridad_f1 = 'positive'; tipo_f1 = preg_base_csv_f1[:30]
                    info_confirmada_f1 = preguntas_con_polaridad_confirmada.get(data_key_f1)
                    if info_confirmada_f1: polaridad_f1 = info_confirmada_f1['polaridad']; tipo_f1 = info_confirmada_f1['tipo_propuesto']
                    defs_grupo_actual_f1[data_key_f1] = { "text": preg_base_csv_f1, "type": tipo_f1, "polarity": polaridad_f1, "order": len(defs_grupo_actual_f1) + 100, "data_key": data_key_f1, "max_selections": max_sel_final_calculado_f1, "allow_self_selection": allow_self_global_para_nuevas_f1 }
                    _import_session_data['contadores']['defs_preguntas_creadas'] += 1
                    defs_realmente_modificadas_este_grupo_f1 = True
                else:
                    _import_session_data['contadores']['defs_preg_ya_existentes_omitidas'] +=1

            if defs_realmente_modificadas_este_grupo_f1:
                clases_afectadas_por_cambios_en_defs.add((inst_destino_f1, grp_destino_f1))
        
        if clases_afectadas_por_cambios_en_defs:
            # _log_proceso_interno("Regenerando mapas de relación post-actualización de definiciones...")
            for inst_map_f1, grp_map_f1 in clases_afectadas_por_cambios_en_defs:
                sociograma_data.regenerate_relationship_maps_for_class(inst_map_f1, grp_map_f1)

    # --- FASE 3: Procesar Respuestas ---
    if _import_session_data.get('import_respuestas_selected', False):
        # _log_proceso_interno("Ejecutando: Guardado de Respuestas...")
        for row_idx_resp_f2, row_dict_csv_resp_f2 in enumerate(_import_session_data.get('csv_data_list', [])):
            inst_resp_csv_f2 = str(row_dict_csv_resp_f2.get("Institucion", "")).strip()
            grp_resp_csv_f2 = str(row_dict_csv_resp_f2.get("Grupo", "")).strip()
            nom_ap_csv_nominador_f2 = str(row_dict_csv_resp_f2.get("Nombre y Apellido", "")).strip()
            if not all([inst_resp_csv_f2, grp_resp_csv_f2, nom_ap_csv_nominador_f2]): continue
            
            nombre_nominador_parsed_f2, apellido_nominador_parsed_f2 = parse_nombre_apellido(nom_ap_csv_nominador_f2)
            nombre_nominador_para_clave_f2 = f"{nombre_nominador_parsed_f2.title()} {apellido_nominador_parsed_f2.title()}".strip()
            
            if not (inst_resp_csv_f2 in sociograma_data.schools_data and any(c.get('name') == grp_resp_csv_f2 for c in sociograma_data.classes_data.get(inst_resp_csv_f2, []))): continue
            
            defs_grupo_resp_final_f2 = sociograma_data.get_class_question_definitions(inst_resp_csv_f2, grp_resp_csv_f2)
            if not defs_grupo_resp_final_f2: continue
            
            respuestas_nom_actual_final_f2 = {}
            for preg_base_csv_resp_f2, cols_op_resp_f2 in _import_session_data['parsed_questions_from_csv_headers'].items():
                data_key_preg_resp_f2 = generar_data_key_desde_texto(preg_base_csv_resp_f2)
                q_def_actual_para_resp_f2 = defs_grupo_resp_final_f2.get(data_key_preg_resp_f2)
                if not q_def_actual_para_resp_f2: continue

                max_sel_efectivo_para_esta_fila_f2 = q_def_actual_para_resp_f2.get('max_selections', 0)
                allow_self_actual_de_definicion_f2 = q_def_actual_para_resp_f2.get('allow_self_selection', False)
                elecciones_raw_csv_preg_actual_f2 = [str(row_dict_csv_resp_f2.get(op['col_header'], "")).strip() for op in sorted(cols_op_resp_f2, key=lambda x: x['option_num']) if str(row_dict_csv_resp_f2.get(op['col_header'], "")).strip()]
                
                elecciones_validas_preg_actual_final_f2_para_pregunta = []
                for elegido_orig_csv_resp_f2 in elecciones_raw_csv_preg_actual_f2:
                    if len(elecciones_validas_preg_actual_final_f2_para_pregunta) >= max_sel_efectivo_para_esta_fila_f2: break
                    
                    nombre_elegido_parsed_f2, apellido_elegido_parsed_f2 = parse_nombre_apellido(elegido_orig_csv_resp_f2)
                    nombre_elegido_final_para_guardar_f2 = f"{nombre_elegido_parsed_f2.title()} {apellido_elegido_parsed_f2.title()}".strip()
                    
                    if nombre_nominador_para_clave_f2 == nombre_elegido_final_para_guardar_f2 and not allow_self_actual_de_definicion_f2: continue
                    if nombre_elegido_final_para_guardar_f2 in elecciones_validas_preg_actual_final_f2_para_pregunta: continue

                    elecciones_validas_preg_actual_final_f2_para_pregunta.append(nombre_elegido_final_para_guardar_f2)
                
                if elecciones_validas_preg_actual_final_f2_para_pregunta:
                    respuestas_nom_actual_final_f2[data_key_preg_resp_f2] = elecciones_validas_preg_actual_final_f2_para_pregunta
            
            if respuestas_nom_actual_final_f2:
                clave_resp_miembro_final_f2 = (inst_resp_csv_f2, grp_resp_csv_f2, nombre_nominador_para_clave_f2)
                sociograma_data.questionnaire_responses_data[clave_resp_miembro_final_f2] = respuestas_nom_actual_final_f2
                _import_session_data['contadores']['respuestas_importadas_ok'] += 1

    # --- FASE 4: Mostrar Resumen Final ---
    # _log_proceso_interno("Ejecución finalizada. Mostrando resumen...")
    _display_import_summary_static(
        ui_main_institutions_dict_ref_ff,
        app_state_ref_ff,
        institution_refresh_func_ref_ff,
        registro_output_ref_ff
    )
# --- FIN BLOQUE 4 ---
# --- BLOQUE 5: MOSTRAR RESUMEN DE IMPORTACIÓN Y REFRESCO DE UI ---
def _display_import_summary_static(ui_main_institutions_dict_ref, app_state, institution_refresh_func_ref, registro_output_ref_summary):
    global _import_session_data
    import_status_output_widget_local = ui_main_institutions_dict_ref.get("import_status_output_csv")
    
    if not import_status_output_widget_local:
        # _log_proceso_interno("Error crítico: Widget de estado de importación local (import_status_output_csv) no encontrado para mostrar resumen.")
        if registro_output_ref_summary and isinstance(registro_output_ref_summary, widgets.Output):
            with registro_output_ref_summary:
                print("[CSV Import]: ERROR CRÍTICO - Widget de estado de importación local no encontrado. Resumen no mostrado en UI de importación.")
        return
    
    contadores = _import_session_data.get('contadores', collections.defaultdict(int))
    errores_list = _import_session_data.get('errores_detalle', [])
    advertencias_list = _import_session_data.get('advertencias_detalle', [])
    f_name = _import_session_data.get('file_name_original', 'Desconocido')
    
    res_html = f"<h4>Resultados Importación CSV '{f_name}':</h4>"
    res_html += "<p><b>Opciones de Importación Seleccionadas:</b><ul style='list-style-type: none; padding-left: 10px;'>"
    if _import_session_data.get('import_escuelas_selected', False): res_html += "<li>- Importar/Crear Instituciones</li>"
    if _import_session_data.get('import_grupos_selected', False): res_html += "<li>- Importar/Crear Grupos</li>"
    if _import_session_data.get('import_miembros_selected', False): res_html += "<li>- Importar/Crear Miembros (Nominadores)</li>"
    if _import_session_data.get('import_defs_preguntas_selected', False): res_html += "<li>- Importar/Crear Definiciones de Preguntas</li>"
    if _import_session_data.get('import_respuestas_selected', False): 
        res_html += "<li>- Importar Respuestas del Cuestionario"
        if _import_session_data.get('prefill_mentioned_members_if_resp_selected', False):
             res_html += " (con prellenado de miembros mencionados)</li>"
        else:
             res_html += " (SIN prellenado de miembros mencionados)</li>"
    if not any([_import_session_data.get('import_escuelas_selected', False),
                _import_session_data.get('import_grupos_selected', False),
                _import_session_data.get('import_miembros_selected', False),
                _import_session_data.get('import_defs_preguntas_selected', False),
                _import_session_data.get('import_respuestas_selected', False)]):
        res_html += "<li><i>Ningún tipo de dato fue seleccionado para importar.</i></li>"
    res_html += "</ul></p>"

    res_html += "<b>Estadísticas de Importación:</b><ul>"
    res_html += f"<li>Filas CSV leídas (excluyendo encabezado): {contadores.get('filas_leidas_csv',0)}</li>"
    if _import_session_data.get('import_escuelas_selected', False):
        res_html += f"<li>Instituciones creadas: {contadores.get('escuelas_creadas',0)}</li>"
        res_html += f"<li>Instituciones ya existentes (no duplicadas): {contadores.get('escuelas_ya_existentes_omitidas',0)}</li>"
    if _import_session_data.get('import_grupos_selected', False):
        res_html += f"<li>Grupos creados: {contadores.get('grupos_creados',0)}</li>"
        res_html += f"<li>Grupos ya existentes (no duplicados): {contadores.get('grupos_ya_existentes_omitidos',0)}</li>"
    if _import_session_data.get('import_miembros_selected', False):
        res_html += f"<li>Miembros (nominadores) creados desde CSV: {contadores.get('miembros_creados',0)}</li>"
        res_html += f"<li>Miembros (nominadores) ya existentes (no duplicados): {contadores.get('miembros_nomin_ya_existentes_omitidos',0)}</li>"
    if _import_session_data.get('import_respuestas_selected', False) and _import_session_data.get('prefill_mentioned_members_if_resp_selected', False):
        res_html += f"<li>Miembros (mencionados en respuestas) creados: {contadores.get('miembros_creados_por_mencion',0)}</li>"
        res_html += f"<li>Miembros (mencionados) ya existentes (no prellenados de nuevo): {contadores.get('miembros_menc_ya_existentes_no_recreados',0)}</li>"
    if _import_session_data.get('import_defs_preguntas_selected', False):
        res_html += f"<li>Definiciones de preguntas creadas: {contadores.get('defs_preguntas_creadas',0)}</li>"
        res_html += f"<li>Definiciones de preguntas ya existentes (revisadas/potencialmente actualizadas): {contadores.get('defs_preg_ya_existentes_revisadas',0)}</li>"
    if _import_session_data.get('import_respuestas_selected', False):
        res_html += f"<li>Conjuntos de Respuestas de miembros importados/actualizados: {contadores.get('respuestas_importadas_ok',0)}</li>"
    
    res_html += f"<li>Filas con error/omisión total en el procesamiento de respuestas: {contadores.get('filas_con_error_o_skip',0)}</li>"
    res_html += f"<li>Errores de datos individuales (ej. elecciones, etc.): {len(errores_list)}</li>"
    res_html += f"<li>Advertencias generadas durante el proceso: {len(advertencias_list)}</li>"
    res_html += "</ul>"

    if errores_list:
        res_html += "<p><strong>Detalles de Errores (primeros 20):</strong></p><ul style='font-size:0.85em;max-height:120px;overflow-y:auto;border:1px solid #f5c6cb;padding:5px;background-color:#f8d7da;color:#721c24;'>"
        for i, e in enumerate(errores_list[:20]): res_html += f"<li>{i+1}. {e}</li>"
        if len(errores_list) > 20: res_html += f"<li>... y {len(errores_list)-20} más.</li>"
        res_html += "</ul>"
    
    if advertencias_list:
        res_html += "<p><strong>Detalles de Advertencias (primeros 20):</strong></p><ul style='font-size:0.85em;max-height:120px;overflow-y:auto;border:1px solid #ffeeba;padding:5px;background-color:#fff3cd;color:#856404;'>"
        for i, w in enumerate(advertencias_list[:20]): res_html += f"<li>{i+1}. {w}</li>"
        if len(advertencias_list) > 20: res_html += f"<li>... y {len(advertencias_list)-20} más.</li>"
        res_html += "</ul>"

    if not errores_list and contadores.get('filas_con_error_o_skip',0) == 0:
        res_html += "<p style='color:green; font-weight:bold;'>Proceso de importación finalizado con éxito (según opciones seleccionadas).</p>"
    elif not errores_list and contadores.get('filas_con_error_o_skip',0) > 0:
        res_html += "<p style='color:orange; font-weight:bold;'>Proceso de importación finalizado. Algunas filas de respuestas fueron omitidas o tuvieron problemas.</p>"
    else:
        res_html += "<p style='color:red; font-weight:bold;'>Proceso de importación finalizado con errores. Revise los detalles.</p>"
    
    if import_status_output_widget_local:
        with import_status_output_widget_local: clear_output(wait=True); display(HTML(res_html))
    # _log_proceso_interno("Resumen de importación mostrado en la UI local de importación.")
    
    # --- Impresión de resumen en registro global COMENTADA ---
    # if registro_output_ref_summary and isinstance(registro_output_ref_summary, widgets.Output):
        # with registro_output_ref_summary:
            # print("\n--- RESUMEN IMPORTACIÓN CSV (en Registro Global) ---")
            # print(f"Archivo: {_import_session_data.get('file_name_original', 'N/A')}")
            # print(f"Opciones: Inst={_import_session_data.get('import_escuelas_selected')}, Grp={_import_session_data.get('import_grupos_selected')}, Miembros={_import_session_data.get('import_miembros_selected')}, DefP={_import_session_data.get('import_defs_preguntas_selected')}, Resp={_import_session_data.get('import_respuestas_selected')}, Prefill={_import_session_data.get('prefill_mentioned_members_if_resp_selected')}, ExcesoResp='{_import_session_data.get('csv_excess_response_handling_mode')}'")
            # cont_sum = contadores; print(f"  Filas Leídas: {cont_sum.get('filas_leidas_csv',0)}");
            # if _import_session_data.get('import_escuelas_selected'): print(f"  Instituciones Creadas: {cont_sum.get('escuelas_creadas',0)}")
            # if _import_session_data.get('import_grupos_selected'): print(f"  Grupos Creados: {cont_sum.get('grupos_creados',0)}")
            # if _import_session_data.get('import_miembros_selected'): print(f"  Miembros (Nom.): {cont_sum.get('miembros_creados',0)}")
            # if _import_session_data.get('prefill_mentioned_members_if_resp_selected') and _import_session_data.get('import_respuestas_selected'): print(f"  Miembros (Menc.): {cont_sum.get('miembros_creados_por_mencion',0)}")
            # if _import_session_data.get('import_defs_preguntas_selected'): print(f"  Defs. Pregs. Creadas: {cont_sum.get('defs_preguntas_creadas',0)}")
            # if _import_session_data.get('import_respuestas_selected'): print(f"  Respuestas Importadas: {cont_sum.get('respuestas_importadas_ok',0)}")
            # print(f"  Filas Error/Skip Resp: {cont_sum.get('filas_con_error_o_skip',0)}");
            # print(f"  Errores Datos: {len(errores_list)}, Advertencias: {len(advertencias_list)}")
            # if not errores_list and cont_sum.get('filas_con_error_o_skip',0) == 0: print("  Estado General: ÉXITO (según opciones)")
            # else: print("  Estado General: FINALIZADO CON ERRORES/ADVERTENCIAS (según opciones)")
            # print("--- FIN RESUMEN IMPORTACIÓN (Global) ---\n")

    # _log_proceso_interno("REFRESCO UI INSTITUCIONES: Iniciando intento de refresco post-importación...")
    any_data_potentially_changed_summary = any([
        contadores.get('escuelas_creadas', 0) > 0,
        contadores.get('grupos_creados', 0) > 0,
        contadores.get('miembros_creados', 0) > 0,
    ])

    if any_data_potentially_changed_summary:
        if institution_refresh_func_ref and callable(institution_refresh_func_ref):
            try:
                select_institutions_widget_summary = ui_main_institutions_dict_ref.get("select")
                if select_institutions_widget_summary:
                    # _log_proceso_interno("  REFRESCO UI INSTITUCIONES: Hay cambios y función de refresco. Actualizando lista y seleccionando...")
                    current_institution_options_summary = sorted(list(sociograma_data.schools_data.keys()))
                    old_selection_summary_inst = select_institutions_widget_summary.value
                    institution_a_seleccionar_summary = None
                    institutions_recien_creadas_summary = _import_session_data.get('_escuelas_nuevas_sesion', [])

                    if institutions_recien_creadas_summary and institutions_recien_creadas_summary[-1] in current_institution_options_summary:
                        institution_a_seleccionar_summary = institutions_recien_creadas_summary[-1]
                    elif _import_session_data.get('escuela_seleccionada_en_ui_al_importar') and \
                         _import_session_data['escuela_seleccionada_en_ui_al_importar'] in current_institution_options_summary:
                        institution_a_seleccionar_summary = _import_session_data['escuela_seleccionada_en_ui_al_importar']
                    elif old_selection_summary_inst and old_selection_summary_inst in current_institution_options_summary:
                        institution_a_seleccionar_summary = old_selection_summary_inst
                    elif current_institution_options_summary:
                        institution_a_seleccionar_summary = current_institution_options_summary[0]
                    
                    select_institutions_widget_summary.options = current_institution_options_summary
                    # _log_proceso_interno(f"  REFRESCO UI INSTITUCIONES: Opciones del Select actualizadas a: {current_institution_options_summary}")
                    
                    form_institution_vbox_ref_summary = None
                    if 'interfaces' in globals() and isinstance(globals()['interfaces'], dict):
                         form_institution_vbox_ref_summary = globals()['interfaces'].get('form_institution')

                    if select_institutions_widget_summary.value != institution_a_seleccionar_summary:
                        select_institutions_widget_summary.value = institution_a_seleccionar_summary
                        # _log_proceso_interno(f"  REFRESCO UI INSTITUCIONES: Se cambió valor del Select a '{institution_a_seleccionar_summary}'.")
                    elif institution_a_seleccionar_summary is not None:
                        # _log_proceso_interno(f"  REFRESCO UI INSTITUCIONES: Valor del Select ('{institution_a_seleccionar_summary}') no cambió. Forzando handler.")
                        change_event_data_summary_force_inst = {
                            'name': 'value', 'old': old_selection_summary_inst, 'new': institution_a_seleccionar_summary,
                            'owner': select_institutions_widget_summary, 'type': 'change'
                        }
                        institution_refresh_func_ref(change_event_data_summary_force_inst, app_state, ui_main_institutions_dict_ref,
                                                registro_output_ref_summary, form_school_vbox_ref=form_institution_vbox_ref_summary)
                        # _log_proceso_interno("  REFRESCO UI INSTITUCIONES: Llamada forzada al handler completada.")
                    else:
                        # _log_proceso_interno("  REFRESCO UI INSTITUCIONES: No hay valor para seleccionar. Llamando handler con None.")
                        change_event_data_summary_clear_inst = {
                            'name': 'value', 'old': old_selection_summary_inst, 'new': None,
                            'owner': select_institutions_widget_summary, 'type': 'change'
                        }
                        institution_refresh_func_ref(change_event_data_summary_force_inst, app_state, ui_main_institutions_dict_ref,
                                        registro_output_ref_summary, form_institution_vbox_ref=form_institution_vbox_ref_summary)
                else:
                    _add_error_detalle("ADVERTENCIA (Refresco UI Instituciones): Widget Select de instituciones no encontrado.")
            except Exception as e_refresh_ui_summary_inst:
                _add_error_detalle(f"Error al intentar refrescar UI de instituciones post-importación: {e_refresh_ui_summary_inst}")
                # _log_proceso_interno(f"  ERROR refrescando UI post-importación: {e_refresh_ui_summary_inst}\n{traceback.format_exc(limit=1)}")
        else:
            pass # _log_proceso_interno("  ADVERTENCIA (Refresco UI Instituciones): No se proporcionó una función de refresco válida (institution_refresh_func_ref).")
    # else:
        # _log_proceso_interno("  REFRESCO UI INSTITUCIONES: No se detectaron cambios que requieran refresco.")
    
    # _log_proceso_interno("--- FIN _display_import_summary_static ---")
# --- FIN BLOQUE 5 ---
def _validate_import_request(app_state):
    """
    Valida todas las reglas de negocio ANTES de modificar cualquier dato.
    Devuelve True si todo es correcto, False si hay un error.
    Los errores se registran en _import_session_data.
    """
    global _import_session_data
    # _log_proceso_interno("--- INICIO VALIDACIÓN DE IMPORTACIÓN ---")
    is_valid = True

    # Obtener opciones del usuario desde la sesión
    import_inst = _import_session_data.get('import_escuelas_selected', False)
    import_grp = _import_session_data.get('import_grupos_selected', False)
    import_defs = _import_session_data.get('import_defs_preguntas_selected', False)
    add_only = _import_session_data.get('add_new_questions_only_selected', False)
    import_resp = _import_session_data.get('import_respuestas_selected', False)
    prefill_members = _import_session_data.get('prefill_mentioned_members_if_resp_selected', False)
    allow_self_new_q = _import_session_data.get('default_allow_self_for_new_questions', False)
    
    # --- Preparar datos para las validaciones ---
    grupos_en_csv = set((str(r.get("Institucion", "")).strip(), str(r.get("Grupo", "")).strip()) for r in _import_session_data['csv_data_list'] if r.get("Institucion") and r.get("Grupo"))
    data_keys_csv_set = {generar_data_key_desde_texto(p) for p in _import_session_data['parsed_questions_from_csv_headers']}

    # --- REGLA 1: Existencia de Institución/Grupo si no se permite crearlos ---
    for inst_csv, grp_csv in grupos_en_csv:
        if not import_inst and inst_csv not in sociograma_data.schools_data:
            _add_error_detalle(f"Error: La institución '{inst_csv}' del CSV no existe y la opción 'Importar/Crear Instituciones' está desactivada.")
            is_valid = False
        
        institucion_existe_o_se_creara = import_inst or (inst_csv in sociograma_data.schools_data)
        if institucion_existe_o_se_creara and not import_grp and not any(c.get('name') == grp_csv for c in sociograma_data.classes_data.get(inst_csv, [])):
             _add_error_detalle(f"Error: El grupo '{grp_csv}' en la institución '{inst_csv}' no existe y la opción 'Importar/Crear Grupos' está desactivada.")
             is_valid = False
    
    if not is_valid: 
        # _log_proceso_interno("--- FIN VALIDACIÓN: Falló por existencia de Institución/Grupo. ---"); 
        return False

    # --- REGLA 2: Compatibilidad de Preguntas ---
    if not import_defs and not add_only: # Modo estricto
        for inst_csv, grp_csv in grupos_en_csv:
            if not (inst_csv in sociograma_data.schools_data and any(c.get('name') == grp_csv for c in sociograma_data.classes_data.get(inst_csv, []))):
                continue

            defs_existentes = sociograma_data.get_class_question_definitions(inst_csv, grp_csv)
            if not defs_existentes and data_keys_csv_set:
                _add_error_detalle(f"Error de Incompatibilidad: El grupo '{grp_csv}' está vacío, pero el CSV tiene preguntas. Active 'Importar/Crear Defs. Preguntas' para poblarlas.")
                is_valid = False
            elif defs_existentes:
                data_keys_existentes_set = {q_def.get('data_key', q_id) for q_id, q_def in defs_existentes.items()}
                if data_keys_csv_set != data_keys_existentes_set:
                    _add_error_detalle(f"Error de Incompatibilidad: Las preguntas del CSV no coinciden exactamente con las del grupo '{grp_csv}'. Active 'Agregar preguntas faltantes' o asegúrese de que los cuestionarios son idénticos.")
                    is_valid = False

    if not is_valid: 
        # _log_proceso_interno("--- FIN VALIDACIÓN: Falló por incompatibilidad de preguntas. ---"); 
        return False

    # --- REGLA 3: Número de respuestas vs. Miembros y Auto-selección ---
    for inst_csv, grp_csv in grupos_en_csv:
        miembros_actuales_grupo = sociograma_data.members_data.get(inst_csv, {}).get(grp_csv, [])
        nombres_miembros_actuales = {f"{m.get('nome', '').title()} {m.get('cognome', '').title()}".strip() for m in miembros_actuales_grupo}
        
        nuevos_nominadores = set()
        if 'import_miembros' in locals() and import_miembros:
            for r in _import_session_data['csv_data_list']:
                if r.get('Institucion') == inst_csv and r.get('Grupo') == grp_csv:
                    nombre, apellido = parse_nombre_apellido(r.get('Nombre y Apellido', ''))
                    nombre_completo = f"{nombre.title()} {apellido.title()}".strip()
                    if nombre_completo not in nombres_miembros_actuales:
                        nuevos_nominadores.add(nombre_completo)

        nuevos_mencionados = set()
        if prefill_members:
            for r in _import_session_data['csv_data_list']:
                if r.get('Institucion') == inst_csv and r.get('Grupo') == grp_csv:
                    for preg_header, elecciones in r.items():
                        if '[' in preg_header and 'Opcion' in preg_header:
                            nombre, apellido = parse_nombre_apellido(elecciones)
                            nombre_completo = f"{nombre.title()} {apellido.title()}".strip()
                            if nombre_completo and nombre_completo not in nombres_miembros_actuales and nombre_completo not in nuevos_nominadores:
                                nuevos_mencionados.add(nombre_completo)

        num_miembros_total_proyectado = len(nombres_miembros_actuales) + len(nuevos_nominadores) + len(nuevos_mencionados)

        for preg_base_csv, opciones_cols in _import_session_data['parsed_questions_from_csv_headers'].items():
            num_respuestas_csv = len(opciones_cols)
            
            data_key = generar_data_key_desde_texto(preg_base_csv)
            if data_key not in sociograma_data.get_class_question_definitions(inst_csv, grp_csv):
                if not allow_self_new_q and num_miembros_total_proyectado <= 1:
                    _add_error_detalle(f"Error de Configuración: La pregunta nueva '{preg_base_csv[:30]}...' no puede crearse para el grupo '{grp_csv}' porque solo tendría {num_miembros_total_proyectado} miembro(s) y la auto-selección está desactivada por defecto.")
                    is_valid = False
                
                max_posible = num_miembros_total_proyectado if allow_self_new_q else num_miembros_total_proyectado - 1
                if num_respuestas_csv > max_posible:
                    _add_error_detalle(f"Error de Límite: Para la pregunta nueva '{preg_base_csv[:30]}...', el CSV requiere {num_respuestas_csv} elecciones, pero el máximo posible para el grupo '{grp_csv}' será de {max_posible} miembros.")
                    is_valid = False
    
    if not is_valid: 
        # _log_proceso_interno("--- FIN VALIDACIÓN: Falló por número de respuestas o configuración de auto-selección. ---"); 
        return False

    # _log_proceso_interno("--- FIN VALIDACIÓN: Todas las reglas pasaron exitosamente. ---")
    return True

# --- BLOQUE 6 (Parte A y B): HANDLER PRINCIPAL DE IMPORTACIÓN Y PROCESAMIENTO ---
def _process_csv_from_content_path_static(b_ignored, app_state, ui_main_institutions_dict_ref, institution_refresh_func_ref, registro_output):
    global _import_session_data

    # 1. Obtener widgets y verificar que la UI esté completa
    if not ui_main_institutions_dict_ref or not isinstance(ui_main_institutions_dict_ref, dict):
        if registro_output:
          with registro_output: print("[CSV Import]: ERROR CRÍTICO - ui_main_institutions_dict_ref no es un diccionario válido.")
        return
    import_status_output_widget_local = ui_main_institutions_dict_ref.get("import_status_output_csv")
    confirm_polarity_output_widget_local = ui_main_institutions_dict_ref.get("confirm_polarity_output_csv")
    if not import_status_output_widget_local or not confirm_polarity_output_widget_local:
        if registro_output:
          with registro_output: print("[CSV Import]: ERROR CRÍTICO - Widgets de status/confirmación (locales) no encontrados.")
        return
    
    with import_status_output_widget_local: clear_output(wait=True); display(HTML("<i>Iniciando procesamiento de archivo CSV... Por favor, espere.</i>"))
    with confirm_polarity_output_widget_local: clear_output(wait=True)

    # 2. Leer las opciones de la UI
    file_name_widget = ui_main_institutions_dict_ref.get("csv_file_name_input")
    allow_self_default_widget = ui_main_institutions_dict_ref.get("csv_allow_self_default_dropdown")
    cb_institutions_ui = ui_main_institutions_dict_ref.get("import_cb_institutions_csv")
    cb_grupos_ui = ui_main_institutions_dict_ref.get("import_cb_grupos_csv")
    cb_miembros_ui = ui_main_institutions_dict_ref.get("import_cb_alumnos_csv")
    cb_defs_preguntas_ui = ui_main_institutions_dict_ref.get("import_cb_defs_preguntas_csv")
    cb_add_new_questions_only_ui = ui_main_institutions_dict_ref.get("import_cb_add_new_questions_only_csv")
    cb_respuestas_ui = ui_main_institutions_dict_ref.get("import_cb_respuestas_csv")
    cb_prefill_mentioned_ui = ui_main_institutions_dict_ref.get("import_cb_prefill_mentioned_csv")
    csv_excess_resp_mode_widget_ui = ui_main_institutions_dict_ref.get("csv_excess_response_mode_dropdown")

    if not all([file_name_widget, allow_self_default_widget, cb_institutions_ui, cb_grupos_ui, cb_miembros_ui, cb_defs_preguntas_ui, cb_add_new_questions_only_ui, cb_respuestas_ui, cb_prefill_mentioned_ui, csv_excess_resp_mode_widget_ui]):
        err_msg_ui_missing_proc_imp = "<p style='color:red;'><b>ERROR DE CONFIGURACIÓN:</b> Faltan elementos de UI esenciales para la importación.</p>"
        with import_status_output_widget_local: clear_output(wait=True); display(HTML(err_msg_ui_missing_proc_imp))
        if registro_output:
          with registro_output: print(f"[CSV Import]: ERROR - Faltan widgets de configuración esenciales.")
        return

    # 3. Inicializar sesión de importación
    file_name_from_input_proc_imp = file_name_widget.value.strip()
    if not file_name_from_input_proc_imp:
        with import_status_output_widget_local: clear_output(wait=True); display(HTML("<p style='color:red;'>Error: Nombre de archivo CSV no puede estar vacío.</p>")); return
    file_path_to_process_proc_imp = os.path.join("/content/", file_name_from_input_proc_imp)
    if not os.path.exists(file_path_to_process_proc_imp):
        with import_status_output_widget_local: clear_output(wait=True); display(HTML(f"<p style='color:red;'>Error: Archivo CSV '{file_name_from_input_proc_imp}' no encontrado en /content/.</p>")); return
    
    _reset_import_session_data(file_name_from_input_proc_imp)
    _configure_global_registro_output_for_session(registro_output)
    _import_session_data['import_escuelas_selected'] = cb_institutions_ui.value
    _import_session_data['import_grupos_selected'] = cb_grupos_ui.value
    _import_session_data['import_miembros_selected'] = cb_miembros_ui.value
    _import_session_data['import_defs_preguntas_selected'] = cb_defs_preguntas_ui.value
    _import_session_data['add_new_questions_only_selected'] = cb_add_new_questions_only_ui.value
    _import_session_data['import_respuestas_selected'] = cb_respuestas_ui.value
    _import_session_data['prefill_mentioned_members_if_resp_selected'] = cb_prefill_mentioned_ui.value
    _import_session_data['default_allow_self_for_new_questions'] = allow_self_default_widget.value
    _import_session_data['csv_excess_response_handling_mode'] = csv_excess_resp_mode_widget_ui.value
    
    # _log_proceso_interno(f"--- INICIO IMPORTACIÓN CSV (v2.5 - Atómico): {file_name_from_input_proc_imp} ---")
    # _log_proceso_interno(f"Opciones: Inst={cb_institutions_ui.value}, Grp={cb_grupos_ui.value}, Miem={cb_miembros_ui.value}, DefP={cb_defs_preguntas_ui.value}, AddOnly={cb_add_new_questions_only_ui.value}, Resp={cb_respuestas_ui.value}, Prefill={cb_prefill_mentioned_ui.value}")

    # 4. Leer y parsear el archivo CSV
    try:
        with open(file_path_to_process_proc_imp, 'r', encoding='utf-8-sig') as f_csv_proc_imp:
            _import_session_data['csv_data_list'] = list(csv.DictReader(f_csv_proc_imp))
        if not _import_session_data['csv_data_list']:
            _add_error_detalle(f"El archivo CSV '{file_name_from_input_proc_imp}' está vacío o tiene un formato no legible.");
            _display_import_summary_static(ui_main_institutions_dict_ref, app_state, institution_refresh_func_ref, registro_output); return
        _import_session_data['contadores']['filas_leidas_csv'] = len(_import_session_data['csv_data_list'])
        headers_csv_proc_imp = list(_import_session_data['csv_data_list'][0].keys())
        
        if _import_session_data['import_miembros_selected'] or _import_session_data['import_respuestas_selected']:
            if not all(col in headers_csv_proc_imp for col in ESSENTIAL_NOMINATOR_COLS_IF_MEMBERS_OR_RESP):
                missing_cols_ess_proc_imp = ", ".join([c for c in ESSENTIAL_NOMINATOR_COLS_IF_MEMBERS_OR_RESP if c not in headers_csv_proc_imp]);
                _add_error_detalle(f"Faltan columnas esenciales (Institucion, Grupo, Nombre y Apellido, Sexo, Fecha De Nacimiento): {missing_cols_ess_proc_imp}.");
                _display_import_summary_static(ui_main_institutions_dict_ref, app_state, institution_refresh_func_ref, registro_output); return
        
        if _import_session_data.get('import_defs_preguntas_selected', False) or _import_session_data.get('import_respuestas_selected', False):
            last_id_col_idx_proc_imp = -1
            for col_id_try_imp in reversed(NOMINATOR_ID_COLS_ORDERED):
                if col_id_try_imp in headers_csv_proc_imp: last_id_col_idx_proc_imp = headers_csv_proc_imp.index(col_id_try_imp); break
            if last_id_col_idx_proc_imp == -1:
                 _add_error_detalle(f"No se pudo determinar la última columna de ID del nominador. Encabezados CSV: {headers_csv_proc_imp[:10]}...");
                 _display_import_summary_static(ui_main_institutions_dict_ref, app_state, institution_refresh_func_ref, registro_output); return
            question_cols_headers_from_csv_proc_imp = headers_csv_proc_imp[last_id_col_idx_proc_imp + 1:]
            header_parser_regex_proc_imp = re.compile(r"^(.*?)\s*\[(?:Opcion|Opción|Eleccion|Elección|Opc|E|N|Num\.?|#|Pilihan|Choice|Selection)\s*(\d+)\s*\]$", re.IGNORECASE)
            _import_session_data['parsed_questions_from_csv_headers'].clear()
            for q_col_header_str_parse_proc_imp in question_cols_headers_from_csv_proc_imp:
                match_q_parse_proc_imp = header_parser_regex_proc_imp.match(q_col_header_str_parse_proc_imp)
                if match_q_parse_proc_imp: _import_session_data['parsed_questions_from_csv_headers'][match_q_parse_proc_imp.group(1).strip()].append( {'col_header': q_col_header_str_parse_proc_imp, 'option_num': int(match_q_parse_proc_imp.group(2))} )
            if not _import_session_data['parsed_questions_from_csv_headers'] and _import_session_data['import_respuestas_selected']:
                _add_advertencia_detalle("No se parsearon encabezados de preguntas. No se importarán defs. ni respuestas.");
                _import_session_data['contadores']['skip_respuestas_por_errores_previos'] = True
    except Exception as e_parse_csv_final:
        _add_error_detalle(f"Error crítico durante lectura/parseo inicial del CSV: {e_parse_csv_final}");
        # _log_proceso_interno(f"Traceback del error de parseo CSV: {traceback.format_exc(limit=2)}")
        _display_import_summary_static(ui_main_institutions_dict_ref, app_state, institution_refresh_func_ref, registro_output); return
    
    # 5. VALIDACIÓN GUARDIÁN
    if _import_session_data.get('import_respuestas_selected', False) and not _import_session_data.get('import_defs_preguntas_selected', False):
        # _log_proceso_interno("VALIDACIÓN GUARDIÁN: Verificando compatibilidad de preguntas...")
        grupos_en_csv = set((str(r.get("Institucion", "")).strip(), str(r.get("Grupo", "")).strip()) for r in _import_session_data['csv_data_list'] if r.get("Institucion") and r.get("Grupo"))
        for inst_destino_val, grp_destino_val in grupos_en_csv:
            if not (inst_destino_val in sociograma_data.schools_data and any(c.get('name') == grp_destino_val for c in sociograma_data.classes_data.get(inst_destino_val, []))):
                continue
            defs_existentes = sociograma_data.get_class_question_definitions(inst_destino_val, grp_destino_val)
            if not defs_existentes:
                _import_session_data['force_create_defs_for_empty_group'] = True; continue
            data_keys_existentes_set = {q_def.get('data_key', q_id) for q_id, q_def in defs_existentes.items()}
            data_keys_csv_set = {generar_data_key_desde_texto(p) for p in _import_session_data['parsed_questions_from_csv_headers']}
            if data_keys_csv_set != data_keys_existentes_set:
                _add_error_detalle(f"ERROR DE INCOMPATIBILIDAD: Las preguntas en el CSV no coinciden con las del grupo de destino ('{grp_destino_val}'), que ya tiene un cuestionario definido. La importación ha sido CANCELADA. Para continuar, asegúrese de que el CSV tenga las mismas preguntas que el grupo, o active la opción para 'Importar/Crear Defs. Preguntas'.")
                _display_import_summary_static(ui_main_institutions_dict_ref, app_state, institution_refresh_func_ref, registro_output)
                return
    
    # 6. Flujo final
    _import_session_data['questions_needing_polarity_confirm'].clear()
    will_create_new_questions = False
    if _import_session_data.get('import_defs_preguntas_selected', False) or _import_session_data.get('force_create_defs_for_empty_group', False):
        grupos_en_csv = set((str(r.get("Institucion", "")).strip(), str(r.get("Grupo", "")).strip()) for r in _import_session_data['csv_data_list'] if r.get("Institucion") and r.get("Grupo"))
        data_keys_csv_set = {generar_data_key_desde_texto(p) for p in _import_session_data['parsed_questions_from_csv_headers']}
        for inst_destino_val, grp_destino_val in grupos_en_csv:
            if not (inst_destino_val in sociograma_data.schools_data and any(c.get('name') == grp_destino_val for c in sociograma_data.classes_data.get(inst_destino_val, []))):
                if _import_session_data.get('import_grupos_selected', False): will_create_new_questions = True; break
                else: continue
            defs_existentes = sociograma_data.get_class_question_definitions(inst_destino_val, grp_destino_val)
            data_keys_existentes_set = {q_def.get('data_key', q_id) for q_id, q_def in defs_existentes.items()}
            if not data_keys_csv_set.issubset(data_keys_existentes_set): will_create_new_questions = True; break
    
    if will_create_new_questions:
        for preg_base_csv in _import_session_data['parsed_questions_from_csv_headers']:
            data_key_csv = generar_data_key_desde_texto(preg_base_csv)
            _import_session_data['questions_needing_polarity_confirm'][preg_base_csv] = {'data_key': data_key_csv, 'tipo_propuesto': preg_base_csv[:30]}
        first_valid_group = next((g for g in grupos_en_csv if g[0] and g[1]), None)
        if first_valid_group:
            _import_session_data['escuela_ref_for_polarity_confirm'] = first_valid_group[0]
            _import_session_data['grupo_ref_for_polarity_confirm'] = first_valid_group[1]

    if will_create_new_questions and _import_session_data['questions_needing_polarity_confirm']:
        # _log_proceso_interno("PASO FINAL: Se detectaron preguntas nuevas. Mostrando UI para confirmación de polaridad...")
        _display_polarity_confirmation_ui_static(
            ui_main_institutions_dict_ref_dp=ui_main_institutions_dict_ref,
            callback_finalize_import_dp=_finalize_import_stages,
            app_state_dp=app_state,
            institution_refresh_func_dp=institution_refresh_func_ref,
            registro_output_dp=registro_output
        )
    else:
        # _log_proceso_interno("PASO FINAL: No se crearán preguntas nuevas. Procediendo directamente a finalizar etapas.")
        _finalize_import_stages(
            {},
            ui_main_institutions_dict_ref_ff=ui_main_institutions_dict_ref,
            app_state_ref_ff=app_state,
            institution_refresh_func_ref_ff=institution_refresh_func_ref,
            registro_output_ref_ff=registro_output
        )
# --- FIN BLOQUE 6 ---
# --- BLOQUE 7: HANDLERS PARA BOTONES DE EXPORTACIÓN / INSTRUCCIONES ---

def on_csv_instructions_pdf_button_click_handler(b, app_state, registro_output):
    """
    Llama a la función en pdf_generator para generar y ofrecer la descarga
    del PDF con las instrucciones completas del programa.
    """
    # version_log_instr_csv = "v1.12.1 Manual Completo"
    # if registro_output and isinstance(registro_output, widgets.Output):
      # with registro_output:
        # print(f"\nHANDLER (csv_excel {version_log_instr_csv}): Solicitando PDF del Manual de Usuario Completo...")

    if hasattr(pdf_generator, 'generate_complete_instructions_pdf'):
        try:
            pdf_generator.generate_complete_instructions_pdf(registro_output)
            # if registro_output and isinstance(registro_output, widgets.Output):
                # with registro_output: print("  -> PDF del Manual de Usuario generado por pdf_generator.")
        except Exception as e_instr_pdf_call_csv:
            if registro_output and isinstance(registro_output, widgets.Output):
                with registro_output:
                    print(f"  ERROR al llamar a generate_complete_instructions_pdf: {e_instr_pdf_call_csv}")
                    print(traceback.format_exc(limit=1))
    else:
        if registro_output and isinstance(registro_output, widgets.Output):
            with registro_output:
                print("  ERROR CRÍTICO: 'generate_complete_instructions_pdf' no está disponible en el módulo pdf_generator.")

def on_csv_prepare_export_institutions_click_handler(b, app_state, ui_main_institutions_ref, registro_output):
    # version_log_prep_inst = "1.9.x Sexo, Inst/Grp, Miembro"
    # if registro_output:
        # with registro_output:
            # print(f"\n--- HANDLER CSV EXPORT (v{version_log_prep_inst}): on_csv_prepare_export_institutions_click_handler ---")

    if not isinstance(ui_main_institutions_ref, dict):
        if registro_output:
          with registro_output: print("  ERROR (prepare_export_institutions): ui_main_institutions_ref no es dict."); return

    institutions_checkboxes_vbox = ui_main_institutions_ref.get("csv_export_schools_checkboxes_vbox")
    load_groups_button = ui_main_institutions_ref.get("csv_load_groups_for_export_button")
    groups_checkboxes_vbox = ui_main_institutions_ref.get("csv_export_groups_checkboxes_vbox")
    export_selected_groups_button = ui_main_institutions_ref.get("csv_export_selected_button")
    export_status_output_csv_exp = ui_main_institutions_ref.get("csv_export_status_output")

    if not all([institutions_checkboxes_vbox, load_groups_button, groups_checkboxes_vbox, export_selected_groups_button, export_status_output_csv_exp]):
        if registro_output:
          with registro_output: print("  ERROR (prepare_export_institutions): Uno o más Widgets de UI de exportación no encontrados."); return

    if hasattr(export_status_output_csv_exp, 'clear_output'):
        with export_status_output_csv_exp: clear_output()

    groups_checkboxes_vbox.children = []
    groups_checkboxes_vbox.layout.display = 'none'
    export_selected_groups_button.disabled = True
    export_selected_groups_button.layout.display = 'none'

    if not sociograma_data.schools_data:
        # if registro_output:
            # with registro_output: print(f"  INFO: No hay instituciones en el sistema para exportar.")
        institutions_checkboxes_vbox.children = (widgets.Label("No hay instituciones en el sistema para exportar."),)
        load_groups_button.disabled = True
        load_groups_button.layout.display = 'none'
    else:
        # if registro_output:
            # with registro_output: print(f"  INFO: Hay {len(sociograma_data.schools_data)} instituciones para seleccionar.")
        temp_institution_cbs_ui = []
        ui_main_institutions_ref['_internal_temp_export_school_checkboxes'] = []
        sorted_institution_names = sorted(list(sociograma_data.schools_data.keys()))
        for institution_name_cb in sorted_institution_names:
            cb_inst = Checkbox(value=False, description=institution_name_cb, indent=False, layout=Layout(width='98%'))
            temp_institution_cbs_ui.append(cb_inst)
            ui_main_institutions_ref['_internal_temp_export_school_checkboxes'].append({'widget': cb_inst, 'school_name': institution_name_cb})

        institutions_checkboxes_vbox.children = tuple(temp_institution_cbs_ui)
        load_groups_button.disabled = False
        load_groups_button.layout.display = 'inline-block'

    institutions_checkboxes_vbox.layout.display = 'block'
    # if registro_output:
        # with registro_output:
            # print(f"  INFO: Lista de {len(ui_main_institutions_ref.get('_internal_temp_export_school_checkboxes',[]))} instituciones mostrada para selección.")
            # print(f"--- FIN HANDLER CSV EXPORT (v{version_log_prep_inst}) ---")

def on_csv_load_groups_for_export_click_handler(b, app_state, ui_main_institutions_ref, registro_output):
    # version_log_load_grp_csv = "1.9.x Sexo, Inst/Grp, Miembro"
    # if registro_output:
        # with registro_output:
            # print(f"\nHANDLER (csv_excel v{version_log_load_grp_csv}): Cargando grupos de instituciones seleccionadas...")

    if not isinstance(ui_main_institutions_ref, dict):
        if registro_output:
          with registro_output: print("  ERROR (load_groups_export): ui_main_institutions_ref no es dict."); return

    groups_checkboxes_vbox_load = ui_main_institutions_ref.get("csv_export_groups_checkboxes_vbox")
    export_selected_groups_button_load = ui_main_institutions_ref.get("csv_export_selected_button")
    export_status_output_load = ui_main_institutions_ref.get("csv_export_status_output")
    institution_checkboxes_info_load = ui_main_institutions_ref.get('_internal_temp_export_school_checkboxes', [])

    if not all([groups_checkboxes_vbox_load, export_selected_groups_button_load, export_status_output_load]):
        if registro_output:
          with registro_output: print("  ERROR (load_groups_export): Widgets de UI de exportación de grupos no encontrados."); return

    if hasattr(export_status_output_load, 'clear_output'):
        with export_status_output_load: clear_output()
    
    selected_institutions_for_groups = []
    for cb_info_institution in institution_checkboxes_info_load:
        if cb_info_institution.get('widget') and cb_info_institution['widget'].value:
            selected_institutions_for_groups.append(cb_info_institution['school_name'])

    if not selected_institutions_for_groups:
        groups_checkboxes_vbox_load.children = (widgets.Label("Por favor, seleccione al menos una institución primero."),)
        groups_checkboxes_vbox_load.layout.display = 'block'
        export_selected_groups_button_load.disabled = True
        export_selected_groups_button_load.layout.display = 'none'
        # if registro_output:
          # with registro_output: print("  Ninguna institución seleccionada para cargar grupos."); 
        return

    temp_group_cbs_ui_load = []
    ui_main_institutions_ref['_internal_temp_export_group_checkboxes'] = []
    any_group_found_load = False

    for institution_name_grp_load in sorted(selected_institutions_for_groups):
        groups_in_institution_load = sociograma_data.classes_data.get(institution_name_grp_load, [])
        if groups_in_institution_load:
            temp_group_cbs_ui_load.append(widgets.HTML(f"<div style='font-weight:bold; margin-top:7px; margin-bottom:3px;'>Grupos en {institution_name_grp_load}:</div>"))
            sorted_groups_load = sorted(groups_in_institution_load, key=lambda c: c.get('name', ''))
            for group_info_load in sorted_groups_load:
                group_name_load = group_info_load.get('name')
                if group_name_load:
                    any_group_found_load = True
                    cb_group_load = Checkbox(value=True, description=group_name_load, indent=False, layout=Layout(margin_left='20px', width='95%'))
                    temp_group_cbs_ui_load.append(cb_group_load)
                    ui_main_institutions_ref['_internal_temp_export_group_checkboxes'].append({
                        'widget': cb_group_load,
                        'school_name': institution_name_grp_load,
                        'group_name': group_name_load
                    })
        else:
            temp_group_cbs_ui_load.append(widgets.Label(f"No hay grupos definidos para la institución {institution_name_grp_load}."))

    if not any_group_found_load and not selected_institutions_for_groups:
         groups_checkboxes_vbox_load.children = (widgets.Label("Seleccione instituciones primero para cargar sus grupos."),)
    elif not any_group_found_load and selected_institutions_for_groups:
        groups_checkboxes_vbox_load.children = (widgets.Label("No se encontraron grupos en las instituciones seleccionadas."),)
        export_selected_groups_button_load.disabled = True
        export_selected_groups_button_load.layout.display = 'none'
    else:
        groups_checkboxes_vbox_load.children = tuple(temp_group_cbs_ui_load)
        export_selected_groups_button_load.disabled = False
        export_selected_groups_button_load.layout.display = 'inline-block'
        
    groups_checkboxes_vbox_load.layout.display = 'block'
    # if registro_output:
        # with registro_output: print(f"  Lista de grupos para instituciones seleccionadas mostrada.")


def on_csv_export_selected_groups_click_handler(b, app_state, ui_main_institutions_ref, registro_output):
    global _import_session_data
    if not _import_session_data or 'log_proceso' not in _import_session_data:
        _reset_import_session_data(file_name="ExportacionSelectivaGrupos")
        if not _import_session_data.get('global_registro_output_ref') and registro_output:
            _configure_global_registro_output_for_session(registro_output)
        # _log_proceso_interno("INFO: _import_session_data reinicializado para exportación de grupos.")
            
    # version_log_export_grp_csv = "1.9.x Sexo, Inst/Grp, Miembro"
    # if registro_output:
        # with registro_output:
            # print(f"\nHANDLER (csv_excel v{version_log_export_grp_csv}): Iniciando exportación de GRUPOS seleccionados a CSV...")

    if not isinstance(ui_main_institutions_ref, dict):
        if registro_output:
          with registro_output: print("  ERROR (export_selected_groups): ui_main_institutions_ref no es dict."); return
    export_status_output_sel_grp = ui_main_institutions_ref.get("csv_export_status_output")
    if hasattr(export_status_output_sel_grp, 'clear_output'):
      with export_status_output_sel_grp: clear_output()
    # else:
        # if registro_output: print("ADVERTENCIA (export_selected_groups): csv_export_status_output no es Output.")

    selected_groups_to_export_tuples_exp = []
    temp_checkboxes_info_groups_exp = ui_main_institutions_ref.get('_internal_temp_export_group_checkboxes', [])
    if not temp_checkboxes_info_groups_exp:
        if export_status_output_sel_grp:
          with export_status_output_sel_grp: display(HTML("<p style='color:orange;'>Error: No hay lista de grupos. Clic en 'Cargar Grupos...' primero.</p>"))
        if registro_output:
          with registro_output: print("  ERROR (export_selected_groups): No hay lista de checkboxes de grupos."); return

    for cb_info_group_exp in temp_checkboxes_info_groups_exp:
        if cb_info_group_exp.get('widget') and cb_info_group_exp['widget'].value:
            selected_groups_to_export_tuples_exp.append((cb_info_group_exp['school_name'], cb_info_group_exp['group_name']))

    if not selected_groups_to_export_tuples_exp:
        if export_status_output_sel_grp:
          with export_status_output_sel_grp: display(HTML("<p style='color:orange;'>Ningún grupo seleccionado para exportar.</p>"))
        # if registro_output:
          # with registro_output: print("  INFO (export_selected_groups): Ningún grupo seleccionado."); 
        return

    # if registro_output:
        # with registro_output: print(f"  Grupos seleccionados para exportar (institución, grupo): {selected_groups_to_export_tuples_exp}")

    all_rows_for_csv_export_grp_exp = []
    max_selections_per_data_key_sel_grp_exp = collections.defaultdict(int)
    question_text_map_sel_grp_exp = {}

    for institution_name_for_defs_grp, group_name_for_defs_grp in selected_groups_to_export_tuples_exp:
        group_q_defs_sel_grp_exp = sociograma_data.get_class_question_definitions(institution_name_for_defs_grp, group_name_for_defs_grp)
        for data_key_grp_exp, q_def_grp_exp in group_q_defs_sel_grp_exp.items():
            max_selections_per_data_key_sel_grp_exp[data_key_grp_exp] = max(max_selections_per_data_key_sel_grp_exp[data_key_grp_exp], q_def_grp_exp.get('max_selections', 0))
            if data_key_grp_exp not in question_text_map_sel_grp_exp:
                texto_original_pregunta_exp = q_def_grp_exp.get('text', data_key_grp_exp)
                texto_limpio_pregunta_exp = re.sub(r'\s*\(\s*máx\.\s*\d+\s*\)\s*$', '', texto_original_pregunta_exp, flags=re.IGNORECASE).strip()
                question_text_map_sel_grp_exp[data_key_grp_exp] = texto_limpio_pregunta_exp

    sorted_unique_data_keys_sel_grp_exp = sorted(list(max_selections_per_data_key_sel_grp_exp.keys()))
    question_headers_for_csv_sel_grp_exp = []
    for data_key_sel_grp_exp_h in sorted_unique_data_keys_sel_grp_exp:
        texto_pregunta_base_sel_grp_exp = question_text_map_sel_grp_exp.get(data_key_sel_grp_exp_h, data_key_sel_grp_exp_h.replace("q_", "").replace("_", " ").title())
        max_sel_para_este_dk_sel_grp_exp = max_selections_per_data_key_sel_grp_exp[data_key_sel_grp_exp_h]
        for i_sel_grp_exp in range(1, max_sel_para_este_dk_sel_grp_exp + 1):
            question_headers_for_csv_sel_grp_exp.append(f"{texto_pregunta_base_sel_grp_exp} [Opcion {i_sel_grp_exp}]")
            
    base_headers_sel_grp_exp = NOMINATOR_ID_COLS_ORDERED[:]
    full_csv_headers_sel_grp_exp = base_headers_sel_grp_exp + question_headers_for_csv_sel_grp_exp
    all_rows_for_csv_export_grp_exp.append(full_csv_headers_sel_grp_exp)

    for institution_name_exp_final_grp, group_name_exp_final_grp in selected_groups_to_export_tuples_exp:
        members_in_group_exp_final_grp = sociograma_data.members_data.get(institution_name_exp_final_grp, {}).get(group_name_exp_final_grp, [])
        for member_data_exp_final_grp_item in members_in_group_exp_final_grp:
            nombre_exp_final_titulo_grp_item = member_data_exp_final_grp_item.get('nome', '').strip().title()
            apellido_exp_final_titulo_grp_item = member_data_exp_final_grp_item.get('cognome', '').strip().title()
            nombre_completo_csv_export_final_grp_item = f"{nombre_exp_final_titulo_grp_item} {apellido_exp_final_titulo_grp_item}".strip()
            
            row_data_export_grp_item = collections.OrderedDict()
            row_data_export_grp_item["Marca temporal"] = ""
            row_data_export_grp_item["Dirección de correo electrónico"] = ""
            row_data_export_grp_item["Institucion"] = institution_name_exp_final_grp
            row_data_export_grp_item["Grupo"] = group_name_exp_final_grp
            row_data_export_grp_item["Nombre y Apellido"] = nombre_completo_csv_export_final_grp_item
            row_data_export_grp_item["Sexo"] = member_data_exp_final_grp_item.get('sexo', 'Desconocido')
            row_data_export_grp_item["Fecha De Nacimiento"] = member_data_exp_final_grp_item.get('fecha_nac', '')

            member_responses_export_grp_item = sociograma_data.questionnaire_responses_data.get(
                (institution_name_exp_final_grp, group_name_exp_final_grp, nombre_completo_csv_export_final_grp_item), {}
            )

            for data_key_q_exp_sel_final_grp_item in sorted_unique_data_keys_sel_grp_exp:
                texto_base_q_exp_sel_final_grp_item = question_text_map_sel_grp_exp.get(data_key_q_exp_sel_final_grp_item, data_key_q_exp_sel_final_grp_item)
                max_sel_global_q_exp_sel_final_grp_item = max_selections_per_data_key_sel_grp_exp.get(data_key_q_exp_sel_final_grp_item, 0)
                respuestas_para_esta_pregunta_sel_final_grp_item = member_responses_export_grp_item.get(data_key_q_exp_sel_final_grp_item, [])
                
                for i_resp_col_sel_final_grp_item in range(1, max_sel_global_q_exp_sel_final_grp_item + 1):
                    col_header_resp_sel_final_grp_item = f"{texto_base_q_exp_sel_final_grp_item} [Opcion {i_resp_col_sel_final_grp_item}]"
                    if i_resp_col_sel_final_grp_item <= len(respuestas_para_esta_pregunta_sel_final_grp_item):
                        row_data_export_grp_item[col_header_resp_sel_final_grp_item] = respuestas_para_esta_pregunta_sel_final_grp_item[i_resp_col_sel_final_grp_item - 1]
                    else:
                        row_data_export_grp_item[col_header_resp_sel_final_grp_item] = ""
            all_rows_for_csv_export_grp_exp.append([row_data_export_grp_item.get(h, "") for h in full_csv_headers_sel_grp_exp])

    if len(all_rows_for_csv_export_grp_exp) <= 1:
        msg_no_datos_export_grp_fin = "<p style='color:orange;'>No se encontraron datos de miembros con respuestas para los grupos seleccionados.</p>"
        if export_status_output_sel_grp:
          with export_status_output_sel_grp: display(HTML(msg_no_datos_export_grp_fin))
        if registro_output:
          with registro_output: print("  No hay datos para exportar para los grupos seleccionados.");
        return

    try:
        csv_buffer_sel_export_grp_f = io.StringIO()
        writer_sel_export_grp_f = csv.writer(csv_buffer_sel_export_grp_f, quoting=csv.QUOTE_ALL)
        writer_sel_export_grp_f.writerows(all_rows_for_csv_export_grp_exp)
        csv_content_sel_export_grp_f = csv_buffer_sel_export_grp_f.getvalue()
        csv_buffer_sel_export_grp_f.close()
        b64_csv_sel_export_grp_f = base64.b64encode(csv_content_sel_export_grp_f.encode('utf-8')).decode('utf-8')
        export_filename_final_grp_f = f"sociograma_export_grupos_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        link_html_final_export_grp_f = f'<p style="text-align:center; margin-top:10px;"><a download="{export_filename_final_grp_f}" href="data:text/csv;charset=utf-8;base64,{b64_csv_sel_export_grp_f}" target="_blank" style="padding:8px 15px; background-color:#007bff; color:white; text-decoration:none; border-radius:5px; font-weight:bold;">Descargar CSV de Grupo(s): {export_filename_final_grp_f}</a></p>'
        if export_status_output_sel_grp:
          with export_status_output_sel_grp: display(HTML(link_html_final_export_grp_f))
        # if registro_output:
            # with registro_output: print(f"  ÉXITO: Archivo CSV '{export_filename_final_grp_f}' listo para descargar.")
        # _log_proceso_interno(f"Exportación CSV selectiva (por grupos) generada: {export_filename_final_grp_f}")
    except Exception as e_export_sel_final_grp_f:
        err_msg_export_sel_final_grp_f = f"ERROR CRÍTICO durante la exportación CSV selectiva por grupos: {e_export_sel_final_grp_f}\n{traceback.format_exc()}"
        if export_status_output_sel_grp:
          with export_status_output_sel_grp: display(HTML(f"<p style='color:red;'>{err_msg_export_sel_final_grp_f}</p>"))
        if registro_output:
          with registro_output: print(err_msg_export_sel_final_grp_f)
        if 'csv_buffer_sel_export_grp_f' in locals() and hasattr(csv_buffer_sel_export_grp_f, 'closed') and not csv_buffer_sel_export_grp_f.closed:
            csv_buffer_sel_export_grp_f.close()
# --- FIN BLOQUE 7 ---