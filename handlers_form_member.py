# handlers_form_member.py
# (v10.0 - Renombrado de handlers_form_student.py. Usa "miembro", "sexo", "Institución"/"Grupo".)

from ipywidgets import widgets
from IPython.display import clear_output
import functools
import traceback
import collections

from sociograma_data import members_data, classes_data, questionnaire_responses_data, get_class_question_definitions
import sociograma_data

_handlers_utils_ref_hfm = globals().get('handlers_utils')

# Helper para parsear "Nombre Apellido"
def parse_nombre_apellido_flexible_hfm(nombre_completo_str):
    partes = nombre_completo_str.strip().split()
    if not partes: return "", ""
    if len(partes) == 1: return partes[0].strip(), ""
    nombre = " ".join(partes[:-1]).strip()
    apellido = partes[-1].strip()
    return nombre, apellido

# Helper para errores
def _print_error_hfm(ro_widget, message):
    if ro_widget:
        with ro_widget: print(message)

# --- Handlers para Formulario Actualización Miembro (empotrado en main_members) ---

def on_form_member_add_save_button_handler(b, app_state, ui_form_member, ui_members, switch_interface_func, registro_output, member_refresh_func=None):
    # with registro_output:
        # print("HANDLER (form_member v10.0 - Sexo, Inst/Grp): on_form_member_add_save_button_handler")

    form_elements = getattr(ui_form_member, '_ui_elements_ref', None)
    if not form_elements or not isinstance(form_elements, dict):
        _print_error_hfm(registro_output, "  ERROR (form_add_save_member): _ui_elements_ref no encontrado."); return

    group_context_add_mem = app_state.get('current_group_viewing_members')
    if not group_context_add_mem or not all(k in group_context_add_mem for k in ['school', 'class_name']):
        _print_error_hfm(registro_output, "  ERROR (form_add_save_member): Falta contexto de institución/grupo."); return
    institution_name_add_mem = group_context_add_mem['school']
    group_name_add_mem = group_context_add_mem['class_name']

    member_data = {}
    member_data['cognome'] = form_elements.get("cognome_input").value.strip().upper()
    member_data['nome'] = form_elements.get("nome_input").value.strip().title()
    member_data['iniz'] = form_elements.get("iniziali_input").value.strip().upper()

    sexo_seleccionado_widget_val_add = form_elements.get("gender_radio").value
    if sexo_seleccionado_widget_val_add not in ['Masculino', 'Femenino', 'Desconocido']:
        # _print_error_hfm(registro_output, f"  ADVERTENCIA (form_add_save_member): Sexo '{sexo_seleccionado_widget_val_add}' no reconocido, se guardará como 'Desconocido'.")
        sexo_seleccionado_widget_val_add = 'Desconocido'
    member_data['sexo'] = sexo_seleccionado_widget_val_add

    member_data['fecha_nac'] = form_elements.get("dob_input").value.strip()
    member_data['annotations'] = form_elements.get("annotations_textarea").value.strip()

    error_msg = ""
    if not member_data['cognome']: error_msg += "El apellido es obligatorio.\n"
    if not member_data['nome']: error_msg += "El nombre es obligatorio.\n"
    if not member_data['iniz'] or len(member_data['iniz']) < 3 or len(member_data['iniz']) > 4 or not member_data['iniz'].isalpha():
        error_msg += "Las iniciales deben ser 3 o 4 letras (ej. MRG o MRGL).\n"

    nombre_nuevo_titulo_add = member_data['nome']
    apellido_nuevo_mayus_add = member_data['cognome']

    if institution_name_add_mem not in sociograma_data.members_data:
        sociograma_data.members_data[institution_name_add_mem] = collections.OrderedDict()
    if group_name_add_mem not in sociograma_data.members_data[institution_name_add_mem]:
        sociograma_data.members_data[institution_name_add_mem][group_name_add_mem] = []

    existing_members_in_group_add = sociograma_data.members_data[institution_name_add_mem].get(group_name_add_mem, [])
    for existing_member_add in existing_members_in_group_add:
        if existing_member_add.get('cognome','').upper() == apellido_nuevo_mayus_add and \
           existing_member_add.get('nome','').title() == nombre_nuevo_titulo_add:
            error_msg += f"Ya existe un miembro llamado '{nombre_nuevo_titulo_add} {apellido_nuevo_mayus_add.title()}' en este grupo.\n"; break

    if error_msg:
        with registro_output:
             print(f"\n--- ERRORES DE VALIDACIÓN ---\n{error_msg.strip()}\n----------------------------\n"); return

    try:
        sociograma_data.members_data[institution_name_add_mem][group_name_add_mem].append(member_data)
        # with registro_output: print(f"  ÉXITO (form_add_save_member): Miembro '{nombre_nuevo_titulo_add} {apellido_nuevo_mayus_add.title()}' (Sexo: {member_data['sexo']}) añadido a {group_name_add_mem} ({institution_name_add_mem}).");

        app_state['current_member_editing'] = None

        if ui_form_member and hasattr(ui_form_member, 'layout'):
            ui_form_member.layout.display = 'none'

        if ui_members and member_refresh_func and callable(member_refresh_func):
            group_members_list_after_add = sociograma_data.members_data.get(institution_name_add_mem, {}).get(group_name_add_mem, [])
            group_members_list_after_add.sort(key=lambda m: (str(m.get('nome', '')).strip().title(), str(m.get('cognome', '')).strip().title()))

            member_options_display_after_add = []
            utils_ref_add_form_hfm = _handlers_utils_ref_hfm or globals().get('handlers_utils')
            if utils_ref_add_form_hfm and hasattr(utils_ref_add_form_hfm, 'generar_opciones_dropdown_miembros_main_select'):
                member_options_display_after_add = utils_ref_add_form_hfm.generar_opciones_dropdown_miembros_main_select(group_members_list_after_add)
            else:
                # with registro_output: print("ADVERTENCIA (form_add_save_member): generar_opciones_dropdown_miembros_main_select no en utils.")
                for m_refresh_add in group_members_list_after_add:
                    m_n_add, m_c_add, m_i_add = m_refresh_add.get('nome','').title(), m_refresh_add.get('cognome','').title(), m_refresh_add.get('iniz','N/A')
                    member_options_display_after_add.append((f"{m_n_add} {m_c_add} ({m_i_add})", f"{m_n_add} {m_c_add}".strip()))

            select_widget_mem_refresh_add = ui_members.get("select")
            if select_widget_mem_refresh_add:
                current_selection_before_refresh_add = select_widget_mem_refresh_add.value
                select_widget_mem_refresh_add.options = member_options_display_after_add
                valor_a_seleccionar_post_add_ui = f"{nombre_nuevo_titulo_add} {apellido_nuevo_mayus_add.title()}".strip()
                value_to_set_after_add_ui = None
                if valor_a_seleccionar_post_add_ui in [opt[1] for opt in member_options_display_after_add]:
                    value_to_set_after_add_ui = valor_a_seleccionar_post_add_ui
                elif member_options_display_after_add:
                    value_to_set_after_add_ui = member_options_display_after_add[0][1]

                if select_widget_mem_refresh_add.value != value_to_set_after_add_ui:
                    select_widget_mem_refresh_add.value = value_to_set_after_add_ui
                else:
                    change_event_data_add_form = {'name': 'value', 'old': current_selection_before_refresh_add, 'new': value_to_set_after_add_ui, 'owner': select_widget_mem_refresh_add, 'type': 'change'}
                    form_member_vbox_for_refresh_add = getattr(ui_members, 'form_member_embedded_vbox_ref', None)
                    member_refresh_func(change_event_data_add_form, app_state, ui_members, registro_output, form_member_vbox_ref=form_member_vbox_for_refresh_add)
            # with registro_output: print("  INFO (form_add_save_member): Lista de miembros en ui_members refrescada.")

    except Exception as e_add_mem_v10_0_final:
        with registro_output: print(f"  ERROR CRÍTICO al añadir miembro: {e_add_mem_v10_0_final}\n{traceback.format_exc(limit=2)}")


def on_form_member_modify_ok_button_handler(b, app_state, ui_form_member, ui_members, switch_interface_func, registro_output, member_refresh_func=None):
    # with registro_output:
        # print("HANDLER (form_member v10.0 - Sexo, Inst/Grp): on_form_member_modify_ok_button_handler")

    form_elements = getattr(ui_form_member, '_ui_elements_ref', None)
    if not form_elements: _print_error_hfm(registro_output, "  ERROR (form_modify_save_member): _ui_elements_ref no encontrado."); return

    editing_context_mod = app_state.get('current_member_editing')
    if not editing_context_mod or not all(k in editing_context_mod for k in ['school', 'class_name', 'member_name', 'original_data']):
        _print_error_hfm(registro_output, "  ERROR (form_modify_save_member): Falta contexto de edición válido (institución/grupo)."); return

    institution_name_mod_mem = editing_context_mod['school']
    group_name_mod_mem = editing_context_mod['class_name']
    original_member_name_context_mod = editing_context_mod['member_name']
    original_data_dict_mod = editing_context_mod['original_data']

    updated_data = {}
    updated_data['cognome'] = form_elements.get("cognome_input").value.strip().upper()
    updated_data['nome'] = form_elements.get("nome_input").value.strip().title()
    updated_data['iniz'] = form_elements.get("iniziali_input").value.strip().upper()

    sexo_seleccionado_mod_widget_val_ok = form_elements.get("gender_radio").value
    if sexo_seleccionado_mod_widget_val_ok not in ['Masculino', 'Femenino', 'Desconocido']:
        # _print_error_hfm(registro_output, f"  ADVERTENCIA (form_modify_save_member): Sexo '{sexo_seleccionado_mod_widget_val_ok}' no reconocido, guardado como 'Desconocido'.")
        sexo_seleccionado_mod_widget_val_ok = 'Desconocido'
    updated_data['sexo'] = sexo_seleccionado_mod_widget_val_ok

    updated_data['fecha_nac'] = form_elements.get("dob_input").value.strip()
    updated_data['annotations'] = form_elements.get("annotations_textarea").value.strip()

    error_msg = ""
    if not updated_data['cognome']: error_msg += "El apellido es obligatorio.\n"
    if not updated_data['nome']: error_msg += "El nombre es obligatorio.\n"
    if not updated_data['iniz'] or len(updated_data['iniz']) < 3 or len(updated_data['iniz']) > 4 or not updated_data['iniz'].isalpha():
        error_msg += "Las iniciales deben ser 3 o 4 letras.\n"

    nuevo_nombre_para_clave_y_select_mod = f"{updated_data['nome']} {updated_data['cognome'].title()}".strip()

    if nuevo_nombre_para_clave_y_select_mod.lower() != original_member_name_context_mod.lower():
        existing_members_check_mod = sociograma_data.members_data.get(institution_name_mod_mem, {}).get(group_name_mod_mem, [])
        for m_check_mod in existing_members_check_mod:
            existing_nome_check_mod, existing_cognome_check_mod = m_check_mod.get('nome','').strip().title(), m_check_mod.get('cognome','').strip().title()
            if f"{existing_nome_check_mod} {existing_cognome_check_mod}".strip().lower() == nuevo_nombre_para_clave_y_select_mod.lower():
                error_msg += f"Ya existe otro miembro llamado '{nuevo_nombre_para_clave_y_select_mod}' en este grupo.\n"; break
    
    if error_msg:
        with registro_output: print(f"\n--- ERRORES DE VALIDACIÓN ---\n{error_msg.strip()}\n"); return

    try:
        members_list_ref_mod = sociograma_data.members_data.get(institution_name_mod_mem, {}).get(group_name_mod_mem)
        member_found_and_updated_mod = False
        if members_list_ref_mod is not None:
            original_cognome_search_mayus_mod = original_data_dict_mod.get('cognome', '').upper()
            original_nome_search_titulo_mod = original_data_dict_mod.get('nome', '').title()

            for i_mod, member_dict_ref_mod in enumerate(members_list_ref_mod):
                if member_dict_ref_mod.get('cognome', '').upper() == original_cognome_search_mayus_mod and \
                   member_dict_ref_mod.get('nome', '').title() == original_nome_search_titulo_mod:
                    members_list_ref_mod[i_mod].update(updated_data)
                    member_found_and_updated_mod = True
                    if nuevo_nombre_para_clave_y_select_mod.lower() != original_member_name_context_mod.lower():
                        old_resp_key_mod = (institution_name_mod_mem, group_name_mod_mem, original_member_name_context_mod)
                        if old_resp_key_mod in sociograma_data.questionnaire_responses_data:
                            sociograma_data.questionnaire_responses_data[(institution_name_mod_mem, group_name_mod_mem, nuevo_nombre_para_clave_y_select_mod)] = sociograma_data.questionnaire_responses_data.pop(old_resp_key_mod)
                            # with registro_output: print(f"  INFO: Clave de respuestas actualizada de '{original_member_name_context_mod}' a '{nuevo_nombre_para_clave_y_select_mod}'.")
                    break
        
        if not member_found_and_updated_mod:
            with registro_output: print(f"  ERROR (form_modify_save_member): No se encontró miembro original."); return

        # with registro_output: print(f"  ÉXITO: Datos del miembro '{nuevo_nombre_para_clave_y_select_mod}' (Sexo: {updated_data['sexo']}) actualizados en {group_name_mod_mem} ({institution_name_mod_mem}).")
        app_state['current_member_editing'] = None
        
        if ui_form_member and hasattr(ui_form_member, 'layout'):
            ui_form_member.layout.display = 'none'

        if ui_members and member_refresh_func and callable(member_refresh_func):
            group_members_list_refresh_mod = sociograma_data.members_data.get(institution_name_mod_mem, {}).get(group_name_mod_mem, [])
            group_members_list_refresh_mod.sort(key=lambda m: (str(m.get('nome', '')).strip().title(), str(m.get('cognome', '')).strip().title()))
            member_options_display_refresh_mod = []
            utils_ref_mod_form_hfm = _handlers_utils_ref_hfm or globals().get('handlers_utils')
            if utils_ref_mod_form_hfm and hasattr(utils_ref_mod_form_hfm, 'generar_opciones_dropdown_miembros_main_select'):
                member_options_display_refresh_mod = utils_ref_mod_form_hfm.generar_opciones_dropdown_miembros_main_select(group_members_list_refresh_mod)
            else:
                # with registro_output: print("ADVERTENCIA (form_modify_save_member): generar_opciones_dropdown_miembros_main_select no en utils.")
                for m_refresh_mod_ui in group_members_list_refresh_mod:
                    m_n_mod, m_c_mod, m_i_mod = m_refresh_mod_ui.get('nome','').title(), m_refresh_mod_ui.get('cognome','').title(), m_refresh_mod_ui.get('iniz','N/A')
                    member_options_display_refresh_mod.append((f"{m_n_mod} {m_c_mod} ({m_i_mod})", f"{m_n_mod} {m_c_mod}".strip()))

            select_widget_mem_mod_refresh_ui = ui_members.get("select")
            if select_widget_mem_mod_refresh_ui:
                current_selection_before_refresh_mod_ui = select_widget_mem_mod_refresh_ui.value
                select_widget_mem_mod_refresh_ui.options = member_options_display_refresh_mod
                value_to_set_after_mod_ui = nuevo_nombre_para_clave_y_select_mod

                if value_to_set_after_mod_ui in [opt[1] for opt in member_options_display_refresh_mod]:
                    select_widget_mem_mod_refresh_ui.value = value_to_set_after_mod_ui
                elif member_options_display_refresh_mod:
                     select_widget_mem_mod_refresh_ui.value = member_options_display_refresh_mod[0][1]
                else:
                    select_widget_mem_mod_refresh_ui.value = None
                
                if select_widget_mem_mod_refresh_ui.value == value_to_set_after_mod_ui :
                     change_event_data_mod_form = {'name': 'value', 'old': original_member_name_context_mod, 'new': value_to_set_after_mod_ui, 'owner': select_widget_mem_mod_refresh_ui, 'type': 'change'}
                     form_member_vbox_for_refresh_mod_ui = getattr(ui_members, 'form_member_embedded_vbox_ref', None)
                     member_refresh_func(change_event_data_mod_form, app_state, ui_members, registro_output, form_member_vbox_ref=form_member_vbox_for_refresh_mod_ui)

            # with registro_output: print("  INFO (form_modify_save_member): Lista de miembros en ui_members refrescada.")
        
    except Exception as e_mod_mem_v10_0_final:
        with registro_output: print(f"  ERROR CRÍTICO al actualizar: {e_mod_mem_v10_0_final}\n{traceback.format_exc(limit=2)}")


def on_form_member_cancel_button_handler(b, app_state, ui_form_member, switch_interface_func, registro_output, ui_members=None, member_refresh_func=None):
    # with registro_output:
        # print("HANDLER (form_member v10.0 - Sexo, Inst/Grp): on_form_member_cancel_button_handler")
    original_member_context_cancel = app_state.get('current_member_editing')
    app_state['current_member_editing'] = None
    if ui_form_member and hasattr(ui_form_member, 'layout'):
        ui_form_member.layout.display = 'none'
    if ui_members and member_refresh_func and callable(member_refresh_func):
        select_widget_mem_cancel = ui_members.get("select")
        current_selection_to_restore_cancel = None
        if original_member_context_cancel and 'member_name' in original_member_context_cancel:
            current_selection_to_restore_cancel = original_member_context_cancel['member_name']
        elif select_widget_mem_cancel and select_widget_mem_cancel.value is not None:
             current_selection_to_restore_cancel = select_widget_mem_cancel.value
        elif select_widget_mem_cancel and select_widget_mem_cancel.options:
            current_selection_to_restore_cancel = select_widget_mem_cancel.options[0][1] if select_widget_mem_cancel.options and len(select_widget_mem_cancel.options[0]) > 1 else None
        if select_widget_mem_cancel:
            valid_options_cancel = [opt[1] for opt in select_widget_mem_cancel.options if isinstance(opt, tuple) and len(opt) > 1]
            if current_selection_to_restore_cancel not in valid_options_cancel:
                current_selection_to_restore_cancel = valid_options_cancel[0] if valid_options_cancel else None
            if select_widget_mem_cancel.value != current_selection_to_restore_cancel :
                select_widget_mem_cancel.value = current_selection_to_restore_cancel
            else:
                 change_event_cancel_mem = {'name': 'value', 'old': None, 'new': current_selection_to_restore_cancel, 'owner': select_widget_mem_cancel, 'type': 'change'}
                 form_member_vbox_for_cancel_refresh = getattr(ui_members, 'form_member_embedded_vbox_ref', None)
                 member_refresh_func(change_event_cancel_mem, app_state, ui_members, registro_output, form_member_vbox_ref=form_member_vbox_for_cancel_refresh)
        # with registro_output: print(f"  INFO (form_cancel_member): Selección en ui_members verificada/refrescada.")

def on_form_member_q_button_handler(b, app_state, ui_form_member,
                                     switch_interface_main_ref,
                                     registro_output_area_ref,
                                     interfaces_ref,
                                     temp_ui_form_questionnaire_ref,
                                     ui_questions_management_ref,
                                     member_refresh_handler_ref,
                                     app_ui_ref,
                                     handlers_questionnaire_ref,
                                     handlers_questions_module_ref
                                    ):
    if ui_form_member and hasattr(ui_form_member, 'layout') and ui_form_member.layout.display != 'none':
        ui_form_member.layout.display = 'none'

    # with registro_output_area_ref:
        # print(f"\n--- INICIO HANDLER: on_form_member_q_button_handler (v10.0 - Sexo, Inst/Grp) ---")
    
    editing_context_q_btn = app_state.get('current_member_editing')
    if not editing_context_q_btn or not all(k in editing_context_q_btn for k in ['school', 'class_name', 'member_name']):
         with registro_output_area_ref: print("  ERROR (form_q_btn_member): Contexto de edición de miembro inválido (falta inst/grupo/nombre)."); return

    selected_member_full_name_for_q_context_btn = editing_context_q_btn['member_name']
    institution_name_q_btn = editing_context_q_btn['school']
    group_name_q_btn = editing_context_q_btn['class_name']
    
    # with registro_output_area_ref:
        # print(f"  Para miembro (contexto cuestionario): '{selected_member_full_name_for_q_context_btn}' ({group_name_q_btn} - {institution_name_q_btn})")

    app_state['current_questionnaire_member_context'] = { 'school': institution_name_q_btn, 'class_name': group_name_q_btn, 'member': selected_member_full_name_for_q_context_btn }
    app_state['return_interface'] = 'main_members'

    current_app_data_for_form_q_handler = sociograma_data
    if not current_app_data_for_form_q_handler or not hasattr(current_app_data_for_form_q_handler, 'members_data'):
        with registro_output_area_ref: print("  ERROR CRÍTICO (form_q_btn_member): sociograma_data.members_data no disponible."); return
    if not app_ui_ref or not hasattr(app_ui_ref, 'create_form_questionnaire_vbox'):
        with registro_output_area_ref: print("  ERROR CRÍTICO (form_q_btn_member): app_ui_ref no disponible."); return
    if not handlers_questionnaire_ref:
        with registro_output_area_ref: print("  ERROR CRÍTICO (form_q_btn_member): handlers_questionnaire_ref es None."); return
    if not handlers_questions_module_ref:
        with registro_output_area_ref: print(f"  ERROR CRÍTICO (form_q_btn_member): handlers_questions_module_ref es None."); return
    try:
        current_group_question_defs_q_btn = get_class_question_definitions(institution_name_q_btn, group_name_q_btn)
        new_q_vbox_q_btn, new_q_ui_elements_q_btn = app_ui_ref.create_form_questionnaire_vbox(current_group_question_defs_q_btn)
        if interfaces_ref and isinstance(interfaces_ref, dict): interfaces_ref['form_questionnaire'] = new_q_vbox_q_btn
        if temp_ui_form_questionnaire_ref is not None and isinstance(temp_ui_form_questionnaire_ref, dict):
            temp_ui_form_questionnaire_ref.clear(); temp_ui_form_questionnaire_ref.update(new_q_ui_elements_q_btn)
        if isinstance(new_q_ui_elements_q_btn, dict):
            member_label_widget_q_btn = new_q_ui_elements_q_btn.get("student_label")
            if member_label_widget_q_btn and isinstance(member_label_widget_q_btn, widgets.Label):
                member_label_widget_q_btn.value = f"Miembro: {selected_member_full_name_for_q_context_btn} ({group_name_q_btn} - {institution_name_q_btn})"
        # with registro_output_area_ref: print("  INFO (form_q_btn_member): UI cuestionario recreada.")
        if isinstance(new_q_ui_elements_q_btn, dict):
            ui_members_main_table_ref_q_btn = globals().get('ui_members')
            ok_button_q_btn = new_q_ui_elements_q_btn.get("ok_button")
            if ok_button_q_btn and hasattr(handlers_questionnaire_ref, 'on_q_ok_button_click_handler'):
                if hasattr(ok_button_q_btn, '_click_handlers') and ok_button_q_btn._click_handlers: ok_button_q_btn._click_handlers.callbacks = []
                ok_button_q_btn.on_click( functools.partial( handlers_questionnaire_ref.on_q_ok_button_click_handler, app_state=app_state, ui_form_questionnaire=new_q_ui_elements_q_btn, switch_interface_func=switch_interface_main_ref, registro_output=registro_output_area_ref, ui_members=ui_members_main_table_ref_q_btn, member_refresh_func=member_refresh_handler_ref ) )
            salir_button_q_btn = new_q_ui_elements_q_btn.get("salir_button")
            if salir_button_q_btn and hasattr(handlers_questionnaire_ref, 'on_q_salir_button_click_handler'):
                if hasattr(salir_button_q_btn, '_click_handlers') and salir_button_q_btn._click_handlers: salir_button_q_btn._click_handlers.callbacks = []
                salir_button_q_btn.on_click( functools.partial( handlers_questionnaire_ref.on_q_salir_button_click_handler, app_state=app_state, switch_interface_func=switch_interface_main_ref, registro_output=registro_output_area_ref, ui_members=ui_members_main_table_ref_q_btn, member_refresh_func=member_refresh_handler_ref ) )
            pdf_class_btn_q_btn = new_q_ui_elements_q_btn.get("pdf_class_button")
            if pdf_class_btn_q_btn and hasattr(handlers_questionnaire_ref, 'on_q_pdf_class_button_click_handler'):
                if hasattr(pdf_class_btn_q_btn, '_click_handlers') and pdf_class_btn_q_btn._click_handlers: pdf_class_btn_q_btn._click_handlers.callbacks = []
                pdf_class_btn_q_btn.on_click( functools.partial( handlers_questionnaire_ref.on_q_pdf_class_button_click_handler, app_state=app_state, registro_output=registro_output_area_ref ) )
            manage_q_button_q_btn = new_q_ui_elements_q_btn.get("manage_questions_button")
            if manage_q_button_q_btn and hasattr(handlers_questionnaire_ref, 'on_q_manage_questions_button_handler'):
                if hasattr(manage_q_button_q_btn, '_click_handlers') and manage_q_button_q_btn._click_handlers: manage_q_button_q_btn._click_handlers.callbacks = []
                if ui_questions_management_ref and handlers_questions_module_ref:
                    manage_q_button_q_btn.on_click( functools.partial( handlers_questionnaire_ref.on_q_manage_questions_button_handler, app_state=app_state, ui_form_questionnaire=new_q_ui_elements_q_btn, ui_questions_management=ui_questions_management_ref, switch_interface_func=switch_interface_main_ref, registro_output=registro_output_area_ref, handlers_questions_ref=handlers_questions_module_ref ))
            # with registro_output_area_ref: print("  INFO (form_q_btn_member): Eventos controles cuestionario enlazados.")
        if hasattr(handlers_questionnaire_ref, '_populate_questionnaire_dropdowns'):
            handlers_questionnaire_ref._populate_questionnaire_dropdowns( app_state, new_q_ui_elements_q_btn, registro_output_area_ref, app_data_ref=current_app_data_for_form_q_handler )
            # with registro_output_area_ref: print("  INFO (form_q_btn_member): _populate_questionnaire_dropdowns finalizado.")
        else:
            with registro_output_area_ref: print(f"  ERROR (form_q_btn_member): '_populate_questionnaire_dropdowns' no encontrado."); app_state['current_questionnaire_member_context'] = None; return
        if switch_interface_main_ref: switch_interface_main_ref('form_questionnaire')
        else: 
          with registro_output_area_ref: print("  ERROR CRÍTICO (form_q_btn_member): switch_interface_main_ref no encontrado.")
    except Exception as e_recreate_form_q_v10_0_final:
        with registro_output_area_ref: print(f"  ERROR CRÍTICO (form_q_btn_member) al recrear UI cuestionario: {e_recreate_form_q_v10_0_final}"); print(traceback.format_exc(limit=2))
        app_state['current_questionnaire_member_context'] = None