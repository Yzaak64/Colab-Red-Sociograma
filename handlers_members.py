# handlers_members.py
# (v11.3 - Asegura visibilidad del contenedor del formulario.
#          Usa "miembro", "Institución"/"Grupo" y "sexo".)

import traceback
import sys
import collections
import functools
from ipywidgets import widgets
from IPython.display import clear_output, display, HTML as IPHTML

from sociograma_data import members_data, classes_data, questionnaire_responses_data, get_class_question_definitions
import sociograma_data

_handlers_utils_ref_hm = globals().get('handlers_utils')

def parse_valor_select_en_nombre_apellido(valor_select_str):
    partes = valor_select_str.strip().split()
    if not partes: return "", ""
    if len(partes) == 1: return partes[0].strip(), ""
    nombre = " ".join(partes[:-1]).strip()
    apellido = partes[-1].strip()
    return nombre, apellido

# --- Handlers para la Interfaz "Tabla de Miembros" (main_members) ---

def on_members_select_change_handler(change, app_state, ui_members, registro_output,
                                      form_member_vbox_ref=None):
    # with registro_output:
        # new_value_selected = change.get('new', 'N/A')
        # print(f"HANDLER (members v11.3): on_members_select_change_handler, nuevo miembro: '{new_value_selected}'")

    selected_member_name_from_select = change.get('new')
    group_context = app_state.get('current_group_viewing_members')
    member_info_from_data = None

    if group_context and selected_member_name_from_select:
        institution_name = group_context.get('school')
        group_name = group_context.get('class_name')

        if institution_name and group_name and \
           institution_name in members_data and group_name in members_data.get(institution_name, {}):
            
            group_members_list_data = members_data[institution_name].get(group_name, [])
            nombre_sel_parsed, apellido_sel_parsed = parse_valor_select_en_nombre_apellido(selected_member_name_from_select)
            
            for m_data_iter in group_members_list_data:
                m_nome_data_titulo = m_data_iter.get('nome','').strip().title()
                m_cognome_data_original_mayus = m_data_iter.get('cognome','').strip()
                if nombre_sel_parsed.lower() == m_nome_data_titulo.lower() and \
                   apellido_sel_parsed.lower() == m_cognome_data_original_mayus.title().lower():
                    member_info_from_data = m_data_iter
                    break

    is_selection_valid = bool(member_info_from_data)

    if isinstance(ui_members, dict):
        if form_member_vbox_ref and hasattr(form_member_vbox_ref, 'layout') and form_member_vbox_ref.layout.display != 'none':
            form_member_vbox_ref.layout.display = 'none'
            form_member_container_in_ui_members = ui_members.get('form_member_container')
            if form_member_container_in_ui_members and hasattr(form_member_container_in_ui_members, 'layout'):
                form_member_container_in_ui_members.layout.display = 'none'
            # if registro_output:
                # with registro_output: print("  INFO (members_select): Formulario miembro empotrado y su contenedor ocultados.")
        
        current_utils_select_mem_hm = _handlers_utils_ref_hm or globals().get('handlers_utils')
        if member_info_from_data:
            ui_members.get("cognome_text", widgets.Text()).value = member_info_from_data.get('cognome', '').title()
            ui_members.get("nome_text", widgets.Text()).value = member_info_from_data.get('nome', '').title()
            ui_members.get("iniz_text", widgets.Text()).value = member_info_from_data.get('iniz', '')
            ui_members.get("annotations_textarea", widgets.Textarea()).value = member_info_from_data.get('annotations', '')
        else:
            if current_utils_select_mem_hm and hasattr(current_utils_select_mem_hm, 'clear_member_details_fields'):
                current_utils_select_mem_hm.clear_member_details_fields(ui_members)
            # elif registro_output:
                 # with registro_output: print("  ADVERTENCIA (members_select): clear_member_details_fields no disponible.")
            # if selected_member_name_from_select and registro_output:
                 # with registro_output: print(f"  Advertencia (members_select): Detalles no encontrados para '{selected_member_name_from_select}'.")

        ui_members.get("modifica_button", widgets.Button()).disabled = not is_selection_valid
        ui_members.get("elimina_button", widgets.Button()).disabled = not is_selection_valid
        ui_members.get("questionario_button", widgets.Button()).disabled = not is_selection_valid
    elif registro_output:
        with registro_output: print("  ERROR (on_members_select_change): ui_members no es dict.")


def on_members_nueva_button_handler(b, app_state, ui_members, ui_form_member, switch_interface_func, registro_output):
    # with registro_output:
        # print("HANDLER (members v11.3): on_members_nueva_button_handler")
    
    group_context_mem_new = app_state.get('current_group_viewing_members')
    if not group_context_mem_new or not all(k in group_context_mem_new for k in ['school', 'class_name']):
        with registro_output: print("  ERROR (members_nueva): No hay grupo/institución seleccionada."); return
        
    institution_name_mem_new = group_context_mem_new['school']
    group_name_mem_new = group_context_mem_new['class_name']
    
    app_state['current_member_editing'] = None
    
    if ui_form_member and hasattr(ui_form_member, 'layout'):
        form_member_elements = getattr(ui_form_member, '_ui_elements_ref', None)
        if not form_member_elements or not isinstance(form_member_elements, dict):
            with registro_output: print("  ERROR (members_nueva): _ui_elements_ref no encontrado."); return
        
        form_member_elements.get('title_label', widgets.Label()).value = f"Nuevo Miembro en {group_name_mem_new} ({institution_name_mem_new})"
        form_member_elements.get('school_text', widgets.Text()).value = institution_name_mem_new
        form_member_elements.get('class_text', widgets.Text()).value = group_name_mem_new
        
        for key, default_val in [ ("cognome_input", ""), ("nome_input", ""), ("iniziali_input", ""),
                                  ("gender_radio", "Desconocido"),
                                  ("dob_input", ""), ("annotations_textarea", "")]:
            widget = form_member_elements.get(key)
            if widget: widget.value = default_val
            if hasattr(widget, 'disabled'): widget.disabled = False
            
        add_hbox = form_member_elements.get("add_buttons_hbox")
        modify_hbox = form_member_elements.get("modify_buttons_hbox")
        if add_hbox and hasattr(add_hbox,'layout'): add_hbox.layout.display = 'flex'
        if modify_hbox and hasattr(modify_hbox,'layout'): modify_hbox.layout.display = 'none'
        
        if ui_members and isinstance(ui_members, dict):
            form_member_container_widget = ui_members.get('form_member_container')
            if form_member_container_widget and hasattr(form_member_container_widget, 'layout'):
                form_member_container_widget.layout.display = 'flex'
        
        ui_form_member.layout.display = 'flex'
        
    else:
        with registro_output: print("  ERROR (members_nueva): ui_form_member (VBox del formulario) no es válido.")


def on_members_modifica_button_handler(b, app_state, ui_members, ui_form_member, switch_interface_func, registro_output):
    select_widget = ui_members.get("select") if isinstance(ui_members, dict) else None
    selected_member_name_from_select = select_widget.value if select_widget else None
    group_context_mem_mod = app_state.get('current_group_viewing_members')
    
    # with registro_output:
        # print(f"HANDLER (members v11.3): on_members_modifica_button_handler para '{selected_member_name_from_select}'")
        
    if group_context_mem_mod and selected_member_name_from_select:
        institution_name_mem_mod = group_context_mem_mod['school']
        group_name_mem_mod = group_context_mem_mod['class_name']

        if institution_name_mem_mod in members_data and group_name_mem_mod in members_data.get(institution_name_mem_mod, {}):
            group_members_list_data_mod = members_data[institution_name_mem_mod].get(group_name_mem_mod, [])
            member_data_to_edit = None
            nombre_sel_mod, apellido_sel_mod = parse_valor_select_en_nombre_apellido(selected_member_name_from_select)
            for m_data_mod_iter in group_members_list_data_mod:
                m_nome_data_mod_titulo = m_data_mod_iter.get('nome','').strip().title()
                m_cognome_data_mod_mayus = m_data_mod_iter.get('cognome','').strip()
                if nombre_sel_mod.lower() == m_nome_data_mod_titulo.lower() and \
                   apellido_sel_mod.lower() == m_cognome_data_mod_mayus.title().lower():
                    member_data_to_edit = m_data_mod_iter
                    break
            
            if member_data_to_edit:
                member_name_for_context_mod_edit = selected_member_name_from_select
                app_state['current_member_editing'] = {
                    'school': institution_name_mem_mod, 
                    'class_name': group_name_mem_mod,
                    'member_name': member_name_for_context_mod_edit,
                    'original_data': member_data_to_edit.copy()
                }
                
                if ui_form_member and hasattr(ui_form_member, 'layout'):
                    form_elements_mod_mem = getattr(ui_form_member, '_ui_elements_ref', None)
                    if not form_elements_mod_mem or not isinstance(form_elements_mod_mem, dict):
                        with registro_output: print("  ERROR (members_modifica): _ui_elements_ref no encontrado."); return
                    
                    form_elements_mod_mem.get('title_label', widgets.Label()).value = f"Modificar Miembro: {member_name_for_context_mod_edit} ({group_name_mem_mod}, {institution_name_mem_mod})"
                    form_elements_mod_mem.get("cognome_input", widgets.Text()).value = member_data_to_edit.get('cognome', '').title()
                    form_elements_mod_mem.get("nome_input", widgets.Text()).value = member_data_to_edit.get('nome', '').title()
                    form_elements_mod_mem.get("iniziali_input", widgets.Text()).value = member_data_to_edit.get('iniz', '')
                    sexo_guardado_val_edit = member_data_to_edit.get('sexo', 'Desconocido')
                    form_elements_mod_mem.get("gender_radio", widgets.RadioButtons()).value = sexo_guardado_val_edit
                    form_elements_mod_mem.get("dob_input", widgets.Text()).value = member_data_to_edit.get('fecha_nac', '')
                    form_elements_mod_mem.get("annotations_textarea", widgets.Textarea()).value = member_data_to_edit.get('annotations', '')
                    
                    for key_enable_mem in ["cognome_input", "nome_input", "iniziali_input", "gender_radio", "dob_input", "annotations_textarea"]:
                        widget_enable_mem = form_elements_mod_mem.get(key_enable_mem)
                        if hasattr(widget_enable_mem, 'disabled'): widget_enable_mem.disabled = False
                    
                    add_hbox_mod_mem = form_elements_mod_mem.get("add_buttons_hbox")
                    modify_hbox_mod_mem = form_elements_mod_mem.get("modify_buttons_hbox")
                    if add_hbox_mod_mem and hasattr(add_hbox_mod_mem,'layout'): add_hbox_mod_mem.layout.display = 'none'
                    if modify_hbox_mod_mem and hasattr(modify_hbox_mod_mem,'layout'): modify_hbox_mod_mem.layout.display = 'flex'
                    
                    if ui_members and isinstance(ui_members, dict):
                        form_member_container_widget = ui_members.get('form_member_container')
                        if form_member_container_widget and hasattr(form_member_container_widget, 'layout'):
                            form_member_container_widget.layout.display = 'flex'
                    
                    ui_form_member.layout.display = 'flex'
                else:
                    with registro_output: print("  ERROR (members_modifica): ui_form_member (VBox) no válido.")
            else:
                with registro_output: print(f"  ERROR (members_modifica): Datos no encontrados para miembro '{selected_member_name_from_select}'.")
        else:
            with registro_output: print("  ERROR (members_modifica): Institución o grupo no encontrado en members_data.")
    else:
        with registro_output: print("  ERROR (members_modifica): No hay miembro seleccionado o falta contexto de grupo/institución.")

def on_members_elimina_button_handler(b, app_state, ui_members, registro_output,
                                       refresh_func=None, form_member_vbox_ref=None):
    select_widget_del = ui_members.get("select") if isinstance(ui_members, dict) else None
    member_name_to_delete_select_val_del = select_widget_del.value if select_widget_del else None
    group_context_del = app_state.get('current_group_viewing_members')
    
    with registro_output:
        clear_output(wait=True)
        # print(f"HANDLER (members v11.3): on_members_elimina_button_handler para '{member_name_to_delete_select_val_del}'")
        pass
        
    if form_member_vbox_ref and hasattr(form_member_vbox_ref, 'layout') and form_member_vbox_ref.layout.display != 'none':
        form_member_vbox_ref.layout.display = 'none'
        form_member_container_in_ui_members = ui_members.get('form_member_container')
        if form_member_container_in_ui_members and hasattr(form_member_container_in_ui_members, 'layout'):
            form_member_container_in_ui_members.layout.display = 'none'
        
    if group_context_del and member_name_to_delete_select_val_del:
        institution_name_del = group_context_del['school']
        group_name_del = group_context_del['class_name']
        
        try:
            if institution_name_del in members_data and group_name_del in members_data.get(institution_name_del, {}):
                original_len_del = len(members_data[institution_name_del][group_name_del])
                nombre_del_sel_parsed, apellido_del_sel_parsed = parse_valor_select_en_nombre_apellido(member_name_to_delete_select_val_del)
                
                members_data[institution_name_del][group_name_del] = [
                    m_del_iter for m_del_iter in members_data[institution_name_del][group_name_del]
                    if not (m_del_iter.get('nome','').strip().lower() == nombre_del_sel_parsed.lower() and \
                            m_del_iter.get('cognome','').strip().title().lower() == apellido_del_sel_parsed.lower())
                ]
                
                if len(members_data[institution_name_del][group_name_del]) < original_len_del:
                    # with registro_output: print(f"  ÉXITO: Miembro '{member_name_to_delete_select_val_del}' eliminado de {group_name_del} ({institution_name_del}).")
                    
                    response_key_to_delete_del = (institution_name_del, group_name_del, member_name_to_delete_select_val_del)
                    if response_key_to_delete_del in questionnaire_responses_data:
                        del questionnaire_responses_data[response_key_to_delete_del]
                        # with registro_output: print(f"  INFO: Respuestas para '{member_name_to_delete_select_val_del}' eliminadas.")
                    
                    current_members_list_data_after_del = members_data[institution_name_del].get(group_name_del, [])
                    current_members_list_data_ordenada_after_del = sorted(
                        current_members_list_data_after_del,
                        key=lambda m_sort_del: (str(m_sort_del.get('nome', '')).strip().title(), str(m_sort_del.get('cognome', '')).strip().title())
                    )
                    
                    new_member_options_after_del = []
                    current_utils_for_options_after_del = _handlers_utils_ref_hm or globals().get('handlers_utils')
                    if current_utils_for_options_after_del and hasattr(current_utils_for_options_after_del, 'generar_opciones_dropdown_miembros_main_select'):
                        new_member_options_after_del = current_utils_for_options_after_del.generar_opciones_dropdown_miembros_main_select(current_members_list_data_ordenada_after_del)
                    else:
                        with registro_output: print("ERROR CRÍTICO (elimina_mem): generar_opciones_dropdown_miembros_main_select no disponible.");
                        for m_opt_fb_del_ui in current_members_list_data_ordenada_after_del:
                            m_n_fb_ui, m_c_fb_ui = m_opt_fb_del_ui.get('nome','').title(), m_opt_fb_del_ui.get('cognome','').title()
                            new_member_options_after_del.append((f"{m_n_fb_ui} {m_c_fb_ui}", f"{m_n_fb_ui} {m_c_fb_ui}"))

                    new_selection_after_delete_ui = new_member_options_after_del[0][1] if new_member_options_after_del else None
                    
                    if select_widget_del:
                        select_widget_del.options = new_member_options_after_del
                        if select_widget_del.value != new_selection_after_delete_ui:
                             select_widget_del.value = new_selection_after_delete_ui
                        elif refresh_func and callable(refresh_func):
                            change_event_del_ui = {'name': 'value', 'old': member_name_to_delete_select_val_del, 'new': new_selection_after_delete_ui, 'owner': select_widget_del, 'type': 'change'}
                            refresh_func(change_event_del_ui, app_state, ui_members, registro_output, form_member_vbox_ref=form_member_vbox_ref)
                    # with registro_output: print("  INFO (members_elimina): Lista de miembros en UI refrescada.")
                else:
                    with registro_output: print(f"  INFO (members_elimina): Miembro '{member_name_to_delete_select_val_del}' no encontrado para eliminar.")
            else:
                with registro_output: print(f"  INFO (members_elimina): Institución/Grupo no encontrado en datos.")
        except Exception as e_elim_mem_fatal:
            with registro_output: print(f"  ERROR al eliminar '{member_name_to_delete_select_val_del}': {e_elim_mem_fatal}\n{traceback.format_exc(limit=2)}")
    else:
        with registro_output: print("  INFO (members_elimina): Por favor, seleccione un miembro o falta contexto de grupo/institución.")


def on_members_questionario_button_handler(b, app_state, ui_members,
                                            switch_interface_main_ref,
                                            interfaces_ref,
                                            temp_ui_form_questionnaire_ref,
                                            ui_questions_management_ref,
                                            member_refresh_handler_ref,
                                            app_ui_ref,
                                            handlers_questionnaire_ref,
                                            handlers_questions_module_ref,
                                            ui_form_member_vbox_to_hide_ref,
                                            registro_output):
    if ui_form_member_vbox_to_hide_ref and hasattr(ui_form_member_vbox_to_hide_ref, 'layout') and ui_form_member_vbox_to_hide_ref.layout.display != 'none':
        ui_form_member_vbox_to_hide_ref.layout.display = 'none'
        if ui_members and isinstance(ui_members, dict):
            form_member_container_in_ui_members = ui_members.get('form_member_container')
            if form_member_container_in_ui_members and hasattr(form_member_container_in_ui_members, 'layout'):
                form_member_container_in_ui_members.layout.display = 'none'

    with registro_output:
        clear_output(wait=True)
        # print(f"\n--- HANDLER EJECUTADO: on_members_questionario_button_handler (v11.3 - Sexo, Inst/Grp) ---")
        pass
        
    select_widget_mem_q = ui_members.get("select") if isinstance(ui_members, dict) else None
    selected_member_name_for_q_ui = select_widget_mem_q.value if select_widget_mem_q else None
    group_context_q = app_state.get('current_group_viewing_members')
    
    if not group_context_q or not selected_member_name_for_q_ui:
        with registro_output: print("  ERROR (members_questionario): Seleccione un miembro o falta contexto de grupo/institución."); return
        
    institution_name_q = group_context_q['school']
    group_name_q = group_context_q['class_name']
    
    # with registro_output: print(f"  Preparando cuestionario para: '{selected_member_name_for_q_ui}' ({group_name_q}, {institution_name_q})")
    
    app_state['current_questionnaire_member_context'] = {'school': institution_name_q, 'class_name': group_name_q, 'member': selected_member_name_for_q_ui}
    app_state['return_interface'] = 'main_members'
    
    current_app_data_for_q_btn_mem = sociograma_data
    if not current_app_data_for_q_btn_mem or not hasattr(current_app_data_for_q_btn_mem, 'members_data'):
        with registro_output: print("  ERROR CRÍTICO (members_q_btn): sociograma_data o members_data no disponible."); return
    if not all([app_ui_ref, hasattr(app_ui_ref, 'create_form_questionnaire_vbox'), interfaces_ref, temp_ui_form_questionnaire_ref, handlers_questionnaire_ref, ui_questions_management_ref, handlers_questions_module_ref]):
        with registro_output: print("  ERROR CRÍTICO (members_q_btn): Faltan referencias esenciales para construir/enlazar UI del cuestionario."); return
    
    try:
        current_group_question_defs = get_class_question_definitions(institution_name_q, group_name_q)
        new_q_vbox_mem, new_q_ui_elements_mem = app_ui_ref.create_form_questionnaire_vbox(current_group_question_defs)
        
        interfaces_ref['form_questionnaire'] = new_q_vbox_mem
        temp_ui_form_questionnaire_ref.clear(); temp_ui_form_questionnaire_ref.update(new_q_ui_elements_mem)
        
        member_label_widget_q_mem = new_q_ui_elements_mem.get("student_label")
        if member_label_widget_q_mem: member_label_widget_q_mem.value = f"Miembro: {selected_member_name_for_q_ui} ({group_name_q} - {institution_name_q})"
        # with registro_output: print("  INFO (members_q_btn): UI del cuestionario (re)creada.")
        
        ok_button_q_mem = new_q_ui_elements_mem.get("ok_button")
        if ok_button_q_mem and hasattr(handlers_questionnaire_ref, 'on_q_ok_button_click_handler'):
            if hasattr(ok_button_q_mem, '_click_handlers') and ok_button_q_mem._click_handlers: ok_button_q_mem._click_handlers.callbacks = []
            ok_button_q_mem.on_click(functools.partial( handlers_questionnaire_ref.on_q_ok_button_click_handler, app_state=app_state, ui_form_questionnaire=new_q_ui_elements_mem, switch_interface_func=switch_interface_main_ref, registro_output=registro_output, ui_members=ui_members, member_refresh_func=member_refresh_handler_ref ))
        
        salir_button_q_mem = new_q_ui_elements_mem.get("salir_button")
        if salir_button_q_mem and hasattr(handlers_questionnaire_ref, 'on_q_salir_button_click_handler'):
            if hasattr(salir_button_q_mem, '_click_handlers') and salir_button_q_mem._click_handlers: salir_button_q_mem._click_handlers.callbacks = []
            salir_button_q_mem.on_click(functools.partial( handlers_questionnaire_ref.on_q_salir_button_click_handler, app_state=app_state, switch_interface_func=switch_interface_main_ref, registro_output=registro_output, ui_members=ui_members, member_refresh_func=member_refresh_handler_ref ))

        pdf_class_btn_q_mem = new_q_ui_elements_mem.get("pdf_class_button")
        if pdf_class_btn_q_mem and hasattr(handlers_questionnaire_ref, 'on_q_pdf_class_button_click_handler'):
            if hasattr(pdf_class_btn_q_mem, '_click_handlers') and pdf_class_btn_q_mem._click_handlers: pdf_class_btn_q_mem._click_handlers.callbacks = []
            pdf_class_btn_q_mem.on_click(functools.partial( handlers_questionnaire_ref.on_q_pdf_class_button_click_handler, app_state=app_state, registro_output=registro_output ))

        manage_q_button_q_mem = new_q_ui_elements_mem.get("manage_questions_button")
        if manage_q_button_q_mem and hasattr(handlers_questionnaire_ref, 'on_q_manage_questions_button_handler'):
            if hasattr(manage_q_button_q_mem, '_click_handlers') and manage_q_button_q_mem._click_handlers: manage_q_button_q_mem._click_handlers.callbacks = []
            manage_q_button_q_mem.on_click(functools.partial( handlers_questionnaire_ref.on_q_manage_questions_button_handler, app_state=app_state, ui_form_questionnaire=new_q_ui_elements_mem, ui_questions_management=ui_questions_management_ref, switch_interface_func=switch_interface_main_ref, registro_output=registro_output, handlers_questions_ref=handlers_questions_module_ref ))
        # with registro_output: print("  INFO (members_q_btn): Eventos de botones del cuestionario (re)enlazados.")

        if hasattr(handlers_questionnaire_ref, '_populate_questionnaire_dropdowns'):
            handlers_questionnaire_ref._populate_questionnaire_dropdowns( app_state, new_q_ui_elements_mem, registro_output, app_data_ref=current_app_data_for_q_btn_mem )
            # with registro_output: print("  INFO (members_q_btn): Dropdowns del cuestionario poblados.")
        else:
            with registro_output: print("  ERROR CRÍTICO (members_q_btn): '_populate_questionnaire_dropdowns' no encontrado en handlers_questionnaire."); return
        
        if switch_interface_main_ref: switch_interface_main_ref('form_questionnaire')
        else:
          with registro_output: print("  ERROR CRÍTICO (members_q_btn): switch_interface_main_ref no disponible."); return
          
    except Exception as e_mem_q_btn_final:
        with registro_output:
            print(f"  ERROR CRÍTICO (members_q_btn) al preparar o cambiar a la UI del cuestionario: {e_mem_q_btn_final}")
            print(traceback.format_exc(limit=2))
        app_state['current_questionnaire_member_context'] = None


def on_members_salir_button_handler(b, app_state, ui_groups, switch_interface_func, registro_output,
                                     group_refresh_func=None, ui_form_member_vbox_ref=None):
    with registro_output:
        clear_output(wait=True)
        # print("HANDLER (members v11.3): on_members_salir_button_handler")
        pass
        
    if ui_form_member_vbox_ref and hasattr(ui_form_member_vbox_ref, 'layout') and ui_form_member_vbox_ref.layout.display != 'none':
        ui_form_member_vbox_ref.layout.display = 'none'
        if isinstance(globals().get('ui_members'), dict):
            form_member_container_in_ui_members = globals().get('ui_members').get('form_member_container')
            if form_member_container_in_ui_members and hasattr(form_member_container_in_ui_members, 'layout'):
                form_member_container_in_ui_members.layout.display = 'none'
        
    current_institution_for_return_mem = app_state.get('current_institution_viewing_groups')
    current_group_context_mem_exit = app_state.get('current_group_viewing_members')
    
    app_state['current_group_viewing_members'] = None
    app_state['current_member_editing'] = None
    
    if current_institution_for_return_mem and current_group_context_mem_exit and \
       group_refresh_func and callable(group_refresh_func) and isinstance(ui_groups, dict):
        
        group_name_to_reselect_mem_exit = current_group_context_mem_exit.get('class_name')
        select_widget_group_exit = ui_groups.get("select")
        
        if select_widget_group_exit and group_name_to_reselect_mem_exit:
            institution_groups_options_list_exit = []
            if current_institution_for_return_mem in classes_data:
                 institution_groups_options_list_exit = sorted([g.get('name') for g in classes_data[current_institution_for_return_mem] if g.get('name')])
            select_widget_group_exit.options = institution_groups_options_list_exit
            
            if group_name_to_reselect_mem_exit in institution_groups_options_list_exit:
                if select_widget_group_exit.value != group_name_to_reselect_mem_exit:
                    select_widget_group_exit.value = group_name_to_reselect_mem_exit
                else:
                    change_event_data_grp_exit = {'name': 'value', 'old': group_name_to_reselect_mem_exit, 'new': group_name_to_reselect_mem_exit, 'owner': select_widget_group_exit, 'type': 'change'}
                    form_group_vbox_for_refresh_exit_mem = ui_groups.get("form_group_embedded_vbox_ref")
                    group_refresh_func(change_event_data_grp_exit, app_state, ui_groups, registro_output, form_group_vbox_ref=form_group_vbox_for_refresh_exit_mem)
                # with registro_output: print(f"  INFO (members_salir): UI de grupos refrescada para grupo '{group_name_to_reselect_mem_exit}'.")
            elif institution_groups_options_list_exit :
                 select_widget_group_exit.value = institution_groups_options_list_exit[0]
            else:
                 select_widget_group_exit.value = None
                 change_event_data_clear_grp_exit = {'name': 'value', 'old': None, 'new': None, 'owner': select_widget_group_exit, 'type': 'change'}
                 form_group_vbox_for_clear_grp_exit = ui_groups.get("form_group_embedded_vbox_ref")
                 group_refresh_func(change_event_data_clear_grp_exit, app_state, ui_groups, registro_output, form_group_vbox_ref=form_group_vbox_for_clear_grp_exit)
                 
    switch_interface_func('main_groups')