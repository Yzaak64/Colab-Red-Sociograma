# handlers_sociogram.py
# (v2.0 - Usa "Institución"/"Grupo" y "Miembro" en logs y contexto PDF)

import functools
from ipywidgets import widgets, IntText
from IPython.display import clear_output, HTML as IPHTML
import traceback
import sys

# Importar funciones necesarias de sociogram_utils
try:
    from sociogram_utils import _prepare_sociogram_draw
except ImportError:
    print("ERROR CRÍTICO (handlers_sociogram EVENTOS v2.0): No se pudo importar _prepare_sociogram_draw de sociogram_utils.")
    _prepare_sociogram_draw = lambda *args, **kwargs: None
    ro_area_fallback_soc_util_final = globals().get('registro_output_area')
    if ro_area_fallback_soc_util_final and isinstance(ro_area_fallback_soc_util_final, widgets.Output):
        with ro_area_fallback_soc_util_final:
            print("ERROR CRÍTICO (handlers_sociogram EVENTOS v2.0): _prepare_sociogram_draw NO PUDO SER IMPORTADO.")

try:
    import pdf_generator
except ImportError:
    print("ERROR CRÍTICO (handlers_sociogram EVENTOS v2.0): No se pudo importar pdf_generator.")
    pdf_generator = None
    ro_area_fallback_soc_pdf_final = globals().get('registro_output_area')
    if ro_area_fallback_soc_pdf_final and isinstance(ro_area_fallback_soc_pdf_final, widgets.Output):
        with ro_area_fallback_soc_pdf_final:
            print("ERROR CRÍTICO (handlers_sociogram EVENTOS v2.0): pdf_generator NO PUDO SER IMPORTADO.")

# --- Handlers para la Interfaz de Sociograma ---

def on_sociogramma_redraw_button_handler(b, app_state, ui_sociogramma, registro_output, app_data_ref, handlers_utils_ref_param):
    if not callable(_prepare_sociogram_draw):
        if registro_output and isinstance(registro_output, widgets.Output):
            with registro_output: print("ERROR HNDL_SOC_EVENTS (redraw v2.0): _prepare_sociogram_draw no está disponible.")
        return
    
    # if registro_output and isinstance(registro_output, widgets.Output):
        # with registro_output:
            # print(f"DEBUG HNDL_SOC_EVENTS (redraw v2.0): Entrando para layout 'cose'.")
    _prepare_sociogram_draw(app_state, ui_sociogramma, registro_output,
                            layout_to_use='cose',
                            app_data_ref=app_data_ref,
                            handlers_utils_ref=handlers_utils_ref_param)

def on_sociogramma_circle_layout_button_handler(b, app_state, ui_sociogramma, registro_output, app_data_ref, handlers_utils_ref_param):
    if not callable(_prepare_sociogram_draw):
        if registro_output and isinstance(registro_output, widgets.Output):
            with registro_output: print("ERROR HNDL_SOC_EVENTS (circle_layout v2.0): _prepare_sociogram_draw no está disponible.")
        return

    # if registro_output and isinstance(registro_output, widgets.Output):
        # with registro_output:
            # print(f"DEBUG HNDL_SOC_EVENTS (circle_layout v2.0): Entrando para layout 'circle'.")
    try:
        _prepare_sociogram_draw(app_state, ui_sociogramma, registro_output,
                                layout_to_use='circle',
                                app_data_ref=app_data_ref,
                                handlers_utils_ref=handlers_utils_ref_param)
    except Exception as e_prep_call_circle_soc_final_v2:
        if registro_output and isinstance(registro_output, widgets.Output):
            with registro_output:
                print(f"  ERROR HNDL_SOC_EVENTS (circle_layout v2.0): Error DENTRO de _prepare_sociogram_draw: {e_prep_call_circle_soc_final_v2}\n{traceback.format_exc(limit=2)}")

def on_sociogramma_pdf_button_handler(b, app_state, ui_sociogramma, registro_output):
    if not registro_output or not isinstance(registro_output, widgets.Output):
        registro_output_fallback_pdf_soc_btn_v2 = globals().get('registro_output_area')
        if registro_output_fallback_pdf_soc_btn_v2 and isinstance(registro_output_fallback_pdf_soc_btn_v2, widgets.Output):
            registro_output = registro_output_fallback_pdf_soc_btn_v2
        else:
            print("ADVERTENCIA (on_sociogramma_pdf_button_handler): registro_output no válido. Usando Output() temporal.")
            registro_output = widgets.Output()

    with registro_output:
        # print(f"\nHANDLER (on_sociogramma_pdf_button_handler v2.0 - Inst/Grp/Miembro): Solicitando PDF...")
        
        context_pdf_soc_btn_v2 = app_state.get('current_group_viewing_members')
        if not context_pdf_soc_btn_v2 or not context_pdf_soc_btn_v2.get('school') or not context_pdf_soc_btn_v2.get('class_name'):
            print("  ERROR - PDF Sociograma: Falta contexto de institución/grupo.")
            return
            
        institution_name_pdf_soc_btn_v2 = context_pdf_soc_btn_v2['school']
        group_name_pdf_soc_btn_v2 = context_pdf_soc_btn_v2['class_name']

        graph_json_elements_for_pdf_soc_btn_v2 = ui_sociogramma.get('_last_graph_elements_json')
        legend_info_for_pdf_soc_btn_v2 = ui_sociogramma.get('_current_legend_info')
        original_layout_name_soc_btn_v2 = ui_sociogramma.get('_last_layout_used', 'cose')
        reciprocal_links_style_checkbox_widget_soc_btn_v2 = ui_sociogramma.get("reciprocal_links_style_checkbox")
        style_reciprocal_links_active_val_soc_btn_v2 = True
        if reciprocal_links_style_checkbox_widget_soc_btn_v2 and hasattr(reciprocal_links_style_checkbox_widget_soc_btn_v2, 'value'):
            style_reciprocal_links_active_val_soc_btn_v2 = reciprocal_links_style_checkbox_widget_soc_btn_v2.value
        
        is_valid_graph_data_soc_btn_v2 = False
        if isinstance(graph_json_elements_for_pdf_soc_btn_v2, dict):
            if graph_json_elements_for_pdf_soc_btn_v2.get('nodes') or graph_json_elements_for_pdf_soc_btn_v2.get('edges'):
                is_valid_graph_data_soc_btn_v2 = True
        
        if not is_valid_graph_data_soc_btn_v2:
            print("  ERROR - PDF Sociograma: No hay datos de grafo JSON válidos. No se puede generar PDF.")
            return
        
        graph_json_full_for_pdf_soc_btn_v2 = {'elements': graph_json_elements_for_pdf_soc_btn_v2 }

        if not legend_info_for_pdf_soc_btn_v2:
            print("  ADVERTENCIA - PDF Sociograma: No hay información de leyenda guardada.")

        if pdf_generator and hasattr(pdf_generator, 'generate_pdf_from_cytoscape_json'):
            try:
                pdf_generator.generate_pdf_from_cytoscape_json(
                    graph_json_full_for_pdf_soc_btn_v2,
                    legend_info_for_pdf_soc_btn_v2,
                    institution_name_pdf_soc_btn_v2, 
                    group_name_pdf_soc_btn_v2,    
                    registro_output,
                    layout_hint=original_layout_name_soc_btn_v2,
                    style_reciprocal_links_active_param=style_reciprocal_links_active_val_soc_btn_v2
                )
            except Exception as e_gen_pdf_json_soc_btn_v2:
                print(f"  ERROR - PDF Sociograma: Excepción al llamar a pdf_generator: {e_gen_pdf_json_soc_btn_v2}\n{traceback.format_exc(limit=3)}")
        else:
            print("  ERROR - PDF Sociograma: 'generate_pdf_from_cytoscape_json' no disponible en pdf_generator.")


def on_sociogramma_highlight_mode_change(change, app_state, ui_sociogramma, registro_output, app_data_ref, handlers_utils_ref_param):
    if not callable(_prepare_sociogram_draw):
        if registro_output and isinstance(registro_output, widgets.Output): print("ERROR HNDL_SOC_EVENTS (highlight_mode v2.0): _prepare_sociogram_draw no disponible."); return
    if not registro_output or not isinstance(registro_output, widgets.Output): registro_output = globals().get('registro_output_area', widgets.Output())
    new_mode_hl_soc_v2 = change.get('new', 'none')
    # with registro_output: print(f"\nHANDLER (sociogram_highlight_mode v2.0): Modo resaltado: '{new_mode_hl_soc_v2}'.")
    highlight_value_widget_hl_soc_v2 = ui_sociogramma.get("highlight_value_input")
    if highlight_value_widget_hl_soc_v2 and isinstance(highlight_value_widget_hl_soc_v2, widgets.IntText):
        if new_mode_hl_soc_v2 == 'none': highlight_value_widget_hl_soc_v2.disabled = True; highlight_value_widget_hl_soc_v2.description = 'Valor (N/A):'
        else: highlight_value_widget_hl_soc_v2.disabled = False;
        if new_mode_hl_soc_v2 == 'top_n': highlight_value_widget_hl_soc_v2.description = 'Top N:'
        elif new_mode_hl_soc_v2 == 'k_th': highlight_value_widget_hl_soc_v2.description = 'K-ésimo:'
    last_layout_hl_soc_v2 = ui_sociogramma.get('_last_layout_used', 'cose')
    # with registro_output: print(f"  Llamando a _prepare_sociogram_draw con layout '{last_layout_hl_soc_v2}'.")
    _prepare_sociogram_draw(app_state, ui_sociogramma, registro_output,
                            layout_to_use=last_layout_hl_soc_v2,
                            app_data_ref=app_data_ref,
                            handlers_utils_ref=handlers_utils_ref_param)

def on_sociogramma_filter_change_handler(change, app_state, ui_sociogramma, registro_output, app_data_ref, handlers_utils_ref_param):
    if not callable(_prepare_sociogram_draw):
        if registro_output and isinstance(registro_output, widgets.Output): print("ERROR HNDL_SOC_EVENTS (filter_change v2.0): _prepare_sociogram_draw no disponible."); return
    if not registro_output or not isinstance(registro_output, widgets.Output): registro_output = globals().get('registro_output_area', widgets.Output())
    
    widget_changed_filter_soc_v2 = change.owner
    widget_name_filter_soc_v2 = "Desconocido";
    if hasattr(widget_changed_filter_soc_v2, 'description') and widget_changed_filter_soc_v2.description: widget_name_filter_soc_v2 = widget_changed_filter_soc_v2.description
    elif hasattr(widget_changed_filter_soc_v2, 'name') and widget_changed_filter_soc_v2.name: widget_name_filter_soc_v2 = widget_changed_filter_soc_v2.name
    
    participant_dropdown_filter_soc_v2 = ui_sociogramma.get("participant_select_dropdown")
    connection_focus_radio_filter_soc_v2 = ui_sociogramma.get("connection_focus_radio")

    if widget_changed_filter_soc_v2 == participant_dropdown_filter_soc_v2 and connection_focus_radio_filter_soc_v2:
        is_participant_selected_filter_soc_v2 = (change.new is not None and change.new != '')
        connection_focus_radio_filter_soc_v2.disabled = not is_participant_selected_filter_soc_v2
        if not is_participant_selected_filter_soc_v2: connection_focus_radio_filter_soc_v2.value = 'all'
    
    # with registro_output: print(f"\nHANDLER (sociogram_filter_change v2.0): Filtro '{widget_name_filter_soc_v2}' cambió a '{change.new}'.")
    if widget_changed_filter_soc_v2 == ui_sociogramma.get("highlight_mode_radio"): return
    last_layout_filter_soc_v2 = ui_sociogramma.get('_last_layout_used', 'cose')
    # with registro_output: print(f"  Llamando a _prepare_sociogram_draw con layout '{last_layout_filter_soc_v2}'.")
    _prepare_sociogram_draw(app_state, ui_sociogramma, registro_output,
                            layout_to_use=last_layout_filter_soc_v2,
                            app_data_ref=app_data_ref,
                            handlers_utils_ref=handlers_utils_ref_param)
                               
def on_sociogramma_salir_button_handler(b, app_state, 
                                        ui_groups, 
                                        switch_interface_func, 
                                        registro_output,
                                        group_refresh_func=None, 
                                        ui_sociogramma_dict_ref_on_exit=None, 
                                        app_data_ref=None):
    if not registro_output or not isinstance(registro_output, widgets.Output):
        registro_output = globals().get('registro_output_area', widgets.Output())
    
    with registro_output: 
        clear_output(wait=True)
        # print("HANDLER (sociogram_salir v2.0 - Miembro): Saliendo de sociograma.")
        pass

    ui_to_clear_on_exit_soc_final_v2 = ui_sociogramma_dict_ref_on_exit if isinstance(ui_sociogramma_dict_ref_on_exit, dict) else globals().get('ui_sociogramma')
    if ui_to_clear_on_exit_soc_final_v2 and isinstance(ui_to_clear_on_exit_soc_final_v2, dict):
        def _reset_widget_value_soc_final_v2(widget_key, default_val, is_dd_opts=False):
            w_reset_v2 = ui_to_clear_on_exit_soc_final_v2.get(widget_key)
            if w_reset_v2:
                if is_dd_opts and hasattr(w_reset_v2,'options'): w_reset_v2.options=default_val; w_reset_v2.value=None
                elif hasattr(w_reset_v2,'value'): w_reset_v2.value=default_val
                if hasattr(w_reset_v2,'disabled') and widget_key in ["connection_focus_radio", "highlight_value_input"]: w_reset_v2.disabled=True
        
        _reset_widget_value_soc_final_v2("gender_filter_radio",'Todos')
        _reset_widget_value_soc_final_v2("label_display_dropdown",'nombre_apellido')
        _reset_widget_value_soc_final_v2("active_members_filter_checkbox",False)
        _reset_widget_value_soc_final_v2("nominators_option_checkbox",True)
        _reset_widget_value_soc_final_v2("received_color_checkbox",False)
        _reset_widget_value_soc_final_v2("reciprocal_nodes_color_checkbox",False)
        _reset_widget_value_soc_final_v2("reciprocal_links_style_checkbox",True)
        _reset_widget_value_soc_final_v2("gender_links_radio",'todas')
        _reset_widget_value_soc_final_v2("participant_select_dropdown",[('Todos (Grafo Completo)',None)],is_dd_opts=True)
        _reset_widget_value_soc_final_v2("connection_focus_radio",'all')
        _reset_widget_value_soc_final_v2("highlight_mode_radio",'none')
        _reset_widget_value_soc_final_v2("highlight_value_input",1)
        
        ui_to_clear_on_exit_soc_final_v2['_current_cytoscape_widget']=None
        ui_to_clear_on_exit_soc_final_v2['_current_legend_info']=None
        ui_to_clear_on_exit_soc_final_v2['_last_drawn_graph_G']=None
        ui_to_clear_on_exit_soc_final_v2['_last_graph_elements_json']=None
        
        if '_relations_checkbox_widgets' in ui_to_clear_on_exit_soc_final_v2 and isinstance(ui_to_clear_on_exit_soc_final_v2['_relations_checkbox_widgets'],list):
            for cb_info_exit_soc_final_v2 in ui_to_clear_on_exit_soc_final_v2['_relations_checkbox_widgets']:
                if isinstance(cb_info_exit_soc_final_v2,dict) and 'widget' in cb_info_exit_soc_final_v2 and hasattr(cb_info_exit_soc_final_v2['widget'],'value'):
                    cb_info_exit_soc_final_v2['widget'].value=True
        
        for out_key_iteration_var in ["graph_output","legend_output"]:
            output_widget_to_clear =ui_to_clear_on_exit_soc_final_v2.get(out_key_iteration_var)
            if output_widget_to_clear and isinstance(output_widget_to_clear,widgets.Output):
                with output_widget_to_clear: clear_output(wait=True)
        # with registro_output: print("  INFO (sociogram_salir): UI del sociograma reseteada.")
    else:
        with registro_output: print("  ADVERTENCIA (sociogram_salir): ui_sociogramma_dict_ref_on_exit no válido, no se reseteó UI.")

    return_interface_target_soc_exit_final_v2 = app_state.get('return_interface', 'main_groups')
    if return_interface_target_soc_exit_final_v2 != 'main_groups':
        with registro_output: print(f"  ADVERTENCIA (sociogram_salir): return_interface era '{return_interface_target_soc_exit_final_v2}', forzando a 'main_groups'.")
        return_interface_target_soc_exit_final_v2 = 'main_groups'
    app_state['return_interface'] = None

    if return_interface_target_soc_exit_final_v2 == 'main_groups':
        last_viewed_group_context_for_refresh_soc_final_v2 = app_state.get('current_group_viewing_members')
        current_institution_for_refresh_soc_exit_final_v2 = last_viewed_group_context_for_refresh_soc_final_v2.get('school') if last_viewed_group_context_for_refresh_soc_final_v2 else None

        if current_institution_for_refresh_soc_exit_final_v2 and ui_groups and isinstance(ui_groups, dict):
            select_widget_group_soc_exit_final_v2 = ui_groups.get("select")
            if select_widget_group_soc_exit_final_v2 and hasattr(select_widget_group_soc_exit_final_v2, 'options'):
                institution_groups_list_soc_exit_final_v2 = []
                if app_data_ref and hasattr(app_data_ref, 'classes_data'):
                    institution_groups_list_soc_exit_final_v2 = app_data_ref.classes_data.get(current_institution_for_refresh_soc_exit_final_v2, [])
                elif registro_output: 
                    with registro_output: print("  ERROR CRÍTICO (sociogram_salir): app_data_ref.classes_data no disponible para refrescar UI de grupos.")
                
                group_options_for_select_soc_exit_final_v2 = sorted([g.get('name') for g in institution_groups_list_soc_exit_final_v2 if g.get('name')])
                preferred_group_on_return_soc_exit_final_v2 = last_viewed_group_context_for_refresh_soc_final_v2.get('class_name') if last_viewed_group_context_for_refresh_soc_final_v2 else None
                current_value_in_select_soc_exit_final_v2 = select_widget_group_soc_exit_final_v2.value
                new_value_to_set_group_soc_exit_final_v2 = None

                if preferred_group_on_return_soc_exit_final_v2 and preferred_group_on_return_soc_exit_final_v2 in group_options_for_select_soc_exit_final_v2:
                    new_value_to_set_group_soc_exit_final_v2 = preferred_group_on_return_soc_exit_final_v2
                elif current_value_in_select_soc_exit_final_v2 and current_value_in_select_soc_exit_final_v2 in group_options_for_select_soc_exit_final_v2:
                    new_value_to_set_group_soc_exit_final_v2 = current_value_in_select_soc_exit_final_v2
                elif group_options_for_select_soc_exit_final_v2:
                    new_value_to_set_group_soc_exit_final_v2 = group_options_for_select_soc_exit_final_v2[0]
                
                select_widget_group_soc_exit_final_v2.options = group_options_for_select_soc_exit_final_v2
                
                if select_widget_group_soc_exit_final_v2.value != new_value_to_set_group_soc_exit_final_v2:
                    select_widget_group_soc_exit_final_v2.value = new_value_to_set_group_soc_exit_final_v2
                elif group_refresh_func and callable(group_refresh_func): 
                    # if registro_output: 
                        # with registro_output: print(f"  INFO (sociogram_salir): Forzando refresco de ui_groups para '{new_value_to_set_group_soc_exit_final_v2}'.")
                    change_event_data_exit_soc_final_v2 = {'name': 'value', 'old': new_value_to_set_group_soc_exit_final_v2, 'new': new_value_to_set_group_soc_exit_final_v2, 'owner': select_widget_group_soc_exit_final_v2, 'type': 'change'}
                    try:
                        form_group_vbox_for_refresh_exit_final_v2 = ui_groups.get("form_group_embedded_vbox_ref")
                        group_refresh_func(change_event_data_exit_soc_final_v2, app_state, ui_groups, registro_output, form_group_vbox_ref=form_group_vbox_for_refresh_exit_final_v2)
                    except Exception as e_refresh_force_exit_soc_final_v2: 
                        if registro_output: 
                            with registro_output: print(f"  ERROR (sociogram_salir) al forzar refresco de ui_groups: {e_refresh_force_exit_soc_final_v2}")
            elif registro_output: 
                with registro_output: print("  ADVERTENCIA (sociogram_salir): Select widget de grupos no encontrado o sin opciones para refrescar.")
        elif registro_output: 
            with registro_output: print("  ADVERTENCIA (sociogram_salir): No se pudo refrescar UI de grupos (institución actual, ui_groups o app_data_ref no válidos).")

    switch_interface_func(return_interface_target_soc_exit_final_v2)