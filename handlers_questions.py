# handlers_questions.py
# (v18.0 - Usa "Institución"/"Grupo" y "Miembro" en logs y contextos.)

# --- BLOQUE 1: IMPORTACIONES Y FUNCIONES HELPER PRINCIPALES ---

import sys
import collections
from ipywidgets import widgets, Layout
from IPython.display import clear_output, display
import traceback
import functools

from sociograma_data import (
    questionnaire_responses_data,
    regenerate_relationship_maps_for_class,
    get_class_question_definitions,
    members_data
)

_handlers_questionnaire_hq = globals().get('handlers_questionnaire')
_app_ui_hq = globals().get('app_ui')


# --- Funciones Helper Internas ---

def _actualizar_estado_botones_gestion_preguntas(app_state, ui_questions_management, registro_output):
    if not isinstance(ui_questions_management, dict):
        if registro_output and isinstance(registro_output, widgets.Output):
            with registro_output: print("ADVERTENCIA (_actualizar_botones_q_mgmt): ui_questions_management no es dict.")
        return

    modifica_btn_q_mgmt = ui_questions_management.get("modifica_button")
    elimina_btn_q_mgmt = ui_questions_management.get("elimina_button")
    nueva_btn_q_mgmt = ui_questions_management.get("nueva_button")

    pregunta_seleccionada_valida_botones = False
    selected_q_id_for_buttons = app_state.get('current_question_editing_id')
    group_context_for_buttons = app_state.get('current_context_for_question_management')

    if nueva_btn_q_mgmt:
        nueva_btn_q_mgmt.disabled = not bool(group_context_for_buttons and \
                                          isinstance(group_context_for_buttons, dict) and \
                                          group_context_for_buttons.get('school') and \
                                          group_context_for_buttons.get('class_name'))

    if selected_q_id_for_buttons and group_context_for_buttons and \
       isinstance(group_context_for_buttons, dict) and \
       group_context_for_buttons.get('school') and group_context_for_buttons.get('class_name'):
        
        institution_name_ctx_btn = group_context_for_buttons.get('school')
        group_name_ctx_btn = group_context_for_buttons.get('class_name')
        current_group_defs_for_buttons = get_class_question_definitions(institution_name_ctx_btn, group_name_ctx_btn)
        
        if current_group_defs_for_buttons and selected_q_id_for_buttons in current_group_defs_for_buttons:
            pregunta_seleccionada_valida_botones = True

    if modifica_btn_q_mgmt:
        modifica_btn_q_mgmt.disabled = not pregunta_seleccionada_valida_botones
    if elimina_btn_q_mgmt:
        elimina_btn_q_mgmt.disabled = not pregunta_seleccionada_valida_botones

    # if registro_output and isinstance(registro_output, widgets.Output):
        # with registro_output:
            # log_msg_q_mgmt_btns = "  INFO (_actualizar_botones_q_mgmt v18.0 - Inst/Grp/Miembro): "
            # if nueva_btn_q_mgmt: log_msg_q_mgmt_btns += f"Nueva.disabled={nueva_btn_q_mgmt.disabled}, "
            # if modifica_btn_q_mgmt: log_msg_q_mgmt_btns += f"Modificar.disabled={modifica_btn_q_mgmt.disabled}, "
            # if elimina_btn_q_mgmt: log_msg_q_mgmt_btns += f"Eliminar.disabled={elimina_btn_q_mgmt.disabled}"
            # print(log_msg_q_mgmt_btns)


def _refresh_questions_list_options(app_state, questions_select_widget, registro_output, preferred_selection_id=None,
                                    ui_questions_management_ref=None):
    if not isinstance(questions_select_widget, widgets.Select):
        if registro_output and isinstance(registro_output, widgets.Output):
            with registro_output: print("Advertencia (_refresh_q_list): Widget de selección de preguntas no es del tipo Select.")
        return

    options_list_builder_refresh = []
    group_context_list_refresh = app_state.get('current_context_for_question_management')
    has_valid_group_context_refresh = bool(
        group_context_list_refresh and
        isinstance(group_context_list_refresh, dict) and
        group_context_list_refresh.get('school') and
        group_context_list_refresh.get('class_name')
    )

    if has_valid_group_context_refresh:
        institution_name_list_refresh = group_context_list_refresh['school']
        group_name_list_refresh = group_context_list_refresh['class_name']
        current_group_defs_list_refresh = get_class_question_definitions(institution_name_list_refresh, group_name_list_refresh)
        
        # if registro_output and isinstance(registro_output, widgets.Output):
            # with registro_output: print(f"INFO (_refresh_q_list): Cargando preguntas para {institution_name_list_refresh}/{group_name_list_refresh}. {len(current_group_defs_list_refresh) if current_group_defs_list_refresh is not None else 0} defs.")

        if isinstance(current_group_defs_list_refresh, collections.OrderedDict) and current_group_defs_list_refresh:
            try:
                sorted_q_items_list_refresh = sorted(current_group_defs_list_refresh.items(), key=lambda item: (item[1].get('order', 99), item[0]))
                for q_id_list_refresh, q_def_list_refresh in sorted_q_items_list_refresh:
                    polarity_short_list_refresh = 'Pos' if q_def_list_refresh.get('polarity') == 'positive' else 'Neg' if q_def_list_refresh.get('polarity') == 'negative' else '?'
                    max_sel_list_refresh = q_def_list_refresh.get('max_selections', '?')
                    self_sel_list_refresh = "Sí" if q_def_list_refresh.get('allow_self_selection') else "No"
                    label_id_part_list_refresh = f"{q_id_list_refresh}"
                    if q_def_list_refresh.get('data_key') and q_def_list_refresh.get('data_key') != q_id_list_refresh:
                        label_id_part_list_refresh += f" (DK: {q_def_list_refresh.get('data_key')})"
                    label_list_refresh = f"[{q_def_list_refresh.get('order', '?')}] {q_def_list_refresh.get('type', 'N/D')} ({polarity_short_list_refresh}, Máx:{max_sel_list_refresh}, Auto:{self_sel_list_refresh}) - {label_id_part_list_refresh}"
                    options_list_builder_refresh.append((label_list_refresh, q_id_list_refresh))
            except Exception as e_sort_list_refresh:
                if registro_output and isinstance(registro_output, widgets.Output):
                    with registro_output: print(f"ERROR (_refresh_q_list): Al formatear lista de preguntas: {e_sort_list_refresh}")
                options_list_builder_refresh.append(("Error al cargar lista de preguntas", "error_val_list_refresh"))
        # elif registro_output and current_group_defs_list_refresh is not None and isinstance(registro_output, widgets.Output):
             # with registro_output: print(f"INFO (_refresh_q_list): No hay preguntas definidas para {institution_name_list_refresh}/{group_name_list_refresh}.")
    elif registro_output and isinstance(registro_output, widgets.Output):
            with registro_output: print("Advertencia (_refresh_q_list): No hay contexto de institución/grupo válido. Lista de preguntas vacía.")

    final_options_tuples_list_refresh = options_list_builder_refresh
    current_value_in_widget_before_options_change_list = questions_select_widget.value

    try:
        questions_select_widget.options = final_options_tuples_list_refresh
        valid_option_values_list_refresh = [opt[1] for opt in final_options_tuples_list_refresh]
        new_value_to_set_list_refresh = None

        if preferred_selection_id and preferred_selection_id in valid_option_values_list_refresh:
            new_value_to_set_list_refresh = preferred_selection_id
        elif current_value_in_widget_before_options_change_list in valid_option_values_list_refresh:
            new_value_to_set_list_refresh = current_value_in_widget_before_options_change_list
        elif final_options_tuples_list_refresh:
            new_value_to_set_list_refresh = final_options_tuples_list_refresh[0][1]
        
        questions_select_widget.value = new_value_to_set_list_refresh
        is_valid_current_selection_list_refresh = False
        if new_value_to_set_list_refresh and group_context_list_refresh and \
           isinstance(group_context_list_refresh, dict) and \
           group_context_list_refresh.get('school') and group_context_list_refresh.get('class_name'):
            defs_for_validation_list = get_class_question_definitions(group_context_list_refresh['school'], group_context_list_refresh['class_name'])
            if defs_for_validation_list and new_value_to_set_list_refresh in defs_for_validation_list:
                is_valid_current_selection_list_refresh = True
        
        app_state['current_question_editing_id'] = new_value_to_set_list_refresh if is_valid_current_selection_list_refresh else None
        
        if ui_questions_management_ref:
            _actualizar_estado_botones_gestion_preguntas(app_state, ui_questions_management_ref, registro_output)

    except Exception as e_set_val_list_refresh:
        if registro_output and isinstance(registro_output, widgets.Output):
            with registro_output: print(f"ERROR (_refresh_q_list): Al establecer options/value del Select: {e_set_val_list_refresh}.")
        try:
            questions_select_widget.options = []; questions_select_widget.value = None
            if ui_questions_management_ref:
                app_state['current_question_editing_id'] = None
                _actualizar_estado_botones_gestion_preguntas(app_state, ui_questions_management_ref, registro_output)
        except: pass

    # if registro_output and isinstance(registro_output, widgets.Output):
        # with registro_output:
            # log_msg_refresh = f"DEBUG (_refresh_q_list v18.0 - Inst/Grp/Miembro): Opciones actualizadas. "
            # log_msg_refresh += f"Select.value='{questions_select_widget.value}'. "
            # log_msg_refresh += f"Preferred='{preferred_selection_id}'. "
            # log_msg_refresh += f"AppState.current_q_id='{app_state.get('current_question_editing_id')}'"
            # print(log_msg_refresh)
# --- FIN BLOQUE 1 ---
# --- BLOQUE 2: HANDLERS DE LA LISTA DE PREGUNTAS Y HELPERS DEL FORMULARIO DE PREGUNTA ---
def on_questions_select_change_handler(change, app_state, ui_questions_management, registro_output):
    selected_q_id_on_change_list = change.get('new')
    # if registro_output and isinstance(registro_output, widgets.Output):
        # with registro_output:
            # print(f"HANDLER (questions_select_on_change v18.0 - Inst/Grp/Miembro): Selección cambió a: '{selected_q_id_on_change_list}'")

    group_context_on_change_list = app_state.get('current_context_for_question_management')
    is_valid_question_selected_on_change_list = False

    if selected_q_id_on_change_list and group_context_on_change_list and \
       isinstance(group_context_on_change_list, dict) and \
       group_context_on_change_list.get('school') and group_context_on_change_list.get('class_name'):
        
        institution_name_ctx_on_change = group_context_on_change_list.get('school')
        group_name_ctx_on_change = group_context_on_change_list.get('class_name')
        current_group_defs_on_change_list = get_class_question_definitions(institution_name_ctx_on_change, group_name_ctx_on_change)
        
        if current_group_defs_on_change_list and selected_q_id_on_change_list in current_group_defs_on_change_list:
            is_valid_question_selected_on_change_list = True

    app_state['current_question_editing_id'] = selected_q_id_on_change_list if is_valid_question_selected_on_change_list else None
    _actualizar_estado_botones_gestion_preguntas(app_state, ui_questions_management, registro_output)

    # if registro_output and isinstance(registro_output, widgets.Output):
        # with registro_output:
            # print(f"  on_q_select_change: app_state['current_question_editing_id'] AHORA ES = '{app_state.get('current_question_editing_id')}'")


def _clear_form_question_fields(ui_form_question_elements_clear):
    if isinstance(ui_form_question_elements_clear, dict):
        fields_to_clear_q_form = [
            ("id_input", widgets.Text, ""),
            ("text_input", widgets.Textarea, ""),
            ("type_input", widgets.Text, ""),
            ("polarity_radio", widgets.RadioButtons, "positive"),
            ("order_input", widgets.IntText, 0),
            ("data_key_input", widgets.Text, ""),
            ("max_selections_input", widgets.IntText, 1),
            ("allow_self_selection_checkbox", widgets.Checkbox, False)
        ]
        for key_clear, widget_type_clear, default_value_clear in fields_to_clear_q_form:
            widget_clear = ui_form_question_elements_clear.get(key_clear)
            if widget_clear and isinstance(widget_clear, widget_type_clear):
                widget_clear.value = default_value_clear
            elif widget_clear and key_clear == "polarity_radio" and hasattr(widget_clear, 'value'):
                widget_clear.value = default_value_clear


def _get_num_members_in_group(app_state, registro_output):
    """Obtiene el número de miembros en el grupo actualmente en contexto."""
    group_context_num_mem = app_state.get('current_context_for_question_management')
    num_members_in_group_val = 0
    if group_context_num_mem and isinstance(group_context_num_mem, dict) and \
       'school' in group_context_num_mem and 'class_name' in group_context_num_mem:
        
        institution_name_num_mem = group_context_num_mem['school']
        group_name_num_mem = group_context_num_mem['class_name']
        if institution_name_num_mem in members_data and group_name_num_mem in members_data.get(institution_name_num_mem, {}):
            num_members_in_group_val = len(members_data[institution_name_num_mem].get(group_name_num_mem, []))
            
    if registro_output and isinstance(registro_output, widgets.Output):
        if num_members_in_group_val == 0:
            with registro_output: print("ADVERTENCIA (_get_num_members_in_group): N=0 o contexto no definido.")
    return num_members_in_group_val


def _get_max_possible_selections(app_state, allow_self_selection_value, registro_output):
    """Calcula el máximo número de selecciones posibles basado en N y si se permite auto-selección."""
    num_members_in_group_max_sel = _get_num_members_in_group(app_state, registro_output)
    if num_members_in_group_max_sel <= 0: return 0
    if num_members_in_group_max_sel == 1 and not allow_self_selection_value: return 0
    
    max_sel_calc_val = num_members_in_group_max_sel if allow_self_selection_value else (num_members_in_group_max_sel - 1)
    return max(0, max_sel_calc_val)


def _update_max_selections_limit(app_state, ui_form_question_elements_update, registro_output):
    if not isinstance(ui_form_question_elements_update, dict): return
    
    max_selections_widget_upd = ui_form_question_elements_update.get("max_selections_input")
    allow_self_checkbox_upd = ui_form_question_elements_update.get("allow_self_selection_checkbox")
    
    if not max_selections_widget_upd or not isinstance(max_selections_widget_upd, widgets.IntText) or \
       not allow_self_checkbox_upd or not isinstance(allow_self_checkbox_upd, widgets.Checkbox):
        if registro_output and isinstance(registro_output, widgets.Output):
          with registro_output: print("Advertencia (_update_max_selections_limit): Widgets necesarios no encontrados o tipo incorrecto.")
        return
        
    allow_self_val_for_update = allow_self_checkbox_upd.value
    max_possible_for_update = _get_max_possible_selections(app_state, allow_self_val_for_update, registro_output)
    
    current_max_sel_val_in_widget = max_selections_widget_upd.value
    max_selections_widget_upd.min = 0
    max_selections_widget_upd.max = max(0, max_possible_for_update)
    
    if current_max_sel_val_in_widget > max_selections_widget_upd.max:
        max_selections_widget_upd.value = max_selections_widget_upd.max
    elif current_max_sel_val_in_widget < max_selections_widget_upd.min:
        max_selections_widget_upd.value = max_selections_widget_upd.min


def on_allow_self_selection_change(change, app_state, ui_form_question, registro_output):
    form_q_elements_allow_self_change = getattr(ui_form_question, '_ui_elements_ref', None)
    if form_q_elements_allow_self_change:
        _update_max_selections_limit(app_state, form_q_elements_allow_self_change, registro_output)
    elif registro_output and isinstance(registro_output, widgets.Output):
      with registro_output: print("ERROR (on_allow_self_selection_change): No se pudo obtener _ui_elements_ref de ui_form_question.")
# --- FIN BLOQUE 2 ---
# --- BLOQUE 3: HANDLERS DE BOTONES DE GESTIÓN Y FORMULARIO DE PREGUNTAS ---
def on_questions_nueva_button_handler(b, app_state, ui_questions_management, ui_form_question, switch_interface_func, registro_output):
    # if registro_output and isinstance(registro_output, widgets.Output):
        # with registro_output: print("--- HANDLER (questions v18.0 - Inst/Grp/Miembro): on_questions_nueva_button_handler ---")

    group_context_q_nueva_btn = app_state.get('current_context_for_question_management')
    if not group_context_q_nueva_btn or not (isinstance(group_context_q_nueva_btn, dict) and group_context_q_nueva_btn.get('school') and group_context_q_nueva_btn.get('class_name')):
        if registro_output and isinstance(registro_output, widgets.Output):
            with registro_output: print("ERROR (q_nueva_btn): No hay contexto de institución/grupo válido para añadir pregunta."); return

    select_widget_q_list_nueva = ui_questions_management.get("select") if isinstance(ui_questions_management, dict) else None
    app_state['_temp_id_before_editing_form'] = select_widget_q_list_nueva.value if select_widget_q_list_nueva else None

    if ui_form_question and hasattr(ui_form_question, 'layout') and ui_form_question.layout is not None:
        form_q_elements_nueva_btn = getattr(ui_form_question, '_ui_elements_ref', None)
        if not form_q_elements_nueva_btn or not isinstance(form_q_elements_nueva_btn, dict):
             if registro_output and isinstance(registro_output, widgets.Output):
                with registro_output: print("ERROR (q_nueva_btn): _ui_elements_ref no encontrado en ui_form_question."); return

        institution_name_q_nueva = group_context_q_nueva_btn['school']
        group_name_q_nueva = group_context_q_nueva_btn['class_name']
        # if registro_output and isinstance(registro_output, widgets.Output):
            # with registro_output: print(f"  INFO (q_nueva_btn): Preparando formulario para NUEVA pregunta en {institution_name_q_nueva}/{group_name_q_nueva}.")

        title_label_nueva_btn = form_q_elements_nueva_btn.get("title_label", widgets.Label())
        title_label_nueva_btn.value = f"Nueva Pregunta para {group_name_q_nueva} ({institution_name_q_nueva})"

        _clear_form_question_fields(form_q_elements_nueva_btn)
        for widget_key_nueva_btn in ["id_input", "data_key_input", "text_input", "type_input", "polarity_radio", "order_input", "max_selections_input", "allow_self_selection_checkbox"]:
            widget_nueva_btn_enable = form_q_elements_nueva_btn.get(widget_key_nueva_btn)
            if widget_nueva_btn_enable and hasattr(widget_nueva_btn_enable, 'disabled'): widget_nueva_btn_enable.disabled = False

        _update_max_selections_limit(app_state, form_q_elements_nueva_btn, registro_output)

        add_hbox_nueva_btn = form_q_elements_nueva_btn.get("add_buttons_hbox")
        modify_hbox_nueva_btn = form_q_elements_nueva_btn.get("modify_buttons_hbox")
        if add_hbox_nueva_btn and hasattr(add_hbox_nueva_btn,'layout'): add_hbox_nueva_btn.layout.display = 'flex'
        if modify_hbox_nueva_btn and hasattr(modify_hbox_nueva_btn,'layout'): modify_hbox_nueva_btn.layout.display = 'none'

        ui_form_question.layout.display = 'flex'
        # if registro_output and isinstance(registro_output, widgets.Output):
            # with registro_output: print(f"  INFO (q_nueva_btn): Formulario NUEVA visible. Selección lista: '{app_state.get('current_question_editing_id')}'")
    else:
        if registro_output and isinstance(registro_output, widgets.Output):
            with registro_output: print(f"ERROR (q_nueva_btn): ui_form_question (VBox) no es válido o sin layout.")


def on_questions_modifica_button_handler(b, app_state, ui_questions_management, ui_form_question, switch_interface_func, registro_output):
    # if registro_output and isinstance(registro_output, widgets.Output):
        # with registro_output: print("--- HANDLER (questions v18.0 - Inst/Grp/Miembro): on_questions_modifica_button_handler ---")

    selected_q_id_to_modify_btn = app_state.get('current_question_editing_id')
    if not selected_q_id_to_modify_btn:
        # if registro_output and isinstance(registro_output, widgets.Output):
            # with registro_output: print("INFO (q_modifica_btn): Ninguna pregunta seleccionada en la lista para modificar.");
        if ui_form_question and hasattr(ui_form_question, 'layout') and ui_form_question.layout.display != 'none':
            form_q_elements_check_mod_btn = getattr(ui_form_question, '_ui_elements_ref', None)
            if form_q_elements_check_mod_btn and form_q_elements_check_mod_btn.get("add_buttons_hbox") and \
               hasattr(form_q_elements_check_mod_btn.get("add_buttons_hbox"), 'layout') and \
               form_q_elements_check_mod_btn.get("add_buttons_hbox").layout.display == 'flex':
                ui_form_question.layout.display = 'none'
        return

    app_state['_temp_id_before_editing_form'] = selected_q_id_to_modify_btn

    group_context_mod_btn = app_state.get('current_context_for_question_management')
    if not group_context_mod_btn or not (isinstance(group_context_mod_btn, dict) and group_context_mod_btn.get('school') and group_context_mod_btn.get('class_name')):
        if registro_output: 
          with registro_output: print("ERROR (q_modifica_btn): No hay contexto de institución/grupo válido."); return

    institution_name_mod_q = group_context_mod_btn['school']
    group_name_mod_q = group_context_mod_btn['class_name']
    current_group_defs_mod_btn = get_class_question_definitions(institution_name_mod_q, group_name_mod_q)

    if current_group_defs_mod_btn and selected_q_id_to_modify_btn in current_group_defs_mod_btn:
        q_def_mod_btn = current_group_defs_mod_btn[selected_q_id_to_modify_btn]
        if ui_form_question and hasattr(ui_form_question, 'layout') and ui_form_question.layout is not None:
            form_q_elements_mod_btn_load = getattr(ui_form_question, '_ui_elements_ref', None)
            if not form_q_elements_mod_btn_load or not isinstance(form_q_elements_mod_btn_load, dict):
                if registro_output: 
                  with registro_output: print("ERROR (q_modifica_btn): _ui_elements_ref no encontrada."); return

            # if registro_output: 
              # with registro_output: print(f"  INFO (q_modifica_btn): Cargando datos para MODIFICAR pregunta ID: {selected_q_id_to_modify_btn}.")

            form_q_elements_mod_btn_load.get("title_label", widgets.Label()).value = f"Modificar Pregunta: {selected_q_id_to_modify_btn} ({group_name_mod_q} - {institution_name_mod_q})"
            form_q_elements_mod_btn_load.get("id_input", widgets.Text()).value = selected_q_id_to_modify_btn
            form_q_elements_mod_btn_load.get("text_input", widgets.Textarea()).value = q_def_mod_btn.get('text', '')
            form_q_elements_mod_btn_load.get("type_input", widgets.Text()).value = q_def_mod_btn.get('type', '')
            form_q_elements_mod_btn_load.get("polarity_radio", widgets.RadioButtons()).value = q_def_mod_btn.get('polarity', 'positive')
            form_q_elements_mod_btn_load.get("order_input", widgets.IntText()).value = q_def_mod_btn.get('order', 0)
            form_q_elements_mod_btn_load.get("data_key_input", widgets.Text()).value = q_def_mod_btn.get('data_key', selected_q_id_to_modify_btn)
            form_q_elements_mod_btn_load.get("max_selections_input", widgets.IntText()).value = q_def_mod_btn.get('max_selections', 1)
            form_q_elements_mod_btn_load.get("allow_self_selection_checkbox", widgets.Checkbox()).value = q_def_mod_btn.get('allow_self_selection', False)

            for widget_key_mod_btn_enable in ["id_input", "data_key_input", "text_input", "type_input", "polarity_radio", "order_input", "max_selections_input", "allow_self_selection_checkbox"]:
                widget_mod_btn_enable_field = form_q_elements_mod_btn_load.get(widget_key_mod_btn_enable);
                if widget_mod_btn_enable_field and hasattr(widget_mod_btn_enable_field, 'disabled'): widget_mod_btn_enable_field.disabled = False
            _update_max_selections_limit(app_state, form_q_elements_mod_btn_load, registro_output)

            add_hbox_mod_btn_form = form_q_elements_mod_btn_load.get("add_buttons_hbox")
            modify_hbox_mod_btn_form = form_q_elements_mod_btn_load.get("modify_buttons_hbox")
            if add_hbox_mod_btn_form and hasattr(add_hbox_mod_btn_form,'layout'): add_hbox_mod_btn_form.layout.display = 'none'
            if modify_hbox_mod_btn_form and hasattr(modify_hbox_mod_btn_form,'layout'): modify_hbox_mod_btn_form.layout.display = 'flex'
            ui_form_question.layout.display = 'flex'
            # if registro_output: 
              # with registro_output: print(f"  INFO (q_modifica_btn): Formulario visible en modo MODIFICAR para '{selected_q_id_to_modify_btn}'.")
        else:
            if registro_output: 
              with registro_output: print(f"ERROR (q_modifica_btn): ui_form_question (VBox) no es válido o falta layout.")
    else:
        if registro_output: 
          with registro_output: print(f"ERROR (q_modifica_btn): Pregunta ID '{selected_q_id_to_modify_btn}' no encontrada para modificar.");
        app_state['current_question_editing_id'] = None
        _actualizar_estado_botones_gestion_preguntas(app_state, ui_questions_management, registro_output)


def on_questions_elimina_button_handler(b, app_state, ui_questions_management, registro_output):
    form_question_vbox_to_hide_del = None
    if 'interfaces' in globals() and isinstance(globals()['interfaces'], dict):
        form_question_vbox_to_hide_del = globals()['interfaces'].get('form_question')

    if form_question_vbox_to_hide_del and hasattr(form_question_vbox_to_hide_del, 'layout') and form_question_vbox_to_hide_del.layout.display != 'none':
        form_question_vbox_to_hide_del.layout.display = 'none'
        # if registro_output: 
          # with registro_output: print("  INFO (q_elimina_btn): Formulario de pregunta (empotrado) ocultado antes de eliminar.")

    selected_q_id_from_app_state_del_btn = app_state.get('current_question_editing_id')
    # with registro_output: print(f"HANDLER (questions v18.0 - Inst/Grp/Miembro): on_questions_elimina_button_handler"); print(f"  ID a eliminar: '{selected_q_id_from_app_state_del_btn}'")
    if not selected_q_id_from_app_state_del_btn:
      with registro_output: print("INFO (q_elimina_btn): No hay pregunta seleccionada."); return
    
    group_context_del_btn = app_state.get('current_context_for_question_management')
    if not group_context_del_btn or not (isinstance(group_context_del_btn, dict) and group_context_del_btn.get('school') and group_context_del_btn.get('class_name')):
        with registro_output: print("ERROR (q_elimina_btn): No hay contexto de institución/grupo válido."); return
        
    institution_name_del_q = group_context_del_btn['school']
    group_name_del_q = group_context_del_btn['class_name']
    current_group_defs_del_btn = get_class_question_definitions(institution_name_del_q, group_name_del_q)

    if current_group_defs_del_btn and selected_q_id_from_app_state_del_btn in current_group_defs_del_btn:
        try:
            q_def_to_delete_del_btn = current_group_defs_del_btn.get(selected_q_id_from_app_state_del_btn, {});
            data_key_to_clean_del_btn = q_def_to_delete_del_btn.get('data_key', selected_q_id_from_app_state_del_btn)
            del current_group_defs_del_btn[selected_q_id_from_app_state_del_btn]
            # with registro_output: print(f"ÉXITO (q_elimina_btn): Definición de pregunta '{selected_q_id_from_app_state_del_btn}' eliminada.")
            
            cleaned_responses_count_del_btn = 0
            if isinstance(questionnaire_responses_data, collections.OrderedDict):
                 responses_keys_for_group_del = [ k_del_resp for k_del_resp in questionnaire_responses_data if isinstance(k_del_resp, tuple) and len(k_del_resp) == 3 and k_del_resp[0] == institution_name_del_q and k_del_resp[1] == group_name_del_q ]
                 for resp_key_tuple_del_btn in responses_keys_for_group_del:
                      if resp_key_tuple_del_btn in questionnaire_responses_data:
                          student_responses_del_btn = questionnaire_responses_data[resp_key_tuple_del_btn]
                          if data_key_to_clean_del_btn in student_responses_del_btn:
                              del student_responses_del_btn[data_key_to_clean_del_btn]; cleaned_responses_count_del_btn += 1
            # if cleaned_responses_count_del_btn > 0:
              # with registro_output: print(f"INFO (q_elimina_btn): {cleaned_responses_count_del_btn} respuestas asociadas a data_key '{data_key_to_clean_del_btn}' limpiadas.")
            
            regenerate_relationship_maps_for_class(institution_name_del_q, group_name_del_q)
            # with registro_output: print(f"INFO (q_elimina_btn): Mapas de relación regenerados para {institution_name_del_q}/{group_name_del_q}.")
            
            select_widget_del_q_list_ui = ui_questions_management.get("select") if isinstance(ui_questions_management, dict) else None
            if select_widget_del_q_list_ui:
                _refresh_questions_list_options(app_state, select_widget_del_q_list_ui, registro_output, preferred_selection_id=None, ui_questions_management_ref=ui_questions_management)
            else:
                app_state['current_question_editing_id'] = None
                _actualizar_estado_botones_gestion_preguntas(app_state, ui_questions_management, registro_output)
        except Exception as e_elim_q_final_btn:
          with registro_output: print(f"ERROR CRÍTICO al eliminar la pregunta '{selected_q_id_from_app_state_del_btn}': {e_elim_q_final_btn}\n{traceback.format_exc()}")
    else:
        with registro_output: print(f"ERROR (q_elimina_btn): La pregunta ID '{selected_q_id_from_app_state_del_btn}' no fue encontrada en el grupo actual.");
        app_state['current_question_editing_id'] = None
        _actualizar_estado_botones_gestion_preguntas(app_state, ui_questions_management, registro_output)


def _validate_question_definition(app_state, form_q_elements_val, registro_output, is_new_question=True, original_q_id=None, original_data_key=None):
    q_id_val_form = form_q_elements_val.get("id_input").value.strip(); q_text_val_form = form_q_elements_val.get("text_input").value.strip(); q_data_key_val_form = form_q_elements_val.get("data_key_input").value.strip(); q_max_selections_val_form = form_q_elements_val.get("max_selections_input").value; q_allow_self_selection_val_form = form_q_elements_val.get("allow_self_selection_checkbox").value
    error_msg_val_form = ""
    if not q_id_val_form: error_msg_val_form += "ID de pregunta es obligatorio.\n"
    if not q_text_val_form: error_msg_val_form += "Texto de pregunta es obligatorio.\n"
    if not q_data_key_val_form: error_msg_val_form += "Clave de Datos (Data Key) es obligatoria.\n"
    
    group_context_val_form = app_state.get('current_context_for_question_management')
    if not group_context_val_form or not (isinstance(group_context_val_form,dict) and group_context_val_form.get('school') and group_context_val_form.get('class_name')):
        error_msg_val_form += "Contexto de institución/grupo no encontrado o inválido para validación.\n"
    else:
        institution_name_val_form = group_context_val_form['school']
        group_name_val_form = group_context_val_form['class_name']
        current_group_defs_val_form = get_class_question_definitions(institution_name_val_form, group_name_val_form)
        
        if is_new_question and q_id_val_form in current_group_defs_val_form: error_msg_val_form += f"Ya existe una pregunta con ID '{q_id_val_form}'.\n"
        elif not is_new_question and q_id_val_form != original_q_id and q_id_val_form in current_group_defs_val_form: error_msg_val_form += f"El nuevo ID de pregunta '{q_id_val_form}' ya existe.\n"
        
        if is_new_question and any(d_val_form.get('data_key') == q_data_key_val_form for d_val_form in current_group_defs_val_form.values()): error_msg_val_form += f"Ya existe una pregunta con Data Key '{q_data_key_val_form}'.\n"
        elif not is_new_question and q_data_key_val_form != original_data_key and any(d_val_form.get('data_key') == q_data_key_val_form for id_iter_val_form, d_val_form in current_group_defs_val_form.items() if id_iter_val_form != original_q_id): error_msg_val_form += f"La nueva Clave de Datos '{q_data_key_val_form}' ya existe para otra pregunta.\n"
        
        num_members_actual_val_form = _get_num_members_in_group(app_state, registro_output)
        max_permitido_segun_N_val_form = _get_max_possible_selections(app_state, q_allow_self_selection_val_form, registro_output)
        if q_max_selections_val_form < 0: error_msg_val_form += "Máximo de selecciones no puede ser negativo.\n"
        elif q_max_selections_val_form > max_permitido_segun_N_val_form:
            if num_members_actual_val_form == 0: error_msg_val_form += f"Máximo de selecciones ({q_max_selections_val_form}) es inválido. No hay miembros, debe ser 0.\n"
            elif num_members_actual_val_form == 1 and not q_allow_self_selection_val_form: error_msg_val_form += f"Máximo de selecciones ({q_max_selections_val_form}) es inválido. Solo 1 miembro y no auto-selección, debe ser 0.\n"
            else: error_msg_val_form += f"Máximo de selecciones ({q_max_selections_val_form}) excede el límite permitido ({max_permitido_segun_N_val_form} basado en N miembros y auto-selección).\n"
        
        if q_max_selections_val_form == 0 and num_members_actual_val_form > 0 and not (num_members_actual_val_form == 1 and not q_allow_self_selection_val_form):
             _add_warning_if_possible(registro_output, "Advertencia: Máximo de selecciones es 0, pero hay miembros elegibles. ¿Es correcto?")
             
    if error_msg_val_form:
        if registro_output and isinstance(registro_output, widgets.Output):
          with registro_output: print(f"ERRORES DE VALIDACIÓN (Pregunta):\n{error_msg_val_form.strip()}");
        return False, None
        
    return True, { 'text': q_text_val_form, 'type': form_q_elements_val.get("type_input").value.strip(), 'polarity': form_q_elements_val.get("polarity_radio").value, 'order': form_q_elements_val.get("order_input").value, 'data_key': q_data_key_val_form, 'max_selections': q_max_selections_val_form, 'allow_self_selection': q_allow_self_selection_val_form }

def _add_warning_if_possible(ro_warn, msg_warn):
    if ro_warn and isinstance(ro_warn, widgets.Output):
        with ro_warn: print(f"  ADVERTENCIA (VALIDATE_Q_HELPER): {msg_warn}")


def on_form_question_add_save_handler(b, app_state, ui_form_question, ui_questions_management, switch_interface_func, registro_output):
    # if registro_output and isinstance(registro_output, widgets.Output):
        # with registro_output: print("HANDLER (questions v18.0 - Inst/Grp/Miembro): on_form_question_add_save_handler")
    
    form_q_elements_add_save = getattr(ui_form_question, '_ui_elements_ref', None)
    if not form_q_elements_add_save:
        if registro_output: 
          with registro_output: print("ERROR (add_save_q_form): _ui_elements_ref no encontrado."); return
        
    is_valid_add_q_form, new_q_def_data_add_q_form = _validate_question_definition(app_state, form_q_elements_add_save, registro_output, is_new_question=True)
    if not is_valid_add_q_form: return
    
    q_id_add_form = form_q_elements_add_save.get("id_input").value.strip()
    group_context_add_q_form = app_state.get('current_context_for_question_management')
    if not group_context_add_q_form or not (isinstance(group_context_add_q_form,dict) and group_context_add_q_form.get('school') and group_context_add_q_form.get('class_name')):
        if registro_output: 
          with registro_output: print("ERROR (add_save_q_form): Contexto de institución/grupo no válido."); return
        
    institution_name_add_q = group_context_add_q_form['school']
    group_name_add_q = group_context_add_q_form['class_name']
    current_group_defs_add_q_form = get_class_question_definitions(institution_name_add_q, group_name_add_q)
    
    try:
        current_group_defs_add_q_form[q_id_add_form] = new_q_def_data_add_q_form
        regenerate_relationship_maps_for_class(institution_name_add_q, group_name_add_q)
        # with registro_output: print(f"ÉXITO (add_save_q_form): Pregunta '{q_id_add_form}' añadida a {institution_name_add_q}/{group_name_add_q}.")
        
        if hasattr(ui_form_question, 'layout') and ui_form_question.layout is not None:
            ui_form_question.layout.display = 'none'

        if ui_questions_management and isinstance(ui_questions_management, dict):
            select_widget_add_q_form = ui_questions_management.get("select")
            if select_widget_add_q_form:
                _refresh_questions_list_options(app_state, select_widget_add_q_form, registro_output,
                                                preferred_selection_id=q_id_add_form,
                                                ui_questions_management_ref=ui_questions_management)
        if '_temp_id_before_editing_form' in app_state: del app_state['_temp_id_before_editing_form']
    except Exception as e_add_q_final_form:
      with registro_output: print(f"ERROR al guardar nueva pregunta: {e_add_q_final_form}\n{traceback.format_exc()}")


def on_form_question_modify_save_handler(b, app_state, ui_form_question, ui_questions_management, switch_interface_func, registro_output):
    # if registro_output and isinstance(registro_output, widgets.Output):
        # with registro_output: print(f"HANDLER (questions v18.0 - Inst/Grp/Miembro): on_form_question_modify_save_handler")

    original_editing_q_id_mod_save = app_state.get('current_question_editing_id')
    if not original_editing_q_id_mod_save:
        if registro_output: 
          with registro_output: print("ERROR (modify_save_q_form): No hay pregunta en edición."); return

    form_q_elements_mod_q_save = getattr(ui_form_question, '_ui_elements_ref', None)
    if not form_q_elements_mod_q_save:
        if registro_output: 
          with registro_output: print("ERROR (modify_save_q_form): _ui_elements_ref no encontrado."); return

    group_context_mod_q_save = app_state.get('current_context_for_question_management')
    if not group_context_mod_q_save or not (isinstance(group_context_mod_q_save,dict) and group_context_mod_q_save.get('school') and group_context_mod_q_save.get('class_name')):
        if registro_output: 
          with registro_output: print("ERROR (modify_save_q_form): No hay contexto de institución/grupo válido."); return
        
    institution_name_mod_q_save = group_context_mod_q_save['school']
    group_name_mod_q_save = group_context_mod_q_save['class_name']
    current_group_defs_mod_q_save = get_class_question_definitions(institution_name_mod_q_save, group_name_mod_q_save)

    if original_editing_q_id_mod_save not in current_group_defs_mod_q_save:
        if registro_output: 
          with registro_output: print(f"ERROR (modify_save_q_form): Pregunta ID original '{original_editing_q_id_mod_save}' no encontrada."); return

    original_data_key_for_validation_mod_save = current_group_defs_mod_q_save[original_editing_q_id_mod_save].get('data_key', original_editing_q_id_mod_save)
    is_valid_mod_q_save, updated_q_def_data_mod_q_save = _validate_question_definition( app_state, form_q_elements_mod_q_save, registro_output, is_new_question=False, original_q_id=original_editing_q_id_mod_save, original_data_key=original_data_key_for_validation_mod_save )
    if not is_valid_mod_q_save: return

    new_q_id_mod_q_save = form_q_elements_mod_q_save.get("id_input").value.strip(); new_data_key_mod_q_save = updated_q_def_data_mod_q_save['data_key']
    try:
        if new_q_id_mod_q_save != original_editing_q_id_mod_save:
            del current_group_defs_mod_q_save[original_editing_q_id_mod_save]
            current_group_defs_mod_q_save[new_q_id_mod_q_save] = updated_q_def_data_mod_q_save
        else:
            current_group_defs_mod_q_save[original_editing_q_id_mod_save].update(updated_q_def_data_mod_q_save)

        if new_data_key_mod_q_save != original_data_key_for_validation_mod_save:
            migrated_responses_count_mod_q_save = 0
            for response_tuple_key_mod_q_save in list(questionnaire_responses_data.keys()):
                resp_institution_mod_q, resp_group_mod_q, resp_student_name_mod_q = response_tuple_key_mod_q_save
                if resp_institution_mod_q == institution_name_mod_q_save and resp_group_mod_q == group_name_mod_q_save:
                    student_responses_dict_mod_q = questionnaire_responses_data.get(response_tuple_key_mod_q_save)
                    if student_responses_dict_mod_q and original_data_key_for_validation_mod_save in student_responses_dict_mod_q:
                        student_responses_dict_mod_q[new_data_key_mod_q_save] = student_responses_dict_mod_q.pop(original_data_key_for_validation_mod_save); migrated_responses_count_mod_q_save += 1
            # if migrated_responses_count_mod_q_save > 0:
                # if registro_output: 
                  # with registro_output: print(f"    ÉXITO: {migrated_responses_count_mod_q_save} conjuntos de respuestas migradas a nueva data_key '{new_data_key_mod_q_save}'.")

        regenerate_relationship_maps_for_class(institution_name_mod_q_save, group_name_mod_q_save)
        # with registro_output: print(f"ÉXITO (modify_save_q_form): Pregunta '{new_q_id_mod_q_save}' actualizada (Data Key: '{new_data_key_mod_q_save}').")
        if hasattr(ui_form_question, 'layout') and ui_form_question.layout is not None: ui_form_question.layout.display = 'none'

        if ui_questions_management and isinstance(ui_questions_management, dict):
            select_widget_mod_q_save_ui = ui_questions_management.get("select")
            if select_widget_mod_q_save_ui:
                _refresh_questions_list_options(app_state, select_widget_mod_q_save_ui, registro_output,
                                                preferred_selection_id=new_q_id_mod_q_save,
                                                ui_questions_management_ref=ui_questions_management)
        if '_temp_id_before_editing_form' in app_state: del app_state['_temp_id_before_editing_form']
    except Exception as e_mod_save_q_final:
        with registro_output: print(f"ERROR al guardar cambios en la pregunta: {e_mod_save_q_final}\n{traceback.format_exc()}")


def on_form_question_cancel_handler(b, app_state, switch_interface_func, registro_output, ui_questions_management=None, ui_form_question=None):
    # with registro_output:
        # print("HANDLER (questions v18.0 - Inst/Grp/Miembro): on_form_question_cancel_handler")

    if ui_form_question and hasattr(ui_form_question, 'layout') and ui_form_question.layout is not None:
        ui_form_question.layout.display = 'none'
        # if registro_output: 
          # with registro_output: print(f"  INFO (cancel_form_q): ui_form_question (VBox) ocultado.")

    id_a_restaurar_tras_cancel_q_form = app_state.pop('_temp_id_before_editing_form', None)
    app_state['current_question_editing_id'] = id_a_restaurar_tras_cancel_q_form

    # if registro_output: 
      # with registro_output: print(f"  INFO (cancel_form_q): ID de pregunta a restaurar: '{id_a_restaurar_tras_cancel_q_form}'. `current_question_editing_id` es '{app_state.get('current_question_editing_id')}'.")

    if ui_questions_management and isinstance(ui_questions_management, dict):
         select_widget_cancel_q_form_ui = ui_questions_management.get("select")
         if select_widget_cancel_q_form_ui:
            _refresh_questions_list_options(app_state, select_widget_cancel_q_form_ui, registro_output,
                                            preferred_selection_id=id_a_restaurar_tras_cancel_q_form,
                                            ui_questions_management_ref=ui_questions_management)
            # if registro_output: 
              # with registro_output: print(f"  DEBUG (cancel_form_q): Select.value después de refresh: '{select_widget_cancel_q_form_ui.value}'. AppState.current_q_id: '{app_state.get('current_question_editing_id')}'.")
    else:
        if ui_questions_management:
             _actualizar_estado_botones_gestion_preguntas(app_state, ui_questions_management, registro_output)
# --- FIN BLOQUE 3 ---
# --- BLOQUE 4: HANDLER DE SALIDA PRINCIPAL DE LA GESTIÓN DE PREGUNTAS ---
def on_questions_management_salir_button_handler(b, app_state, switch_interface_func, registro_output,
                                                 interfaces_ref,
                                                 temp_ui_form_q_ref,
                                                 ui_members_ref,
                                                 member_refresh_handler_ref,
                                                 ui_questions_management_for_q_ref,
                                                 app_ui_module_ref,
                                                 handlers_questionnaire_module_ref,
                                                 handlers_questions_module_ref,
                                                 handlers_schools_module_ref,
                                                 ui_form_question_vbox_ref
                                                ):
    if registro_output is None:
        print("ADVERTENCIA CRÍTICA (q_mgmt_salir): 'registro_output' ES None.")
        registro_output = Output()
    try:
        with registro_output:
            clear_output(wait=True)
            # print(f"HANDLER (questions v18.0 - Inst/Grp/Miembro): on_questions_management_salir_button_handler. INICIANDO...")
            pass
    except Exception as e_clear_q_mgmt_salir:
        print(f"  DEBUG CRÍTICO (q_mgmt_salir): EXCEPCIÓN durante clear_output: {e_clear_q_mgmt_salir}")
        traceback.print_exc()
        return

    if ui_form_question_vbox_ref and hasattr(ui_form_question_vbox_ref, 'layout') and \
       ui_form_question_vbox_ref.layout is not None and ui_form_question_vbox_ref.layout.display != 'none':
        try:
            ui_form_question_vbox_ref.layout.display = 'none'
            # with registro_output: print("  INFO (q_mgmt_salir): Formulario de pregunta (empotrado) ocultado.")
        except Exception as e_hide_form_q_salir:
            with registro_output: print(f"  ERROR (q_mgmt_salir): al ocultar ui_form_question_vbox_ref: {e_hide_form_q_salir}")

    default_return_ui_q_mgmt_salir = 'form_questionnaire'
    return_interface_q_mgmt_salir = app_state.get('return_interface', default_return_ui_q_mgmt_salir) if app_state else default_return_ui_q_mgmt_salir

    if return_interface_q_mgmt_salir != 'form_questionnaire':
        if registro_output and return_interface_q_mgmt_salir is not None :
            with registro_output: print(f"  ADVERTENCIA (q_mgmt_salir): 'return_interface' era '{return_interface_q_mgmt_salir}', forzando a '{default_return_ui_q_mgmt_salir}'.")
        return_interface_q_mgmt_salir = default_return_ui_q_mgmt_salir

    if app_state:
        app_state['return_interface'] = None
        app_state['current_question_editing_id'] = None
    else:
        with registro_output: print("  ERROR CRÍTICO (q_mgmt_salir): app_state es None. No se pueden limpiar estados.")

    if ui_questions_management_for_q_ref and isinstance(ui_questions_management_for_q_ref, dict):
        try:
            _actualizar_estado_botones_gestion_preguntas(app_state, ui_questions_management_for_q_ref, registro_output)
            # with registro_output: print(f"  INFO (q_mgmt_salir): Botones de la UI 'questions_management' reseteados.")
        except Exception as e_update_btns_q_mgmt_salir:
            with registro_output: print(f"  ERROR (q_mgmt_salir): al llamar a _actualizar_estado_botones_gestion_preguntas: {e_update_btns_q_mgmt_salir}")
    else:
        with registro_output: print(f"  ADVERTENCIA (q_mgmt_salir): ui_questions_management_for_q_ref no válido, no se resetearon botones.")

    if return_interface_q_mgmt_salir == 'form_questionnaire':
        q_context_return_q_mgmt = app_state.get('current_questionnaire_member_context') if app_state else None
        # if registro_output: 
          # with registro_output: print(f"  DEBUG (q_mgmt_salir): Contexto del cuestionario para volver: {q_context_return_q_mgmt}")

        if q_context_return_q_mgmt and isinstance(q_context_return_q_mgmt, dict) and \
           q_context_return_q_mgmt.get('school') and q_context_return_q_mgmt.get('class_name') and q_context_return_q_mgmt.get('member'):

            institution_name_return_q = q_context_return_q_mgmt['school']
            group_name_return_q = q_context_return_q_mgmt['class_name']
            member_name_return_q = q_context_return_q_mgmt['member']

            # with registro_output: print(f"  INFO (q_mgmt_salir): Reconstruyendo UI del cuestionario para {institution_name_return_q}/{group_name_return_q}, Miembro: {member_name_return_q}")
            try:
                regenerate_relationship_maps_for_class(institution_name_return_q, group_name_return_q)
                # with registro_output: print(f"  INFO (q_mgmt_salir): Mapas de relación regenerados para {institution_name_return_q}/{group_name_return_q}.")
            except Exception as e_regen_q_mgmt_salir_btn_final:
                with registro_output: print(f"  ERROR al regenerar mapas en on_q_mgmt_salir: {e_regen_q_mgmt_salir_btn_final}")

            current_app_data_for_q_salir_final_rebuild = globals().get('sociograma_data')
            if not current_app_data_for_q_salir_final_rebuild:
                with registro_output: print("  ERROR CRÍTICO (q_mgmt_salir): Módulo 'sociograma_data' no encontrado globalmente.");
                switch_interface_func(return_interface_q_mgmt_salir); return

            try:
                if not all([app_ui_module_ref, hasattr(app_ui_module_ref, 'create_form_questionnaire_vbox'),
                            interfaces_ref, isinstance(interfaces_ref, dict),
                            temp_ui_form_q_ref, isinstance(temp_ui_form_q_ref, dict),
                            handlers_questionnaire_module_ref,
                            ui_questions_management_for_q_ref,
                            handlers_questions_module_ref]):
                    with registro_output: print("  ERROR CRÍTICO (q_mgmt_salir): Faltan referencias de módulos/UI para reconstruir el cuestionario.");
                    switch_interface_func(return_interface_q_mgmt_salir); return

                current_group_q_defs_return_q_mgmt = get_class_question_definitions(institution_name_return_q, group_name_return_q)
                new_q_vbox_return_q_mgmt, new_q_ui_elements_return_q_mgmt = app_ui_module_ref.create_form_questionnaire_vbox(current_group_q_defs_return_q_mgmt)

                interfaces_ref['form_questionnaire'] = new_q_vbox_return_q_mgmt
                temp_ui_form_q_ref.clear(); temp_ui_form_q_ref.update(new_q_ui_elements_return_q_mgmt)

                member_label_widget_return_q_mgmt = new_q_ui_elements_return_q_mgmt.get("student_label")
                if member_label_widget_return_q_mgmt :
                    member_label_widget_return_q_mgmt.value = f"Miembro: {member_name_return_q} ({group_name_return_q} - {institution_name_return_q})"
                
                ok_button_q_return = new_q_ui_elements_return_q_mgmt.get("ok_button")
                if ok_button_q_return and hasattr(handlers_questionnaire_module_ref, 'on_q_ok_button_click_handler'):
                    if hasattr(ok_button_q_return, '_click_handlers') and ok_button_q_return._click_handlers: ok_button_q_return._click_handlers.callbacks = []
                    ok_button_q_return.on_click(functools.partial( handlers_questionnaire_module_ref.on_q_ok_button_click_handler, app_state=app_state, ui_form_questionnaire=new_q_ui_elements_return_q_mgmt, switch_interface_func=switch_interface_func, registro_output=registro_output, ui_members=ui_members_ref, member_refresh_func=member_refresh_handler_ref ))
                
                salir_button_q_return = new_q_ui_elements_return_q_mgmt.get("salir_button")
                if salir_button_q_return and hasattr(handlers_questionnaire_module_ref, 'on_q_salir_button_click_handler'):
                    if hasattr(salir_button_q_return, '_click_handlers') and salir_button_q_return._click_handlers: salir_button_q_return._click_handlers.callbacks = []
                    salir_button_q_return.on_click(functools.partial( handlers_questionnaire_module_ref.on_q_salir_button_click_handler, app_state=app_state, switch_interface_func=switch_interface_func, registro_output=registro_output, ui_members=ui_members_ref, member_refresh_func=member_refresh_handler_ref ))

                pdf_class_btn_q_return = new_q_ui_elements_return_q_mgmt.get("pdf_class_button")
                if pdf_class_btn_q_return and hasattr(handlers_questionnaire_module_ref, 'on_q_pdf_class_button_click_handler'):
                    if hasattr(pdf_class_btn_q_return, '_click_handlers') and pdf_class_btn_q_return._click_handlers: pdf_class_btn_q_return._click_handlers.callbacks = []
                    pdf_class_btn_q_return.on_click(functools.partial( handlers_questionnaire_module_ref.on_q_pdf_class_button_click_handler, app_state=app_state, registro_output=registro_output ))

                manage_q_button_q_return = new_q_ui_elements_return_q_mgmt.get("manage_questions_button")
                if manage_q_button_q_return and hasattr(handlers_questionnaire_module_ref, 'on_q_manage_questions_button_handler'):
                    if hasattr(manage_q_button_q_return, '_click_handlers') and manage_q_button_q_return._click_handlers: manage_q_button_q_return._click_handlers.callbacks = []
                    manage_q_button_q_return.on_click( functools.partial( handlers_questionnaire_module_ref.on_q_manage_questions_button_handler, app_state=app_state, ui_form_questionnaire=new_q_ui_elements_return_q_mgmt, ui_questions_management=ui_questions_management_for_q_ref, switch_interface_func=switch_interface_func, registro_output=registro_output, handlers_questions_ref=handlers_questions_module_ref ))
                # with registro_output: print("  INFO (q_mgmt_salir): Re-enlace de botones del cuestionario reconstruido completo.")

                if hasattr(handlers_questionnaire_module_ref, '_populate_questionnaire_dropdowns'):
                    handlers_questionnaire_module_ref._populate_questionnaire_dropdowns(
                        app_state, new_q_ui_elements_return_q_mgmt, registro_output,
                        app_data_ref=current_app_data_for_q_salir_final_rebuild
                    )
                    # with registro_output: print("  INFO (q_mgmt_salir): Llamada a _populate_questionnaire_dropdowns finalizada.")
                else:
                    with registro_output: print("  ERROR CRÍTICO (q_mgmt_salir): _populate_questionnaire_dropdowns no encontrado en handlers_questionnaire.")
            except Exception as e_rebuild_q_ui_salir_final_btn:
                with registro_output:
                    print(f"  ERROR CRÍTICO (q_mgmt_salir): al reconstruir UI del cuestionario: {e_rebuild_q_ui_salir_final_btn}")
                    print(traceback.format_exc(limit=2))
        else:
             with registro_output: print(f"  ADVERTENCIA (q_mgmt_salir): No se está volviendo a form_questionnaire o falta contexto de cuestionario válido ({q_context_return_q_mgmt}).")

    # with registro_output: print(f"Saliendo de la gestión de preguntas. Intentando cambiar a la interfaz: '{return_interface_q_mgmt_salir}'")
    try:
        switch_interface_func(return_interface_q_mgmt_salir)
        # with registro_output: print(f"  INFO (q_mgmt_salir): switch_interface_func('{return_interface_q_mgmt_salir}') LLAMADO y completado.")
    except Exception as e_switch_final_q_mgmt:
        # print(f"  DEBUG CRÍTICO (q_mgmt_salir): EXCEPCIÓN durante switch_interface_func: {e_switch_final_q_mgmt}")
        traceback.print_exc()
        with registro_output: print(f"  ERROR CRÍTICO (q_mgmt_salir): al llamar a switch_interface_func: {e_switch_final_q_mgmt}.")
# --- FIN BLOQUE 4 ---