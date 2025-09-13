# handlers_print_view.py
# (v4.2 - Usa "Institución"/"Grupo" y "Miembro" en textos y logs. Llama a pdf_generator.)

# --- Importaciones ---
import sys
import io
import re
import collections
import traceback
from IPython.display import Javascript, display, clear_output, HTML
from ipywidgets import widgets

# Importar datos globales y el módulo pdf_generator
from sociograma_data import (
    members_data,
    questionnaire_responses_data,
    get_class_question_definitions
)
import pdf_generator

# Dependencias PDF (ReportLab)
try:
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE_HPV = True
except ImportError:
    REPORTLAB_AVAILABLE_HPV = False

# Descarga en Colab
try:
    from google.colab import files
    COLAB_AVAILABLE_HPV = True
except ImportError:
    COLAB_AVAILABLE_HPV = False


# --- Función Helper Interna para Generar Contenido HTML (Vista Previa) ---
def _generate_questionnaire_html_content_hpv(institution_name, group_name, registro_output=None):
    """Genera el contenido HTML para la vista previa del cuestionario respondido."""
    # if registro_output:
        # with registro_output: print(f"DEBUG (print_view_html_hpv v4.2): Generando HTML para '{group_name}' en '{institution_name}'...")

    html_content_pv = f"<h2 style='text-align:center; color:#333;'>Respuestas del Cuestionario</h2>"
    html_content_pv += f"<h3 style='text-align:center; color:#555;'>Institución: {institution_name}      Grupo: {group_name}</h3><hr>"

    members_list_pv = members_data.get(institution_name, {}).get(group_name, [])
    if not members_list_pv:
        html_content_pv += "<p style='color:orange; text-align:center;'>No hay miembros registrados en este grupo.</p>"
        # if registro_output:
            # with registro_output: print("INFO (print_view_html_hpv v4.2): No hay miembros para generar HTML.")
        return html_content_pv

    try:
        sorted_members_pv = sorted(members_list_pv, key=lambda s: (s.get('cognome', '').strip().upper(), s.get('nome', '').strip().upper()))
    except Exception as e_sort_pv:
        if registro_output:
            with registro_output: print(f"Advertencia (print_view_html_hpv v4.2): Error al ordenar miembros: {e_sort_pv}. Usando orden sin clasificar.")
        sorted_members_pv = members_list_pv

    current_group_defs_pv = get_class_question_definitions(institution_name, group_name)
    if not current_group_defs_pv:
        html_content_pv += "<p style='color:orange; text-align:center;'>No hay preguntas definidas para este grupo.</p>"
        # if registro_output:
            # with registro_output: print(f"INFO (print_view_html_hpv v4.2): No hay definiciones de preguntas para {institution_name}/{group_name}.")
        return html_content_pv

    try:
        sorted_q_items_pv = sorted(current_group_defs_pv.items(), key=lambda item: (item[1].get('order', 99), item[0]))
    except Exception as e_sort_q_pv:
        if registro_output:
            with registro_output: print(f"Advertencia (print_view_html_hpv v4.2): Error al ordenar preguntas: {e_sort_q_pv}.")
        sorted_q_items_pv = list(current_group_defs_pv.items())

    any_response_found_overall_pv = False
    for member_idx_pv, member_pv in enumerate(sorted_members_pv):
        full_name_pv = f"{member_pv.get('nome', '').strip().title()} {member_pv.get('cognome', '').strip().title()}".strip()
        member_response_key_pv = (institution_name, group_name, full_name_pv)
        member_responses_dict_pv = questionnaire_responses_data.get(member_response_key_pv, {})

        if member_idx_pv > 0:
             html_content_pv += "<hr style='border: 1px dashed #ccc; margin-top: 20px; margin-bottom: 20px;'>"

        html_content_pv += f"<div style='border: 1px solid #e0e0e0; padding: 15px; margin: 15px 0; border-radius: 8px; background-color: #f9f9f9;'>"
        display_name_pv = f"{member_pv.get('cognome', '').strip().title()}, {member_pv.get('nome', '').strip().title()}"
        html_content_pv += f"<h4 style='color:#0056b3; margin-top:0;'>Miembro: {display_name_pv}</h4>"

        if not member_responses_dict_pv:
            html_content_pv += "<p><i>Este miembro no ha respondido el cuestionario.</i></p>"
        else:
            any_response_found_for_member_pv = False
            html_content_pv += "<ul style='list-style-type: none; padding-left: 0;'>"
            for q_id_pv, q_def_pv in sorted_q_items_pv:
                question_text_pv = q_def_pv.get('text', f"Pregunta {q_id_pv}")
                data_key_pv = q_def_pv.get('data_key', q_id_pv)
                responses_for_q_pv = member_responses_dict_pv.get(data_key_pv, [])

                html_content_pv += f"<li style='margin-bottom: 10px;'>"
                html_content_pv += f"<strong style='color:#333;'>{question_text_pv}:</strong>"
                if responses_for_q_pv:
                    any_response_found_for_member_pv = True
                    any_response_found_overall_pv = True
                    html_content_pv += "<ul style='list-style-type: disc; margin-left: 20px; color:#555;'>"
                    for resp_name_pv in responses_for_q_pv:
                        html_content_pv += f"<li>{resp_name_pv}</li>"
                    html_content_pv += "</ul>"
                else:
                    html_content_pv += " <span style='color: #888;'><em>Sin respuesta</em></span>"
                html_content_pv += f"</li>"
            html_content_pv += "</ul>"
            if not any_response_found_for_member_pv and member_responses_dict_pv :
                 html_content_pv += "<p><i>No se encontraron respuestas para las preguntas actuales del cuestionario.</i></p>"
        html_content_pv += "</div>"

    if not any_response_found_overall_pv and members_list_pv:
        html_content_pv += "<p style='text-align:center; color:orange;'>Ningún miembro parece haber respondido a las preguntas actuales del cuestionario para este grupo.</p>"

    # if registro_output:
        # with registro_output: print("DEBUG (print_view_html_hpv v4.2): HTML generado.")
    return html_content_pv


# --- Handlers para Interfaz 9: Vista de Impresión del Cuestionario ---

def on_print_view_stampa_button_handler(b, ui_q_print, app_state, registro_output):
    # with registro_output:
        # clear_output(wait=True)
        # print("HANDLER (print_view v4.2 - Inst/Grp/Miembro): on_print_view_stampa_button_handler (Generando Vista Previa HTML)")

    print_context_pv = app_state.get('print_view_context')
    if not print_context_pv or 'school' not in print_context_pv or 'class_name' not in print_context_pv:
        with registro_output: print("ERROR (PV Stampa): Falta contexto (institución/grupo) para generar vista previa.")
        if isinstance(ui_q_print, dict): ui_q_print.get("content_html", widgets.HTML()).value = "<p style='color:red;'>Error: No se pudo cargar el contexto de institución/grupo.</p>"
        return

    institution_name_pv = print_context_pv['school']
    group_name_pv = print_context_pv['class_name']

    if isinstance(ui_q_print, dict):
        ui_q_print.get("school_name_label", widgets.Label()).value = f"Institución: {institution_name_pv} / Grupo: {group_name_pv}"
        content_html_widget_pv = ui_q_print.get("content_html", widgets.HTML())
        export_pdf_button_pv = ui_q_print.get("export_pdf_button")

        try:
            html_content_gen_pv = _generate_questionnaire_html_content_hpv(institution_name_pv, group_name_pv, registro_output)
            content_html_widget_pv.value = html_content_gen_pv
            # with registro_output: print("INFO (PV Stampa): Vista previa HTML de respuestas generada.")
        except Exception as e_gen_html_pv:
            with registro_output: print(f"ERROR al generar vista previa HTML de respuestas: {e_gen_html_pv}\n{traceback.format_exc()}")
            content_html_widget_pv.value = f"<p style='color:red;'>Error al generar vista previa: {e_gen_html_pv}</p>"

        if export_pdf_button_pv:
            is_pdf_export_possible_pv = REPORTLAB_AVAILABLE_HPV and hasattr(pdf_generator, 'generate_and_download_questionnaire_pdf')
            export_pdf_button_pv.disabled = not is_pdf_export_possible_pv
            # if not is_pdf_export_possible_pv and registro_output:
                # with registro_output: print("INFO (PV Stampa): Exportar PDF de respuestas deshabilitado (ReportLab o función en pdf_generator no disponible).")
    else:
        with registro_output: print("ERROR (PV Stampa): ui_q_print no es un diccionario válido.")


def on_print_view_chiudi_button_handler(b, app_state, switch_interface_func, registro_output,
                                        ui_main_institutions=None, institution_refresh_func=None):
    with registro_output:
        clear_output(wait=True)
        # print("HANDLER (print_view v4.2 - Inst/Grp/Miembro): on_print_view_chiudi_button_handler")
        pass

    app_state['print_view_context'] = None
    default_return_ui_pv = 'main_institutions'
    return_interface_pv = app_state.get('return_interface', default_return_ui_pv)
    if return_interface_pv is None or return_interface_pv not in ['main_institutions', 'main_groups', 'main_members']:
        return_interface_pv = default_return_ui_pv
    app_state['return_interface'] = None

    refreshed_pv = False
    if return_interface_pv == 'main_institutions' and ui_main_institutions and institution_refresh_func and callable(institution_refresh_func):
        select_widget_institution_pv = ui_main_institutions.get("select") if isinstance(ui_main_institutions, dict) else None
        current_selection_pv = select_widget_institution_pv.value if select_widget_institution_pv else None
        change_event_data_pv = {'name': 'value', 'old': None, 'new': current_selection_pv, 'owner': select_widget_institution_pv, 'type': 'change'}
        try:
            form_inst_vbox_for_refresh = globals().get('interfaces', {}).get('form_institution')
            institution_refresh_func(change_event_data_pv, app_state, ui_main_institutions, registro_output, form_school_vbox_ref=form_inst_vbox_for_refresh)
            # print("INFO (PV Chiudi): Interfaz de instituciones refrescada al cerrar vista de impresión.")
            refreshed_pv = True
        except Exception as e_refresh_pv: print(f"ERROR al refrescar UI principal: {e_refresh_pv}")

    if return_interface_pv == 'main_institutions' and not refreshed_pv:
        print("Advertencia (PV Chiudi): No se pudo refrescar UI de instituciones.")

    try:
        switch_interface_func(return_interface_pv)
    except Exception as e_switch_pv:
        with registro_output: print(f"ERROR al cambiar a interfaz '{return_interface_pv}': {e_switch_pv}")
        try: switch_interface_func('main_institutions')
        except: print("Fallback a main_institutions también falló.")


def on_print_view_export_pdf_button_handler(b, ui_q_print, app_state, registro_output):
    # with registro_output:
        # print("HANDLER (print_view v4.2 - Inst/Grp/Miembro): on_print_view_export_pdf_button_handler (Delegando PDF de Respuestas)")

    print_context_pdf_exp = app_state.get('print_view_context')
    if not print_context_pdf_exp or 'school' not in print_context_pdf_exp or 'class_name' not in print_context_pdf_exp:
        with registro_output: print("ERROR (PV Export PDF): Falta contexto (institución/grupo) para generar PDF de respuestas."); return

    institution_name_pdf_exp = print_context_pdf_exp['school']
    group_name_pdf_exp = print_context_pdf_exp['class_name']

    if hasattr(pdf_generator, 'generate_and_download_questionnaire_pdf'):
        try:
            pdf_generator.generate_and_download_questionnaire_pdf(
                institution_name_pdf_exp, group_name_pdf_exp,
                registro_output=registro_output
            )
        except Exception as e_pdf_gen_call_pv:
            with registro_output: print(f"ERROR al llamar a generate_and_download_questionnaire_pdf: {e_pdf_gen_call_pv}\n{traceback.format_exc()}")
    else:
        with registro_output: print("ERROR (PV Export PDF): La función generate_and_download_questionnaire_pdf no está disponible en pdf_generator.")


def on_print_view_export_rtf_button_handler(b, ui_q_print, app_state, registro_output):
     with registro_output:
        print("HANDLER (print_view v4.2 - Inst/Grp/Miembro): on_print_view_export_rtf_button_handler (FUNCIONALIDAD PENDIENTE)")