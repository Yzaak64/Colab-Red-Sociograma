# sociograma_ui.py
# (v23.1 - Corregido error de 'justify_content' en Layouts. Cambios de "Escuela" a "Institución" y "Alumno" a "Miembro" en UI)

from ipywidgets import widgets, VBox, HBox, Label, Text, Textarea, Select, RadioButtons, Checkbox, Dropdown, Output, Layout, Button, HTML, IntText, FileUpload
import collections

# --- Interfaz 1: "Tabla de Instituciones" ---
def create_main_institutions_vbox(institutions_data_keys_list):
    main_title_label = Label("Tabla de Instituciones", style={'font_weight': 'bold', 'font_size': '16px'})

    form_institution_container = VBox(
        [],
        layout=Layout(
            width='98%', margin='10px auto 15px auto', padding='5px',
            display='flex', min_height='50px'
        )
    )

    main_institution_list_label = Label("Institución:")
    options_list = sorted(list(institutions_data_keys_list)) if institutions_data_keys_list is not None else []
    main_institution_select = Select(
        options=options_list, description='', disabled=False,
        layout=Layout(width='95%', height='150px', margin='0 5px 0 0')
    )
    main_annotations_label = Label("Anotaciones de Institución:")
    main_annotations_textarea = Textarea(
        value='', description='', disabled=True,
        layout=Layout(width='95%', height='150px')
    )

    main_left_panel = VBox([main_institution_list_label, main_institution_select], layout=Layout(width='50%'))
    main_right_panel = VBox([main_annotations_label, main_annotations_textarea], layout=Layout(width='50%'))
    main_panels_hbox = HBox([main_left_panel, main_right_panel], layout=Layout(align_items='flex-start'))

    main_nueva_button = Button(description='Nueva Institución', tooltip='Añadir nueva institución')
    main_modifica_button = Button(description='Modificar Institución', tooltip='Modificar nombre y/o anotaciones de la institución')
    main_elimina_button = Button(description='Eliminar Institución', tooltip='Eliminar institución y todos sus datos asociados')
    main_classi_button = Button(description='Ver Grupos', tooltip='Ver/Gestionar grupos de esta institución')
    main_csv_button = Button(description='Importar/Exportar CSV', icon='file-excel-o', tooltip='Mostrar opciones para importar/exportar datos CSV')
    main_salir_button = Button(description='Salir App', tooltip='Cerrar aplicación')

    csv_io_title_label = HTML("<h4>Gestión de Datos con Archivo CSV</h4>")
    
    csv_import_subtitle_label = HTML("<b>Importar Datos desde CSV:</b>")
    csv_import_instructions_html = HTML(
        "<p style='font-size:0.9em;'>"
        "1. Suba su archivo CSV a la carpeta <code>/content/</code> de este entorno Colab.<br>"
        "2. Ingrese el <b>nombre exacto</b> del archivo (ej: <code>mis_datos.csv</code>) abajo.<br>"
        "3. Seleccione los tipos de datos que desea importar.<br>"
        "4. Configure opciones adicionales.<br>"
        "5. Haga clic en 'Procesar CSV'.<br>"
        "   <i>(Nota: La columna para instituciones en el CSV debe llamarse 'Institucion', la de miembros 'Nombre y Apellido')</i>"
        "</p>"
    )
    csv_file_name_input_widget = widgets.Text(
        placeholder='nombre_del_archivo.csv', description='Nombre Archivo en /content/:',
        layout=Layout(width='auto', flex='1 1 auto', min_width='300px'), style={'description_width': 'initial'}
    )
    csv_allow_self_default_dropdown = Dropdown(
        options=[('Nuevas Pregs: Auto-Selección = FALSO (Default)', False), ('Nuevas Pregs: Auto-Selección = VERDADERO', True)],
        value=False, description='Auto-Selección (Nuevas Pregs.):',
        style={'description_width': 'initial'}, layout=Layout(width='auto', margin='5px 0 5px 0')
    )
    import_cb_institutions_csv = Checkbox(value=True, description='Importar/Crear Instituciones', indent=False)
    import_cb_grupos_csv = Checkbox(value=True, description='Importar/Crear Grupos', indent=False)
    import_cb_members_csv = Checkbox(value=True, description='Importar/Crear Miembros', indent=False)
    import_cb_defs_preguntas_csv = Checkbox(value=True, description='Importar/Crear Defs. Preguntas', indent=False)
    
    import_cb_add_new_questions_only_csv = Checkbox(
        value=True, 
        description='Si ya existen, solo agregar preguntas faltantes (no sobreescribir)',
        indent=False, 
        layout=Layout(margin_left='20px')
    )
    
    import_cb_respuestas_csv = Checkbox(value=True, description='Importar Respuestas', indent=False)
    import_cb_prefill_mentioned = Checkbox(value=True, description='Si importan respuestas: crear miembros mencionados si no existen', indent=False, layout=Layout(margin_left='20px'))
    csv_excess_response_mode_dropdown_widget = Dropdown(
        options=[
            ('Exceso Respuestas: Omitir extra (Recomendado)', 'omit_extra'),
            ('Exceso Respuestas: Intentar ampliar max_sel de PREGUNTAS NUEVAS (limitado por N)', 'try_expand_new_q_max_sel'),
        ],
        value='omit_extra', description='Manejo Exceso Respuestas:',
        style={'description_width': 'initial'}, layout=Layout(width='auto', margin='5px 0 10px 0')
    )
    import_options_label = Label("Seleccione los datos a importar del archivo CSV:")
    
    import_options_vbox = VBox([
        import_options_label, import_cb_institutions_csv, import_cb_grupos_csv, import_cb_members_csv,
        import_cb_defs_preguntas_csv,
        import_cb_add_new_questions_only_csv,
        import_cb_respuestas_csv, import_cb_prefill_mentioned,
        csv_excess_response_mode_dropdown_widget
    ], layout=Layout(margin='10px 0', padding='5px', border='1px dashed #e0e0e0'))
    
    csv_import_process_button = Button(description="Procesar CSV (Importar)", button_style='success', icon='cogs')
    csv_import_status_output_widget = Output(layout=Layout(margin='10px 0'))
    csv_confirm_polarity_output_widget = Output(layout=Layout(margin_top='10px'))
    csv_import_section_vbox = VBox([
        csv_import_subtitle_label, csv_import_instructions_html, HBox([csv_file_name_input_widget]),
        csv_allow_self_default_dropdown, import_options_vbox, csv_import_process_button,
        csv_import_status_output_widget, csv_confirm_polarity_output_widget
    ])

    csv_export_title_label = HTML("<b style='margin-top:20px; display:block;'>Exportar Datos a CSV:</b>")
    csv_prepare_export_institutions_button = Button(
        description="1. Cargar Instituciones para Selección",
        icon='university',
        tooltip="Muestra la lista de instituciones para que seleccione cuáles incluir en la exportación.",
        layout=Layout(margin_bottom='5px', width='auto')
    )
    csv_export_institutions_checkboxes_vbox = VBox([], layout=Layout(width='95%', max_height='150px', overflow_y='auto', border='1px solid #e0e0e0', padding='8px', margin='0 0 10px 0', box_sizing='border-box', display='none'))
    csv_load_groups_for_export_button = Button(
        description="2. Cargar Grupos de Instituciones Seleccionadas",
        icon='sitemap',
        tooltip="Muestra los grupos de las instituciones que haya marcado arriba para su selección.",
        disabled=True,
        layout=Layout(margin_bottom='5px', width='auto', display='none')
    )
    csv_export_groups_checkboxes_vbox = VBox([], layout=Layout(width='95%', max_height='200px', overflow_y='auto', border='1px solid #e0e0e0', padding='8px', margin='0 0 10px 0', box_sizing='border-box', display='none'))
    csv_export_selected_groups_button = Button(
        description='3. Generar CSV de Grupo(s) Seleccionado(s)',
        button_style='primary', icon='download',
        tooltip='Exportar los datos de los grupos marcados a un archivo CSV',
        disabled=True, layout=Layout(display='none', margin_top='5px')
    )
    csv_export_status_output = Output(layout=Layout(margin='5px 0'))
    csv_export_section_vbox = VBox([
        csv_export_title_label,
        csv_prepare_export_institutions_button,
        csv_export_institutions_checkboxes_vbox,
        csv_load_groups_for_export_button,
        csv_export_groups_checkboxes_vbox,
        csv_export_selected_groups_button,
        csv_export_status_output
    ])
    
    csv_instructions_pdf_button = Button(description='Ver Instrucciones Formato CSV (PDF)', icon='info-circle', tooltip='Descargar PDF con instrucciones para el formato CSV de importación')
    csv_instructions_section_vbox = VBox(
        [HTML("<b style='margin-top:15px; display:block;'>Documentación:</b>"), csv_instructions_pdf_button],
        layout=Layout(margin='15px 0 0 0', padding_top='10px', border_top='1px solid #ccc')
    )

    csv_controls_main_vbox = VBox([
        csv_io_title_label,
        csv_import_section_vbox,
        HTML("<hr style='margin: 20px 0;'>"),
        csv_export_section_vbox,
        csv_instructions_section_vbox
    ], layout=Layout(display='none', margin='20px 0 0 0', border='1px solid #ccc', padding='15px', width='95%'))
    
    main_buttons_row1_hbox = HBox(
        [main_nueva_button, main_modifica_button, main_elimina_button],
        layout=Layout(justify_content='space-around', margin='10px 0 5px 0', flex_wrap='wrap')
    )
    main_buttons_row2_hbox = HBox(
        [main_classi_button, main_csv_button, main_salir_button],
        layout=Layout(justify_content='space-around', margin='5px 0 0 0', flex_wrap='wrap')
    )
    
    vbox = VBox([main_title_label,
                 form_institution_container,
                 main_panels_hbox,
                 main_buttons_row1_hbox,
                 main_buttons_row2_hbox,
                 csv_controls_main_vbox
                ])
    
    ui_elements = {
        "form_institution_container": form_institution_container,
        "select": main_institution_select, "annotations": main_annotations_textarea,
        "nueva_button": main_nueva_button, "modifica_button": main_modifica_button,
        "elimina_button": main_elimina_button, "classi_button": main_classi_button,
        "csv_button": main_csv_button,
        "salir_button": main_salir_button,
        
        "csv_controls_main_vbox": csv_controls_main_vbox,
        "csv_file_name_input": csv_file_name_input_widget,
        "csv_allow_self_default_dropdown": csv_allow_self_default_dropdown,
        
        "import_cb_institutions_csv": import_cb_institutions_csv,
        "import_cb_grupos_csv": import_cb_grupos_csv,
        "import_cb_alumnos_csv": import_cb_members_csv,
        "import_cb_defs_preguntas_csv": import_cb_defs_preguntas_csv,
        "import_cb_add_new_questions_only_csv": import_cb_add_new_questions_only_csv,
        "import_cb_respuestas_csv": import_cb_respuestas_csv,
        "import_cb_prefill_mentioned_csv": import_cb_prefill_mentioned,
        "csv_excess_response_mode_dropdown": csv_excess_response_mode_dropdown_widget,

        "import_process_button_csv": csv_import_process_button,
        "import_status_output_csv": csv_import_status_output_widget,
        "confirm_polarity_output_csv": csv_confirm_polarity_output_widget,
        
        "csv_prepare_export_button": csv_prepare_export_institutions_button,
        "csv_export_schools_checkboxes_vbox": csv_export_institutions_checkboxes_vbox,
        "csv_load_groups_for_export_button": csv_load_groups_for_export_button,
        "csv_export_groups_checkboxes_vbox": csv_export_groups_checkboxes_vbox,
        "csv_export_selected_button": csv_export_selected_groups_button,
        "csv_export_status_output": csv_export_status_output,
        
        "csv_instructions_pdf_button": csv_instructions_pdf_button,
    }
    return vbox, ui_elements

# --- Interfaz 2: Formulario "Actualización de Institución" ---
def create_form_institution_vbox():
    form_institution_title_label = Label(
        "Formulario Institución",
        style={'font_weight': 'bold', 'font_size': '16px'}
    )
    form_institution_name_label = Label("Nombre de la institución:")
    form_institution_name_input = Text(
        placeholder='Introduce el nombre de la institución',
        layout=Layout(width='95%')
    )
    form_institution_annotations_label = Label("Anotaciones varias sobre la institución:")
    form_institution_annotations_textarea = Textarea(
        placeholder='Introduce las anotaciones para la institución',
        layout=Layout(width='95%', height='100px')
    )
    form_institution_add_save_button = Button(
        description='Guardar Nueva Institución',
        button_style='success'
    )
    form_institution_add_cancel_button = Button(description='Cancelar')
    form_institution_add_mode_buttons_hbox = HBox(
        [form_institution_add_save_button, form_institution_add_cancel_button],
        layout=Layout(justify_content='flex-end', margin='10px 0 0 0')
    )
    
    form_institution_modify_ok_button = Button(
        description='Guardar Cambios Institución',
        button_style='success'
    )
    form_institution_modify_cancel_button = Button(description='Cancelar')
    form_institution_modify_mode_buttons_hbox = HBox(
        [form_institution_modify_ok_button, form_institution_modify_cancel_button],
        layout=Layout(justify_content='flex-end', margin='10px 0 0 0')
    )
    
    form_institution_buttons_container = VBox(
        [form_institution_add_mode_buttons_hbox, form_institution_modify_mode_buttons_hbox]
    )
    
    vbox = VBox([
        form_institution_title_label,
        form_institution_name_label,
        form_institution_name_input,
        form_institution_annotations_label,
        form_institution_annotations_textarea,
        form_institution_buttons_container
    ], layout=Layout(border='2px solid brown', padding='10px', margin_top='10px'))
    
    ui_elements = {
        "title_label": form_institution_title_label,
        "name_input": form_institution_name_input,
        "annotations_textarea": form_institution_annotations_textarea,
        "add_save_button": form_institution_add_save_button,
        "add_cancel_button": form_institution_add_cancel_button,
        "modify_ok_button": form_institution_modify_ok_button,
        "modify_cancel_button": form_institution_modify_cancel_button,
        "add_buttons_hbox": form_institution_add_mode_buttons_hbox,
        "modify_buttons_hbox": form_institution_modify_mode_buttons_hbox
    }
    setattr(vbox, '_ui_elements_ref', ui_elements)
    return vbox, ui_elements
# --- Interfaz 3: "Tabla de Grupos" ---
def create_classes_vbox():
    classes_title_label = Label(
        "Tabla de Grupos: [Institución N/A]",
        style={'font_weight': 'bold', 'font_size': '16px'}
    )

    form_class_container = VBox(
        [],
        layout=Layout(
            width='98%', margin='10px auto 15px auto',
            padding='5px',display='flex', min_height='10px'
        )
    )

    classes_select = Select(
        options=[],
        description='Seleccionar Grupo:',
        layout=Layout(width='40%', height='220px', margin='0 15px 0 0'),
        style={'description_width':'initial'}
    )
    classes_details_label = Label("Detalles del Grupo:", style={'font_weight':'bold'})
    classes_coordinator_text = Text(value='', description="Coordinador:", disabled=True, layout=Layout(width='95%'), style={'description_width': 'initial'})
    classes_ins2_text = Text(value='', description="Profesor 2:", disabled=True, layout=Layout(width='95%'), style={'description_width': 'initial'})
    classes_ins3_text = Text(value='', description="Profesor 3:", disabled=True, layout=Layout(width='95%'), style={'description_width': 'initial'})
    classes_sostegno_text = Text(value='', description="Sostén:", disabled=True, layout=Layout(width='95%'), style={'description_width': 'initial'})
    classes_annotations_textarea = Textarea(value='', description="Anotaciones:", disabled=True, layout=Layout(width='95%', height='80px'), style={'description_width': 'initial'})

    classes_right_details_vbox = VBox([
        classes_details_label, classes_coordinator_text, classes_ins2_text,
        classes_ins3_text, classes_sostegno_text, classes_annotations_textarea
    ], layout=Layout(width='60%'))

    classes_panels_hbox = HBox([
        VBox([classes_select], layout=Layout(width='40%')),
        classes_right_details_vbox
    ], layout=Layout(width='100%', align_items='flex-start', margin_bottom='10px'))

    classes_nueva_button = Button(description='Nuevo Grupo', disabled=True, tooltip='Añadir nuevo grupo a la institución actual', icon='plus-square', layout=Layout(min_width='130px'))
    classes_modifica_button = Button(description='Modificar Grupo', tooltip='Modificar datos del grupo seleccionado', icon='edit', layout=Layout(min_width='130px'))
    classes_elimina_button = Button(description='Eliminar Grupo', tooltip='Eliminar grupo seleccionado y todos sus datos', icon='trash', button_style='danger', layout=Layout(min_width='130px'))
    classes_alunni_button = Button(description='Ver Miembros', tooltip='Ver/Gestionar miembros del grupo seleccionado', icon='users', layout=Layout(min_width='130px'))
    
    classes_buttons_row1_hbox = HBox(
        [classes_nueva_button, classes_modifica_button, classes_elimina_button, classes_alunni_button],
        layout=Layout(justify_content='space-around', margin='5px 0', flex_wrap='wrap')
    )

    classes_main_report_button = Button(description='Reportes del Grupo', tooltip='Mostrar/ocultar opciones de reporte para el grupo seleccionado', icon='file-text-o', layout=Layout(min_width='150px'))
    classes_sociogramma_button = Button(description='Ver Sociograma', tooltip='Ver sociograma interactivo del grupo seleccionado', icon='share-alt-square', layout=Layout(min_width='130px'))
    classes_salir_button = Button(description='Volver a Instituciones', tooltip='Volver a la lista de instituciones', icon='arrow-left', layout=Layout(min_width='130px'))

    classes_buttons_row2_hbox = HBox(
        [classes_main_report_button, classes_sociogramma_button, classes_salir_button],
        layout=Layout(justify_content='space-around', margin='5px 0 10px 0', flex_wrap='wrap')
    )

    classes_report_table_button = Button(description='Matriz Sociométrica', button_style='info', icon='table', tooltip='Ver resumen numérico de elecciones del grupo')
    classes_report_data_button = Button(description='PDF Datos Cuestionario', button_style='info', icon='file-pdf-o', tooltip='Generar PDF con las respuestas detalladas del grupo')
    classes_diana_button = Button(description='Diana de Afinidad', button_style='warning', icon='bullseye', tooltip='Generar visualización de Diana de Afinidad para el grupo')

    classes_report_options_hbox = HBox(
        [classes_report_table_button, classes_report_data_button, classes_diana_button],
        layout=Layout(justify_content='flex-start', margin='5px 0 10px 20px', flex_wrap='wrap', display='none')
    )
    
    diana_title_label = HTML("<h4 style='margin-top:0; margin-bottom:5px;'>Configuración Diana de Afinidad:</h4>")
    diana_questions_label = Label("Seleccione preguntas para calcular afinidad (elecciones recibidas):")
    diana_questions_checkboxes_vbox = VBox(
        [], 
        layout=Layout(width='100%', max_height='150px', overflow_y='auto', border='1px solid #E0E0E0',
                      padding='8px', margin_bottom='10px', box_sizing='border-box')
    )
    diana_select_all_btn = Button(description="Todas", tooltip="Seleccionar todas las preguntas", layout=Layout(width='auto', min_width='70px', margin='2px'))
    diana_select_none_btn = Button(description="Ninguna", tooltip="Deseleccionar todas las preguntas", layout=Layout(width='auto', min_width='70px', margin='2px'))
    diana_select_pos_btn = Button(description="Positivas", tooltip="Seleccionar solo preguntas positivas", layout=Layout(width='auto', min_width='80px', margin='2px'))
    diana_select_neg_btn = Button(description="Negativas", tooltip="Seleccionar solo preguntas negativas", layout=Layout(width='auto', min_width='80px', margin='2px'))
    diana_selection_btns_hbox = HBox(
        [diana_select_all_btn, diana_select_none_btn, diana_select_pos_btn, diana_select_neg_btn],
        layout=Layout(flex_wrap='wrap', margin_bottom='10px')
    )
    
    diana_show_lines_checkbox = Checkbox(
        value=True, 
        description="Mostrar Líneas de Elección en Diana",
        indent=False,
        layout=Layout(margin_bottom='10px')
    )

    diana_generate_button = Button(description="Generar/Actualizar Diana", icon="paint-brush", button_style="success", layout=Layout(margin_right='10px'))
    diana_download_button = Button(description="Descargar Diana (PNG)", icon="download", button_style="primary", disabled=True)
    diana_actions_hbox = HBox([diana_generate_button, diana_download_button], layout=Layout(margin_top='10px'))

    diana_output_image = Output(layout=Layout(border='1px dashed #ccc', padding='10px', min_height='300px', display='flex', justify_content='center', align_items='center', width='100%'))
    with diana_output_image:
        display(HTML("<p style='color:grey;text-align:center;'><i>La Diana de Afinidad aparecerá aquí después de generarla.</i></p>"))

    diana_controls_vbox = VBox([
        diana_title_label,
        diana_questions_label,
        diana_questions_checkboxes_vbox,
        diana_selection_btns_hbox,
        diana_show_lines_checkbox,
        diana_actions_hbox,
        diana_output_image
    ], layout=Layout(width='95%', margin='15px auto', padding='15px', border='1px solid #B0BEC5', border_radius='5px', display='none'))

    vbox = VBox([
        classes_title_label,
        form_class_container,
        classes_panels_hbox,
        classes_buttons_row1_hbox,
        classes_buttons_row2_hbox,
        classes_report_options_hbox,
        diana_controls_vbox
    ])
    
    ui_elements = {
        "title_label": classes_title_label,
        "form_class_container": form_class_container,
        "select": classes_select,
        "coord_text": classes_coordinator_text,
        "ins2_text": classes_ins2_text,
        "ins3_text": classes_ins3_text,
        "sostegno_text": classes_sostegno_text,
        "annotations_textarea": classes_annotations_textarea,
        "nueva_button": classes_nueva_button,
        "modifica_button": classes_modifica_button,
        "elimina_button": classes_elimina_button,
        "alunni_button": classes_alunni_button,
        "main_report_button": classes_main_report_button,
        "report_options_hbox": classes_report_options_hbox,
        "report_table_button": classes_report_table_button,
        "report_data_button": classes_report_data_button,
        "sociogramma_button": classes_sociogramma_button,
        "salir_button": classes_salir_button,
        "diana_button": classes_diana_button,
        "diana_controls_vbox": diana_controls_vbox,
        "diana_questions_checkboxes_vbox": diana_questions_checkboxes_vbox,
        "diana_select_all_button": diana_select_all_btn,
        "diana_select_none_button": diana_select_none_btn,
        "diana_select_positive_button": diana_select_pos_btn,
        "diana_select_negative_button": diana_select_neg_btn,
        "diana_show_lines_checkbox": diana_show_lines_checkbox,
        "diana_generate_button": diana_generate_button,
        "diana_download_button": diana_download_button,
        "diana_output_image": diana_output_image,
        "_diana_question_checkboxes_list": [],
        "_diana_last_image_bytes": None
    }
    return vbox, ui_elements

# --- Interfaz 4: Formulario "Actualización de Grupo" ---
def create_form_class_vbox():
    title_label = Label(
        "Formulario Grupo",
        style={'font_weight': 'bold', 'font_size': '16px'}
    )
    institution_label = Label("Institución:", layout=Layout(width='100px'))
    institution_text = Text(value="N/A", disabled=True, layout=Layout(flex='1 1 auto'))
    institution_hbox = HBox([institution_label, institution_text], layout=Layout(margin='5px 0'))

    name_label = Label("Nombre Grupo:", layout=Layout(width='100px'))
    name_input = Text(placeholder="Ej: 2A, Alfa", layout=Layout(flex='1 1 auto'))
    name_hbox = HBox([name_label, name_input], layout=Layout(margin='5px 0'))

    coord_label = Label("Coordinador:", layout=Layout(width='100px'))
    coord_input = Text(placeholder="Nombre del coordinador", layout=Layout(flex='1 1 auto'))
    coord_hbox = HBox([coord_label, coord_input], layout=Layout(margin='5px 0'))

    ins2_label = Label("Profesor 2:", layout=Layout(width='100px'))
    ins2_input = Text(placeholder="(Opcional)", layout=Layout(flex='1 1 auto'))
    ins2_hbox = HBox([ins2_label, ins2_input], layout=Layout(margin='5px 0'))

    ins3_label = Label("Profesor 3:", layout=Layout(width='100px'))
    ins3_input = Text(placeholder="(Opcional)", layout=Layout(flex='1 1 auto'))
    ins3_hbox = HBox([ins3_label, ins3_input], layout=Layout(margin='5px 0'))

    sost_label = Label("Sostén:", layout=Layout(width='100px'))
    sost_input = Text(placeholder="(Opcional)", layout=Layout(flex='1 1 auto'))
    sost_hbox = HBox([sost_label, sost_input], layout=Layout(margin='5px 0'))

    annot_label = Label("Anotaciones:", layout=Layout(width='100px', align_self='flex-start'))
    annot_textarea = Textarea(placeholder="Notas sobre el grupo...", layout=Layout(flex='1 1 auto', height='80px'))
    annot_hbox = HBox([annot_label, annot_textarea], layout=Layout(margin='5px 0', align_items='flex-start'))

    add_save_button = Button(description='Guardar Nuevo Grupo', button_style='success')
    add_cancel_button = Button(description='Cancelar')
    add_buttons_hbox = HBox(
        [add_save_button, add_cancel_button],
        layout=Layout(justify_content='flex-end', margin='15px 0 0 0')
    )

    modify_save_button = Button(description='Guardar Cambios Grupo', button_style='success')
    modify_cancel_button = Button(description='Cancelar')
    modify_buttons_hbox = HBox(
        [modify_save_button, modify_cancel_button],
        layout=Layout(justify_content='flex-end', margin='15px 0 0 0')
    )
    
    buttons_container = VBox([add_buttons_hbox, modify_buttons_hbox])
    
    vbox = VBox([
        title_label,
        institution_hbox,
        name_hbox,
        coord_hbox,
        ins2_hbox,
        ins3_hbox,
        sost_hbox,
        annot_hbox,
        buttons_container
    ], layout=Layout(border='2px solid cyan', padding='10px', margin_top='10px'))
    
    ui_elements = {
        "title_label": title_label,
        "school_text": institution_text,
        "name_input": name_input,
        "coord_input": coord_input,
        "ins2_input": ins2_input,
        "ins3_input": ins3_input,
        "sost_input": sost_input,
        "annot_textarea": annot_textarea,
        "add_save_button": add_save_button,
        "add_cancel_button": add_cancel_button,
        "modify_save_button": modify_save_button,
        "modify_cancel_button": modify_cancel_button,
        "add_buttons_hbox": add_buttons_hbox,
        "modify_buttons_hbox": modify_buttons_hbox
    }
    setattr(vbox, '_ui_elements_ref', ui_elements)
    return vbox, ui_elements
# --- Interfaz 5: "Tabla de Miembros" ---
def create_members_vbox():
    members_title_label = Label(
        "Tabla de Miembros: [Grupo N/A] (Institución: [Institución N/A])",
        style={'font_weight': 'bold', 'font_size': '16px'}
    )
    
    form_member_container = VBox(
        [],
        layout=Layout(
            width='98%', margin='10px auto 15px auto',
            padding='5px',display='flex', min_height='50px'
        )
    )
    
    members_select = Select(
        options=[],
        description='Seleccionar Miembro:',
        layout=Layout(width='40%', height='250px', margin='0 15px 0 0'),
        style={'description_width':'initial'}
    )
    
    members_details_label = Label("Detalles del Miembro:", style={'font_weight':'bold'})
    members_cognome_text = Text(value='', description="Apellido:", disabled=True, layout=Layout(width='95%'), style={'description_width': 'initial'})
    members_nome_text = Text(value='', description="Nombre:", disabled=True, layout=Layout(width='95%'), style={'description_width': 'initial'})
    members_iniz_text = Text(value='', description="Iniciales:", disabled=True, layout=Layout(width='95%'), style={'description_width': 'initial'})
    members_annotations_textarea = Textarea(value='', description="Anotaciones:", disabled=True, layout=Layout(width='95%', height='120px'), style={'description_width': 'initial'})
    
    members_right_details_vbox = VBox([
        members_details_label,
        members_cognome_text,
        members_nome_text,
        members_iniz_text,
        members_annotations_textarea
    ], layout=Layout(width='60%'))
    
    members_panels_hbox = HBox(
        [VBox([members_select], layout=Layout(width='40%')), members_right_details_vbox],
        layout=Layout(width='100%', align_items='flex-start')
    )
    
    members_nueva_button = Button(description='Nuevo Miembro', tooltip='Añadir nuevo miembro al grupo actual')
    members_modifica_button = Button(description='Modificar Miembro', tooltip='Modificar datos del miembro seleccionado')
    members_elimina_button = Button(description='Eliminar Miembro', tooltip='Eliminar miembro seleccionado y sus respuestas')
    members_questionario_button = Button(description='Cuestionario', tooltip='Ver/Editar respuestas del cuestionario del miembro seleccionado')
    members_salir_button = Button(description='Volver a Grupos', tooltip='Volver a la lista de grupos de la institución actual')
    
    members_buttons_hbox = HBox([
        members_nueva_button,
        members_modifica_button,
        members_elimina_button,
        members_questionario_button,
        members_salir_button
    ], layout=Layout(justify_content='space-around', margin='10px 0 0 0', flex_wrap='wrap'))
    
    vbox = VBox([members_title_label, form_member_container, members_panels_hbox, members_buttons_hbox])
    
    ui_elements = {
        "title_label": members_title_label,
        "form_member_container": form_member_container,
        "select": members_select,
        "cognome_text": members_cognome_text,
        "nome_text": members_nome_text,
        "iniz_text": members_iniz_text,
        "annotations_textarea": members_annotations_textarea,
        "nueva_button": members_nueva_button,
        "modifica_button": members_modifica_button,
        "elimina_button": members_elimina_button,
        "questionario_button": members_questionario_button,
        "salir_button": members_salir_button
    }
    return vbox, ui_elements

# --- Interfaz 6: Formulario "Actualización de Miembro" ---
def create_form_member_vbox():
    form_member_title_label = Label(
        "Formulario Miembro",
        style={'font_weight':'bold','font_size':'16px'}
    )
    form_member_institution_text = Text(
        value='N/A', 
        description="Institución:",
        disabled=True, 
        layout=Layout(width='auto', flex='1 1 auto'), 
        style={'description_width':'initial'}
    )
    form_member_class_text = Text(
        value='N/A', 
        description="Grupo:", 
        disabled=True, 
        layout=Layout(width='auto', flex='1 1 auto'), 
        style={'description_width':'initial'}
    )
    form_member_context_hbox = HBox(
        [form_member_institution_text, form_member_class_text],
        layout=Layout(margin='0 0 10px 0')
    )
    
    form_member_cognome_input = Text(placeholder='Apellido', layout=Layout(width='48%', margin='0 4% 0 0'))
    form_member_nome_input = Text(placeholder='Nombre', layout=Layout(width='48%'))
    form_member_cognome_nome_hbox = HBox([form_member_cognome_input, form_member_nome_input])
    
    form_member_iniziali_input = Text(description="Iniciales (3-4 letras):", layout=Layout(width='auto'), style={'description_width': 'initial'})
    form_member_sex_radio = RadioButtons(
        options=['Masculino','Femenino','Desconocido'],
        description="Sexo:",
        value='Desconocido', 
        layout=Layout(width='max-content', margin='0 10px'), 
        style={'description_width':'initial'}
    )
    form_member_dob_input = Text(placeholder='DD/MM/YYYY', description="Fecha nac.:", layout=Layout(width='auto'), style={'description_width': 'initial'})
    
    form_member_details_row = HBox(
        [form_member_iniziali_input, form_member_sex_radio, form_member_dob_input],
        layout=Layout(align_items='center', justify_content='flex-start', margin='10px 0 10px 0', flex_wrap='wrap')
    )
    
    form_member_annotations_textarea = Textarea(
        placeholder='Anotaciones sobre el miembro...',
        description="Anotaciones:",
        layout=Layout(width='95%', height='80px'),
        style={'description_width': 'initial'}
    )
    
    form_member_add_save_button = Button(description='Guardar Nuevo Miembro', button_style='success')
    form_member_add_cancel_button = Button(description='Cancelar')
    form_member_add_mode_buttons_hbox = HBox(
        [form_member_add_save_button, form_member_add_cancel_button],
        layout=Layout(justify_content='flex-end', margin='10px 0 0 0')
    )
    
    form_member_modify_ok_button = Button(description='Guardar Cambios Miembro', button_style='success')
    form_member_form_questionario_button = Button(description='Ir a Cuestionario', tooltip='Ver/Editar respuestas del cuestionario')
    form_member_modify_cancel_button = Button(description='Cancelar y Volver')
    
    form_member_modify_mode_buttons_hbox = HBox(
        [form_member_modify_ok_button, form_member_form_questionario_button,
         form_member_modify_cancel_button],
        layout=Layout(justify_content='space-between', margin='10px 0 0 0', flex_wrap='wrap')
    )
    
    form_member_buttons_container = VBox([form_member_add_mode_buttons_hbox, form_member_modify_mode_buttons_hbox])
    
    vbox = VBox([
        form_member_title_label,
        form_member_context_hbox,
        Label("Apellido y Nombre:"),
        form_member_cognome_nome_hbox,
        form_member_details_row,
        form_member_annotations_textarea,
        form_member_buttons_container
    ], layout=Layout(border='2px solid purple', padding='10px', margin_top='10px'))
    
    ui_elements = {
        "title_label":form_member_title_label,
        "school_text":form_member_institution_text,
        "class_text":form_member_class_text,
        "cognome_input":form_member_cognome_input,
        "nome_input":form_member_nome_input,
        "iniziali_input":form_member_iniziali_input,
        "gender_radio":form_member_sex_radio,
        "dob_input":form_member_dob_input,
        "annotations_textarea":form_member_annotations_textarea,
        "add_save_button":form_member_add_save_button,
        "add_cancel_button":form_member_add_cancel_button,
        "modify_ok_button":form_member_modify_ok_button,
        "q_button":form_member_form_questionario_button,
        "modify_cancel_button":form_member_modify_cancel_button,
        "add_buttons_hbox": form_member_add_mode_buttons_hbox,
        "modify_buttons_hbox": form_member_modify_mode_buttons_hbox
    }
    setattr(vbox, '_ui_elements_ref', ui_elements)
    return vbox, ui_elements
# --- Interfaz 7: Formulario "Cuestionario del Miembro" ---
def create_form_questionnaire_vbox(question_definitions_dict):
    form_q_title = Label(
        "Cuestionario del Miembro:",
        style={'font_weight':'bold','font_size':'16px'}
    )
    form_q_student_label = Label(
        "Miembro: N/A (Institución: N/A - Grupo: N/A)",
        style={'font_weight':'bold', 'margin_bottom':'10px'}
    )
    
    q_widgets = {}
    questions_vbox_children = []

    if isinstance(question_definitions_dict, dict):
        try:
            sorted_q_items = sorted(
                question_definitions_dict.items(),
                key=lambda item: (item[1].get('order', 99), item[0])
            )
        except Exception:
            sorted_q_items = list(question_definitions_dict.items())
    else:
        sorted_q_items = []

    for q_id_original, q_def in sorted_q_items:
        question_text = q_def.get("text", f"Pregunta {q_id_original} - Texto no disponible")
        data_key = q_def.get("data_key", q_id_original)
        max_selections = q_def.get("max_selections", 0)
        
        q_label_widget = Label(value=f"{question_text} (máximo {max_selections} selecciones)")
        q_widgets[f"{data_key}_label"] = q_label_widget

        dropdown_hbox_children = []
        if max_selections > 0:
            num_dd_for_layout = max_selections
            total_width_percentage = 98
            dropdown_width_percentage = (total_width_percentage / num_dd_for_layout) - (0.5 if num_dd_for_layout > 1 else 0)
            if dropdown_width_percentage < 15: dropdown_width_percentage = 15
            flex_wrap_style_dd = 'wrap' if num_dd_for_layout > 4 else 'nowrap'

            for i in range(max_selections):
                dd_widget_key = f"{data_key}_dd{i+1}"
                dropdown = Dropdown(
                    options=[('Seleccionar',None)],
                    value=None,
                    layout=Layout(width=f'{dropdown_width_percentage:.1f}%', margin='0 0.25% 5px 0.25%')
                )
                q_widgets[dd_widget_key] = dropdown
                dropdown_hbox_children.append(dropdown)
        
        dropdown_container_hbox = HBox(dropdown_hbox_children, layout=Layout(flex_wrap=flex_wrap_style_dd))
        questions_vbox_children.append(
            VBox([q_label_widget, dropdown_container_hbox], layout=Layout(margin='0 0 15px 0'))
        )
    
    form_q_questions_vbox = VBox(questions_vbox_children)
    
    form_q_ok_button = Button(description='Guardar Respuestas', button_style='success')
    form_q_pdf_class_button = Button(
        description='Generar PDF Cuestionario (Plantilla)',
        tooltip='Generar PDF con la plantilla de preguntas para este grupo',
        button_style='info'
    )
    form_q_salir_button = Button(description='Salir sin Guardar')
    form_q_manage_questions_button = Button(
        description='Gestionar Preguntas',
        tooltip='Añadir/modificar preguntas para este grupo en esta institución'
    )
    
    form_q_buttons_hbox = HBox(
        [form_q_ok_button, form_q_pdf_class_button, form_q_manage_questions_button, form_q_salir_button],
        layout=Layout(justify_content='space-between', margin='15px 0 0 0', flex_wrap='wrap')
    )
    
    vbox = VBox([form_q_title, form_q_student_label, form_q_questions_vbox, form_q_buttons_hbox])
    
    q_widgets.update({
        "title_label": form_q_title,
        "student_label": form_q_student_label,
        "ok_button": form_q_ok_button,
        "pdf_class_button": form_q_pdf_class_button,
        "salir_button": form_q_salir_button,
        "manage_questions_button": form_q_manage_questions_button,
        "questions_vbox": form_q_questions_vbox
    })
    
    return vbox, q_widgets

# --- Interfaz 8: Visualización de Sociograma ---
def create_sociogramma_vbox(sociogram_relation_options_map_dict):
    sociogramma_title_label = Label(
        "Sociograma: [Institución N/A - Grupo N/A]",
        style={'font_weight':'bold','font_size':'16px'}
    )
    sociogramma_controls_label = Label("Opciones de visualización:", style={'font_weight':'bold'})

    soc_gender_filter_radio = RadioButtons(
        options=[('Todos','Todos'),('Solo M','Masculino'),('Solo F','Femenino'), ('Solo D', 'Desconocido')],
        value='Todos',
        description="Sexo Miembros:",
        layout=Layout(width='max-content', margin='0 10px 0 0'),
        style={'description_width':'initial'}
    )
    soc_label_display_dropdown = Dropdown(
        options=[('Nombre A.','nombre_apellido'),('Iniciales','iniciales'),('Anónimo','anonimo')],
        value='nombre_apellido',
        description='Etiquetas Nodos:',
        layout=Layout(width='auto'),
        style={'description_width':'initial'}
    )
    filter_row1_hbox = HBox(
        [soc_gender_filter_radio, soc_label_display_dropdown],
        layout=Layout(margin='0 0 8px 0', align_items='center', flex_wrap='wrap')
    )

    soc_active_members_filter_cb = Checkbox(value=False, description='Miembros Activos', tooltip="FILTRAR: Mostrar solo nodos que nominan a otros", indent=False, layout=Layout(width='auto', margin='0 10px 0 0'))
    soc_nominators_option_cb = Checkbox(value=True, description='Nominadores/Aislados (Color/Ocultar)', tooltip="MARCADO: Colorea no elegidos. DESMARCADO: Oculta aislados.", indent=False, layout=Layout(width='auto', margin='0 10px 0 0'))
    soc_received_color_cb = Checkbox(value=False, description='Solo Reciben (Color)', tooltip="COLOREAR: Nodos que solo reciben elecciones o se auto-nominan", indent=False, layout=Layout(width='auto', margin='0 10px 0 0'))
    soc_reciprocal_nodes_color_cb = Checkbox(value=False, description='Nodos Recíprocos (Color)', tooltip="COLOREAR: Nodos que participan en al menos una relación recíproca", indent=False, layout=Layout(width='auto', margin='0 5px 0 0'))
    soc_reciprocal_links_style_cb = Checkbox(value=True, description='Aristas Recíprocas (Estilo)', tooltip="Estilo especial (línea discontinua, doble flecha) para aristas recíprocas", indent=False, layout=Layout(width='auto', margin='0 10px 0 0'))
    
    filter_row2_hbox = HBox(
        [soc_active_members_filter_cb, soc_nominators_option_cb, soc_received_color_cb, 
         soc_reciprocal_nodes_color_cb, soc_reciprocal_links_style_cb],
        layout=Layout(margin='0 0 8px 0', align_items='center', flex_wrap='wrap')
    )

    soc_gender_links_radio = RadioButtons(
        options=[('Todas','todas'),('Mismo Sexo','mismo_genero'),('Diferente Sexo','diferente_genero')],
        value='todas',
        description="Conexión por Sexo:",
        layout=Layout(width='max-content', margin='0 10px 0 0'),
        style={'description_width':'initial'}
    )
    filter_row3_hbox = HBox(
        [soc_gender_links_radio],
        layout=Layout(margin='0 0 10px 0', align_items='center', flex_wrap='wrap')
    )

    soc_participant_select_dropdown = Dropdown(
        options=[('Todos (Grafo Completo)', None)],
        value=None,
        description='Ver Conexiones de:',
        layout=Layout(width='auto', min_width='250px', margin='0 10px 5px 0'),
        style={'description_width':'initial'}
    )
    soc_connection_focus_radio = RadioButtons(
        options=[('Todas', 'all'), ('Salientes', 'outgoing'), ('Entrantes', 'incoming')],
        value='all',
        description='Mostrar Conexiones:',
        layout=Layout(width='max-content', margin='0 10px 5px 0'),
        style={'description_width':'initial'},
        disabled=True
    )
    participant_focus_hbox = HBox(
        [soc_participant_select_dropdown, soc_connection_focus_radio],
        layout=Layout(margin='0 0 10px 0', align_items='center', flex_wrap='wrap')
    )

    soc_highlight_mode_radio = RadioButtons(
        options=[('Ninguno', 'none'), ('Top N', 'top_n'), ('K-ésimo', 'k_th')],
        value='none',
        description='Resaltar Líderes:',
        layout=Layout(width='max-content', margin='0 10px 5px 0'),
        style={'description_width':'initial'}
    )
    soc_highlight_value_input = IntText(
        value=1, min=1,
        description='Valor (N o K):',
        disabled=True,
        layout=Layout(width='180px'),
        style={'description_width':'initial'}
    )
    highlight_controls_hbox = HBox(
        [soc_highlight_mode_radio, soc_highlight_value_input],
        layout=Layout(margin='0 0 10px 0', align_items='center', flex_wrap='wrap')
    )
    
    relations_checkboxes_label = Label("Relaciones Específicas a Incluir en el Grafo:", style={'font_weight':'normal', 'margin_bottom':'5px'})
    relations_checkboxes_vbox = VBox(
        [],
        layout=Layout(width='98%', max_height='150px', overflow_y='auto',
                      border='1px solid #E0E0E0', padding='8px',
                      margin='0 0 10px 0', box_sizing='border-box')
    )
    
    sociogramma_controls_vbox = VBox(
        [sociogramma_controls_label,
         relations_checkboxes_label, relations_checkboxes_vbox,
         filter_row1_hbox, filter_row2_hbox, filter_row3_hbox,
         Label("Foco en Participante (Opcional):", style={'font_weight':'normal', 'margin_top':'5px'}),
         participant_focus_hbox,
         highlight_controls_hbox
        ],
        layout=Layout(border='1px solid lightgray', padding='10px', margin='0 0 10px 0')
    )
    
    sociogramma_graph_output = Output(layout=Layout(width='98%',height='1000px',border='1px solid #e0e0e0',overflow='hidden'))
    sociogramma_legend_output = Output(layout=Layout(width='98%',margin_top='10px',padding='5px'))
    
    soc_redraw_btn = Button(description='Redibujar Sociograma (Cose)', button_style='info', tooltip='Redibujar con layout COSE y opciones actuales')
    soc_circle_layout_btn = Button(description='Dibujar en Círculo', button_style='success', tooltip='Redibujar con layout circular y opciones actuales')
    soc_pdf_btn = Button(description='Generar PDF del Sociograma', button_style='primary', icon='file-pdf-o', tooltip='Crear un PDF con el sociograma y su leyenda')
    soc_salir_btn = Button(description='Volver a Grupos', tooltip='Regresar a la lista de grupos de la institución')
    
    sociogramma_buttons_hbox = HBox(
        [soc_redraw_btn, soc_circle_layout_btn, soc_pdf_btn, soc_salir_btn],
        layout=Layout(justify_content='space-around', margin='10px 0 0 0', flex_wrap='wrap')
    )
    
    vbox = VBox([
        sociogramma_title_label,
        sociogramma_controls_vbox,
        sociogramma_graph_output,
        sociogramma_legend_output,
        sociogramma_buttons_hbox
    ])
    
    ui_elements = {
        "title_label":sociogramma_title_label,
        "graph_output":sociogramma_graph_output,
        "legend_output": sociogramma_legend_output,
        "redraw_button":soc_redraw_btn,
        "circle_layout_button": soc_circle_layout_btn,
        "pdf_button": soc_pdf_btn,
        "salir_button":soc_salir_btn,
        "gender_filter_radio":soc_gender_filter_radio,
        "label_display_dropdown":soc_label_display_dropdown,
        "active_members_filter_checkbox": soc_active_members_filter_cb,
        "nominators_option_checkbox": soc_nominators_option_cb,
        "received_color_checkbox": soc_received_color_cb,
        "reciprocal_nodes_color_checkbox": soc_reciprocal_nodes_color_cb,
        "reciprocal_links_style_checkbox":soc_reciprocal_links_style_cb,
        "gender_links_radio":soc_gender_links_radio,
        "participant_select_dropdown": soc_participant_select_dropdown,
        "connection_focus_radio": soc_connection_focus_radio,
        "highlight_mode_radio": soc_highlight_mode_radio,
        "highlight_value_input": soc_highlight_value_input,
        "relations_checkboxes_vbox": relations_checkboxes_vbox,
        "_current_cytoscape_widget": None,
        "_current_legend_info": None,
        "_last_drawn_graph_G": None,
        "_last_graph_elements_json": None,
        "_last_layout_used": 'cose',
        "_is_pdf_generation_call": False,
        "_keep_output_for_pdf_prep": False,
        "_relations_checkbox_widgets": []
    }
    return vbox, ui_elements

# --- Interfaz 9: Vista de Impresión del Cuestionario ---
def create_questionnaire_print_view_vbox():
    q_print_title_label = Label(
        "Vista Previa HTML de Respuestas del Cuestionario",
        style={'font_weight':'bold','font_size':'16px'}
    )
    q_print_stampa_button = Button(
        description="Generar Vista Previa HTML",
        tooltip="Genera la vista previa HTML de las respuestas del grupo actual"
    )
    q_print_chiudi_button = Button(
        description="Cerrar Vista",
        tooltip="Volver a la pantalla anterior"
    )
    q_print_export_pdf_button = Button(
        description="Exportar PDF Respuestas",
        tooltip="Genera y descarga un archivo PDF con las respuestas del grupo actual"
    )
    q_print_export_rtf_button = Button(
        description="Exportar RTF (Pend.)",
        disabled=True,
        tooltip="Funcionalidad pendiente para exportar a formato RTF"
    )
    
    q_print_toolbar_hbox = HBox([
        q_print_stampa_button,
        Label(layout=Layout(flex='1')),
        q_print_chiudi_button,
        q_print_export_pdf_button,
        q_print_export_rtf_button
    ], layout=Layout(border='1px solid lightgray', padding='5px', margin='0 0 10px 0', width='100%', flex_wrap='wrap'))
    
    q_print_context_label = Label(
        "Institución: N/A / Grupo: N/A",
        style={'font_weight':'bold', 'margin':'0 0 10px 20px'}
    )
    
    q_print_content_html = HTML(
        value="<i>Haga clic en 'Generar Vista Previa HTML' para ver las respuestas del cuestionario.</i>",
        layout=Layout(border='1px dashed #ccc', padding='15px', min_height='400px', width='100%')
    )
    
    q_print_content_area = VBox(
        [q_print_context_label, q_print_content_html],
        layout=Layout(overflow_y='auto', padding='10px')
    )
    
    vbox = VBox([q_print_title_label, q_print_toolbar_hbox, q_print_content_area])
    
    ui_elements = {
        "school_name_label": q_print_context_label,
        "content_html": q_print_content_html,
        "stampa_button": q_print_stampa_button,
        "chiudi_button": q_print_chiudi_button,
        "export_pdf_button": q_print_export_pdf_button,
        "export_rtf_button": q_print_export_rtf_button
    }
    return vbox, ui_elements

# --- Interfaz 10: Gestión de Preguntas (Lista) ---
def create_questions_management_vbox():
    mgmt_title_label = Label(
        "Gestionar Preguntas del Cuestionario",
        style={'font_weight': 'bold', 'font_size': '16px'}
    )
    mgmt_description_label = Label(
        "Selecciona una pregunta para modificar o eliminar, o añade una nueva para el grupo actual de la institución."
    )
    
    form_question_container = VBox(
        [],
        layout=Layout(
            width='98%', margin='10px auto 15px auto',
            padding='5px',display='flex', min_height='50px'
        )
    )
    
    mgmt_select = Select(
        options=[],
        description='Preguntas Definidas (para la institución/grupo actual):',
        disabled=False,
        layout=Layout(width='95%', height='250px', margin='0 5px 10px 0'),
        style={'description_width': 'initial'}
    )
    
    mgmt_nueva_button = Button(
        description='Nueva Pregunta',
        tooltip='Añadir nueva pregunta individual para este grupo'
    )
    mgmt_modifica_button = Button(
        description='Modificar Pregunta',
        tooltip='Modificar la pregunta seleccionada de la lista'
    )
    mgmt_elimina_button = Button(
        description='Eliminar Pregunta',
        tooltip='Eliminar la pregunta seleccionada de la lista'
    )
    mgmt_salir_button = Button(
        description='Volver al Cuestionario',
        tooltip='Regresar al formulario del cuestionario del miembro'
    )
    
    mgmt_buttons_hbox = HBox(
        [mgmt_nueva_button, mgmt_modifica_button, mgmt_elimina_button, mgmt_salir_button],
        layout=Layout(justify_content='space-around', margin='10px 0 0 0', flex_wrap='wrap')
    )
    
    vbox = VBox([
        mgmt_title_label,
        mgmt_description_label,
        form_question_container,
        mgmt_select,
        mgmt_buttons_hbox
    ])
    
    ui_elements = {
        "title_label": mgmt_title_label,
        "description_label": mgmt_description_label,
        "form_question_container": form_question_container,
        "select": mgmt_select,
        "nueva_button": mgmt_nueva_button,
        "modifica_button": mgmt_modifica_button,
        "elimina_button": mgmt_elimina_button,
        "salir_button": mgmt_salir_button
    }
    return vbox, ui_elements

# --- Interfaz 11: Formulario de Pregunta (Añadir/Modificar) ---
def create_form_question_vbox():
    form_q_title_label = Label(
        "Formulario de Pregunta",
        style={'font_weight': 'bold', 'font_size': '16px'}
    )
    form_q_id_input = Text(
        description='ID Único Pregunta:',
        placeholder='Ej: q_asiento_pos (no modificar si se edita, debe ser único en el grupo)',
        layout=Layout(width='95%'),
        style={'description_width': 'initial'}
    )
    form_q_text_input = Textarea(
        description='Texto de la Pregunta:',
        placeholder='Ej: ¿Con quién te gustaría sentarte?',
        layout=Layout(width='95%', height='80px'),
        style={'description_width': 'initial'}
    )
    form_q_type_input = Text(
        description='Tipo/Categoría Pregunta:',
        placeholder='Ej: Asiento, Tarea Escolar, Picnic/Juego',
        layout=Layout(width='95%'),
        style={'description_width': 'initial'}
    )
    form_q_polarity_radio = RadioButtons(
        options=[('Positiva', 'positive'), ('Negativa', 'negative')],
        description="Polaridad:",
        value='positive',
        layout={'width': 'max-content'},
        style={'description_width': 'initial'}
    )
    form_q_order_input = IntText(
        description='Orden (menor se muestra primero):',
        value=0,
        layout=Layout(width='250px'),
        style={'description_width': 'initial'}
    )
    form_q_data_key_input = Text(
        description='Clave de Datos (Data Key, única en el grupo):',
        placeholder='Ej: q_asiento_pos (usada para guardar respuestas, ¡cuidado al cambiar!)',
        layout=Layout(width='95%'),
        style={'description_width': 'initial'}
    )
    form_q_max_selections_input = IntText(
        description='Máximo de Selecciones Permitidas:',
        value=2, min=0,
        max=20,
        layout=Layout(width='280px'),
        style={'description_width': 'initial'}
    )
    form_q_allow_self_selection_checkbox = Checkbox(
        value=False,
        description="Permitir auto-selección (que el miembro se elija a sí mismo)",
        indent=False,
        layout=Layout(margin='5px 0')
    )
    
    form_q_add_save_button = Button(description='Guardar Nueva Pregunta', button_style='success')
    form_q_add_cancel_button = Button(description='Cancelar')
    form_q_add_mode_buttons_hbox = HBox(
        [form_q_add_save_button, form_q_add_cancel_button],
        layout=Layout(justify_content='flex-end', margin='15px 0 0 0')
    )
    
    form_q_modify_save_button = Button(description='Guardar Cambios en Pregunta', button_style='success')
    form_q_modify_cancel_button = Button(description='Cancelar')
    form_q_modify_mode_buttons_hbox = HBox(
        [form_q_modify_save_button, form_q_modify_cancel_button],
        layout=Layout(justify_content='flex-end', margin='15px 0 0 0')
    )
    
    form_q_buttons_container = VBox([form_q_add_mode_buttons_hbox, form_q_modify_mode_buttons_hbox])
    
    vbox = VBox([
        form_q_title_label,
        form_q_id_input,
        form_q_text_input,
        form_q_type_input,
        form_q_polarity_radio,
        form_q_order_input,
        form_q_data_key_input,
        form_q_max_selections_input,
        form_q_allow_self_selection_checkbox,
        form_q_buttons_container
    ], layout=Layout(border='2px solid red', padding='10px', margin_top='10px'))
    
    ui_elements = {
        "title_label": form_q_title_label,
        "id_input": form_q_id_input,
        "text_input": form_q_text_input,
        "type_input": form_q_type_input,
        "polarity_radio": form_q_polarity_radio,
        "order_input": form_q_order_input,
        "data_key_input": form_q_data_key_input,
        "max_selections_input": form_q_max_selections_input,
        "allow_self_selection_checkbox": form_q_allow_self_selection_checkbox,
        "add_save_button": form_q_add_save_button,
        "add_cancel_button": form_q_add_cancel_button,
        "modify_save_button": form_q_modify_save_button,
        "modify_cancel_button": form_q_modify_cancel_button,
        "add_buttons_hbox": form_q_add_mode_buttons_hbox,
        "modify_buttons_hbox": form_q_modify_mode_buttons_hbox
    }
    setattr(vbox, '_ui_elements_ref', ui_elements)
    return vbox, ui_elements            