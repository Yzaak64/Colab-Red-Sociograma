# handlers_groups.py (antes handlers_classes.py)
# (v16.0 - Cambios de "Clase/Escuela" a "Grupo/Institución" y "alumno" a "miembro")

# --- Importaciones Estándar de Python ---
import sys
import collections
import traceback
import io
import base64
import re
import datetime

# --- Importaciones de ipywidgets y IPython.display ---
from ipywidgets import widgets, VBox, HBox, Label, Text, Textarea, Select, Button, Output, Layout, HTML, Checkbox
from IPython.display import clear_output, display, HTML as IPHTML

# --- Importaciones de Módulos Personalizados ---
import sociograma_data
from sociograma_data import (
    classes_data,
    members_data, # CAMBIO: de students_data a members_data
    schools_data,
    questionnaire_responses_data,
    get_class_question_definitions,
    question_definitions,
    regenerate_relationship_maps_for_class
)

_utils_ref_hg = globals().get('handlers_utils')

# --- Handlers para la Interfaz "Tabla de Grupos" (main_groups) ---

# --- BLOQUE 1: on_groups_select_change_handler ---
def on_groups_select_change_handler(change, app_state, ui_groups, registro_output,
                                     form_group_vbox_ref=None):
    # with registro_output:
        # new_value = change.get('new', 'N/A')
        # print(f"HANDLER (groups v16.0): on_groups_select_change_handler, nuevo grupo: {new_value}")

    selected_group_name = change.get('new')
    institution_name = app_state.get('current_institution_viewing_groups')
    is_selection_valid = False
    group_info = None

    if institution_name and selected_group_name and institution_name in classes_data:
        institution_groups = classes_data.get(institution_name, [])
        group_info = next((g for g in institution_groups if g.get('name') == selected_group_name), None)
    # elif registro_output and institution_name and selected_group_name:
        # with registro_output: print(f"  INFO (groups_select): Grupo '{selected_group_name}' no encontrado en datos de institución '{institution_name}'.")

    if isinstance(ui_groups, dict):
        if form_group_vbox_ref and hasattr(form_group_vbox_ref, 'layout') and form_group_vbox_ref.layout.display != 'none':
            form_group_vbox_ref.layout.display = 'none'
            # if registro_output:
                # with registro_output: print("  INFO (groups_select): Formulario de grupo empotrado ocultado por cambio de selección.")
        
        current_handlers_utils_select_grp = _utils_ref_hg or globals().get('handlers_utils')
        if group_info:
            ui_groups.get("coord_text", widgets.Text()).value = group_info.get('coordinator', '')
            ui_groups.get("ins2_text", widgets.Text()).value = group_info.get('ins2', '')
            ui_groups.get("ins3_text", widgets.Text()).value = group_info.get('ins3', '')
            ui_groups.get("sostegno_text", widgets.Text()).value = group_info.get('sostegno', '')
            ui_groups.get("annotations_textarea", widgets.Textarea()).value = group_info.get('annotations', '')
            is_selection_valid = True
        else:
            if current_handlers_utils_select_grp and hasattr(current_handlers_utils_select_grp, 'clear_class_details_fields'):
                current_handlers_utils_select_grp.clear_class_details_fields(ui_groups)
            # elif registro_output:
                # with registro_output: print("  ADVERTENCIA (groups_select): handlers_utils.clear_class_details_fields no disponible.")
            # if selected_group_name and registro_output:
                 # with registro_output: print(f"  Advertencia (groups_select): Detalles no encontrados para el grupo '{selected_group_name}'.")

        ui_groups.get("modifica_button", widgets.Button()).disabled = not is_selection_valid
        ui_groups.get("elimina_button", widgets.Button()).disabled = not is_selection_valid
        ui_groups.get("alunni_button", widgets.Button()).disabled = not is_selection_valid
        ui_groups.get("sociogramma_button", widgets.Button()).disabled = not is_selection_valid
        ui_groups.get("main_report_button", widgets.Button()).disabled = not is_selection_valid
        ui_groups.get("nueva_button", widgets.Button()).disabled = not bool(institution_name)
        
        report_options_hbox = ui_groups.get("report_options_hbox")
        if report_options_hbox and hasattr(report_options_hbox, 'layout'):
            if not is_selection_valid:
                report_options_hbox.layout.display = 'none'
        
        diana_controls_vbox = ui_groups.get("diana_controls_vbox")
        if diana_controls_vbox and hasattr(diana_controls_vbox, 'layout'):
            diana_controls_vbox.layout.display = 'none'

    elif registro_output:
        with registro_output: print("  ERROR (on_groups_select_change): ui_groups no es un diccionario válido.")
# --- FIN DEL BLOQUE 1 ---
# --- BLOQUE 2: on_groups_nueva_button_handler, on_groups_modifica_button_handler ---
def on_groups_nueva_button_handler(b, app_state, ui_form_group, switch_interface_func, registro_output):
    # with registro_output:
        # print("HANDLER (groups v16.0): on_groups_nueva_button_handler")
    
    institution_name = app_state.get('current_institution_viewing_groups')
    if not institution_name:
        with registro_output: print("  ERROR (groups_nueva): No hay institución seleccionada para añadir un grupo."); return
        
    app_state['current_group_editing'] = None
    
    if ui_form_group and hasattr(ui_form_group, 'layout'):
        form_group_elements = getattr(ui_form_group, '_ui_elements_ref', None)
        if not form_group_elements or not isinstance(form_group_elements, dict):
            with registro_output: print("  ERROR (groups_nueva): _ui_elements_ref no encontrado en ui_form_group."); return
        
        title_widget_fg = form_group_elements.get('title_label')
        institution_widget_fg = form_group_elements.get('school_text') 
        
        if title_widget_fg: title_widget_fg.value = f"Nuevo Grupo en {institution_name}"
        if institution_widget_fg: institution_widget_fg.value = institution_name
        
        for key in ["name_input", "coord_input", "ins2_input", "ins3_input", "sost_input", "annot_textarea"]:
            widget = form_group_elements.get(key)
            if widget: widget.value = ""
            if hasattr(widget, 'disabled'): widget.disabled = False 
            
        add_hbox_fg = form_group_elements.get("add_buttons_hbox")
        modify_hbox_fg = form_group_elements.get("modify_buttons_hbox")
        if add_hbox_fg and hasattr(add_hbox_fg,'layout'): add_hbox_fg.layout.display = 'flex'
        if modify_hbox_fg and hasattr(modify_hbox_fg,'layout'): modify_hbox_fg.layout.display = 'none'
        
        ui_form_group.layout.display = 'flex'
        # with registro_output: print("  INFO (groups_nueva): Formulario de grupo (empotrado) preparado para NUEVO y visible.")
    else:
        with registro_output: print("  ERROR (groups_nueva): ui_form_group (VBox del formulario) no es válido o no tiene layout.")

def on_groups_modifica_button_handler(b, app_state, ui_groups, ui_form_group, switch_interface_func, registro_output):
    select_widget = ui_groups.get("select") if isinstance(ui_groups, dict) else None
    selected_group_name = select_widget.value if select_widget else None
    institution_name = app_state.get('current_institution_viewing_groups')
    
    # with registro_output:
        # print(f"HANDLER (groups v16.0): on_groups_modifica_button_handler para '{selected_group_name}' en '{institution_name}'")
    
    if institution_name and selected_group_name and institution_name in classes_data:
        institution_groups_list_mod = classes_data.get(institution_name, [])
        group_info_mod = next((g for g in institution_groups_list_mod if g.get('name') == selected_group_name), None)
        
        if group_info_mod:
            app_state['current_group_editing'] = {
                'institution': institution_name,
                'group_name': selected_group_name,
                'original_data': group_info_mod.copy()
            }
            
            if ui_form_group and hasattr(ui_form_group, 'layout'):
                form_group_elements_mod = getattr(ui_form_group, '_ui_elements_ref', None)
                if not form_group_elements_mod or not isinstance(form_group_elements_mod, dict):
                    with registro_output: print("  ERROR (groups_modifica): _ui_elements_ref no encontrado en ui_form_group."); return
                
                title_fg_mod = form_group_elements_mod.get('title_label')
                institution_txt_fg_mod = form_group_elements_mod.get('school_text')
                
                if title_fg_mod: title_fg_mod.value = f"Modificar Grupo: {selected_group_name} ({institution_name})"
                if institution_txt_fg_mod: institution_txt_fg_mod.value = institution_name
                
                form_group_elements_mod.get("name_input", widgets.Text()).value = group_info_mod.get("name", "")
                form_group_elements_mod.get("coord_input", widgets.Text()).value = group_info_mod.get("coordinator", "")
                form_group_elements_mod.get("ins2_input", widgets.Text()).value = group_info_mod.get("ins2", "")
                form_group_elements_mod.get("ins3_input", widgets.Text()).value = group_info_mod.get("ins3", "")
                form_group_elements_mod.get("sost_input", widgets.Text()).value = group_info_mod.get("sostegno", "")
                form_group_elements_mod.get("annot_textarea", widgets.Textarea()).value = group_info_mod.get("annotations", "")

                for key_enable in ["name_input", "coord_input", "ins2_input", "ins3_input", "sost_input", "annot_textarea"]:
                    widget_enable = form_group_elements_mod.get(key_enable)
                    if hasattr(widget_enable, 'disabled'): widget_enable.disabled = False
                
                add_hbox_fgm = form_group_elements_mod.get("add_buttons_hbox")
                modify_hbox_fgm = form_group_elements_mod.get("modify_buttons_hbox")
                if add_hbox_fgm and hasattr(add_hbox_fgm,'layout'): add_hbox_fgm.layout.display = 'none'
                if modify_hbox_fgm and hasattr(modify_hbox_fgm,'layout'): modify_hbox_fgm.layout.display = 'flex'
                
                ui_form_group.layout.display = 'flex'
                # with registro_output: print("  INFO (groups_modifica): Formulario de grupo (empotrado) preparado para MODIFICAR y visible.")
            else:
              with registro_output: print("  ERROR (groups_modifica): ui_form_group (VBox del formulario) no es válido o no tiene layout.")
        else:
          with registro_output: print(f"  ERROR (groups_modifica): Datos no encontrados para el grupo '{selected_group_name}'.")
    else:
      with registro_output: print("  ERROR (groups_modifica): No hay grupo seleccionado, o institución no seleccionada/encontrada.")
# --- FIN DEL BLOQUE 2 ---
# --- BLOQUE 3: Handlers del Formulario de Grupo (form_group) ---
def on_form_group_add_save_handler(b, app_state, ui_form_group, ui_groups, switch_interface_func, registro_output, group_refresh_func=None):
    # with registro_output: print("HANDLER (groups v16.0): on_form_group_add_save_handler")
    
    form_elements = getattr(ui_form_group, '_ui_elements_ref', None)
    if not form_elements or not isinstance(form_elements, dict):
        with registro_output: print("  ERROR (form_add_save_grp): _ui_elements_ref no encontrado en ui_form_group."); return

    institution_name_form = app_state.get('current_institution_viewing_groups')
    if not institution_name_form:
      with registro_output: print("  ERROR (form_add_save_grp): No hay institución activa para añadir el grupo."); return
    
    new_group_name_form = form_elements.get("name_input").value.strip()
    if not new_group_name_form:
      with registro_output: print("  ERROR (form_add_save_grp): El nombre del grupo no puede estar vacío."); return

    existing_groups_in_institution = classes_data.get(institution_name_form, [])
    if any(g.get('name') == new_group_name_form for g in existing_groups_in_institution):
        with registro_output: print(f"  ERROR (form_add_save_grp): El grupo '{new_group_name_form}' ya existe en esta institución."); return

    new_group_data_dict = {
        "name": new_group_name_form,
        "coordinator": form_elements.get("coord_input").value.strip(),
        "ins2": form_elements.get("ins2_input").value.strip(),
        "ins3": form_elements.get("ins3_input").value.strip(),
        "sostegno": form_elements.get("sost_input").value.strip(),
        "annotations": form_elements.get("annot_textarea").value.strip()
    }
    try:
        classes_data.setdefault(institution_name_form, []).append(new_group_data_dict)
        members_data.setdefault(institution_name_form, collections.OrderedDict()).setdefault(new_group_name_form, [])
        get_class_question_definitions(institution_name_form, new_group_name_form)

        # with registro_output: print(f"  ÉXITO (form_add_save_grp): Grupo '{new_group_name_form}' añadido a la institución '{institution_name_form}'.")
        app_state['current_group_editing'] = None
        
        if hasattr(ui_form_group, 'layout'):
            ui_form_group.layout.display = 'none'
            # with registro_output: print("  INFO (form_add_save_grp): Formulario de grupo ocultado.")

        if ui_groups and group_refresh_func and callable(group_refresh_func):
            select_grp_widget_form = ui_groups.get("select")
            if select_grp_widget_form:
                current_group_options_after_add = sorted([g.get('name') for g in classes_data.get(institution_name_form, []) if g.get('name')])
                current_selection_before_refresh_grp = select_grp_widget_form.value
                select_grp_widget_form.options = current_group_options_after_add
                
                value_to_set_grp = new_group_name_form
                if new_group_name_form not in current_group_options_after_add:
                    value_to_set_grp = current_group_options_after_add[0] if current_group_options_after_add else None
                
                if select_grp_widget_form.value != value_to_set_grp:
                    select_grp_widget_form.value = value_to_set_grp
                else:
                    change_event_grp_add = {'name': 'value', 'old': current_selection_before_refresh_grp, 'new': value_to_set_grp, 'owner': select_grp_widget_form, 'type': 'change'}
                    group_refresh_func(change_event_grp_add, app_state, ui_groups, registro_output, form_group_vbox_ref=ui_form_group)
                # with registro_output: print("  INFO (form_add_save_grp): Lista de grupos en ui_groups refrescada.")
        
    except Exception as e_save_group_form:
      with registro_output: print(f"  ERROR al guardar el nuevo grupo: {e_save_group_form}\n{traceback.format_exc(limit=2)}")


def on_form_group_modify_save_handler(b, app_state, ui_form_group, ui_groups, switch_interface_func, registro_output, group_refresh_func=None):
    # with registro_output: print("HANDLER (groups v16.0): on_form_group_modify_save_handler")
    
    form_elements = getattr(ui_form_group, '_ui_elements_ref', None)
    if not form_elements or not isinstance(form_elements, dict):
        with registro_output: print("  ERROR (form_modify_save_grp): _ui_elements_ref no encontrado."); return

    editing_context_form_grp = app_state.get('current_group_editing')
    if not editing_context_form_grp or not all(k in editing_context_form_grp for k in ['institution', 'group_name']):
        with registro_output: print("  ERROR (form_modify_save_grp): Falta contexto de edición para el grupo."); return

    institution_form_modify_grp = editing_context_form_grp['institution']
    original_group_name_form_modify_grp = editing_context_form_grp['group_name']

    new_name_form_modify_grp = form_elements.get("name_input").value.strip()
    if not new_name_form_modify_grp:
      with registro_output: print("  ERROR (form_modify_save_grp): El nombre del grupo no puede estar vacío."); return

    updated_data_form_modify_grp = {
        "name": new_name_form_modify_grp,
        "coordinator": form_elements.get("coord_input").value.strip(),
        "ins2": form_elements.get("ins2_input").value.strip(),
        "ins3": form_elements.get("ins3_input").value.strip(),
        "sostegno": form_elements.get("sost_input").value.strip(),
        "annotations": form_elements.get("annot_textarea").value.strip()
    }
    name_changed_form_modify_grp = (new_name_form_modify_grp != original_group_name_form_modify_grp)
    if name_changed_form_modify_grp:
        existing_groups_in_institution_form_modify_grp = classes_data.get(institution_form_modify_grp, [])
        if any(g.get('name') == new_name_form_modify_grp for g in existing_groups_in_institution_form_modify_grp if g.get('name') != original_group_name_form_modify_grp):
             with registro_output: print(f"  ERROR (form_modify_save_grp): Un grupo con el nuevo nombre '{new_name_form_modify_grp}' ya existe en esta institución."); return
    try:
        institution_groups_list_form_modify_grp = classes_data.get(institution_form_modify_grp)
        if institution_groups_list_form_modify_grp is None: raise ValueError(f"Institución '{institution_form_modify_grp}' no encontrada en classes_data.")

        group_found_for_modify_form = False
        for i, grp_dict_modify_form in enumerate(institution_groups_list_form_modify_grp):
            if grp_dict_modify_form.get('name') == original_group_name_form_modify_grp:
                institution_groups_list_form_modify_grp[i].update(updated_data_form_modify_grp)
                group_found_for_modify_form = True; break
        if not group_found_for_modify_form: raise ValueError(f"Grupo original '{original_group_name_form_modify_grp}' no encontrado para modificar.")

        if name_changed_form_modify_grp:
            if institution_form_modify_grp in members_data and original_group_name_form_modify_grp in members_data[institution_form_modify_grp]:
                 members_data[institution_form_modify_grp][new_name_form_modify_grp] = members_data[institution_form_modify_grp].pop(original_group_name_form_modify_grp)
            
            keys_to_update_resp_form_modify_grp = [k for k in questionnaire_responses_data if k[0] == institution_form_modify_grp and k[1] == original_group_name_form_modify_grp]
            for old_key_resp_form_modify_grp in keys_to_update_resp_form_modify_grp:
                 value_resp_form_modify_grp = questionnaire_responses_data.pop(old_key_resp_form_modify_grp)
                 new_key_resp_form_modify_grp = (institution_form_modify_grp, new_name_form_modify_grp, old_key_resp_form_modify_grp[2])
                 questionnaire_responses_data[new_key_resp_form_modify_grp] = value_resp_form_modify_grp
            
            old_q_def_key_form_modify_grp = (institution_form_modify_grp, original_group_name_form_modify_grp)
            if old_q_def_key_form_modify_grp in question_definitions:
                q_defs_content_form_modify_grp = question_definitions.pop(old_q_def_key_form_modify_grp)
                new_q_def_key_form_modify_grp = (institution_form_modify_grp, new_name_form_modify_grp)
                question_definitions[new_q_def_key_form_modify_grp] = q_defs_content_form_modify_grp

        # with registro_output: print(f"  ÉXITO (form_modify_save_grp): Grupo '{new_name_form_modify_grp}' actualizado en institución '{institution_form_modify_grp}'.")
        app_state['current_group_editing'] = None
        
        if hasattr(ui_form_group, 'layout'):
            ui_form_group.layout.display = 'none'
            # with registro_output: print("  INFO (form_modify_save_grp): Formulario de grupo ocultado.")

        if ui_groups and isinstance(ui_groups, dict) and group_refresh_func and callable(group_refresh_func):
            select_grp_widget_form_modify_grp = ui_groups.get("select")
            if select_grp_widget_form_modify_grp:
                current_sel_before_refresh_mod_grp_form = select_grp_widget_form_modify_grp.value
                current_group_options_after_modify_form = sorted([g.get('name') for g in classes_data.get(institution_form_modify_grp, []) if g.get('name')])
                select_grp_widget_form_modify_grp.options = current_group_options_after_modify_form
                
                value_to_set_mod_grp_form = new_name_form_modify_grp
                if new_name_form_modify_grp not in current_group_options_after_modify_form:
                     value_to_set_mod_grp_form = current_group_options_after_modify_form[0] if current_group_options_after_modify_form else None
                
                if select_grp_widget_form_modify_grp.value != value_to_set_mod_grp_form:
                    select_grp_widget_form_modify_grp.value = value_to_set_mod_grp_form
                else: 
                    change_event_mod_grp_form = {'name': 'value', 'old': current_sel_before_refresh_mod_grp_form, 'new': value_to_set_mod_grp_form, 'owner': select_grp_widget_form_modify_grp, 'type': 'change'}
                    group_refresh_func(change_event_mod_grp_form, app_state, ui_groups, registro_output, form_group_vbox_ref=ui_form_group)
                # with registro_output: print("  INFO (form_modify_save_grp): Lista de grupos en ui_groups refrescada.")
    except Exception as e_modify_group_form:
      with registro_output: print(f"  ERROR al actualizar el grupo: {e_modify_group_form}\n{traceback.format_exc(limit=2)}")


def on_form_group_cancel_handler(b, app_state, ui_form_group, switch_interface_func, registro_output, ui_groups=None, group_refresh_func=None):
    # with registro_output:
        # print("HANDLER (groups v16.0): on_form_group_cancel_handler")

    app_state['current_group_editing'] = None
    
    if hasattr(ui_form_group, 'layout'):
        ui_form_group.layout.display = 'none'
        # with registro_output: print("  INFO (form_cancel_grp): Formulario de grupo ocultado.")

    if ui_groups and isinstance(ui_groups, dict) and group_refresh_func and callable(group_refresh_func):
        select_grp_widget_on_cancel_form = ui_groups.get("select")
        if select_grp_widget_on_cancel_form:
            current_selection_to_restore_grp_form = select_grp_widget_on_cancel_form.value
            
            change_event_cancel_grp_form = {'name': 'value', 'old': current_selection_to_restore_grp_form, 'new': current_selection_to_restore_grp_form, 'owner': select_grp_widget_on_cancel_form, 'type': 'change'}
            try: 
                group_refresh_func(change_event_cancel_grp_form, app_state, ui_groups, registro_output, form_group_vbox_ref=ui_form_group)
                # with registro_output: print("  INFO (form_cancel_grp): Detalles de grupo en ui_groups refrescados.")
            except Exception as e_refresh_cancel_grp_form: 
                with registro_output: print(f"  ERROR al refrescar UI de grupos al cancelar form: {e_refresh_cancel_grp_form}")
# --- FIN DEL BLOQUE 3 ---
# --- BLOQUE 4: on_groups_elimina_button_handler ---
def on_groups_elimina_button_handler(b, app_state, ui_groups, registro_output,
                                      refresh_func=None, form_group_vbox_ref=None):
    institution_name = app_state.get('current_institution_viewing_groups')
    select_widget = ui_groups.get("select") if isinstance(ui_groups, dict) else None
    group_name_to_delete = select_widget.value if select_widget else None

    with registro_output:
        clear_output(wait=True)
        # print(f"HANDLER (groups v16.0): on_groups_elimina_button_handler para '{group_name_to_delete}' de institución '{institution_name}'")
        pass

    if form_group_vbox_ref and hasattr(form_group_vbox_ref, 'layout') and form_group_vbox_ref.layout.display != 'none':
        form_group_vbox_ref.layout.display = 'none'
        # with registro_output: print("  INFO (groups_elimina): Formulario de grupo empotrado ocultado.")

    if institution_name and group_name_to_delete:
        try:
            deleted_items_count = 0
            if institution_name in classes_data:
                original_length = len(classes_data[institution_name])
                classes_data[institution_name] = [g for g in classes_data[institution_name] if g.get('name') != group_name_to_delete]
                if len(classes_data[institution_name]) < original_length:
                    deleted_items_count +=1
            
            if institution_name in members_data and group_name_to_delete in members_data.get(institution_name, {}):
                del members_data[institution_name][group_name_to_delete]
                deleted_items_count +=1

            keys_to_delete_resp_grp = [k for k in questionnaire_responses_data if k[0] == institution_name and k[1] == group_name_to_delete]
            if keys_to_delete_resp_grp:
                 for key_resp_grp in keys_to_delete_resp_grp:
                     del questionnaire_responses_data[key_resp_grp]
                 deleted_items_count += len(keys_to_delete_resp_grp)

            group_q_def_key_del = (institution_name, group_name_to_delete)
            if group_q_def_key_del in question_definitions:
                 del question_definitions[group_q_def_key_del]
                 deleted_items_count +=1
                 # with registro_output: print(f"  INFO (groups_elimina): Definiciones de preguntas para '{group_q_def_key_del}' eliminadas.")

            if deleted_items_count > 0:
                 # with registro_output: print(f"  ÉXITO: Grupo '{group_name_to_delete}' y sus datos asociados han sido eliminados de la institución '{institution_name}'.")
                 
                 current_group_options_display_del = sorted([g.get('name') for g in classes_data.get(institution_name, []) if g.get('name')]) if institution_name in classes_data else []
                 new_selection_after_delete_grp = None
                 if select_widget:
                     current_sel_before_refresh_del_grp_ui = select_widget.value
                     select_widget.options = current_group_options_display_del
                     if current_group_options_display_del:
                         new_selection_after_delete_grp = current_group_options_display_del[0]
                         select_widget.value = new_selection_after_delete_grp
                     else:
                         select_widget.value = None
                 
                 if refresh_func and callable(refresh_func) and \
                    (not select_widget or select_widget.value == new_selection_after_delete_grp):
                     change_event_del_grp_ui = {'name': 'value', 'old': group_name_to_delete, 'new': new_selection_after_delete_grp, 'owner': select_widget, 'type': 'change'}
                     refresh_func(change_event_del_grp_ui, app_state, ui_groups, registro_output, form_group_vbox_ref=form_group_vbox_ref)
            else:
              with registro_output: print(f"  INFO (groups_elimina): Grupo '{group_name_to_delete}' no encontrado o no tenía datos asociados para eliminar en la institución '{institution_name}'.")
        except Exception as e_elim_grp_fatal:
          with registro_output: print(f"  ERROR al eliminar el grupo '{group_name_to_delete}': {e_elim_grp_fatal}\n{traceback.format_exc(limit=2)}")
    else:
      with registro_output: print("  INFO (groups_elimina): Por favor, seleccione una institución y un grupo para eliminar.")
# --- FIN DEL BLOQUE 4 ---
# --- BLOQUE 5: on_groups_alunni_button_handler (ahora on_groups_members_button_handler) ---
def on_groups_members_button_handler(b, app_state, ui_groups, ui_members, switch_interface_func, registro_output,
                                     member_refresh_func=None, form_group_vbox_ref=None):
    institution_name = app_state.get('current_institution_viewing_groups')
    select_widget_group = ui_groups.get("select") if isinstance(ui_groups, dict) else None
    group_name = select_widget_group.value if select_widget_group else None

    with registro_output:
        clear_output(wait=True)
        # print(f"HANDLER (groups v16.0): on_groups_members_button_handler para grupo '{group_name}' en institución '{institution_name}'")
        pass

    if form_group_vbox_ref and hasattr(form_group_vbox_ref, 'layout') and form_group_vbox_ref.layout.display != 'none':
        form_group_vbox_ref.layout.display = 'none'
        # with registro_output: print("  INFO (groups_members): Formulario de grupo empotrado ocultado.")

    if institution_name and group_name and \
       institution_name in members_data and group_name in members_data.get(institution_name, {}):
        
        app_state['current_group_viewing_members'] = {'school': institution_name, 'class_name': group_name}
        app_state['return_interface'] = 'main_groups'

        if isinstance(ui_members, dict):
            title_label_mem_ui = ui_members.get("title_label")
            if title_label_mem_ui:
                title_label_mem_ui.value = f"Tabla de Miembros: {group_name} ({institution_name})"
            
            group_members_list_data_val = members_data[institution_name].get(group_name, [])
            group_members_list_data_ordenada_val = sorted(
                group_members_list_data_val,
                key=lambda m_sort_val: (
                    str(m_sort_val.get('nome', '')).strip().title(),
                    str(m_sort_val.get('cognome', '')).strip().title()
                )
            )
            
            member_options_display_val = []
            current_utils_for_members_grp_val = _utils_ref_hg or globals().get('handlers_utils')
            if current_utils_for_members_grp_val and hasattr(current_utils_for_members_grp_val, 'generar_opciones_dropdown_miembros_main_select'):
                member_options_display_val = current_utils_for_members_grp_val.generar_opciones_dropdown_miembros_main_select(group_members_list_data_ordenada_val)
            else:
                with registro_output: print("  ERROR CRÍTICO (members_btn_grp): generar_opciones_dropdown_miembros_main_select no disponible en handlers_utils.")
                for m_fb_grp_val in group_members_list_data_ordenada_val:
                    nome_fb_grp_val = m_fb_grp_val.get('nome','').strip().title()
                    cognome_fb_grp_val = m_fb_grp_val.get('cognome','').strip().title()
                    member_options_display_val.append((f"{nome_fb_grp_val} {cognome_fb_grp_val}", f"{nome_fb_grp_val} {cognome_fb_grp_val}"))

            select_widget_mem_ui = ui_members.get("select")
            new_member_selection_val_ui = member_options_display_val[0][1] if member_options_display_val else None
            
            if select_widget_mem_ui:
                current_mem_sel_before_refresh_ui = select_widget_mem_ui.value
                select_widget_mem_ui.options = member_options_display_val
                
                if select_widget_mem_ui.value != new_member_selection_val_ui:
                     select_widget_mem_ui.value = new_member_selection_val_ui
                elif member_refresh_func and callable(member_refresh_func):
                     change_event_mem_ui = {'name': 'value', 'old': current_mem_sel_before_refresh_ui, 'new': new_member_selection_val_ui, 'owner': select_widget_mem_ui, 'type': 'change'}
                     try:
                         form_mem_vbox_for_refresh_members_ui = ui_members.get("form_member_container")
                         member_refresh_func(change_event_mem_ui, app_state, ui_members, registro_output, form_member_vbox_ref=form_mem_vbox_for_refresh_members_ui)
                     except Exception as e_mem_refresh_expl_ui:
                          with registro_output: print(f"    ERROR al refrescar ui_members (explícito) desde botón Miembros: {e_mem_refresh_expl_ui}")
            
            ui_members.get("nueva_button", widgets.Button()).disabled = False
        else:
          with registro_output: print("  ERROR (groups_members): ui_members no es un diccionario válido."); return
        
        switch_interface_func('main_members')
    else:
      with registro_output: print("  INFO (groups_members): Seleccione institución y grupo válidos, o el grupo no tiene miembros registrados.")
# --- FIN DEL BLOQUE 5 ---
# --- BLOQUE 6: Otros Handlers de la Interfaz "Tabla de Grupos" (main_groups) ---
def on_groups_sociogramma_button_handler(b, app_state, ui_groups, ui_sociogramma,
                                          switch_interface_func, registro_output,
                                          handlers_sociogram_module_ref,
                                          app_data_ref,
                                          handlers_utils_ref_param,
                                          form_group_vbox_ref=None):
    # with registro_output:
        # print(f"HANDLER (groups v16.0): Entrando en on_groups_sociogramma_button_handler")
    
    if form_group_vbox_ref and hasattr(form_group_vbox_ref, 'layout') and form_group_vbox_ref.layout.display != 'none':
        form_group_vbox_ref.layout.display = 'none'
        # with registro_output: print("  INFO (groups_sociogramma): Formulario de grupo empotrado ocultado.")

    institution_name = app_state.get('current_institution_viewing_groups')
    select_widget_group_soc = ui_groups.get("select") if isinstance(ui_groups, dict) else None
    group_name_soc = select_widget_group_soc.value if select_widget_group_soc else None
    
    if institution_name and group_name_soc:
        app_state['current_group_viewing_members'] = {'school': institution_name, 'class_name': group_name_soc}
        app_state['return_interface'] = 'main_groups'
        
        if isinstance(ui_sociogramma, dict):
            title_socio_widget = ui_sociogramma.get("title_label")
            if title_socio_widget:
                title_socio_widget.value = f"Sociograma: {group_name_soc} ({institution_name})"
            
            if handlers_sociogram_module_ref and hasattr(handlers_sociogram_module_ref, 'on_sociogramma_circle_layout_button_handler'):
                if not app_data_ref:
                     with registro_output: print(f"  ERROR CRÍTICO (sociogramma_btn_grp): app_data_ref NO FUE PASADO.")
                if not handlers_utils_ref_param:
                     with registro_output: print(f"  ERROR CRÍTICO (sociogramma_btn_grp): handlers_utils_ref_param NO FUE PASADO.")
                try:
                    handlers_sociogram_module_ref.on_sociogramma_circle_layout_button_handler(
                        None, app_state, ui_sociogramma, registro_output,
                        app_data_ref=app_data_ref,
                        handlers_utils_ref_param=handlers_utils_ref_param
                    )
                except Exception as e_circle_draw_call_grp_ui:
                    with registro_output: print(f"  ERROR CRÍTICO llamando a on_sociogramma_circle_layout_button_handler: {e_circle_draw_call_grp_ui}\n{traceback.format_exc(limit=2)}")
            else:
                with registro_output: print(f"  ERROR CRÍTICO (sociogramma_btn_grp): El módulo 'handlers_sociogram' o su función no están disponibles.")
        else:
             with registro_output: print("  ERROR (sociogramma_btn_grp): ui_sociogramma no es un diccionario válido."); return
        
        switch_interface_func('sociogram')
    else:
         with registro_output: print("  INFO (sociogramma_btn_grp): Por favor, seleccione una institución y un grupo válidos para ver el sociograma.")


def on_groups_main_report_button_handler(b, app_state, ui_groups, registro_output):
    # with registro_output: print("HANDLER (groups v16.0): on_groups_main_report_button_handler")
    report_options_hbox = ui_groups.get("report_options_hbox")
    if report_options_hbox and hasattr(report_options_hbox, 'layout'):
        is_visible = report_options_hbox.layout.display != 'none' and report_options_hbox.layout.display is not None
        report_options_hbox.layout.display = 'none' if is_visible else 'flex'
        # with registro_output: print(f"  Opciones de reporte ahora: {'ocultas' if is_visible else 'visibles'}")
    elif registro_output:
      with registro_output: print("  ERROR (groups_main_report): 'report_options_hbox' no encontrado en ui_groups.")


def on_groups_report_table_button_handler(b, app_state, ui_groups, registro_output, ui_sociomatrix_ref,
                                           switch_interface_func_ref, on_sociomatrix_enter_func_ref,
                                           form_group_vbox_ref=None):
    # with registro_output: print("HANDLER (groups v16.0): on_groups_report_table_button_handler (Ir a Matriz)")
    
    if form_group_vbox_ref and hasattr(form_group_vbox_ref, 'layout') and form_group_vbox_ref.layout.display != 'none':
        form_group_vbox_ref.layout.display = 'none'
        # with registro_output: print("  INFO (groups_report_table): Formulario de grupo empotrado ocultado.")
    
    institution_name = app_state.get('current_institution_viewing_groups')
    group_select_widget = ui_groups.get("select") if isinstance(ui_groups, dict) else None
    group_name = group_select_widget.value if group_select_widget and group_select_widget.value else None
    
    if not institution_name or not group_name:
      with registro_output: print("  ERROR (report_table_btn_grp): Institución o grupo no seleccionado para la Matriz."); return
    
    if not ui_sociomatrix_ref or not callable(on_sociomatrix_enter_func_ref) or not callable(switch_interface_func_ref):
        with registro_output: print("  ERROR (report_table_btn_grp): Referencias necesarias no disponibles para Matriz Sociométrica."); return
    
    app_state['current_group_viewing_members'] = {'school': institution_name, 'class_name': group_name}
    app_state['return_interface'] = 'main_groups'
    
    try:
        on_sociomatrix_enter_func_ref(app_state, ui_sociomatrix_ref, registro_output)
        switch_interface_func_ref('sociomatrix_view')
    except Exception as e_matrix_grp_call:
      with registro_output: print(f"  ERROR al abrir la vista de matriz sociométrica: {e_matrix_grp_call}\n{traceback.format_exc(limit=2)}")


def on_groups_report_data_button_handler(b, app_state, ui_groups, registro_output,
                                          form_group_vbox_ref=None, pdf_gen_module_explicit=None):
    # if registro_output and isinstance(registro_output, widgets.Output):
        # with registro_output:
            # print(f"\nHANDLER (groups v16.0): on_groups_report_data_button_handler (Generar PDF Resumen/Datos)")
            # print(f"  DEBUG: pdf_gen_module_explicit recibido: {type(pdf_gen_module_explicit)}")

    if form_group_vbox_ref and hasattr(form_group_vbox_ref, 'layout') and form_group_vbox_ref.layout.display != 'none':
        form_group_vbox_ref.layout.display = 'none'
        # if registro_output and isinstance(registro_output, widgets.Output):
            # with registro_output: print("  INFO (groups_report_data): Formulario de grupo empotrado ocultado.")

    institution_name = app_state.get('current_institution_viewing_groups')
    group_select_widget_pdf_grp = ui_groups.get("select") if isinstance(ui_groups, dict) else None
    group_name_pdf_grp = group_select_widget_pdf_grp.value if group_select_widget_pdf_grp and hasattr(group_select_widget_pdf_grp, 'value') else None
    
    if not institution_name or not group_name_pdf_grp:
        if registro_output:
            with registro_output: print("  ERROR (report_data_btn_grp): Institución o grupo no seleccionado para generar PDF de datos.");
        return

    if pdf_gen_module_explicit and hasattr(pdf_gen_module_explicit, 'generate_class_summary_report_pdf'):
        # if registro_output:
            # with registro_output: print(f"  INFO: Llamando a generate_class_summary_report_pdf para {institution_name}/{group_name_pdf_grp}")
        try:
            pdf_gen_module_explicit.generate_class_summary_report_pdf(
                institution_name, group_name_pdf_grp, registro_output=registro_output
            )
        except Exception as e_pdf_sum_grp_call:
            if registro_output:
                with registro_output: print(f"  ERROR al intentar generar PDF resumen del grupo: {e_pdf_sum_grp_call}\n{traceback.format_exc(limit=2)}")
    else:
        if registro_output:
            if not pdf_gen_module_explicit: print("  ERROR CRÍTICO (report_data_btn_grp): El módulo pdf_generator no fue proporcionado.")
            else: print("  ERROR CRÍTICO (report_data_btn_grp): La función 'generate_class_summary_report_pdf' no se encuentra en pdf_generator.")


def on_groups_salir_button_handler(b, app_state, ui_main_institutions, switch_interface_func, registro_output,
                                    institution_refresh_func=None, form_group_vbox_ref=None):
    with registro_output:
        clear_output(wait=True)
        # print("HANDLER (groups v16.0): on_groups_salir_button_handler")
        pass

    if form_group_vbox_ref and hasattr(form_group_vbox_ref, 'layout') and form_group_vbox_ref.layout.display != 'none':
        form_group_vbox_ref.layout.display = 'none'
        # with registro_output: print("  INFO (groups_salir): Formulario de grupo empotrado ocultado.")
    
    last_viewed_institution = app_state.get('current_institution_viewing_groups')
    
    app_state['current_institution_viewing_groups'] = None
    app_state['current_group_viewing_members'] = None
    app_state['current_group_editing'] = None
    
    current_institution_selection_on_return_ui = None
    select_widget_institution_ui = ui_main_institutions.get("select") if isinstance(ui_main_institutions, dict) else None
    
    if select_widget_institution_ui and hasattr(select_widget_institution_ui, 'options') and schools_data :
        current_options_institutions_ui = sorted(list(schools_data.keys()))
        select_widget_institution_ui.options = current_options_institutions_ui

        if last_viewed_institution and last_viewed_institution in current_options_institutions_ui:
            current_institution_selection_on_return_ui = last_viewed_institution
        elif select_widget_institution_ui.value and select_widget_institution_ui.value in current_options_institutions_ui:
            current_institution_selection_on_return_ui = select_widget_institution_ui.value
        elif current_options_institutions_ui:
            current_institution_selection_on_return_ui = current_options_institutions_ui[0]
        
        if select_widget_institution_ui.value != current_institution_selection_on_return_ui :
            select_widget_institution_ui.value = current_institution_selection_on_return_ui
        elif institution_refresh_func and callable(institution_refresh_func) and current_institution_selection_on_return_ui is not None:
            change_event_data_inst_ui = {'name': 'value', 'old': current_institution_selection_on_return_ui,
                                 'new': current_institution_selection_on_return_ui, 'owner': select_widget_institution_ui, 'type': 'change'}
            try:
                form_institution_vbox_for_refresh_main_ui = globals().get('interfaces',{}).get('form_institution')
                institution_refresh_func(change_event_data_inst_ui, app_state, ui_main_institutions, registro_output, form_school_vbox_ref=form_institution_vbox_for_refresh_main_ui)
            except Exception as e_institution_refresh_ui:
              with registro_output: print(f"  ERROR al refrescar ui_main_institutions: {e_institution_refresh_ui}")
    elif select_widget_institution_ui :
         select_widget_institution_ui.options = []
         select_widget_institution_ui.value = None
         if institution_refresh_func and callable(institution_refresh_func):
            change_event_clear_inst_ui = {'name': 'value', 'old': None, 'new': None, 'owner': select_widget_institution_ui, 'type': 'change'}
            form_institution_vbox_for_clear_main_ui = globals().get('interfaces',{}).get('form_institution')
            institution_refresh_func(change_event_clear_inst_ui, app_state, ui_main_institutions, registro_output, form_institution_vbox_ref=form_institution_vbox_for_clear_main_ui)

    switch_interface_func('main_institutions')
# --- FIN DEL BLOQUE 6 ---
# --- BLOQUE 7: HANDLERS PARA DIANA DE AFINIDAD ---

def _populate_diana_questions_checkboxes(app_state, ui_groups, registro_output):
    if not isinstance(ui_groups, dict):
        if registro_output and isinstance(registro_output, widgets.Output):
            with registro_output: print("ERROR (_populate_diana_q_grp): ui_groups no es dict.")
        return

    diana_q_checkboxes_vbox_grp = ui_groups.get("diana_questions_checkboxes_vbox")
    if not diana_q_checkboxes_vbox_grp or not hasattr(diana_q_checkboxes_vbox_grp, 'children'):
        if registro_output and isinstance(registro_output, widgets.Output):
            with registro_output: print("ERROR (_populate_diana_q_grp): diana_questions_checkboxes_vbox no encontrado o no es VBox.")
        return

    diana_q_checkboxes_vbox_grp.children = []
    if "_diana_question_checkboxes_list" not in ui_groups:
        ui_groups["_diana_question_checkboxes_list"] = []
    else:
        ui_groups["_diana_question_checkboxes_list"].clear()

    selected_group_name_diana_pop = ui_groups.get("select").value if isinstance(ui_groups.get("select"), widgets.Select) else None
    institution_name_diana_pop = app_state.get('current_institution_viewing_groups')

    if not institution_name_diana_pop or not selected_group_name_diana_pop:
        # if registro_output and isinstance(registro_output, widgets.Output):
            # with registro_output: print("ADVERTENCIA (_populate_diana_q_grp): No se pudo determinar contexto institución/grupo para cargar preguntas.")
        diana_q_checkboxes_vbox_grp.children = [Label("Seleccione un grupo para ver sus preguntas.")]
        return
            
    question_defs_diana = get_class_question_definitions(institution_name_diana_pop, selected_group_name_diana_pop)

    if question_defs_diana:
        sorted_q_items_diana = sorted(question_defs_diana.items(), key=lambda item: (item[1].get('order', 99), item[0]))
        temp_checkboxes_diana = []
        for q_id_diana, q_def_diana in sorted_q_items_diana:
            q_text_short_diana = q_def_diana.get('text', q_id_diana)[:50] + ("..." if len(q_def_diana.get('text', q_id_diana)) > 50 else "")
            q_type_diana = q_def_diana.get('type', 'General')
            data_key_diana = q_def_diana.get('data_key', q_id_diana)
            polarity_diana = q_def_diana.get('polarity', 'neutral')
            polarity_display_diana = polarity_diana[:3].title() if polarity_diana != 'neutral' else 'Neut'
            label_desc_diana = f"({polarity_display_diana}) {q_type_diana}: {q_text_short_diana}"
            default_checked_diana = (polarity_diana == 'positive')

            cb_diana = Checkbox(description=label_desc_diana, value=default_checked_diana, indent=False, layout=Layout(width='98%', margin_bottom='1px'))
            ui_groups["_diana_question_checkboxes_list"].append({'widget': cb_diana, 'data_key': data_key_diana, 'polarity': polarity_diana})
            temp_checkboxes_diana.append(cb_diana)
        
        if not temp_checkboxes_diana:
             diana_q_checkboxes_vbox_grp.children = [Label("No hay preguntas definidas para este grupo.")]
        else:
            diana_q_checkboxes_vbox_grp.children = tuple(temp_checkboxes_diana)
        # if registro_output and isinstance(registro_output, widgets.Output):
            # with registro_output: print(f"INFO (_populate_diana_q_grp): {len(temp_checkboxes_diana)} checkboxes de preguntas poblados para Diana en {institution_name_diana_pop}/{selected_group_name_diana_pop}.")
    else:
        diana_q_checkboxes_vbox_grp.children = [Label("No hay preguntas definidas para este grupo.")]
        # if registro_output and isinstance(registro_output, widgets.Output):
            # with registro_output: print(f"INFO (_populate_diana_q_grp): No hay definiciones de preguntas para {institution_name_diana_pop}/{selected_group_name_diana_pop}.")

def on_classes_diana_button_click_handler(b, app_state, ui_groups, registro_output):
    if not isinstance(ui_groups, dict):
        if registro_output and isinstance(registro_output, widgets.Output): print("ERROR (diana_btn_click_grp): ui_groups no es dict."); return

    diana_controls_panel_grp = ui_groups.get("diana_controls_vbox")
    if not diana_controls_panel_grp or not hasattr(diana_controls_panel_grp, 'layout'):
        if registro_output and isinstance(registro_output, widgets.Output): print("ERROR (diana_btn_click_grp): diana_controls_vbox no encontrado o sin layout."); return

    is_currently_hidden_diana = diana_controls_panel_grp.layout.display == 'none'
    new_display_status_diana = 'flex' if is_currently_hidden_diana else 'none'
    diana_controls_panel_grp.layout.display = new_display_status_diana

    # if registro_output and isinstance(registro_output, widgets.Output):
        # with registro_output:
            # print(f"\nHANDLER (groups v16.0): on_classes_diana_button_click_handler")
            # print(f"  Panel de Controles de Diana de Afinidad ahora: {'VISIBLE' if new_display_status_diana == 'flex' else 'OCULTO'}")

    if new_display_status_diana == 'flex':
        _populate_diana_questions_checkboxes(app_state, ui_groups, registro_output)
        diana_output_image_widget_grp = ui_groups.get("diana_output_image")
        if diana_output_image_widget_grp and isinstance(diana_output_image_widget_grp, widgets.Output):
            with diana_output_image_widget_grp:
                clear_output(wait=True)
                display(HTML("<p style='color:grey;text-align:center;'><i>Configure y genere la diana.</i></p>"))
        diana_download_btn_grp = ui_groups.get("diana_download_button")
        if diana_download_btn_grp:
            diana_download_btn_grp.disabled = True
        if isinstance(ui_groups, dict):
            ui_groups['_diana_last_image_bytes'] = None

def _set_diana_checkboxes_state(ui_groups, select_all=False, select_none=False, select_positive=None, select_negative=None):
    if not isinstance(ui_groups, dict): return
    checkbox_infos_diana_set = ui_groups.get("_diana_question_checkboxes_list", [])
    if not checkbox_infos_diana_set: return
    for info_diana_set in checkbox_infos_diana_set:
        cb_diana_set = info_diana_set.get('widget')
        if not cb_diana_set or not hasattr(cb_diana_set, 'value'): continue
        if select_all: cb_diana_set.value = True
        elif select_none: cb_diana_set.value = False
        else:
            is_positive_cb_diana = info_diana_set.get('polarity') == 'positive'
            is_negative_cb_diana = info_diana_set.get('polarity') == 'negative'
            if select_positive is not None and is_positive_cb_diana: cb_diana_set.value = select_positive
            elif select_negative is not None and is_negative_cb_diana: cb_diana_set.value = select_negative
            elif select_positive is not None and not is_positive_cb_diana: cb_diana_set.value = False
            elif select_negative is not None and not is_negative_cb_diana: cb_diana_set.value = False

def on_diana_select_all_button_click_handler(b, app_state, ui_groups, registro_output):
    # if registro_output: 
      # with registro_output: print("HANDLER (diana_select_all_grp): Seleccionando todas.")
    _set_diana_checkboxes_state(ui_groups, select_all=True)

def on_diana_select_none_button_click_handler(b, app_state, ui_groups, registro_output):
    # if registro_output: 
      # with registro_output: print("HANDLER (diana_select_none_grp): Deseleccionando todas.")
    _set_diana_checkboxes_state(ui_groups, select_none=True)

def on_diana_select_positive_button_click_handler(b, app_state, ui_groups, registro_output):
    # if registro_output: 
      # with registro_output: print("HANDLER (diana_select_positive_grp): Seleccionando positivas.")
    _set_diana_checkboxes_state(ui_groups, select_positive=True, select_negative=False)

def on_diana_select_negative_button_click_handler(b, app_state, ui_groups, registro_output):
    # if registro_output: 
      # with registro_output: print("HANDLER (diana_select_negative_grp): Seleccionando negativas.")
    _set_diana_checkboxes_state(ui_groups, select_positive=False, select_negative=True)

def on_diana_generate_button_click_handler(b, app_state, ui_groups, registro_output, pdf_gen_module_explicit=None):
    # print("--- DEBUG HANDLER: on_diana_generate_button_click_handler INVOCADO (handlers_groups.py v16.1) ---")

    # if registro_output and isinstance(registro_output, widgets.Output):
        # with registro_output:
            # print("\n--- HANDLER (groups v16.1): on_diana_generate_button_click_handler ---")
            # print(f"  DEBUG: pdf_gen_module_explicit recibido: {type(pdf_gen_module_explicit)}")
    # else:
        # print("ADVERTENCIA: registro_output no es un widget Output válido en on_diana_generate_button_click_handler.")

    diana_output_widget = ui_groups.get("diana_output_image")
    if diana_output_widget and isinstance(diana_output_widget, widgets.Output):
        with diana_output_widget:
            clear_output(wait=True)
            display(HTML("<p style='color:blue;text-align:center;'><i>Generando Diana de Afinidad... Por favor, espere.</i></p>"))
    else:
        if registro_output: print("  ERROR: El widget 'diana_output_image' no es un Output válido.")
        return

    selected_group_name = ui_groups.get("select").value if isinstance(ui_groups.get("select"), widgets.Select) else None
    institution_name = app_state.get('current_institution_viewing_groups')

    if not institution_name or not selected_group_name:
        if registro_output: print("  ERROR: No se pudo determinar la institución o grupo seleccionada para la Diana.")
        if diana_output_widget:
            with diana_output_widget: clear_output(wait=True); display(HTML("<p style='color:red;text-align:center;'>Error: Seleccione una institución y un grupo primero.</p>"))
        return
    # if registro_output: print(f"  Contexto Diana: Institución='{institution_name}', Grupo='{selected_group_name}'")

    selected_diana_q_keys = []
    if isinstance(ui_groups, dict) and "_diana_question_checkboxes_list" in ui_groups:
        for item in ui_groups["_diana_question_checkboxes_list"]:
            if item.get('widget') and hasattr(item['widget'], 'value') and item['widget'].value:
                data_key_item = item.get('data_key')
                if data_key_item: selected_diana_q_keys.append(data_key_item)
    if not selected_diana_q_keys:
        # if registro_output: print("  ADVERTENCIA: No hay preguntas seleccionadas para la Diana.")
        if diana_output_widget:
            with diana_output_widget: clear_output(wait=True); display(HTML("<p style='color:orange;text-align:center;'>Por favor, seleccione al menos una pregunta.</p>"))
        if isinstance(ui_groups, dict): ui_groups['_diana_last_image_bytes'] = None
        diana_download_btn = ui_groups.get("diana_download_button")
        if diana_download_btn: diana_download_btn.disabled = True
        return
    # if registro_output: print(f"  Preguntas seleccionadas para la Diana: {selected_diana_q_keys}")

    class_members_raw = sociograma_data.members_data.get(institution_name, {}).get(selected_group_name, [])
    if not class_members_raw:
        if registro_output: print(f"  ERROR: No hay miembros para {institution_name}/{selected_group_name}.")
        if diana_output_widget:
            with diana_output_widget: clear_output(wait=True); display(HTML(f"<p style='color:red;'>Error: No hay miembros en el grupo {selected_group_name}.</p>"))
        return
        
    member_info_intermediate = {}
    for m_dict_orig in class_members_raw:
        nombre_t = m_dict_orig.get('nome','').strip().title()
        cognome_t = m_dict_orig.get('cognome','').strip().title()
        full_n_key_diana = f"{nombre_t} {cognome_t}".strip()
        if full_n_key_diana:
            member_info_intermediate[full_n_key_diana] = {
                'id_corto': m_dict_orig.get('iniz', 'N/A'),
                'sexo': m_dict_orig.get('sexo', 'Desconocido')
            }
    # if registro_output: print(f"  {len(member_info_intermediate)} miembros con ID corto y sexo mapeados.")

    detailed_affinity_scores = collections.defaultdict(lambda: {
        'total_recibido': 0,
        'choices_by_pos': collections.defaultdict(int)
    })
    edges_data_for_diana_viz = []
    members_in_class_actual_set_diana = set(member_info_intermediate.keys())

    for (rs_diana, rc_diana, nominator_key_diana), resp_dict_diana in sociograma_data.questionnaire_responses_data.items():
        if rs_diana == institution_name and rc_diana == selected_group_name and nominator_key_diana in members_in_class_actual_set_diana:
            for q_key_diana, nominees_list_diana in resp_dict_diana.items():
                if q_key_diana in selected_diana_q_keys:
                    for idx_election, nominee_key_diana in enumerate(nominees_list_diana):
                        if nominee_key_diana in members_in_class_actual_set_diana:
                            detailed_affinity_scores[nominee_key_diana]['total_recibido'] += 1
                            detailed_affinity_scores[nominee_key_diana]['choices_by_pos'][idx_election] += 1
                            edges_data_for_diana_viz.append((nominator_key_diana, nominee_key_diana, q_key_diana, idx_election))
    
    members_data_list_detailed_final = []
    for member_name_key_final, info_base_final in member_info_intermediate.items():
        scores_final = detailed_affinity_scores.get(member_name_key_final, {'total_recibido': 0, 'choices_by_pos': collections.defaultdict(int)})
        members_data_list_detailed_final.append({
            'nombre_completo': member_name_key_final,
            'id_corto': info_base_final['id_corto'],
            'sexo': info_base_final['sexo'],
            'total_recibido': scores_final['total_recibido'],
            'primeras_opciones': scores_final['choices_by_pos'].get(0, 0),
            'segundas_opciones': scores_final['choices_by_pos'].get(1, 0),
            'terceras_opciones': scores_final['choices_by_pos'].get(2, 0)
        })

    # if registro_output:
        # print(f"  Puntajes de afinidad detallados calculados para {len(members_data_list_detailed_final)} miembros.")
        # print(f"  Se recolectaron {len(edges_data_for_diana_viz)} aristas para las preguntas seleccionadas.")

    show_lines_in_diana_val = ui_groups.get("diana_show_lines_checkbox").value if isinstance(ui_groups.get("diana_show_lines_checkbox"), widgets.Checkbox) else True
    # if registro_output: print(f"  Opción Mostrar Líneas en Diana: {show_lines_in_diana_val}")

    image_buffer_result = None
    if pdf_gen_module_explicit and hasattr(pdf_gen_module_explicit, 'generate_affinity_diana_image'):
        try:
            num_zonas_diana = 4
            labels_diana_zonas = ["Populares ++", "Populares +", "Aceptados", "Periféricos"]
            # if registro_output: print(f"  Llamando a generate_affinity_diana_image con {num_zonas_diana} zonas...")
            
            image_buffer_result = pdf_gen_module_explicit.generate_affinity_diana_image(
                institution_name=institution_name,
                group_name=selected_group_name,
                members_data_list_detailed=members_data_list_detailed_final,
                edges_data=edges_data_for_diana_viz,
                show_lines=show_lines_in_diana_val,
                registro_output=registro_output,
                num_zonas_definidas=num_zonas_diana,
                labels_zonas=labels_diana_zonas
            )
        except TypeError as te_call_diana_gen:
             if registro_output: print(f"  ERROR DE TIPO al llamar a generate_affinity_diana_image: {te_call_diana_gen}\n{traceback.format_exc(limit=2)}")
             image_buffer_result = None
        except Exception as e_gen_diana_img_call_final:
            if registro_output: print(f"  ERROR GENERAL al llamar a generate_affinity_diana_image: {e_gen_diana_img_call_final}\n{traceback.format_exc(limit=2)}")
            image_buffer_result = None
    else:
        if registro_output: print("ERROR: pdf_gen_module_explicit o generate_affinity_diana_image no disponibles.")

    diana_download_btn = ui_groups.get("diana_download_button")
    if image_buffer_result and isinstance(image_buffer_result, io.BytesIO):
        image_bytes_val = image_buffer_result.getvalue()
        b64_image_val = base64.b64encode(image_bytes_val).decode('utf-8')
        if diana_output_widget:
            with diana_output_widget:
                clear_output(wait=True)
                display(HTML(f"<img src='data:image/png;base64,{b64_image_val}' alt='Diana de Afinidad' style='max-width:100%; height:auto; border:1px solid #ccc;'/>"))
        if isinstance(ui_groups, dict):
             ui_groups['_diana_last_image_bytes'] = image_bytes_val
        if diana_download_btn:
            diana_download_btn.disabled = False
        # if registro_output: print("  INFO: Diana de Afinidad generada y mostrada.")
    else:
        if diana_output_widget:
            with diana_output_widget:
                clear_output(wait=True)
                display(HTML("<p style='color:red;text-align:center;'>Error al generar la imagen de la Diana. Verifique los logs.</p>"))
        if diana_download_btn:
            diana_download_btn.disabled = True
        if registro_output: print("  ERROR: No se pudo obtener el buffer de la imagen de la Diana.")

def on_diana_download_button_click_handler(b, app_state, ui_groups, registro_output):
    # if registro_output and isinstance(registro_output, widgets.Output):
        # with registro_output: print("\n--- HANDLER (groups v16.0): on_diana_download_button_click_handler ---")

    image_bytes_to_download_diana = ui_groups.get('_diana_last_image_bytes') if isinstance(ui_groups, dict) else None
    if image_bytes_to_download_diana:
        institution_name_dl = app_state.get('current_institution_viewing_groups', "Institucion")
        group_name_select_dl = ui_groups.get("select")
        group_name_dl = group_name_select_dl.value if group_name_select_dl and hasattr(group_name_select_dl, 'value') else "Grupo"
        clean_institution_name_dl = re.sub(r'[^\w\s-]', '', institution_name_dl).replace(' ', '_')
        clean_group_name_dl = re.sub(r'[^\w\s-]', '', group_name_dl).replace(' ', '_')
        timestamp_str_dl = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename_diana_final_dl = f"DianaAfinidad_{clean_institution_name_dl}_{clean_group_name_dl}_{timestamp_str_dl}.png"
        b64_png_download_diana = base64.b64encode(image_bytes_to_download_diana).decode('utf-8')
        download_html_code_diana = f'<p style="text-align:center; margin-top:10px;"><a download="{filename_diana_final_dl}" href="data:image/png;base64,{b64_png_download_diana}" target="_blank" style="padding:8px 15px; background-color:#007bff; color:white; text-decoration:none; border-radius:5px; font-weight:bold;">Descargar Diana: {filename_diana_final_dl}</a></p>'
        diana_output_widget_for_dl_link_grp = ui_groups.get("diana_output_image")
        if diana_output_widget_for_dl_link_grp and isinstance(diana_output_widget_for_dl_link_grp, widgets.Output):
            with diana_output_widget_for_dl_link_grp: display(HTML(download_html_code_diana))
        # if registro_output: print(f"  INFO (diana_dl_grp): Enlace de descarga para '{filename_diana_final_dl}' generado.")
    else:
        if registro_output: print("  ERROR (diana_dl_grp): No hay imagen de Diana para descargar.")
        diana_output_widget_err_dl_msg_grp = ui_groups.get("diana_output_image")
        if diana_output_widget_err_dl_msg_grp and isinstance(diana_output_widget_err_dl_msg_grp, widgets.Output):
            with diana_output_widget_err_dl_msg_grp: display(HTML("<p style='color:red; text-align:center;'>Error: Primero genere una Diana para poder descargarla.</p>"))
# --- FIN DEL BLOQUE 7 ---