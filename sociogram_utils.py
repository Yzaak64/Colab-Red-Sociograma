# sociogram_utils.py
# (v1.11.0 - Usa 'current_group_viewing_members' para el contexto.
#            Terminología "Miembro" en logs y comentarios.)

import collections
from ipywidgets import widgets, Layout, Checkbox, Label, Dropdown, RadioButtons, IntText
from IPython.display import clear_output, display, HTML as IPHTML
import traceback
import time
import sys

# --- Funciones Helper Internas ---

def _get_registro_output_widget(ui_sociogramma_ref=None, registro_output_param=None):
    if registro_output_param and isinstance(registro_output_param, widgets.Output):
        return registro_output_param
    if isinstance(ui_sociogramma_ref, dict) and '_temp_registro_output_ref' in ui_sociogramma_ref:
        ro_widget_temp_util = ui_sociogramma_ref['_temp_registro_output_ref']
        if isinstance(ro_widget_temp_util, widgets.Output):
            return ro_widget_temp_util
    ro_widget_global_util = globals().get('registro_output_area')
    if isinstance(ro_widget_global_util, widgets.Output):
        return ro_widget_global_util
    return None

def _log_message(registro_output_widget_log, prefix_log, message_log):
    # Esta función ahora no hace nada para mantener la salida limpia.
    # Se podría activar para depuración si fuera necesario.
    pass

def get_widget_value(ui_dict_gwv, key_gwv, default_value_gwv):
    if not isinstance(ui_dict_gwv, dict): return default_value_gwv
    widget_gwv = ui_dict_gwv.get(key_gwv)
    return widget_gwv.value if widget_gwv and hasattr(widget_gwv, 'value') else default_value_gwv

def _update_participant_dropdown(app_state, ui_sociogramma, app_data_ref, handlers_utils_ref):
    local_registro_output_upd = _get_registro_output_widget(ui_sociogramma)
    # _log_message(local_registro_output_upd, "UTIL_LOG_DD", f"(_update_participant_dropdown v1.11.0 - Inst/Grp/Miembro): Iniciando.")

    context_upd_dd = app_state.get('current_group_viewing_members')
    # _log_message(local_registro_output_upd, "UTIL_LOG_DD", f"  Contexto (current_group_viewing_members): {context_upd_dd}")

    participant_dropdown_upd = ui_sociogramma.get("participant_select_dropdown")
    if not participant_dropdown_upd:
        with local_registro_output_upd: print("  ERROR: Widget 'participant_select_dropdown' no encontrado.")
        return

    if not context_upd_dd or not context_upd_dd.get('school') or not context_upd_dd.get('class_name'):
        # _log_message(local_registro_output_upd, "UTIL_LOG_DD", "  ADVERTENCIA: Contexto institución/grupo no válido.")
        participant_dropdown_upd.options = [('Todos (Grafo Completo)', None)]; participant_dropdown_upd.value = None
        connection_focus_radio_upd = ui_sociogramma.get("connection_focus_radio")
        if connection_focus_radio_upd: connection_focus_radio_upd.disabled = True
        return

    institution_name_upd = context_upd_dd['school']
    group_name_upd = context_upd_dd['class_name']
    # _log_message(local_registro_output_upd, "UTIL_LOG_DD", f"  Institución: '{institution_name_upd}', Grupo: '{group_name_upd}'.")

    current_app_data_for_options_upd = app_data_ref
    if not current_app_data_for_options_upd:
        with local_registro_output_upd: print("  ADVERTENCIA CRÍTICA: app_data_ref es None. Usando fallback global 'sociograma_data'.")
        current_app_data_for_options_upd = globals().get('sociograma_data')
        if not current_app_data_for_options_upd:
            with local_registro_output_upd: print("  ERROR CRÍTICO: Fallback a 'sociograma_data' falló.")
            participant_dropdown_upd.options = [('Error datos', None)]; return
    
    get_member_options_func_runtime_upd = getattr(handlers_utils_ref, 'get_member_options_for_dropdown', None)
    if not callable(get_member_options_func_runtime_upd):
        with local_registro_output_upd: print("  ERROR CRÍTICO: get_member_options_for_dropdown no llamable.")
        participant_dropdown_upd.options = [('Error func', None)]; return
    
    try:
        member_options_raw_upd = get_member_options_func_runtime_upd(
            school_name=institution_name_upd,
            class_name=group_name_upd,
            app_data_ref=current_app_data_for_options_upd,
            registro_output_fallback=local_registro_output_upd
        )
    except Exception as e_get_opts_upd:
        with local_registro_output_upd: print(f"    EXCEPCIÓN en get_member_options_for_dropdown: {e_get_opts_upd}")
        member_options_raw_upd = [('Error crítico', None)]

    final_options_for_dropdown_upd = [('Todos (Grafo Completo)', None)]
    if isinstance(member_options_raw_upd, list):
        for label_opt, value_opt in member_options_raw_upd:
            if value_opt is not None: final_options_for_dropdown_upd.append((label_opt, value_opt))
            elif label_opt is not None and str(label_opt).lower() != 'seleccionar': final_options_for_dropdown_upd.append((label_opt,value_opt))

    current_value_in_dropdown_upd = participant_dropdown_upd.value
    participant_dropdown_upd.options = final_options_for_dropdown_upd
    valid_option_values_final_upd = [opt_val for _, opt_val in final_options_for_dropdown_upd]
    if current_value_in_dropdown_upd in valid_option_values_final_upd: participant_dropdown_upd.value = current_value_in_dropdown_upd
    else: participant_dropdown_upd.value = None
    
    connection_focus_radio_final_upd = ui_sociogramma.get("connection_focus_radio")
    if connection_focus_radio_final_upd:
        is_specific_participant_selected_upd = (participant_dropdown_upd.value is not None)
        connection_focus_radio_final_upd.disabled = not is_specific_participant_selected_upd
        if not is_specific_participant_selected_upd: connection_focus_radio_final_upd.value = 'all'
    # _log_message(local_registro_output_upd, "UTIL_LOG_DD", f"(_update_participant_dropdown v1.11.0 - Inst/Grp/Miembro): Finalizado.")

def _update_relations_checkboxes(app_state, ui_sociogramma, registro_output_ref_param, app_data_ref):
    local_registro_output_cb_upd = _get_registro_output_widget(ui_sociogramma, registro_output_ref_param)
    # _log_message(local_registro_output_cb_upd, "UTIL_LOG_CB", f"(_update_relations_checkboxes v1.11.0 - Inst/Grp/Miembro): Iniciando.")
    
    context_cb_upd = app_state.get('current_group_viewing_members')
    # _log_message(local_registro_output_cb_upd, "UTIL_LOG_CB", f"  Contexto (current_group_viewing_members): {context_cb_upd}")
    
    checkboxes_vbox_upd = ui_sociogramma.get("relations_checkboxes_vbox")
    if not context_cb_upd or not checkboxes_vbox_upd:
        # _log_message(local_registro_output_cb_upd, "UTIL_LOG_CB", "  ADVERTENCIA: Contexto o VBox de checkboxes no disponible.")
        if checkboxes_vbox_upd: checkboxes_vbox_upd.children = [Label("Error: Contexto de institución/grupo no definido.")]
        return
    
    institution_name_cb_upd = context_cb_upd['school']
    group_name_cb_upd = context_cb_upd['class_name']
    # _log_message(local_registro_output_cb_upd, "UTIL_LOG_CB", f"  Institución: '{institution_name_cb_upd}', Grupo: '{group_name_cb_upd}'.")

    if not app_data_ref or not hasattr(app_data_ref, 'regenerate_relationship_maps_for_class') or not hasattr(app_data_ref, 'sociogram_relation_options_map'):
        with local_registro_output_cb_upd: print("  ERROR CRÍTICO: app_data_ref no válido para regenerar mapas."); return
    
    try:
        app_data_ref.regenerate_relationship_maps_for_class(institution_name_cb_upd, group_name_cb_upd)
    except Exception as e_regen_maps_cb_upd:
        with local_registro_output_cb_upd: print(f"  ERROR en regenerate_relationship_maps: {e_regen_maps_cb_upd}"); return

    current_relation_options_map_cb_upd = app_data_ref.sociogram_relation_options_map
    new_checkbox_widgets_info_list_final_upd = []
    temp_checkbox_widgets_for_vbox_final_upd = []
    existing_checkbox_states_final_upd = {}
    if '_relations_checkbox_widgets' in ui_sociogramma and isinstance(ui_sociogramma['_relations_checkbox_widgets'], list):
        for cb_info_old_dict_upd in ui_sociogramma['_relations_checkbox_widgets']:
            if isinstance(cb_info_old_dict_upd, dict) and 'data_key' in cb_info_old_dict_upd and 'widget' in cb_info_old_dict_upd and hasattr(cb_info_old_dict_upd['widget'], 'value'):
                existing_checkbox_states_final_upd[cb_info_old_dict_upd['data_key']] = cb_info_old_dict_upd['widget'].value

    if current_relation_options_map_cb_upd and isinstance(current_relation_options_map_cb_upd, dict):
        sorted_relation_items_final_upd = sorted([(k, l) for k,l in current_relation_options_map_cb_upd.items() if k != 'all'], key=lambda item: item[1])
        if not sorted_relation_items_final_upd: temp_checkbox_widgets_for_vbox_final_upd.append(Label("No hay relaciones/preguntas específicas."))
        else:
            for data_key_final_upd, label_for_cb_final_upd in sorted_relation_items_final_upd:
                current_cb_value_final_upd = existing_checkbox_states_final_upd.get(data_key_final_upd, True)
                cb_final_upd = Checkbox(description=label_for_cb_final_upd, value=current_cb_value_final_upd, indent=False, layout=Layout(width='auto', margin_bottom='2px'))
                new_checkbox_widgets_info_list_final_upd.append({'widget': cb_final_upd, 'data_key': data_key_final_upd, 'label': label_for_cb_final_upd})
                temp_checkbox_widgets_for_vbox_final_upd.append(cb_final_upd)
    else: temp_checkbox_widgets_for_vbox_final_upd.append(Label("No hay opciones de relación."))
    
    checkboxes_vbox_upd.children = tuple(temp_checkbox_widgets_for_vbox_final_upd)
    ui_sociogramma["_relations_checkbox_widgets"] = new_checkbox_widgets_info_list_final_upd
    selected_now_count_upd = sum(1 for info_upd in new_checkbox_widgets_info_list_final_upd if info_upd['widget'].value)
    # _log_message(local_registro_output_cb_upd, "UTIL_LOG_CB", f"(_update_relations_checkboxes v1.11.0 - Inst/Grp/Miembro): Checkboxes actualizados. {selected_now_count_upd} seleccionados.")

def _prepare_sociogram_draw(app_state, ui_sociogramma, registro_output, layout_to_use,
                           app_data_ref, handlers_utils_ref):
    try:
        from sociogram_engine import draw_sociogramma
    except ImportError:
        if registro_output and isinstance(registro_output, widgets.Output):
             with registro_output: print("ERROR CRÍTICO (_prepare_sociogram_draw v1.11.0): No se pudo importar draw_sociogramma de sociogram_engine.")
        return

    local_registro_prepare_draw = _get_registro_output_widget(ui_sociogramma, registro_output)
    # _log_message(local_registro_prepare_draw, "PREP_LOG", f"**** _prepare_sociogram_draw (v1.11.0 - Usando current_group_viewing_members) EJECUTÁNDOSE. Layout: '{layout_to_use}' ****")
    # _log_message(local_registro_prepare_draw, "PREP_LOG", f"  app_data_ref: {type(app_data_ref)}, handlers_utils_ref recibido: {type(handlers_utils_ref)}")
    
    if not app_data_ref:
        with local_registro_prepare_draw: print("  ERROR CRÍTICO (_prepare_sociogram_draw): app_data_ref es None."); return
    
    context_prepare_draw = app_state.get('current_group_viewing_members')
    
    if not context_prepare_draw or not context_prepare_draw.get('school') or not context_prepare_draw.get('class_name'):
        with local_registro_prepare_draw: print("  ERROR: Falta contexto de institución/grupo (leyendo de 'current_group_viewing_members').")
        if isinstance(ui_sociogramma, dict):
            graph_widget_err_prep_draw = ui_sociogramma.get("graph_output")
            if graph_widget_err_prep_draw and isinstance(graph_widget_err_prep_draw, widgets.Output):
                with graph_widget_err_prep_draw: clear_output(wait=True); display(IPHTML("<p style='color:red;'>Error: Contexto de inst/grupo no disponible.</p>"))
        return
        
    institution_name_prepare = context_prepare_draw['school']
    group_name_prepare = context_prepare_draw['class_name']
    # _log_message(local_registro_prepare_draw, "PREP_LOG", f"  Contexto para sociograma: Institución='{institution_name_prepare}', Grupo='{group_name_prepare}'.")

    if isinstance(ui_sociogramma, dict): ui_sociogramma['_temp_registro_output_ref'] = local_registro_prepare_draw
    _update_participant_dropdown(app_state, ui_sociogramma, app_data_ref, handlers_utils_ref)
    _update_relations_checkboxes(app_state, ui_sociogramma, local_registro_prepare_draw, app_data_ref)
    if isinstance(ui_sociogramma, dict) and '_temp_registro_output_ref' in ui_sociogramma: del ui_sociogramma['_temp_registro_output_ref']

    selected_data_keys_list_prepare = []
    if ui_sociogramma and isinstance(ui_sociogramma, dict):
        checkbox_widgets_info_list_prepare = ui_sociogramma.get('_relations_checkbox_widgets', [])
        for cb_info_dict_prepare in checkbox_widgets_info_list_prepare:
            cb_widget_prepare = cb_info_dict_prepare.get('widget')
            if cb_widget_prepare and hasattr(cb_widget_prepare, 'value') and cb_widget_prepare.value == True:
                 data_key_cb_prepare = cb_info_dict_prepare.get('data_key')
                 if data_key_cb_prepare: selected_data_keys_list_prepare.append(data_key_cb_prepare)
    # _log_message(local_registro_prepare_draw, "PREP_LOG", f"  Data keys seleccionados para dibujar: {selected_data_keys_list_prepare}")

    node_gender_filter_val_prep = get_widget_value(ui_sociogramma, "gender_filter_radio", 'Todos')
    label_display_mode_val_prep = get_widget_value(ui_sociogramma, "label_display_dropdown", 'nombre_apellido')
    connection_gender_type_val_prep = get_widget_value(ui_sociogramma, "gender_links_radio", 'todas')
    active_members_filter_val_prep = get_widget_value(ui_sociogramma, "active_members_filter_checkbox", False)
    nominators_option_val_prep = get_widget_value(ui_sociogramma, "nominators_option_checkbox", True)
    received_color_val_prep = get_widget_value(ui_sociogramma, "received_color_checkbox", False)
    reciprocal_nodes_color_val_prep = get_widget_value(ui_sociogramma, "reciprocal_nodes_color_checkbox", False)
    style_reciprocal_val_prep = get_widget_value(ui_sociogramma, "reciprocal_links_style_checkbox", True)
    selected_participant_focus_val_prep = get_widget_value(ui_sociogramma, "participant_select_dropdown", None)
    connection_focus_mode_val_prep = get_widget_value(ui_sociogramma, "connection_focus_radio", 'all')
    if selected_participant_focus_val_prep is None and connection_focus_mode_val_prep != 'all':
        connection_focus_mode_val_prep = 'all'
        connection_focus_radio_widget_prep = ui_sociogramma.get("connection_focus_radio")
        if connection_focus_radio_widget_prep and connection_focus_radio_widget_prep.value != 'all': connection_focus_radio_widget_prep.value = 'all'
    highlight_mode_val_prep = get_widget_value(ui_sociogramma, "highlight_mode_radio", 'none')
    highlight_value_val_prep = get_widget_value(ui_sociogramma, "highlight_value_input", 1)

    # _log_message(local_registro_prepare_draw, "PREP_LOG", f"  Llamando a draw_sociogramma (engine) para {institution_name_prepare}/{group_name_prepare}")
    try:
        widget_instance_prep, legend_data_prep, graph_json_prep = draw_sociogramma(
            school_name=institution_name_prepare, class_name=group_name_prepare, app_data_ref=app_data_ref,
            node_gender_filter=node_gender_filter_val_prep, label_display_mode=label_display_mode_val_prep,
            selected_data_keys_from_checkboxes=selected_data_keys_list_prepare,
            connection_gender_type=connection_gender_type_val_prep, active_members_filter=active_members_filter_val_prep,
            nominators_option=nominators_option_val_prep, received_color_filter=received_color_val_prep,
            reciprocal_nodes_color_filter=reciprocal_nodes_color_val_prep, style_reciprocal_links=style_reciprocal_val_prep,
            selected_participant_focus=selected_participant_focus_val_prep, connection_focus_mode=connection_focus_mode_val_prep,
            ui_sociogramma_dict_ref=ui_sociogramma, registro_output=local_registro_prepare_draw,
            layout_to_use=layout_to_use, highlight_mode=highlight_mode_val_prep, highlight_value=highlight_value_val_prep
        )
        # _log_message(local_registro_prepare_draw, "PREP_LOG", f"(_prepare_sociogram_draw v1.11.0 - Inst/Grp/Miembro): Llamada a draw_sociogramma finalizada.")
    except Exception as e_draw_call_prepare_draw:
        _log_message(local_registro_prepare_draw, "PREP_LOG", f"  ERROR CRÍTICO (_prepare_sociogram_draw) al llamar a draw_sociogramma: {e_draw_call_prepare_draw}\n{traceback.format_exc(limit=2)}")
        if isinstance(ui_sociogramma, dict):
            graph_widget_err_prep_draw_final = ui_sociogramma.get("graph_output")
            if graph_widget_err_prep_draw_final and isinstance(graph_widget_err_prep_draw_final, widgets.Output):
                with graph_widget_err_prep_draw_final: clear_output(wait=True); display(IPHTML(f"<p style='color:red;'>Error al dibujar sociograma ({layout_to_use}): {e_draw_call_prepare_draw}</p>"))