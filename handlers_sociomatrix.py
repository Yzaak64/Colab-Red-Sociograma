# handlers_sociomatrix.py
# (v27.0 - Usa "Institución"/"Grupo", "sexo" y "miembro")

from ipywidgets import widgets, Checkbox, Label, HBox, VBox, Button, Output, Layout
from IPython.display import display, HTML, clear_output
import collections
import functools
import sys
import traceback
import re
import io
import base64
import datetime

from sociograma_data import members_data, get_class_question_definitions, questionnaire_responses_data, classes_data
import pdf_generator

def draw_sociomatrix_as_html_multi(institution_name, group_name, selected_data_keys_list, registro_output):
    if not institution_name or not group_name:
        return "<p style='color:red;'>Error: Institución o grupo no especificados.</p>"
    if not selected_data_keys_list:
        return "<p style='color:grey; text-align:center; padding-top:20px;'><i>Seleccione al menos una pregunta y haga clic en 'Actualizar Matriz'.</i></p>"

    members_list_raw_sm = members_data.get(institution_name, {}).get(group_name, [])
    if not members_list_raw_sm:
        return f"<p style='color:orange;'>No hay miembros registrados en el grupo '{group_name}' de la institución '{institution_name}' para generar la matriz.</p>"

    key_sort_display_sm = lambda s: (
        str(s.get('nome','').strip()).title(),
        str(s.get('cognome','').strip()).title()
    )
    all_members_sorted_for_matrix_sm = sorted(members_list_raw_sm, key=key_sort_display_sm)

    member_initials_for_cols_display_sm = []
    member_fullnames_for_cols_key_format_sm = []
    member_fullnames_for_cols_display_label_sm = []

    for m_col_matrix_sm in all_members_sorted_for_matrix_sm:
        nome_col_titulo_matrix_sm = m_col_matrix_sm.get('nome','').strip().title()
        cognome_col_titulo_matrix_sm = m_col_matrix_sm.get('cognome','').strip().title()
        member_initials_for_cols_display_sm.append(m_col_matrix_sm.get('iniz','N/A').upper())
        member_fullnames_for_cols_key_format_sm.append(f"{nome_col_titulo_matrix_sm} {cognome_col_titulo_matrix_sm}".strip())
        member_fullnames_for_cols_display_label_sm.append(f"{nome_col_titulo_matrix_sm[:1]}. {cognome_col_titulo_matrix_sm}")

    election_matrix_sm = collections.defaultdict(lambda: collections.defaultdict(int))
    for (resp_institution, resp_group, nominator_name_key_sm), member_responses_dict_sm in questionnaire_responses_data.items():
        if resp_institution == institution_name and resp_group == group_name:
            for question_data_key_sm in selected_data_keys_list:
                if question_data_key_sm in member_responses_dict_sm:
                    nominated_by_this_member_for_q_sm = member_responses_dict_sm[question_data_key_sm]
                    for nominee_name_key_sm in nominated_by_this_member_for_q_sm:
                        election_matrix_sm[nominator_name_key_sm][nominee_name_key_sm] += 1
    
    html_sm = "<style>"
    html_sm += "body { font-family: sans-serif; }"
    html_sm += "div.matrix-container { overflow-x: auto; max-width: 100%; background-color: #fff; padding:10px; box-sizing: border-box; }"
    html_sm += "table.sociomatrix { border-collapse: collapse; font-size: 10px; margin: 10px 0; table-layout: auto; width: 1%; white-space: nowrap; }"
    html_sm += "table.sociomatrix th, table.sociomatrix td { border: 1px solid #ccc; padding: 5px 7px; text-align: center; vertical-align: middle; background-color: white; }"
    color_nominativi_header_bg_sm = "#e0e0e0"; color_nominativi_cell_bg_sm = "white"
    color_scelte_header_bg_sm = "#ddeeff"; color_total_header_bg_sm = "#e0e0e0"
    color_total_cell_data_bg_sm = "#f0f0f0"; color_self_choice_bg_sm = "#dddddd" 
    color_gender_group_header_bg_sm = "#cce5ff"; color_gender_total_row_bg_sm = "#e9e9e9"
    color_tfoot_nominativi_bg_sm = "#d0d0d0"; color_tfoot_total_bg_sm = "#d0d0d0"
    html_sm += f"table.sociomatrix th.nominativi-header {{ text-align: left; background-color: {color_nominativi_header_bg_sm}; font-weight:bold; min-width:180px; position: sticky; left: 0; z-index: 10; box-shadow: 2px 0 3px -1px rgba(0,0,0,0.1); }}"
    html_sm += f"table.sociomatrix td.nominativi-cell {{ text-align: left; background-color: {color_nominativi_cell_bg_sm}; font-weight:normal; position: sticky; left: 0; z-index: 9; box-shadow: 2px 0 3px -1px rgba(0,0,0,0.1);}}"
    html_sm += f"table.sociomatrix th.scelte-header {{ background-color: {color_scelte_header_bg_sm}; font-weight:bold; min-width:45px; max-width:70px; overflow:hidden; text-overflow:ellipsis; vertical-align:middle; padding-bottom:4px; padding-top:4px; }}"
    html_sm += "table.sociomatrix td.choice-cell { min-width:45px; }"
    html_sm += f"table.sociomatrix th.total-header {{ font-weight:bold; background-color: {color_total_header_bg_sm}; min-width:50px; }}"
    html_sm += f"table.sociomatrix td.total-cell {{ font-weight:bold; background-color: {color_total_cell_data_bg_sm}; }}"
    html_sm += f"table.sociomatrix td.self-choice-cell {{ background-color: {color_self_choice_bg_sm} !important; }}"
    html_sm += f"tr.gender-group-header td {{ background-color: {color_gender_group_header_bg_sm} !important; font-weight: bold; text-align:left !important; padding-left: 5px !important; z-index: 11 !important; position:sticky; left:0; }}"
    html_sm += f"tr.gender-total-row td {{ background-color: {color_gender_total_row_bg_sm} !important; font-weight: bold; }}"
    html_sm += f"tr.gender-total-row td.nominativi-cell {{ background-color: {color_gender_total_row_bg_sm} !important; }}"
    html_sm += f"tfoot td.nominativi-cell {{ background-color: {color_tfoot_nominativi_bg_sm} !important; }}"
    html_sm += f"tfoot td.total-cell {{ background-color: {color_tfoot_total_bg_sm} !important; }}"
    html_sm += """@media print { @page { size: A4 landscape; margin: 1cm; } body { font-family: sans-serif; -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; } table.sociomatrix { font-size: 7.5pt; line-height: 1.5; width: 100%; table-layout: fixed; border-spacing: 0; margin: 0; } table.sociomatrix th, table.sociomatrix td { padding: 4px 3px; border: 0.5pt solid #ccc; word-wrap: break-word; }"""
    html_sm += f"table.sociomatrix thead tr th.nominativi-header {{ background-color: {color_nominativi_header_bg_sm} !important; }}"
    html_sm += f"table.sociomatrix tbody tr td.nominativi-cell {{ background-color: {color_nominativi_cell_bg_sm} !important; }}"
    html_sm += f"table.sociomatrix thead tr th.scelte-header {{ background-color: {color_scelte_header_bg_sm} !important; }}"
    html_sm += f"table.sociomatrix thead tr th.total-header {{ background-color: {color_total_header_bg_sm} !important; }}"
    html_sm += f"table.sociomatrix tbody tr td.choice-cell {{ background-color: white !important; }}"
    html_sm += f"table.sociomatrix tbody tr td.total-cell {{ background-color: {color_total_cell_data_bg_sm} !important; }}"
    html_sm += f"table.sociomatrix tbody tr td.self-choice-cell {{ background-color: {color_self_choice_bg_sm} !important; }}"
    html_sm += f"table.sociomatrix tbody tr.gender-group-header td {{ background-color: {color_gender_group_header_bg_sm} !important; }}"
    html_sm += f"table.sociomatrix tbody tr.gender-total-row td {{ background-color: {color_gender_total_row_bg_sm} !important; }}"
    html_sm += f"table.sociomatrix tbody tr.gender-total-row td.nominativi-cell {{ background-color: {color_gender_total_row_bg_sm} !important; }}"
    html_sm += f"table.sociomatrix tfoot tr td.nominativi-cell {{ background-color: {color_tfoot_nominativi_bg_sm} !important; }}"
    html_sm += f"tfoot tr td.total-cell {{ background-color: {color_tfoot_total_bg_sm} !important; }}"
    html_sm += """ table.sociomatrix th.nominativi-header { width: 28%; min-width: 140px; text-align: left; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-size: 7.5pt; position: static !important; box-shadow: none !important; } table.sociomatrix td.nominativi-cell { text-align: left; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-size: 7.5pt; position: static !important; box-shadow: none !important; } table.sociomatrix th.scelte-header { font-size: 7pt; padding: 3px 1.5px; letter-spacing: 0.3px; line-height: 1.2; } table.sociomatrix td.choice-cell { font-size: 7.5pt; } table.sociomatrix th.total-header { width: 7%; min-width: 30px; font-size: 7pt;} table.sociomatrix td.total-cell { font-size: 7.5pt; } tr.gender-group-header td { padding-top: 3px !important; padding-bottom: 3px !important; position: static !important; } tr.gender-total-row td { padding-top: 3px !important; padding-bottom: 3px !important; } tfoot td { padding-top: 3px !important; padding-bottom: 3px !important; } div.matrix-container { overflow-x: visible; padding: 0; } } </style>"""
    html_sm += "<div class='matrix-container'><table class='sociomatrix'><thead><tr><th class='nominativi-header'>Nominador \\ Elegido</th>"
    for idx_header_col_sm, initial_header_col_sm in enumerate(member_initials_for_cols_display_sm):
        html_sm += f"<th class='scelte-header' title='{member_fullnames_for_cols_display_label_sm[idx_header_col_sm]}'>{initial_header_col_sm}</th>"
    html_sm += "<th class='total-header'>TOTAL<br/>Hechas</th></tr></thead><tbody>"
    
    members_f_matrix_sm = [s for s in all_members_sorted_for_matrix_sm if s.get('sexo','').lower() == 'femenino']
    members_m_matrix_sm = [s for s in all_members_sorted_for_matrix_sm if s.get('sexo','').lower() == 'masculino']
    members_o_matrix_sm = [s for s in all_members_sorted_for_matrix_sm if s.get('sexo','').lower() not in ['femenino', 'masculino']]
    
    nominators_grouped_matrix_sm = []
    if members_f_matrix_sm: nominators_grouped_matrix_sm.append(("Femenino", members_f_matrix_sm))
    if members_m_matrix_sm: nominators_grouped_matrix_sm.append(("Masculino", members_m_matrix_sm))
    if members_o_matrix_sm: nominators_grouped_matrix_sm.append(("Sexo Desconocido/Otro", members_o_matrix_sm))
    
    grand_total_selections_made_overall_matrix_sm = 0
    grand_column_totals_received_overall_matrix_sm = [0] * len(all_members_sorted_for_matrix_sm)
    
    for group_name_matrix_sm, members_in_group_for_rows_matrix_sm in nominators_grouped_matrix_sm:
        if not members_in_group_for_rows_matrix_sm: continue
        html_sm += f"<tr class='gender-group-header'><td colspan='{len(member_initials_for_cols_display_sm) + 2}'>{group_name_matrix_sm}</td></tr>"
        
        group_column_selections_made_to_nominees_matrix_sm = [0] * len(all_members_sorted_for_matrix_sm)
        group_total_selections_made_by_group_matrix_sm = 0
        
        for nominator_info_matrix_sm in members_in_group_for_rows_matrix_sm:
            nominator_nome_titulo_fila_matrix_sm = nominator_info_matrix_sm.get('nome','').strip().title()
            nominator_cognome_titulo_fila_matrix_sm = nominator_info_matrix_sm.get('cognome','').strip().title()
            nominator_full_name_key_format_fila_matrix_sm = f"{nominator_nome_titulo_fila_matrix_sm} {nominator_cognome_titulo_fila_matrix_sm}".strip()
            nominator_display_label_fila_matrix_sm = f"{nominator_cognome_titulo_fila_matrix_sm}, {nominator_nome_titulo_fila_matrix_sm}" 
            html_sm += f"<tr><td class='nominativi-cell'>{nominator_display_label_fila_matrix_sm}</td>"
            row_total_selections_made_by_nominator_matrix_sm = 0
            
            for i_col_matrix_sm, nominee_full_name_for_col_key_format_matrix_sm in enumerate(member_fullnames_for_cols_key_format_sm):
                if nominator_full_name_key_format_fila_matrix_sm == nominee_full_name_for_col_key_format_matrix_sm:
                    html_sm += f"<td class='choice-cell self-choice-cell'></td>"; continue
                count_sm = election_matrix_sm[nominator_full_name_key_format_fila_matrix_sm].get(nominee_full_name_for_col_key_format_matrix_sm, 0)
                display_val_sm = str(count_sm) if count_sm > 0 else ""; html_sm += f"<td class='choice-cell'>{display_val_sm}</td>"
                row_total_selections_made_by_nominator_matrix_sm += count_sm
                group_column_selections_made_to_nominees_matrix_sm[i_col_matrix_sm] += count_sm
                grand_column_totals_received_overall_matrix_sm[i_col_matrix_sm] += count_sm
            html_sm += f"<td class='total-cell'>{row_total_selections_made_by_nominator_matrix_sm}</td>"
            group_total_selections_made_by_group_matrix_sm += row_total_selections_made_by_nominator_matrix_sm
            html_sm += "</tr>"
        html_sm += f"<tr class='gender-total-row'><td class='nominativi-cell'><b>Total por {group_name_matrix_sm} (Hechas)</b></td>"
        for total_made_to_nominee_matrix_sm in group_column_selections_made_to_nominees_matrix_sm: html_sm += f"<td class='total-cell'>{total_made_to_nominee_matrix_sm}</td>"
        html_sm += f"<td class='total-cell'>{group_total_selections_made_by_group_matrix_sm}</td></tr>"
        
    grand_total_selections_made_overall_matrix_sm = sum(grand_column_totals_received_overall_matrix_sm)
    html_sm += "</tbody><tfoot><tr><td class='nominativi-cell'><b>TOTAL GENERAL Recibidas</b></td>"
    for total_received_matrix_sm in grand_column_totals_received_overall_matrix_sm: html_sm += f"<td class='total-cell'>{total_received_matrix_sm}</td>"
    html_sm += f"<td class='total-cell'><b>{grand_total_selections_made_overall_matrix_sm}</b></td></tr></tfoot></table></div>"
    return html_sm

def on_sociomatrix_enter(app_state, ui_sociomatrix, registro_output):
    # with registro_output: print("HANDLER (sociomatrix v27.0 - Sexo, Inst/Grp, Miembro): Entrando a vista de matriz.")
    if isinstance(ui_sociomatrix, dict): ui_sociomatrix['_last_generated_matrix_html'] = ""
    group_context_sm_enter = app_state.get('current_group_viewing_members')
    if not group_context_sm_enter or not all(k in group_context_sm_enter for k in ['school', 'class_name']):
        if isinstance(ui_sociomatrix, dict) and "html_table_output" in ui_sociomatrix:
            with ui_sociomatrix["html_table_output"]: clear_output(wait=True); display(HTML("<p style='color:red;'>Error: Contexto de institución/grupo no válido.</p>"))
        checkbox_container_sm_enter = ui_sociomatrix.get("questions_checkboxes_vbox");
        if checkbox_container_sm_enter: checkbox_container_sm_enter.children = (Label("Error de contexto"),)
        with registro_output: print(f"  ERROR: No se pudo obtener contexto de inst/grupo válido. Contexto: {group_context_sm_enter}"); return
    institution_name_sm_enter = group_context_sm_enter['school']; group_name_sm_enter = group_context_sm_enter['class_name']
    app_state['current_group_viewing_sociomatrix'] = {'school': institution_name_sm_enter, 'class_name': group_name_sm_enter}
    # with registro_output: print(f"  Contexto para sociomatriz: Institución='{institution_name_sm_enter}', Grupo='{group_name_sm_enter}'")
    question_defs_sm_enter = get_class_question_definitions(institution_name_sm_enter, group_name_sm_enter)
    checkboxes_vbox_sm_enter = ui_sociomatrix.get("questions_checkboxes_vbox")
    if "_question_checkboxes_list" not in ui_sociomatrix: ui_sociomatrix["_question_checkboxes_list"] = []
    else: ui_sociomatrix["_question_checkboxes_list"].clear()
    if checkboxes_vbox_sm_enter: checkboxes_vbox_sm_enter.children = []
    else: 
      with registro_output: print("  ERROR: Contenedor 'questions_checkboxes_vbox' no encontrado."); return
    if question_defs_sm_enter:
        sorted_q_items_sm_enter = sorted(question_defs_sm_enter.items(), key=lambda item: (item[1].get('order', 99), item[0]))
        temp_checkboxes_sm_enter = []
        for q_id_sm, q_def_sm in sorted_q_items_sm_enter:
            q_text_short_sm = q_def_sm.get('text', q_id_sm)[:50] + ("..." if len(q_def_sm.get('text', q_id_sm)) > 50 else "")
            q_type_sm = q_def_sm.get('type', 'General'); data_key_sm = q_def_sm.get('data_key', q_id_sm); polarity_sm = q_def_sm.get('polarity', 'neutral')
            cb_sm = Checkbox(description=f"({polarity_sm[:3].title()}) {q_type_sm}: {q_text_short_sm}", value=True, indent=False, layout=Layout(width='98%'))
            ui_sociomatrix["_question_checkboxes_list"].append({'widget': cb_sm, 'data_key': data_key_sm, 'polarity': polarity_sm})
            temp_checkboxes_sm_enter.append(cb_sm)
        if checkboxes_vbox_sm_enter: checkboxes_vbox_sm_enter.children = tuple(temp_checkboxes_sm_enter)
        on_sociomatrix_update_button_click(None, app_state, ui_sociomatrix, registro_output)
    else:
        html_output_widget_no_q_sm = ui_sociomatrix.get("html_table_output")
        if html_output_widget_no_q_sm: 
          with html_output_widget_no_q_sm: clear_output(wait=True); display(HTML("<p>No hay preguntas definidas para este grupo.</p>"))
        ui_sociomatrix['_last_generated_matrix_html'] = "<p>No hay preguntas definidas para este grupo.</p>"

def _set_checkboxes_state(ui_sociomatrix, select_positive=None, select_negative=None, select_all=False, select_none=False):
    checkbox_infos = ui_sociomatrix.get("_question_checkboxes_list", []);
    if not checkbox_infos: return
    for info in checkbox_infos:
        cb = info.get('widget');
        if not cb: continue
        if select_all: cb.value = True
        elif select_none: cb.value = False
        else:
            is_pos = info.get('polarity')=='positive'; is_neg = info.get('polarity')=='negative'
            if select_positive is not None and is_pos: cb.value = select_positive
            elif select_negative is not None and is_neg: cb.value = select_negative
            elif select_positive is not None and not is_pos: cb.value = False
            elif select_negative is not None and not is_neg: cb.value = False

def on_sociomatrix_select_all_click(b, app_state, ui_sociomatrix, registro_output):
    # with registro_output: print("HANDLER (sociomatrix v27.0): Seleccionar Todas las Preguntas")
    _set_checkboxes_state(ui_sociomatrix, select_all=True)

def on_sociomatrix_select_none_click(b, app_state, ui_sociomatrix, registro_output):
    # with registro_output: print("HANDLER (sociomatrix v27.0): Deseleccionar Todas las Preguntas")
    _set_checkboxes_state(ui_sociomatrix, select_none=True)
    html_output_widget = ui_sociomatrix.get("html_table_output")
    if html_output_widget:
        with html_output_widget: clear_output(wait=True); display(HTML("<p style='color:grey;text-align:center;margin-top:20px;'><i>Ninguna pregunta seleccionada. Haga clic en 'Actualizar Matriz'.</i></p>"))
    ui_sociomatrix['_last_generated_matrix_html'] = "<p style='color:grey;text-align:center;margin-top:20px;'><i>Ninguna pregunta seleccionada. Haga clic en 'Actualizar Matriz'.</i></p>"

def on_sociomatrix_select_positive_click(b, app_state, ui_sociomatrix, registro_output):
    # with registro_output: print("HANDLER (sociomatrix v27.0): Seleccionar Solo Positivas")
    _set_checkboxes_state(ui_sociomatrix, select_positive=True, select_negative=False)

def on_sociomatrix_select_negative_click(b, app_state, ui_sociomatrix, registro_output):
    # with registro_output: print("HANDLER (sociomatrix v27.0): Seleccionar Solo Negativas")
    _set_checkboxes_state(ui_sociomatrix, select_positive=False, select_negative=True)

def on_sociomatrix_update_button_click(b, app_state, ui_sociomatrix, registro_output):
    # with registro_output: print("HANDLER (sociomatrix v27.0): Botón Actualizar Matriz presionado.")
    selected_data_keys_sm_upd = []
    checkbox_infos_sm_upd = ui_sociomatrix.get("_question_checkboxes_list", [])
    for info_sm_upd in checkbox_infos_sm_upd:
        if info_sm_upd.get('widget') and info_sm_upd['widget'].value == True:
            selected_data_keys_sm_upd.append(info_sm_upd['data_key'])
    # with registro_output: print(f"  Preguntas seleccionadas para la matriz: {selected_data_keys_sm_upd}")

    context_sm_upd = app_state.get('current_group_viewing_sociomatrix')
    html_output_widget_sm_upd = ui_sociomatrix.get("html_table_output")
    ui_sociomatrix['_last_generated_matrix_html'] = ""
    if not html_output_widget_sm_upd:
        with registro_output: print("  ERROR: Widget 'html_table_output' no encontrado."); return

    if context_sm_upd:
        institution_sm_upd = context_sm_upd['school']
        group_sm_upd = context_sm_upd['class_name']
        html_content_for_display_sm_upd = ""
        if not selected_data_keys_sm_upd:
            html_content_for_display_sm_upd = "<p style='color:grey;text-align:center;margin-top:20px;'><i>Seleccione preguntas y actualice.</i></p>"
        else:
            try:
                html_content_for_display_sm_upd = draw_sociomatrix_as_html_multi(institution_sm_upd, group_sm_upd, selected_data_keys_sm_upd, registro_output)
            except Exception as e_draw_sm_upd_exc:
                html_content_for_display_sm_upd = f"<p style='color:red;'>Error al generar matriz: {e_draw_sm_upd_exc}</p>"
                if registro_output and isinstance(registro_output, widgets.Output):
                    with registro_output:
                        print(f"  ERROR al dibujar matriz HTML (excepción capturada): {e_draw_sm_upd_exc}")
                        print(traceback.format_exc())
        
        ui_sociomatrix['_last_generated_matrix_html'] = html_content_for_display_sm_upd
        if html_output_widget_sm_upd:
            with html_output_widget_sm_upd:
                clear_output(wait=True)
                display(HTML(html_content_for_display_sm_upd))
    else:
        error_html_sm_upd = "<p style='color:red;'>Error: No hay contexto de institución/grupo para generar la matriz.</p>"
        ui_sociomatrix['_last_generated_matrix_html'] = error_html_sm_upd
        if html_output_widget_sm_upd:
            with html_output_widget_sm_upd: clear_output(wait=True); display(HTML(error_html_sm_upd))

def on_sociomatrix_stampa_click(b, app_state, ui_sociomatrix, registro_output):
    # with registro_output: print("HANDLER (sociomatrix v27.0): on_sociomatrix_stampa_click (PDF de Matriz)")
    html_content_to_convert_sm_print = ui_sociomatrix.get("_last_generated_matrix_html", "")
    is_placeholder_sm_print = False
    placeholders = ["<i>Seleccione una pregunta", "<i>Ninguna pregunta seleccionada", "<i>Seleccione al menos una pregunta", "Error: No hay contexto de", "Error de configuración de UI", "<p>No hay preguntas definidas"]
    if not html_content_to_convert_sm_print.strip() or any(ph in html_content_to_convert_sm_print for ph in placeholders): is_placeholder_sm_print = True
    if is_placeholder_sm_print:
        # with registro_output: print("  ADVERTENCIA (stampa_click_sm): No hay contenido de matriz válido para PDF.")
        if isinstance(ui_sociomatrix.get("html_table_output"), widgets.Output):
            with ui_sociomatrix.get("html_table_output"): clear_output(wait=True); display(HTML("<p style='color:orange;'>Genere una matriz válida primero.</p>"))
        return
    context_sm_print = app_state.get('current_group_viewing_sociomatrix')
    pdf_filename_base_sm_print = "MatrizSociometrica_Reporte"
    if context_sm_print and context_sm_print.get('school') and context_sm_print.get('class_name'):
        institution_clean_sm_print = re.sub(r'[^a-zA-Z0-9_]+', '', context_sm_print['school'])
        group_clean_sm_print = re.sub(r'[^a-zA-Z0-9_]+', '', context_sm_print['class_name'])
        pdf_filename_base_sm_print = f"Matriz_{institution_clean_sm_print}_{group_clean_sm_print}"
    if hasattr(pdf_generator, 'generate_pdf_from_html_content'):
        try: pdf_generator.generate_pdf_from_html_content(html_content_to_convert_sm_print, pdf_filename_base_sm_print, registro_output)
        except Exception as e_pdf_html_sm_print: 
          with registro_output: print(f"  ERROR al llamar a PDF desde HTML: {e_pdf_html_sm_print}\n{traceback.format_exc()}")
    else: 
      with registro_output: print("  ERROR: generate_pdf_from_html_content no disponible en pdf_generator.")

def on_sociomatrix_esci_button_click(b, app_state, switch_interface_func, registro_output, ui_groups, group_refresh_func):
    # with registro_output: print("HANDLER (sociomatrix v27.0): Saliendo de vista de matriz.")
    app_state['current_group_viewing_sociomatrix'] = None
    last_viewed_group_context_sm_exit = app_state.get('current_group_viewing_members')
    last_viewed_group_name_sm_exit = last_viewed_group_context_sm_exit.get('class_name') if last_viewed_group_context_sm_exit else None
    current_institution_on_exit_sm = app_state.get('current_institution_viewing_groups')
    if group_refresh_func and callable(group_refresh_func) and isinstance(ui_groups, dict) and 'select' in ui_groups and current_institution_on_exit_sm:
         select_widget_grp_exit = ui_groups.get("select")
         institution_groups_options_exit_sm = sorted([g.get('name') for g in classes_data.get(current_institution_on_exit_sm, []) if g.get('name')])
         select_widget_grp_exit.options = institution_groups_options_exit_sm
         current_group_selection_on_return_sm = None
         if last_viewed_group_name_sm_exit and last_viewed_group_name_sm_exit in institution_groups_options_exit_sm: current_group_selection_on_return_sm = last_viewed_group_name_sm_exit
         elif institution_groups_options_exit_sm: current_group_selection_on_return_sm = institution_groups_options_exit_sm[0]
         if select_widget_grp_exit.value != current_group_selection_on_return_sm : select_widget_grp_exit.value = current_group_selection_on_return_sm
         elif current_group_selection_on_return_sm is not None:
            change_event_data_exit_matrix_sm = {'name': 'value', 'old': current_group_selection_on_return_sm, 'new': current_group_selection_on_return_sm, 'owner': select_widget_grp_exit, 'type': 'change'}
            form_group_vbox_for_refresh_exit_sm = ui_groups.get("form_group_embedded_vbox_ref")
            try: group_refresh_func(change_event_data_exit_matrix_sm, app_state, ui_groups, registro_output, form_group_vbox_ref=form_group_vbox_for_refresh_exit_sm)
            except Exception as e_refresh_exit_matrix_sm: 
              with registro_output: print(f"ERROR al refrescar ui_groups desde matriz: {e_refresh_exit_matrix_sm}")
         elif not institution_groups_options_exit_sm :
            select_widget_grp_exit.value = None
            change_event_clear_matrix_sm = {'name': 'value', 'old': None, 'new': None, 'owner': select_widget_grp_exit, 'type': 'change'}
            form_group_vbox_for_clear_sm = ui_groups.get("form_group_embedded_vbox_ref")
            try: group_refresh_func(change_event_clear_matrix_sm, app_state, ui_groups, registro_output, form_group_vbox_ref=form_group_vbox_for_clear_sm)
            except Exception as e_clear_exit_matrix_sm: 
              with registro_output: print(f"ERROR al limpiar ui_groups desde matriz: {e_clear_exit_matrix_sm}")
    switch_interface_func('main_groups')