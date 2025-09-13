# handlers_institutions.py (antes handlers_schools.py)
# (v17.1 - Cambiado "Escuela" a "Institución", ajustadas claves de app_state y parámetros.
#          Usa "Miembro" en logs y referencias a members_data)

# --- Importaciones ---
import sys
import collections
import traceback
import functools

from ipywidgets import widgets
from IPython.display import clear_output, display, HTML

import sociograma_data # Acceso directo a los datos (schools_data, members_data)
import handlers_csv_excel

_handlers_utils_institutions = globals().get('handlers_utils')
_handlers_groups_module = globals().get('handlers_groups')

# --- Handlers para Interfaz 1: "Tabla de Instituciones" (main_institutions) ---

def on_main_institution_select_change_handler(change, app_state, ui_main_institutions, registro_output,
                                         form_institution_vbox_ref=None):
    selected_institution_name = change.get('new')
    is_selection_valid = False
    if selected_institution_name and selected_institution_name in sociograma_data.schools_data:
        is_selection_valid = True

    if isinstance(ui_main_institutions, dict):
        if form_institution_vbox_ref and hasattr(form_institution_vbox_ref, 'layout') and form_institution_vbox_ref.layout.display != 'none':
            form_institution_vbox_ref.layout.display = 'none'
            # Logs informativos eliminados

        annotations_textarea_inst = ui_main_institutions.get("annotations")
        if annotations_textarea_inst:
            annotations_textarea_inst.value = sociograma_data.schools_data.get(selected_institution_name, "") if is_selection_valid else ""
            annotations_textarea_inst.disabled = not is_selection_valid

        ui_main_institutions.get("modifica_button", widgets.Button()).disabled = not is_selection_valid
        ui_main_institutions.get("elimina_button", widgets.Button()).disabled = not is_selection_valid
        ui_main_institutions.get("classi_button", widgets.Button()).disabled = not is_selection_valid
        ui_main_institutions.get("nueva_button", widgets.Button()).disabled = False
        ui_main_institutions.get("salir_button", widgets.Button()).disabled = False
        ui_main_institutions.get("csv_button", widgets.Button()).disabled = False
    elif registro_output:
        with registro_output: print("ERROR (on_main_institution_select): ui_main_institutions no es dict.")

def on_main_nueva_button_click_handler(b, app_state, ui_form_institution, switch_interface_func, registro_output):
    app_state['current_institution_editing'] = None
    if ui_form_institution and hasattr(ui_form_institution, 'layout'):
        form_institution_elements = getattr(ui_form_institution, '_ui_elements_ref', None)
        if not form_institution_elements or not isinstance(form_institution_elements, dict):
          with registro_output: print("  ERROR (main_nueva_button): _ui_elements_ref no encontrado en ui_form_institution VBox."); return

        title_label_fi_new = form_institution_elements.get("title_label")
        if title_label_fi_new: title_label_fi_new.value = "Nueva Institución"

        name_input_fi_new = form_institution_elements.get("name_input")
        if name_input_fi_new: name_input_fi_new.value = ""; name_input_fi_new.disabled = False
        annotations_fi_new = form_institution_elements.get("annotations_textarea")
        if annotations_fi_new: annotations_fi_new.value = ""
        add_hbox_fi_new = form_institution_elements.get("add_buttons_hbox")
        modify_hbox_fi_new = form_institution_elements.get("modify_buttons_hbox")
        if add_hbox_fi_new and hasattr(add_hbox_fi_new, 'layout'): add_hbox_fi_new.layout.display = 'flex'
        if modify_hbox_fi_new and hasattr(modify_hbox_fi_new, 'layout'): modify_hbox_fi_new.layout.display = 'none'
        ui_form_institution.layout.display = 'flex'
    else:
      with registro_output: print("ERROR (on_main_nueva_button): ui_form_institution (VBox) no es válido o no tiene layout.")

def on_main_modifica_button_handler(b, app_state, ui_main_institutions, ui_form_institution, switch_interface_func, registro_output):
    selected_institution_name_mod = ui_main_institutions.get("select").value if isinstance(ui_main_institutions, dict) and ui_main_institutions.get("select") else None

    if selected_institution_name_mod and selected_institution_name_mod in sociograma_data.schools_data:
        app_state['current_institution_editing'] = selected_institution_name_mod
        if ui_form_institution and hasattr(ui_form_institution, 'layout'):
            form_institution_elements_mod_ui = getattr(ui_form_institution, '_ui_elements_ref', None)
            if not form_institution_elements_mod_ui or not isinstance(form_institution_elements_mod_ui, dict):
              with registro_output: print("  ERROR (main_modifica_button): _ui_elements_ref no encontrado."); return
            
            title_label_fi_mod_ui = form_institution_elements_mod_ui.get("title_label")
            if title_label_fi_mod_ui: title_label_fi_mod_ui.value = f"Modificar Institución: {selected_institution_name_mod}"
            name_input_fi_mod_ui = form_institution_elements_mod_ui.get("name_input")
            if name_input_fi_mod_ui: name_input_fi_mod_ui.value = selected_institution_name_mod; name_input_fi_mod_ui.disabled = False
            annotations_fi_mod_ui = form_institution_elements_mod_ui.get("annotations_textarea")
            if annotations_fi_mod_ui: annotations_fi_mod_ui.value = sociograma_data.schools_data.get(selected_institution_name_mod, "")
            
            add_hbox_fi_mod_ui = form_institution_elements_mod_ui.get("add_buttons_hbox")
            modify_hbox_fi_mod_ui = form_institution_elements_mod_ui.get("modify_buttons_hbox")
            if add_hbox_fi_mod_ui and hasattr(add_hbox_fi_mod_ui, 'layout'): add_hbox_fi_mod_ui.layout.display = 'none'
            if modify_hbox_fi_mod_ui and hasattr(modify_hbox_fi_mod_ui, 'layout'): modify_hbox_fi_mod_ui.layout.display = 'flex'
            ui_form_institution.layout.display = 'flex'
        else:
          with registro_output: print("ERROR (on_main_modifica_button): ui_form_institution (VBox) no es válido.")

def on_main_elimina_button_handler(b, app_state, ui_main_institutions, registro_output,
                                   refresh_func=None, form_institution_vbox_ref=None):
    select_widget_inst_del = ui_main_institutions.get("select") if isinstance(ui_main_institutions, dict) else None
    institution_to_delete_val = select_widget_inst_del.value if select_widget_inst_del else None
    with registro_output:
        clear_output(wait=True)
        pass
    if form_institution_vbox_ref and hasattr(form_institution_vbox_ref, 'layout') and form_institution_vbox_ref.layout.display != 'none':
        form_institution_vbox_ref.layout.display = 'none'
    if institution_to_delete_val and institution_to_delete_val in sociograma_data.schools_data:
        try:
            del sociograma_data.schools_data[institution_to_delete_val]
            if institution_to_delete_val in sociograma_data.classes_data: del sociograma_data.classes_data[institution_to_delete_val]
            if institution_to_delete_val in sociograma_data.members_data: del sociograma_data.members_data[institution_to_delete_val]
            keys_to_delete_q_defs_inst = [k for k in sociograma_data.question_definitions if k[0] == institution_to_delete_val]
            for key_q_def_inst in keys_to_delete_q_defs_inst: del sociograma_data.question_definitions[key_q_def_inst]
            keys_to_delete_resp_inst = [k for k in sociograma_data.questionnaire_responses_data if k[0] == institution_to_delete_val]
            for key_resp_inst in keys_to_delete_resp_inst: del sociograma_data.questionnaire_responses_data[key_resp_inst]
            
            new_options_inst_del = sorted(list(sociograma_data.schools_data.keys()))
            new_selection_inst_del = new_options_inst_del[0] if new_options_inst_del else None
            if select_widget_inst_del:
                current_sel_before_refresh_inst_del = select_widget_inst_del.value
                select_widget_inst_del.options = new_options_inst_del
                if select_widget_inst_del.value != new_selection_inst_del:
                    select_widget_inst_del.value = new_selection_inst_del
                elif refresh_func and callable(refresh_func):
                    change_event_inst_del = {'name': 'value', 'old': current_sel_before_refresh_inst_del, 'new': new_selection_inst_del, 'owner': select_widget_inst_del, 'type': 'change'}
                    refresh_func(change_event_inst_del, app_state, ui_main_institutions, registro_output, form_institution_vbox_ref=form_institution_vbox_ref)
        except Exception as e_elim_inst_final:
          with registro_output: print(f"ERROR al eliminar la institución '{institution_to_delete_val}': {e_elim_inst_final}\n{traceback.format_exc()}")

def on_main_view_groups_button_handler(b, app_state, ui_main_institutions, 
                                        ui_groups,
                                        switch_interface_func, registro_output,
                                        group_refresh_func=None,
                                        form_institution_vbox_ref=None, 
                                        form_group_vbox_ref_on_entry=None):
    selected_institution_name_grp_view = ui_main_institutions.get("select").value if isinstance(ui_main_institutions, dict) and ui_main_institutions.get("select") else None
    with registro_output:
        clear_output(wait=True)
        pass
        
    if form_institution_vbox_ref and hasattr(form_institution_vbox_ref, 'layout') and form_institution_vbox_ref.layout.display != 'none':
        form_institution_vbox_ref.layout.display = 'none'
    if form_group_vbox_ref_on_entry and hasattr(form_group_vbox_ref_on_entry, 'layout') and form_group_vbox_ref_on_entry.layout.display != 'none':
        form_group_vbox_ref_on_entry.layout.display = 'none'
        
    if selected_institution_name_grp_view and selected_institution_name_grp_view in sociograma_data.schools_data:
        app_state['current_institution_viewing_groups'] = selected_institution_name_grp_view
        app_state['return_interface'] = 'main_institutions'
        
        if isinstance(ui_groups, dict):
            title_label_groups_view = ui_groups.get("title_label")
            if title_label_groups_view: title_label_groups_view.value = f"Tabla de Grupos: {selected_institution_name_grp_view}"
            
            institution_groups_list_view = sociograma_data.classes_data.get(selected_institution_name_grp_view, [])
            group_options_for_select_view = sorted([g.get('name') for g in institution_groups_list_view if g.get('name')])
            
            group_select_widget_groups_ui_view = ui_groups.get("select")
            if group_select_widget_groups_ui_view:
                current_group_sel_before_refresh_view = group_select_widget_groups_ui_view.value
                group_select_widget_groups_ui_view.options = group_options_for_select_view
                new_group_selection_on_entry_view = group_options_for_select_view[0] if group_options_for_select_view else None
                
                if group_select_widget_groups_ui_view.value != new_group_selection_on_entry_view:
                    group_select_widget_groups_ui_view.value = new_group_selection_on_entry_view
                elif group_refresh_func and callable(group_refresh_func):
                     change_event_group_entry_view = {'name': 'value', 'old': current_group_sel_before_refresh_view, 'new': new_group_selection_on_entry_view, 'owner': group_select_widget_groups_ui_view, 'type': 'change'}
                     try:
                         group_refresh_func(change_event_group_entry_view, app_state, ui_groups, registro_output, form_group_vbox_ref=form_group_vbox_ref_on_entry)
                     except Exception as e_group_refresh_entry_view:
                         with registro_output: print(f"ERROR al refrescar ui_groups al entrar: {e_group_refresh_entry_view}")
            
            nueva_button_groups_ui_view = ui_groups.get("nueva_button")
            if nueva_button_groups_ui_view: nueva_button_groups_ui_view.disabled = False
        else:
          with registro_output: print("ERROR (on_main_view_groups_button): ui_groups no es un diccionario."); return
        
        switch_interface_func('main_groups')

def on_main_csv_button_click_handler(b, app_state, ui_main_institutions, registro_output):
    csv_main_controls_container_inst = ui_main_institutions.get("csv_controls_main_vbox")
    if csv_main_controls_container_inst and hasattr(csv_main_controls_container_inst, 'layout'):
        is_currently_hidden_csv = csv_main_controls_container_inst.layout.display == 'none'
        new_display_status_csv_inst = 'flex' if is_currently_hidden_csv else 'none'
        csv_main_controls_container_inst.layout.display = new_display_status_csv_inst
    elif registro_output:
        with registro_output: print("  ERROR (on_main_csv_button_click): 'csv_controls_main_vbox' no encontrado.")

def on_process_csv_button_static_click_handler(b, app_state, ui_main_institutions_dict_ref, institution_refresh_func_ref, registro_output_ref):
    if hasattr(handlers_csv_excel, '_process_csv_from_content_path_static'):
        try:
            handlers_csv_excel._process_csv_from_content_path_static(b, app_state, ui_main_institutions_dict_ref, institution_refresh_func_ref, registro_output_ref)
        except Exception as e_call_csv_proc_inst:
            if registro_output_ref:
                with registro_output_ref: print(f"ERROR CRÍTICO (institutions.on_process_csv) llamando a handlers_csv_excel: {e_call_csv_proc_inst}\n{traceback.format_exc()}")
    else:
        if registro_output_ref: 
          with registro_output_ref: print("ERROR CRÍTICO: '_process_csv_from_content_path_static' no encontrado en handlers_csv_excel.")

def on_main_salir_button_handler(b, app_state, registro_output, form_institution_vbox_ref=None):
    with registro_output:
        clear_output(wait=True)
        pass
    if form_institution_vbox_ref and hasattr(form_institution_vbox_ref, 'layout') and form_institution_vbox_ref.layout.display != 'none':
        form_institution_vbox_ref.layout.display = 'none'
    app_main_container_exit = globals().get('app_main_display_container')
    if app_main_container_exit and hasattr(app_main_container_exit, 'children'):
        app_main_container_exit.children = []
    display(HTML("<h3>Aplicación Sociograma Finalizada.</h3><p>Puedes cerrar esta pestaña del navegador.</p>"))

# --- Handlers para Formulario "Actualización de Institución" (empotrado) ---
def on_form_institution_add_save_button_handler(b, app_state, ui_form_institution, ui_main_institutions, switch_interface_func, registro_output, institution_refresh_func=None):
    form_elements_add_inst = getattr(ui_form_institution, '_ui_elements_ref', None)
    if not form_elements_add_inst or not isinstance(form_elements_add_inst, dict):
      with registro_output: print("ERROR (form_add_save_inst): _ui_elements_ref no encontrado."); return
    new_institution_name_add = form_elements_add_inst.get("name_input").value.strip()
    annotations_add = form_elements_add_inst.get("annotations_textarea").value.strip()
    if not new_institution_name_add: 
      with registro_output: print("ERROR (form_add_save_inst): Nombre de institución vacío."); return
    if new_institution_name_add in sociograma_data.schools_data: 
      with registro_output: print(f"ERROR (form_add_save_inst): Institución '{new_institution_name_add}' ya existe."); return
    sociograma_data.schools_data[new_institution_name_add] = annotations_add
    sociograma_data.classes_data.setdefault(new_institution_name_add, [])
    sociograma_data.members_data.setdefault(new_institution_name_add, collections.OrderedDict())
    app_state['current_institution_editing'] = None
    if hasattr(ui_form_institution, 'layout'): ui_form_institution.layout.display = 'none'
    if isinstance(ui_main_institutions, dict) and ui_main_institutions.get("select") and callable(institution_refresh_func):
        select_widget_main_inst_add = ui_main_institutions.get("select")
        current_sel_b4_refresh_add_inst_form = select_widget_main_inst_add.value
        new_options_main_inst_add = sorted(list(sociograma_data.schools_data.keys()))
        select_widget_main_inst_add.options = new_options_main_inst_add
        value_to_set_add_inst_form = new_institution_name_add
        if new_institution_name_add not in new_options_main_inst_add: value_to_set_add_inst_form = new_options_main_inst_add[0] if new_options_main_inst_add else None
        if select_widget_main_inst_add.value != value_to_set_add_inst_form: select_widget_main_inst_add.value = value_to_set_add_inst_form
        else:
            change_event_add_inst_force_form = {'name': 'value', 'old': current_sel_b4_refresh_add_inst_form, 'new': value_to_set_add_inst_form, 'owner': select_widget_main_inst_add, 'type': 'change'}
            institution_refresh_func(change_event_add_inst_force_form, app_state, ui_main_institutions, registro_output, form_institution_vbox_ref=ui_form_institution)

def on_form_institution_modify_ok_button_handler(b, app_state, ui_form_institution, ui_main_institutions, switch_interface_func, registro_output, institution_refresh_func=None):
    form_elements_mod_inst = getattr(ui_form_institution, '_ui_elements_ref', None)
    if not form_elements_mod_inst or not isinstance(form_elements_mod_inst, dict):
      with registro_output: print("ERROR (form_modify_ok_inst): _ui_elements_ref no encontrado."); return
    original_institution_name_mod_ok = app_state.get('current_institution_editing')
    if not original_institution_name_mod_ok or original_institution_name_mod_ok not in sociograma_data.schools_data:
      with registro_output: print("ERROR (form_modify_ok_inst): No hay institución en edición o no existe."); return
    new_institution_name_mod_ok = form_elements_mod_inst.get("name_input").value.strip()
    new_annotations_mod_ok = form_elements_mod_inst.get("annotations_textarea").value.strip()
    if not new_institution_name_mod_ok: 
      with registro_output: print("ERROR (form_modify_ok_inst): Nombre de institución vacío."); return
    if new_institution_name_mod_ok != original_institution_name_mod_ok and new_institution_name_mod_ok in sociograma_data.schools_data:
      with registro_output: print(f"ERROR (form_modify_ok_inst): Ya existe institución con nombre '{new_institution_name_mod_ok}'."); return
    try:
        name_changed_mod_ok = (new_institution_name_mod_ok != original_institution_name_mod_ok)
        if name_changed_mod_ok:
            sociograma_data.schools_data[new_institution_name_mod_ok] = new_annotations_mod_ok; del sociograma_data.schools_data[original_institution_name_mod_ok]
            if original_institution_name_mod_ok in sociograma_data.classes_data: sociograma_data.classes_data[new_institution_name_mod_ok] = sociograma_data.classes_data.pop(original_institution_name_mod_ok)
            else: sociograma_data.classes_data.setdefault(new_institution_name_mod_ok, [])
            if original_institution_name_mod_ok in sociograma_data.members_data: sociograma_data.members_data[new_institution_name_mod_ok] = sociograma_data.members_data.pop(original_institution_name_mod_ok)
            else: sociograma_data.members_data.setdefault(new_institution_name_mod_ok, collections.OrderedDict())
            keys_to_migrate_q_defs_mod_ok = [k for k in list(sociograma_data.question_definitions.keys()) if k[0]==original_institution_name_mod_ok]
            for old_k_qd_mod in keys_to_migrate_q_defs_mod_ok: sociograma_data.question_definitions[(new_institution_name_mod_ok,)+old_k_qd_mod[1:]]=sociograma_data.question_definitions.pop(old_k_qd_mod)
            keys_to_migrate_resp_mod_ok = [k for k in list(sociograma_data.questionnaire_responses_data.keys()) if k[0]==original_institution_name_mod_ok]
            for old_k_resp_mod in keys_to_migrate_resp_mod_ok: sociograma_data.questionnaire_responses_data[(new_institution_name_mod_ok,)+old_k_resp_mod[1:]]=sociograma_data.questionnaire_responses_data.pop(old_k_resp_mod)
        else: sociograma_data.schools_data[original_institution_name_mod_ok] = new_annotations_mod_ok; 
        app_state['current_institution_editing'] = None;
        if hasattr(ui_form_institution, 'layout'): ui_form_institution.layout.display = 'none'
        if isinstance(ui_main_institutions, dict) and ui_main_institutions.get("select") and callable(institution_refresh_func):
            select_widget_main_inst_mod_ok = ui_main_institutions.get("select")
            current_sel_b4_refresh_mod_inst_ok = select_widget_main_inst_mod_ok.value
            new_options_main_inst_mod_ok = sorted(list(sociograma_data.schools_data.keys()))
            select_widget_main_inst_mod_ok.options = new_options_main_inst_mod_ok
            value_to_set_mod_inst_ok = new_institution_name_mod_ok
            if value_to_set_mod_inst_ok not in new_options_main_inst_mod_ok: value_to_set_mod_inst_ok = new_options_main_inst_mod_ok[0] if new_options_main_inst_mod_ok else None
            if select_widget_main_inst_mod_ok.value != value_to_set_mod_inst_ok: select_widget_main_inst_mod_ok.value = value_to_set_mod_inst_ok
            else:
                change_event_mod_inst_force_ok = {'name':'value','old':current_sel_b4_refresh_mod_inst_ok,'new':value_to_set_mod_inst_ok,'owner':select_widget_main_inst_mod_ok,'type':'change'}
                institution_refresh_func(change_event_mod_inst_force_ok,app_state,ui_main_institutions,registro_output,form_institution_vbox_ref=ui_form_institution)
    except Exception as e_mod_inst_critical_ok:
      with registro_output: print(f"ERROR CRÍTICO al modificar institución: {e_mod_inst_critical_ok}\n{traceback.format_exc(limit=2)}")

def on_form_institution_cancel_button_handler(b, app_state, ui_form_institution, switch_interface_func, registro_output, ui_main_institutions=None, institution_refresh_func=None):
    app_state['current_institution_editing'] = None
    if hasattr(ui_form_institution, 'layout'): ui_form_institution.layout.display = 'none'
    if ui_main_institutions and institution_refresh_func and callable(institution_refresh_func):
        select_widget_main_inst_cancel_form = ui_main_institutions.get("select") if isinstance(ui_main_institutions, dict) else None
        if select_widget_main_inst_cancel_form:
            current_selection_to_restore_cancel_form = select_widget_main_inst_cancel_form.value
            change_event_cancel_inst_form = {'name':'value','old':current_selection_to_restore_cancel_form,'new':current_selection_to_restore_cancel_form,'owner':select_widget_main_inst_cancel_form,'type':'change'}
            try: institution_refresh_func(change_event_cancel_inst_form, app_state, ui_main_institutions, registro_output, form_institution_vbox_ref=ui_form_institution)
            except Exception as e_refresh_cancel_inst_form_final: 
              with registro_output: print(f"  ERROR (form_cancel_inst): Al refrescar UI: {e_refresh_cancel_inst_form_final}")