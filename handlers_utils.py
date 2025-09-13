# handlers_utils.py
# (v1.4 - Cambiado "alumno" a "miembro", "students_data" a "members_data")

from ipywidgets import widgets, Output

# --- Funciones Helper para Limpiar Campos de UI ---

def clear_class_details_fields(ui_classes):
    """Limpia los campos de texto de detalles del grupo."""
    if isinstance(ui_classes, dict):
        ui_classes.get("coord_text", widgets.Text()).value = ""
        ui_classes.get("ins2_text", widgets.Text()).value = ""
        ui_classes.get("ins3_text", widgets.Text()).value = ""
        ui_classes.get("sostegno_text", widgets.Text()).value = ""
        ui_classes.get("annotations_textarea", widgets.Textarea()).value = ""
    pass


def clear_member_details_fields(ui_members):
    """Limpia los campos de texto de detalles del miembro."""
    if isinstance(ui_members, dict):
        ui_members.get("cognome_text", widgets.Text()).value = ""
        ui_members.get("nome_text", widgets.Text()).value = ""
        ui_members.get("iniz_text", widgets.Text()).value = ""
        ui_members.get("annotations_textarea", widgets.Textarea()).value = ""
    pass


# --- Función Helper para Obtener Opciones de Miembros ---

def get_member_options_for_dropdown(school_name, class_name,
                                     order_by='Apellido',
                                     exclude_member_display_name=None,
                                     app_data_ref=None,
                                     registro_output_fallback=None):

    ro_utils_log_widget = globals().get('registro_output_area')
    if not ro_utils_log_widget and registro_output_fallback:
        ro_utils_log_widget = registro_output_fallback

    def _log_util_hu(message, is_error=False):
        if is_error and ro_utils_log_widget and isinstance(ro_utils_log_widget, Output):
            with ro_utils_log_widget:
                print(f"HNDL_UTILS_LOG (get_mem_opts v1.4): {message}")
        # Los logs no-error se omiten
        pass

    # _log_util_hu(f"Iniciando para Institución='{school_name}', Grupo='{class_name}'. app_data_ref tipo: {type(app_data_ref)}")
    # _log_util_hu(f"  order_by='{order_by}', exclude_member_display_name='{exclude_member_display_name}'")
    
    default_option = [('Seleccionar', None)]
    local_members_data = None

    if app_data_ref and hasattr(app_data_ref, 'members_data') and isinstance(app_data_ref.members_data, dict) :
        local_members_data = app_data_ref.members_data
    else:
        _log_util_hu(f"  ERROR CRÍTICO: app_data_ref no válido o sin 'members_data'. Retornando default_option.", is_error=True)
        return default_option

    if school_name not in local_members_data or class_name not in local_members_data.get(school_name, {}):
        # _log_util_hu(f"  ADVERTENCIA: Datos no encontrados para '{school_name}'/'{class_name}'. Retornando default_option.")
        return default_option

    members_list_all = local_members_data[school_name].get(class_name, [])
    if not members_list_all:
        # _log_util_hu(f"  Lista de miembros vacía. Retornando default_option.")
        return default_option

    options = list(default_option)
    members_to_process = members_list_all

    if exclude_member_display_name:
        # _log_util_hu(f"  Excluyendo al miembro: '{exclude_member_display_name}' (formato esperado: Nombre Apellido Título)")
        members_to_process_temp = []
        for m_exclude in members_list_all:
            nombre_m_ex = m_exclude.get('nome', '').strip().title()
            cognome_m_ex = m_exclude.get('cognome', '').strip().title()
            full_name_m_ex = f"{nombre_m_ex} {cognome_m_ex}".strip()
            
            if full_name_m_ex.lower() != str(exclude_member_display_name).strip().lower():
                members_to_process_temp.append(m_exclude)
        members_to_process = members_to_process_temp
        # _log_util_hu(f"  Número de miembros después de exclusión: {len(members_to_process)}")

    if order_by == 'Nombre':
        key_func = lambda s: (str(s.get('nome', '')).strip().upper(), str(s.get('cognome', '')).strip().upper())
    else:
        key_func = lambda s: (str(s.get('cognome', '')).strip().upper(), str(s.get('nome', '')).strip().upper())

    try:
        sorted_members = sorted(members_to_process, key=key_func)
    except Exception as e_sort_hu:
        _log_util_hu(f"  ERROR al ordenar miembros: {e_sort_hu}. Usando lista sin ordenar.", is_error=True)
        sorted_members = members_to_process

    for member_dict_data in sorted_members:
        nombre_original_data = str(member_dict_data.get('nome', '')).strip()
        cognome_original_data = str(member_dict_data.get('cognome', '')).strip()
        
        nombre_titulo = nombre_original_data.title()
        cognome_titulo = cognome_original_data.title()

        display_label = f"{nombre_titulo} {cognome_titulo}".strip()
        internal_value = display_label

        if internal_value:
            options.append((display_label, internal_value))

    # _log_util_hu(f"  Opciones finales generadas: {len(options)} (incluyendo 'Seleccionar'). Primeras 5: {options[:5]}")
    return options