# handlers_questionnaire.py
# (v15.0 - Usa "Institución"/"Grupo" y "Miembro" en logs y títulos.
#          Formato de nombre "Nombre Apellido" Título en contexto y logs.)

# --- Importaciones ---
import collections
from ipywidgets import widgets, Output
from IPython.display import clear_output, display, HTML
import functools
import sys
import traceback

# Módulos de datos y el generador de PDF
from sociograma_data import (
    questionnaire_responses_data,
    get_class_question_definitions,
    regenerate_relationship_maps_for_class
)
import pdf_generator

# Utilidades
try:
    from handlers_utils import get_member_options_for_dropdown
except ImportError:
    print("ERROR CRÍTICO (handlers_questionnaire v15.0): No se pudo importar get_member_options_for_dropdown.")
    def get_member_options_for_dropdown(*args, **kwargs):
        ro_fb_hq_pop_util = kwargs.get('registro_output_fallback')
        if ro_fb_hq_pop_util and isinstance(ro_fb_hq_pop_util, Output):
            with ro_fb_hq_pop_util: print("Fallback get_member_options_for_dropdown (hquest) llamado.")
        return [('Error al cargar opciones (fallback)', None)]


# --- Funciones Helper Internas ---

def _populate_questionnaire_dropdowns(app_state, ui_form_questionnaire, registro_output, app_data_ref):
    if not registro_output: registro_output = Output()

    # with registro_output:
        # print(f"DEBUG (_populate_q_dd v15.0): Iniciando _populate_questionnaire_dropdowns.")

    context_q_dd = app_state.get('current_questionnaire_member_context')
    if not context_q_dd or not isinstance(context_q_dd, dict) or \
       not all(k in context_q_dd for k in ['school', 'class_name', 'member']):
        with registro_output: print("  ERROR (_populate_q_dd): Contexto de miembro inválido o incompleto."); return

    institution_name_q_dd = context_q_dd['school']
    group_name_q_dd = context_q_dd['class_name']
    current_member_name_key_q_dd = context_q_dd['member']

    # with registro_output:
        # print(f"  _populate_q_dd: Contexto - Institución: '{institution_name_q_dd}', Grupo: '{group_name_q_dd}', Miembro: '{current_member_name_key_q_dd}'")

    if not isinstance(ui_form_questionnaire, dict):
        with registro_output: print("  ERROR (_populate_q_dd): ui_form_questionnaire no es un diccionario."); return

    current_group_defs_q_dd = get_class_question_definitions(institution_name_q_dd, group_name_q_dd)
    # if not current_group_defs_q_dd:
        # with registro_output: print(f"  INFO (_populate_q_dd): No hay definiciones de preguntas para {institution_name_q_dd}/{group_name_q_dd}."); return
    # with registro_output: print(f"  _populate_q_dd: {len(current_group_defs_q_dd)} Definiciones de preguntas cargadas.")

    if not app_data_ref or not hasattr(app_data_ref, 'members_data') or not isinstance(app_data_ref.members_data, dict):
        with registro_output: print(f"  CRITICAL_ERROR (_populate_q_dd): app_data_ref no válido o sin 'members_data'."); return

    data_key_member_lookup_q_dd = (institution_name_q_dd, group_name_q_dd, current_member_name_key_q_dd)
    saved_responses_for_member_q_dd = questionnaire_responses_data.get(data_key_member_lookup_q_dd, {})
    # with registro_output:
        # print(f"  _populate_q_dd: Buscando respuestas guardadas con clave: {data_key_member_lookup_q_dd}")

    sorted_q_items_populate = []
    if isinstance(current_group_defs_q_dd, collections.OrderedDict) and current_group_defs_q_dd:
        try: sorted_q_items_populate = sorted(current_group_defs_q_dd.items(), key=lambda item: (item[1].get('order', 99), item[0]))
        except Exception as e_sort_populate_q_dd:
            with registro_output: print(f"  ADVERTENCIA (_populate_q_dd): Error al ordenar preguntas: {e_sort_populate_q_dd}.");
            sorted_q_items_populate = list(current_group_defs_q_dd.items())

    for q_id_in_def_pop, q_def_pop in sorted_q_items_populate:
        data_key_q_pop = q_def_pop.get('data_key', q_id_in_def_pop)
        max_selections_q_pop = q_def_pop.get('max_selections', 0)
        allow_self_q_pop = q_def_pop.get('allow_self_selection', False)
        exclude_name_for_options_q_pop = current_member_name_key_q_dd if not allow_self_q_pop else None

        member_options_for_this_q_pop = []
        try:
            member_options_for_this_q_pop = get_member_options_for_dropdown(
                school_name=institution_name_q_dd,
                class_name=group_name_q_dd,
                order_by='Apellido',
                exclude_member_display_name=exclude_name_for_options_q_pop,
                app_data_ref=app_data_ref,
                registro_output_fallback=registro_output
            )
        except Exception as e_get_opts_populate_dd:
             with registro_output: print(f"    _populate_q_dd: EXCEPCIÓN en get_member_options_for_dropdown para '{data_key_q_pop}'. Error: {e_get_opts_populate_dd}");
             member_options_for_this_q_pop = [('Error opciones', None)]

        valid_option_values_for_this_q_pop = [opt_val for opt_label, opt_val in member_options_for_this_q_pop if opt_val is not None]
        num_elegibles_esperado_pop = len(valid_option_values_for_this_q_pop)
        if num_elegibles_esperado_pop < max_selections_q_pop and max_selections_q_pop > 0:
            with registro_output:
                message_warn_pop = f"  ADVERTENCIA (_populate_q_dd): Pregunta '{data_key_q_pop}', hay {num_elegibles_esperado_pop} elegible(s)"
                if exclude_name_for_options_q_pop: message_warn_pop += f" (excl. '{current_member_name_key_q_dd}')."
                else: message_warn_pop += "."
                message_warn_pop += f" Menor que max_selections ({max_selections_q_pop})."
                print(message_warn_pop)

        saved_q_responses_list_pop = saved_responses_for_member_q_dd.get(data_key_q_pop, [])
        if max_selections_q_pop == 0: continue

        for i_pop in range(max_selections_q_pop):
            dd_widget_key_pop = f"{data_key_q_pop}_dd{i_pop+1}"
            dropdown_widget_pop = ui_form_questionnaire.get(dd_widget_key_pop)

            if dropdown_widget_pop and hasattr(dropdown_widget_pop, 'options'):
                dropdown_widget_pop.options = member_options_for_this_q_pop
                saved_value_for_this_dd_pop = saved_q_responses_list_pop[i_pop] if i_pop < len(saved_q_responses_list_pop) else None
                if saved_value_for_this_dd_pop and saved_value_for_this_dd_pop in valid_option_values_for_this_q_pop:
                    try: dropdown_widget_pop.value = saved_value_for_this_dd_pop
                    except Exception as e_set_dd_value_pop:
                        with registro_output: print(f"        _populate_q_dd: ERROR al establecer valor '{saved_value_for_this_dd_pop}' en '{dd_widget_key_pop}': {e_set_dd_value_pop}");
                        dropdown_widget_pop.value = None
                else:
                    dropdown_widget_pop.value = None
            elif max_selections_q_pop > 0 :
                with registro_output: print(f"      _populate_q_dd: ADVERTENCIA - Dropdown '{dd_widget_key_pop}' NO encontrado para pregunta '{data_key_q_pop}'.")

    # with registro_output: print(f"DEBUG (_populate_q_dd v15.0): Finalizado _populate_questionnaire_dropdowns.")


# --- Handlers para Interfaz 7: Formulario Cuestionario ---

def on_q_ok_button_click_handler(b, app_state, ui_form_questionnaire, switch_interface_func, registro_output, ui_members=None, member_refresh_func=None):
    if not registro_output: registro_output = Output()
    with registro_output: 
        clear_output(wait=True)
        # print(f"\n--- HANDLER: on_q_ok_button_click_handler (v15.0 - Inst/Grp/Miembro) ---")
        pass
    
    context_q_ok = app_state.get('current_questionnaire_member_context')
    if not context_q_ok or not all(k in context_q_ok for k in ['school', 'class_name', 'member']):
        with registro_output: print("  ERROR (on_q_ok): Falta contexto de miembro (institución/grupo/nombre)."); return

    institution_name_q_ok = context_q_ok['school']
    group_name_q_ok = context_q_ok['class_name']
    member_name_key_q_ok = context_q_ok['member']
    data_key_member_q_ok = (institution_name_q_ok, group_name_q_ok, member_name_key_q_ok)
    
    all_member_responses_for_data_key_q_ok = {}
    validation_ok_q_ok = True; error_msg_accumulated_q_ok = ""
    if not isinstance(ui_form_questionnaire, dict):
         with registro_output: print("  ERROR (on_q_ok): ui_form_questionnaire no es dict."); return

    current_group_defs_q_ok = get_class_question_definitions(institution_name_q_ok, group_name_q_ok)
    if not current_group_defs_q_ok:
        with registro_output: print(f"  ADVERTENCIA (on_q_ok): No hay defs. de preguntas para {institution_name_q_ok}/{group_name_q_ok}.");
        if data_key_member_q_ok not in questionnaire_responses_data: questionnaire_responses_data[data_key_member_q_ok] = {}
        app_state['current_questionnaire_member_context'] = None; return_interface_q_ok = app_state.get('return_interface', 'main_members')
        if return_interface_q_ok not in ['main_members', 'form_member']: return_interface_q_ok = 'main_members'
        switch_interface_func(return_interface_q_ok); return

    sorted_q_items_ok = []
    if isinstance(current_group_defs_q_ok, collections.OrderedDict) and current_group_defs_q_ok:
        try: sorted_q_items_ok = sorted(current_group_defs_q_ok.items(), key=lambda item: (item[1].get('order', 99),item[0]))
        except Exception as e_sort_q_ok_btn: 
          with registro_output: print(f"  ADVERTENCIA (on_q_ok): Error al ordenar: {e_sort_q_ok_btn}."); sorted_q_items_ok = list(current_group_defs_q_ok.items())

    for q_id_in_def_ok, q_def_ok in sorted_q_items_ok:
        question_data_key_ok = q_def_ok.get('data_key', q_id_in_def_ok); max_selections_ok = q_def_ok.get('max_selections', 0)
        question_text_short_ok = q_def_ok.get('text', q_id_in_def_ok)[:30] + "..."
        current_q_selections_ok = []
        if max_selections_ok > 0:
            for i_ok in range(max_selections_ok):
                dd_widget_key_ok = f"{question_data_key_ok}_dd{i_ok+1}"; dropdown_widget_ok = ui_form_questionnaire.get(dd_widget_key_ok)
                if dropdown_widget_ok and hasattr(dropdown_widget_ok, 'value'):
                    selection_value_ok = dropdown_widget_ok.value
                    if selection_value_ok is not None: current_q_selections_ok.append(selection_value_ok)
                elif registro_output: 
                  with registro_output: print(f"  ADVERTENCIA (on_q_ok): Dropdown '{dd_widget_key_ok}' no encontrado al guardar.")
            counts_ok = collections.Counter(current_q_selections_ok)
            if any(count > 1 for count in counts_ok.values()):
                validation_ok_q_ok = False; first_duplicate_ok = next((item for item, count in counts_ok.items() if count > 1), "desconocido")
                error_msg_accumulated_q_ok += f"Pregunta '{question_text_short_ok}': Selecciones duplicadas ('{first_duplicate_ok}').\n"
        all_member_responses_for_data_key_q_ok[question_data_key_ok] = current_q_selections_ok

    if validation_ok_q_ok:
        if not isinstance(questionnaire_responses_data, collections.OrderedDict):
             globals()['questionnaire_responses_data'] = collections.OrderedDict()
             if registro_output: 
              with registro_output: print("  CRITICAL (on_q_ok): questionnaire_responses_data re-inicializado.")
        questionnaire_responses_data[data_key_member_q_ok] = all_member_responses_for_data_key_q_ok
        # if registro_output: 
          # with registro_output: print(f"  ÉXITO (on_q_ok): Respuestas guardadas para '{member_name_key_q_ok}'.")
        
        app_state['current_questionnaire_member_context'] = None; return_interface_q_ok_final = app_state.get('return_interface', 'main_members')
        if return_interface_q_ok_final not in ['main_members', 'form_member']: return_interface_q_ok_final = 'main_members'
        app_state['return_interface'] = None

        if return_interface_q_ok_final == 'main_members':
            if ui_members and member_refresh_func and callable(member_refresh_func):
                select_widget_mem_q_ok = ui_members.get("select") if isinstance(ui_members, dict) else None
                current_selection_on_return_q_ok = member_name_key_q_ok
                if select_widget_mem_q_ok and hasattr(select_widget_mem_q_ok, 'options'):
                    valid_options_q_ok = [opt[1] for opt in select_widget_mem_q_ok.options if isinstance(opt, tuple) and len(opt)>1 and opt[1] is not None]
                    if current_selection_on_return_q_ok not in valid_options_q_ok: current_selection_on_return_q_ok = valid_options_q_ok[0] if valid_options_q_ok else None
                else: current_selection_on_return_q_ok = None
                if select_widget_mem_q_ok :
                    change_event_data_q_ok = {'name': 'value', 'old': None, 'new': current_selection_on_return_q_ok, 'owner': select_widget_mem_q_ok, 'type': 'change'}
                    try:
                        form_member_vbox_ref_q_ok_call = getattr(ui_members, 'form_member_embedded_vbox_ref', None)
                        member_refresh_func(change_event_data_q_ok, app_state, ui_members, registro_output, form_member_vbox_ref=form_member_vbox_ref_q_ok_call)
                    except Exception as e_refresh_q_ok_call:
                      if registro_output: 
                        with registro_output: print(f"  ERROR (on_q_ok) al refrescar ui_members: {e_refresh_q_ok_call}")
        try: switch_interface_func(return_interface_q_ok_final)
        except Exception as e_switch_q_ok_final:
          if registro_output: 
            with registro_output: print(f"  ERROR (on_q_ok) al cambiar a '{return_interface_q_ok_final}': {e_switch_q_ok_final}\n{traceback.format_exc(limit=1)}")
    else:
        if registro_output: 
          with registro_output: print(f"\n--- ERRORES DE VALIDACIÓN ---\n{error_msg_accumulated_q_ok.strip()}\n----------------------------\nCorrige los errores.");


def on_q_salir_button_click_handler(b, app_state, switch_interface_func, registro_output, ui_members=None, member_refresh_func=None):
    if not registro_output: registro_output = Output()
    with registro_output: 
        clear_output(wait=True)
        # print(f"\n--- HANDLER: on_q_salir_button_click_handler (v15.0 - Inst/Grp/Miembro) ---")
        pass
    
    context_on_exit_q_salir = app_state.get('current_questionnaire_member_context')
    member_name_to_reselect_on_exit_q_salir = None
    if context_on_exit_q_salir and 'member' in context_on_exit_q_salir:
        member_name_to_reselect_on_exit_q_salir = context_on_exit_q_salir['member']

    app_state['current_questionnaire_member_context'] = None; return_interface_q_salir_final = app_state.get('return_interface', 'main_members')
    if return_interface_q_salir_final not in ['main_members', 'form_member']: return_interface_q_salir_final = 'main_members'
    app_state['return_interface'] = None

    if return_interface_q_salir_final == 'main_members':
        if ui_members and member_refresh_func and callable(member_refresh_func):
            select_widget_mem_q_salir = ui_members.get("select") if isinstance(ui_members, dict) else None
            current_selection_to_restore_q_salir = member_name_to_reselect_on_exit_q_salir
            if select_widget_mem_q_salir and hasattr(select_widget_mem_q_salir, 'options'):
                valid_options_q_salir = [opt[1] for opt in select_widget_mem_q_salir.options if isinstance(opt, tuple) and len(opt)>1 and opt[1] is not None]
                if not current_selection_to_restore_q_salir or current_selection_to_restore_q_salir not in valid_options_q_salir:
                    current_selection_to_restore_q_salir = valid_options_q_salir[0] if valid_options_q_salir else None
            if select_widget_mem_q_salir:
                change_event_data_q_salir = {'name': 'value', 'old': select_widget_mem_q_salir.value, 'new': current_selection_to_restore_q_salir, 'owner': select_widget_mem_q_salir, 'type': 'change'}
                if select_widget_mem_q_salir.value != current_selection_to_restore_q_salir :
                     select_widget_mem_q_salir.value = current_selection_to_restore_q_salir
                else:
                    try:
                        form_member_vbox_ref_q_salir_call = getattr(ui_members, 'form_member_embedded_vbox_ref', None)
                        member_refresh_func(change_event_data_q_salir, app_state, ui_members, registro_output, form_member_vbox_ref=form_member_vbox_ref_q_salir_call)
                    except Exception as e_refresh_q_salir_call:
                      if registro_output: 
                        with registro_output: print(f"  ERROR (on_q_salir) al refrescar ui_members: {e_refresh_q_salir_call}")
    try: switch_interface_func(return_interface_q_salir_final)
    except Exception as e_switch_q_salir_final:
      if registro_output: 
        with registro_output: print(f"  ERROR (on_q_salir) al cambiar a '{return_interface_q_salir_final}': {e_switch_q_salir_final}\n{traceback.format_exc(limit=1)}")


def on_q_manage_questions_button_handler(b, app_state, ui_form_questionnaire,
                                         ui_questions_management, switch_interface_func,
                                         registro_output, handlers_questions_ref):
    if not registro_output: registro_output = Output()
    with registro_output: 
        clear_output(wait=True)
        # print(f"\n--- HANDLER: on_q_manage_questions_button_handler (v15.0 - Inst/Grp/Miembro) ---")
        pass
    
    current_q_context_mgmt = app_state.get('current_questionnaire_member_context')
    group_context_for_mgmt_q = None

    if current_q_context_mgmt and 'school' in current_q_context_mgmt and 'class_name' in current_q_context_mgmt:
        institution_name_q_mgmt = current_q_context_mgmt['school']
        group_name_q_mgmt = current_q_context_mgmt['class_name']
        group_context_for_mgmt_q = {'school': institution_name_q_mgmt, 'class_name': group_name_q_mgmt }
        app_state['current_context_for_question_management'] = group_context_for_mgmt_q
        try:
            regenerate_relationship_maps_for_class(institution_name_q_mgmt, group_name_q_mgmt)
            # with registro_output: print(f"  INFO (on_q_manage): Mapas de relación regenerados para {institution_name_q_mgmt}/{group_name_q_mgmt}.")
        except Exception as e_regen_q_mgmt_btn:
          with registro_output: print(f"  ERROR al regenerar mapas en on_q_manage_questions_button_handler: {e_regen_q_mgmt_btn}")
    else:
        app_state['current_context_for_question_management'] = None;
        with registro_output: print("  ERROR (on_q_manage): No se pudo obtener contexto de institución/grupo. No se puede gestionar preguntas."); return

    if not handlers_questions_ref or not hasattr(handlers_questions_ref, '_refresh_questions_list_options'):
        with registro_output: print("  ERROR CRÍTICO (on_q_manage): 'handlers_questions_ref' o su función '_refresh_questions_list_options' no disponibles."); return

    select_widget_q_mgmt_ui = ui_questions_management.get("select") if isinstance(ui_questions_management, dict) else None
    if select_widget_q_mgmt_ui:
        try:
            handlers_questions_ref._refresh_questions_list_options(
                app_state, select_widget_q_mgmt_ui, registro_output,
                preferred_selection_id=None,
                ui_questions_management_ref=ui_questions_management
            )
            newly_selected_id_in_q_mgmt_after_refresh_ui = select_widget_q_mgmt_ui.value
            # with registro_output: print(f"  INFO (on_q_manage): Lista de preguntas en 'questions_management' refrescada. Selección: '{newly_selected_id_in_q_mgmt_after_refresh_ui}'")
        except Exception as e_refresh_q_mgmt_call_btn:
          if registro_output: 
            with registro_output: print(f"  ERROR al llamar a _refresh_questions_list_options: {e_refresh_q_mgmt_call_btn}\n{traceback.format_exc(limit=1)}")
    else:
        if registro_output: 
          with registro_output: print("  ADVERTENCIA (on_q_manage): Widget 'select' no encontrado en ui_questions_management.")
    
    app_state['return_interface'] = 'form_questionnaire'
    switch_interface_func('questions_management')


def on_q_pdf_class_button_click_handler(b, app_state, registro_output):
    if not registro_output: registro_output = Output()
    with registro_output: 
        clear_output(wait=True)
        # print(f"\n--- HANDLER: on_q_pdf_class_button_click_handler (v15.0 - Inst/Grp/Miembro) ---")
        pass
    
    context_q_pdf = app_state.get('current_questionnaire_member_context')
    if not context_q_pdf or not all(k in context_q_pdf for k in ['school', 'class_name']):
        with registro_output: print("  ERROR (PDF Plantilla): Falta contexto institución/grupo."); return
        
    institution_name_q_pdf = context_q_pdf['school']
    group_name_q_pdf = context_q_pdf['class_name']
    
    if hasattr(pdf_generator, 'generate_class_questionnaire_template_pdf'):
        try:
            pdf_generator.generate_class_questionnaire_template_pdf(institution_name_q_pdf, group_name_q_pdf, registro_output=registro_output)
        except Exception as e_pdf_tpl_call:
          with registro_output: print(f"  ERROR (PDF Plantilla) llamando a generar: {e_pdf_tpl_call}\n{traceback.format_exc(limit=1)}")
    else:
      with registro_output: print("  ERROR (PDF Plantilla): Función generate_class_questionnaire_template_pdf no disponible en pdf_generator.");