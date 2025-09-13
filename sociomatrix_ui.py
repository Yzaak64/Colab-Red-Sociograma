# sociomatrix_ui.py
# (v4.1 - UI con Checkboxes, texto actualizado para "Miembro")

from ipywidgets import widgets, VBox, HBox, Label, Checkbox, Button, Output, Layout, HTML

def create_sociomatrix_interface():
    """
    Crea la interfaz de usuario para la visualización de la matriz sociométrica
    con selección múltiple de preguntas.
    """
    title_label = Label(
        "Visualización Matriz Sociométrica (Resumen de Conteo)",
        style={'font_weight': 'bold', 'font_size': '16px', 'margin_bottom': '15px'}
    )

    questions_checkboxes_vbox = VBox(
        [], 
        layout=Layout(
            width='100%',        
            max_height='180px',
            overflow_y='auto',
            border='1px solid #E0E0E0',
            padding='10px',
            margin_bottom='10px',
            box_sizing='border-box'
        )
    )
    
    select_all_button = Button(description="Todas", tooltip="Seleccionar todas las preguntas", layout=Layout(width='auto', min_width='80px', margin='0 5px 5px 0'))
    select_none_button = Button(description="Ninguna", tooltip="Deseleccionar todas las preguntas", layout=Layout(width='auto', min_width='80px', margin='0 5px 5px 0'))
    select_positive_button = Button(description="Positivas", tooltip="Seleccionar solo preguntas positivas", layout=Layout(width='auto', min_width='90px', margin='0 5px 5px 0'))
    select_negative_button = Button(description="Negativas", tooltip="Seleccionar solo preguntas negativas", layout=Layout(width='auto', min_width='90px', margin='0 15px 5px 0'))
    
    update_matrix_button = Button(
        description="Actualizar Matriz", 
        button_style="info", 
        icon="refresh", 
        tooltip="Generar la matriz con las preguntas seleccionadas",
        layout=Layout(width='auto', min_width='150px', margin='0 0 5px 0')
    )

    checkbox_selection_buttons_hbox = HBox(
        [select_all_button, select_none_button, select_positive_button, select_negative_button],
        layout=Layout(flex_wrap='wrap')
    )

    controls_vbox = VBox([
        Label("Seleccione las preguntas a incluir en la matriz:"),
        questions_checkboxes_vbox,
        checkbox_selection_buttons_hbox,
        update_matrix_button 
    ], layout=Layout(margin_bottom='20px', padding='10px', border='1px solid #f0f0f0', border_radius='4px'))


    html_table_output = Output(
        layout=Layout(width='100%', border='1px solid #B0B0B0', min_height='350px', overflow_x='auto', padding='5px', background_color='#fdfdfd')
    )
    with html_table_output:
        display(HTML("<p style='color:grey;text-align:center;margin-top:20px;'><i>Seleccione una o más preguntas y haga clic en 'Actualizar Matriz'.</i></p>"))


    stampa_button = Button(
        description="Generar PDF de Matriz",
        tooltip="Genera un archivo PDF de la matriz sociométrica actual",
        button_style='primary',
        icon='file-pdf-o',
        layout=Layout(margin_right='10px')
    )
    esci_button = Button(
        description="Volver a Tabla de Grupos",
        tooltip="Regresar a la lista de grupos de la institución",
        button_style='', 
        icon='arrow-left'
    )
    
    action_buttons_hbox = HBox(
        [stampa_button, esci_button],
        layout=Layout(justify_content='flex-end', margin_top='20px')
    )

    main_vbox = VBox(
        [title_label, controls_vbox, html_table_output, action_buttons_hbox],
        layout=Layout(width='calc(100% - 20px)', padding='10px', margin='0 auto')
    )

    ui_elements = {
        "title_label": title_label,
        "questions_checkboxes_vbox": questions_checkboxes_vbox,
        "select_all_button": select_all_button,
        "select_none_button": select_none_button,
        "select_positive_button": select_positive_button,
        "select_negative_button": select_negative_button,
        "update_matrix_button": update_matrix_button,
        "html_table_output": html_table_output,
        "stampa_button": stampa_button,
        "esci_button": esci_button,
        "main_vbox": main_vbox,
        "_question_checkboxes_list": [],
        "_last_generated_matrix_html": "" 
    }
    
    return main_vbox, ui_elements