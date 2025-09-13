# pdf_generator.py
# (v1.11 - Usa "Institución" en logs/textos, "sexo" para datos de Diana,
#          y "miembro" donde antes era "alumno", usa "members_data")

# --- BLOQUE 1: IMPORTACIONES Y CONFIGURACIÓN DE DEPENDENCIAS ---

# --- Importaciones Estándar de Python ---
import sys
import io
import re
import collections
import traceback
import base64
import datetime
import math
import unicodedata

# --- Importaciones de IPython/ipywidgets (principalmente para tipos) ---
from IPython.display import display, HTML, clear_output
from ipywidgets import widgets

# --- Importaciones de Módulos Personalizados ---
import sociograma_data

# --- Dependencias de ReportLab (para generación de PDF) ---
REPORTLAB_AVAILABLE = False
# Fallbacks para constantes y clases de ReportLab
A4_SIZE, LANDSCAPE_FUNC, LETTER_SIZE, CM_UNIT, INCH_UNIT, MM_UNIT = (595.27,841.89), lambda x: x, (612.0,792.0), 28.3464566929, 72, 2.83464566929
ParagraphStyleClass = type('ParagraphStyle', (object,), {'__init__': lambda self, name, **kwargs: setattr(self, 'name', name)})
SpacerClass, PageBreakClass, FrameClass, PageTemplateClass, BaseDocTemplateClass, TableClass, TableStyleClass, ImageClass, KeepInFrameClass, ListFlowableClass, ListItemClass = (type(f'DummyRL_{i}', (object,), {}) for i in range(11))
ALIGN_CENTER, ALIGN_LEFT, ALIGN_JUSTIFY, ALIGN_RIGHT = 1,0,4,2
HexColorFunc = lambda x: None; color_black = None; color_lightgrey = None; color_white = None; color_grey = None; ColorClass = lambda r,g,b,a=1: None; toColorFunc = lambda x: None

def getSampleStyleSheet_fallback_func():
    default_styles = collections.defaultdict(lambda: ParagraphStyleClass(name='Normal'))
    default_styles['Normal'] = ParagraphStyleClass(name='Normal')
    default_styles['h1'] = ParagraphStyleClass(name='h1')
    style_names_to_add_fb = ['h2', 'h3', 'Bullet_Point', 'Member_Name_Header',
                              'Questionnaire_Header', 'Question_Text', 'Response_Line',
                              'Response_Label', 'Small_Info', 'Table_Header', 'Table_Cell',
                              'Table_Cell_Left', 'Legend_MainTitle', 'Legend_Subtitle',
                              'Legend_Item_Color_Symbol', 'Legend_Item_Text', 'Legend_Item_Width_Symbol',
                              'H1_Manual', 'H2_Manual', 'H3_Manual', 'H4_Manual',
                              'Normal_Manual', 'Table_Header_Manual', 'Table_Cell_Manual',
                              'Bullet_Manual', 'Bullet_Sub_Manual', 'Code_Manual']
    for style_n_fb in style_names_to_add_fb:
        default_styles[style_n_fb] = ParagraphStyleClass(name=style_n_fb)
    return default_styles
getSampleStyleSheet_actual = getSampleStyleSheet_fallback_func

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4 as RL_A4, landscape as RL_landscape, letter as RL_letter
    from reportlab.lib.units import cm as RL_cm, inch as RL_inch, mm as RL_mm
    from reportlab.lib.styles import getSampleStyleSheet as RL_getSampleStyleSheet, ParagraphStyle as RL_ParagraphStyle
    from reportlab.platypus import Paragraph, Spacer as RL_Spacer, PageBreak as RL_PageBreak, Frame as RL_Frame, PageTemplate as RL_PageTemplate, BaseDocTemplate as RL_BaseDocTemplate, Table as RL_Table, TableStyle as RL_TableStyle, Image as RL_Image, KeepInFrame as RL_KeepInFrame, ListFlowable as RL_ListFlowable, ListItem as RL_ListItem
    from reportlab.lib.enums import TA_CENTER as RL_TA_CENTER, TA_LEFT as RL_TA_LEFT, TA_JUSTIFY as RL_TA_JUSTIFY, TA_RIGHT as RL_TA_RIGHT
    from reportlab.lib.colors import HexColor as RL_HexColor, black as RL_black, lightgrey as RL_lightgrey, white as RL_white, grey as RL_grey, Color as RL_Color, toColor as RL_toColor
    
    REPORTLAB_AVAILABLE = True
    A4_SIZE, LANDSCAPE_FUNC, LETTER_SIZE, CM_UNIT, INCH_UNIT, MM_UNIT = RL_A4, RL_landscape, RL_letter, RL_cm, RL_inch, RL_mm
    ParagraphStyleClass = RL_ParagraphStyle
    SpacerClass, PageBreakClass, FrameClass, PageTemplateClass, BaseDocTemplateClass, TableClass, TableStyleClass, ImageClass, KeepInFrameClass, ListFlowableClass, ListItemClass = RL_Spacer, RL_PageBreak, RL_Frame, RL_PageTemplate, RL_BaseDocTemplate, RL_Table, RL_TableStyle, RL_Image, RL_KeepInFrame, RL_ListFlowable, RL_ListItem
    ALIGN_CENTER, ALIGN_LEFT, ALIGN_JUSTIFY, ALIGN_RIGHT = RL_TA_CENTER, RL_TA_LEFT, RL_TA_JUSTIFY, RL_TA_RIGHT
    HexColorFunc, color_black, color_lightgrey, color_white, color_grey, ColorClass, toColorFunc = RL_HexColor, RL_black, RL_lightgrey, RL_white, RL_grey, RL_Color, RL_toColor
    getSampleStyleSheet_actual = RL_getSampleStyleSheet
except ImportError:
    pass

# --- Dependencias de Pillow, xhtml2pdf, Matplotlib... ---
PILLOW_AVAILABLE = False
try:
    from PIL import Image as PILImage_local, ImageDraw as ImageDraw_local, ImageFont as ImageFont_local
    PILImage, ImageDraw, ImageFont = PILImage_local, ImageDraw_local, ImageFont_local
    PILLOW_AVAILABLE = True
except ImportError: pass
XHTML2PDF_AVAILABLE = False
try:
    from xhtml2pdf import pisa
    XHTML2PDF_AVAILABLE = True
except ImportError: pass
MATPLOTLIB_AVAILABLE = False
try:
    import matplotlib.pyplot as plt_local
    import matplotlib.patches as mpatches_local
    import numpy as np_local
    import matplotlib.lines as mlines_local
    import networkx as nx_local
    plt, mpatches, np, mlines, nx = plt_local, mpatches_local, np_local, mlines_local, nx_local
    MATPLOTLIB_AVAILABLE = True
except ImportError: pass
# --- FIN BLOQUE 1 ---
# --- BLOQUE 2: FUNCIONES HELPER GENERALES DE PDF ---
def _draw_page_number_manual(canvas, doc):
    if not REPORTLAB_AVAILABLE: return
    canvas.saveState()
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(color_grey if color_grey else ColorClass(0.5,0.5,0.5))
    margin_adj = 1.5 * CM_UNIT
    doc_width = getattr(doc, 'width', A4_SIZE[0] - 2 * margin_adj)
    canvas.drawRightString(doc_width + 1*CM_UNIT, 1 * CM_UNIT, f"Página {doc.page}")
    canvas.restoreState()

def _create_pdf_styles_manual():
    styles = getSampleStyleSheet_actual()
    if not REPORTLAB_AVAILABLE: return styles
    styles.add(ParagraphStyleClass(name='H1_Manual', parent=styles['h1'], alignment=ALIGN_CENTER, fontSize=18, spaceBefore=12, spaceAfter=8, textColor=HexColorFunc("#2c3e50")))
    styles.add(ParagraphStyleClass(name='H2_Manual', parent=styles['h2'], fontSize=15, spaceBefore=12, spaceAfter=6, alignment=ALIGN_LEFT, textColor=HexColorFunc("#34495e")))
    styles.add(ParagraphStyleClass(name='H3_Manual', parent=styles['h3'], fontSize=12, spaceBefore=10, spaceAfter=5, alignment=ALIGN_LEFT, textColor=HexColorFunc("#2980b9")))
    styles.add(ParagraphStyleClass(name='H4_Manual', parent=styles['h4'], fontSize=10, spaceBefore=6, spaceAfter=3, alignment=ALIGN_LEFT, textColor=HexColorFunc("#34495e"), fontName='Helvetica-Bold'))
    styles.add(ParagraphStyleClass(name='Normal_Manual', parent=styles['Normal'], fontSize=10, leading=14, spaceBefore=3, spaceAfter=3, alignment=ALIGN_JUSTIFY))
    styles.add(ParagraphStyleClass(name='Table_Header_Manual', parent=styles['Normal_Manual'], fontName='Helvetica-Bold', fontSize=8, alignment=ALIGN_LEFT, leading=10))
    styles.add(ParagraphStyleClass(name='Table_Cell_Manual', parent=styles['Normal_Manual'], fontSize=8, alignment=ALIGN_LEFT, leading=10))
    styles.add(ParagraphStyleClass(name='Bullet_Manual', parent=styles['Normal_Manual'], leftIndent=1*CM_UNIT, firstLineIndent=-0.5*CM_UNIT, bulletIndent=0*CM_UNIT, spaceBefore=2, fontSize=9, leading=12))
    styles.add(ParagraphStyleClass(name='Bullet_Sub_Manual', parent=styles['Bullet_Manual'], leftIndent=2.5*CM_UNIT))
    return styles

def _create_legend_line_image_pil(color_hex, line_style_name, arrow_shape_name, source_arrow_shape_name,
                                 img_width_px=60, img_height_px=20, line_thickness=2):
    if not PILLOW_AVAILABLE or not PILImage or not ImageDraw:
        return None
    try:
        pil_color_val_legend = (0,0,0)
        if color_hex.startswith('#') and len(color_hex) == 7:
            pil_color_val_legend = (int(color_hex[1:3], 16), int(color_hex[3:5], 16), int(color_hex[5:7], 16))
        elif REPORTLAB_AVAILABLE and toColorFunc:
            try:
                rl_color_obj_legend = toColorFunc(color_hex)
                if rl_color_obj_legend: pil_color_val_legend = tuple(int(c * 255) for c in rl_color_obj_legend.rgb())
            except: pass

        img_legend_line = PILImage.new("RGBA", (img_width_px, img_height_px), (255, 255, 255, 0))
        draw_legend_line = ImageDraw.Draw(img_legend_line)
        y_center_img_line = img_height_px // 2
        line_start_x_img_line = 5
        line_end_x_img_line = img_width_px - 5

        if line_style_name == 'dashed':
            for i_dash_leg in range(line_start_x_img_line, line_end_x_img_line, 8):
                draw_legend_line.line([(i_dash_leg, y_center_img_line), (min(i_dash_leg + 4, line_end_x_img_line), y_center_img_line)], fill=pil_color_val_legend, width=line_thickness)
        elif line_style_name == 'dotted':
            for i_dot_leg in range(line_start_x_img_line, line_end_x_img_line, 4):
                draw_legend_line.line([(i_dot_leg, y_center_img_line), (min(i_dot_leg + 1, line_end_x_img_line), y_center_img_line)], fill=pil_color_val_legend, width=line_thickness)
        else:
            draw_legend_line.line([(line_start_x_img_line, y_center_img_line), (line_end_x_img_line, y_center_img_line)], fill=pil_color_val_legend, width=line_thickness)

        arrow_head_size_leg = 6
        if arrow_shape_name != 'none' and arrow_shape_name in ['triangle', 'chevron', 'diamond', 'tee']:
            points_target_arrow_leg = []
            if arrow_shape_name == 'triangle' or arrow_shape_name == 'chevron':
                points_target_arrow_leg = [(line_end_x_img_line - arrow_head_size_leg, y_center_img_line - arrow_head_size_leg//2),
                                     (line_end_x_img_line, y_center_img_line),
                                     (line_end_x_img_line - arrow_head_size_leg, y_center_img_line + arrow_head_size_leg//2)]
            elif arrow_shape_name == 'diamond':
                points_target_arrow_leg = [(line_end_x_img_line, y_center_img_line), 
                                     (line_end_x_img_line - arrow_head_size_leg//2, y_center_img_line - arrow_head_size_leg//2),
                                     (line_end_x_img_line - arrow_head_size_leg, y_center_img_line),
                                     (line_end_x_img_line - arrow_head_size_leg//2, y_center_img_line + arrow_head_size_leg//2)]
            elif arrow_shape_name == 'tee':
                draw_legend_line.line([(line_end_x_img_line, y_center_img_line - arrow_head_size_leg//2), (line_end_x_img_line, y_center_img_line + arrow_head_size_leg//2)], fill=pil_color_val_legend, width=line_thickness)
            if points_target_arrow_leg: draw_legend_line.polygon(points_target_arrow_leg, fill=pil_color_val_legend)

        if source_arrow_shape_name != 'none' and source_arrow_shape_name in ['triangle', 'chevron', 'diamond', 'tee']:
            points_source_arrow_leg = []
            if source_arrow_shape_name == 'triangle' or source_arrow_shape_name == 'chevron':
                points_source_arrow_leg = [(line_start_x_img_line + arrow_head_size_leg, y_center_img_line - arrow_head_size_leg//2),
                                     (line_start_x_img_line, y_center_img_line),
                                     (line_start_x_img_line + arrow_head_size_leg, y_center_img_line + arrow_head_size_leg//2)]
            elif source_arrow_shape_name == 'diamond':
                 points_source_arrow_leg = [(line_start_x_img_line, y_center_img_line),
                                     (line_start_x_img_line + arrow_head_size_leg//2, y_center_img_line - arrow_head_size_leg//2),
                                     (line_start_x_img_line + arrow_head_size_leg, y_center_img_line),
                                     (line_start_x_img_line + arrow_head_size_leg//2, y_center_img_line + arrow_head_size_leg//2)]
            elif source_arrow_shape_name == 'tee':
                draw_legend_line.line([(line_start_x_img_line, y_center_img_line - arrow_head_size_leg//2), (line_start_x_img_line, y_center_img_line + arrow_head_size_leg//2)], fill=pil_color_val_legend, width=line_thickness)
            if points_source_arrow_leg: draw_legend_line.polygon(points_source_arrow_leg, fill=pil_color_val_legend)
            
        buffer_img_leg = io.BytesIO()
        img_legend_line.save(buffer_img_leg, format="PNG")
        buffer_img_leg.seek(0)
        return buffer_img_leg
    except Exception:
        return None
# --- FIN BLOQUE 2 ---
# --- BLOQUE 3: PDF DE INSTRUCCIONES DE IMPORTACIÓN CSV ---
def _draw_page_number_csv_instructions(canvas, doc):
    if not REPORTLAB_AVAILABLE: return
    canvas.saveState()
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(color_grey if color_grey else ColorClass(0.5,0.5,0.5))
    margin_adj_instr_page = 1 * CM_UNIT
    doc_width_page = getattr(doc, 'width', A4_SIZE[0] - 2 * margin_adj_instr_page)
    doc_left_margin_page = getattr(doc, 'leftMargin', margin_adj_instr_page)
    canvas.drawRightString(doc_width_page + doc_left_margin_page - margin_adj_instr_page, margin_adj_instr_page, f"Página {doc.page}")
    canvas.restoreState()

def _create_pdf_styles_csv_instructions():
    styles_instr_csv = getSampleStyleSheet_actual()
    if not REPORTLAB_AVAILABLE: return styles_instr_csv
    styles_instr_csv.add(ParagraphStyleClass(name='H1_Custom_Instr', parent=styles_instr_csv['h1'], alignment=ALIGN_CENTER, fontSize=18, spaceBefore=12, spaceAfter=8, textColor=HexColorFunc("#2c3e50")))
    styles_instr_csv.add(ParagraphStyleClass(name='H2_Custom_Instr', parent=styles_instr_csv['h2'], fontSize=14, spaceBefore=10, spaceAfter=5, alignment=ALIGN_LEFT, textColor=HexColorFunc("#34495e")))
    styles_instr_csv.add(ParagraphStyleClass(name='H3_Custom_Instr', parent=styles_instr_csv['h3'], fontSize=11, spaceBefore=8, spaceAfter=4, alignment=ALIGN_LEFT, textColor=HexColorFunc("#2980b9")))
    styles_instr_csv.add(ParagraphStyleClass(name='Normal_Custom_Instr', parent=styles_instr_csv['Normal'], fontSize=10, leading=14, spaceBefore=3, spaceAfter=3, alignment=ALIGN_JUSTIFY))
    styles_instr_csv.add(ParagraphStyleClass(name='Code_Instr', parent=styles_instr_csv['Normal'], fontName='Courier', fontSize=9,textColor=HexColorFunc("#c0392b"), backColor=HexColorFunc("#ecf0f1"), borderPadding=4, borderRadius=2, spaceBefore=4, spaceAfter=4))
    styles_instr_csv.add(ParagraphStyleClass(name='Table_Header_Instr', parent=styles_instr_csv['Normal_Custom_Instr'], fontName='Helvetica-Bold', fontSize=8, alignment=ALIGN_LEFT, leading=10))
    styles_instr_csv.add(ParagraphStyleClass(name='Table_Cell_Left_Instr', parent=styles_instr_csv['Normal_Custom_Instr'], fontSize=8, alignment=ALIGN_LEFT, leading=10))
    styles_instr_csv.add(ParagraphStyleClass(name='Bullet_Point_Instr', parent=styles_instr_csv['Normal_Custom_Instr'], leftIndent=1*CM_UNIT, firstLineIndent=-0.5*CM_UNIT, bulletIndent=0*CM_UNIT, spaceBefore=2, fontSize=9, leading=12))
    return styles_instr_csv

# Esta función parece ser un duplicado de la del bloque 2, la incluyo por si acaso.
def _draw_page_number_manual(canvas, doc):
    if not REPORTLAB_AVAILABLE: return
    canvas.saveState()
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(color_grey if color_grey else ColorClass(0.5,0.5,0.5))
    margin_adj = 1.5 * CM_UNIT
    doc_width = getattr(doc, 'width', A4_SIZE[0] - 2 * margin_adj)
    canvas.drawRightString(doc_width + 1*CM_UNIT, 1 * CM_UNIT, f"Página {doc.page}")
    canvas.restoreState()

# Esta función parece ser un duplicado de la del bloque 2, la incluyo por si acaso.
def _create_pdf_styles_manual():
    styles = getSampleStyleSheet_actual()
    if not REPORTLAB_AVAILABLE: return styles
    styles.add(ParagraphStyleClass(name='H1_Manual', parent=styles['h1'], alignment=ALIGN_CENTER, fontSize=18, spaceBefore=12, spaceAfter=8, textColor=HexColorFunc("#2c3e50")))
    styles.add(ParagraphStyleClass(name='H2_Manual', parent=styles['h2'], fontSize=15, spaceBefore=12, spaceAfter=6, alignment=ALIGN_LEFT, textColor=HexColorFunc("#34495e")))
    styles.add(ParagraphStyleClass(name='H3_Manual', parent=styles['h3'], fontSize=12, spaceBefore=10, spaceAfter=5, alignment=ALIGN_LEFT, textColor=HexColorFunc("#2980b9")))
    styles.add(ParagraphStyleClass(name='H4_Manual', parent=styles['h4'], fontSize=10, spaceBefore=6, spaceAfter=3, alignment=ALIGN_LEFT, textColor=HexColorFunc("#34495e"), fontName='Helvetica-Bold'))
    styles.add(ParagraphStyleClass(name='Normal_Manual', parent=styles['Normal'], fontSize=10, leading=14, spaceBefore=3, spaceAfter=3, alignment=ALIGN_JUSTIFY))
    styles.add(ParagraphStyleClass(name='Table_Header_Manual', parent=styles['Normal_Manual'], fontName='Helvetica-Bold', fontSize=8, alignment=ALIGN_LEFT, leading=10))
    styles.add(ParagraphStyleClass(name='Table_Cell_Manual', parent=styles['Normal_Manual'], fontSize=8, alignment=ALIGN_LEFT, leading=10))
    styles.add(ParagraphStyleClass(name='Bullet_Manual', parent=styles['Normal_Manual'], leftIndent=1*CM_UNIT, firstLineIndent=-0.5*CM_UNIT, bulletIndent=0*CM_UNIT, spaceBefore=2, fontSize=9, leading=12))
    styles.add(ParagraphStyleClass(name='Bullet_Sub_Manual', parent=styles['Bullet_Manual'], leftIndent=2.5*CM_UNIT))
    return styles

def generate_complete_instructions_pdf(registro_output):
    """
    Genera un manual de usuario completo y detallado en PDF.
    Construido en bloques.
    """
    if not REPORTLAB_AVAILABLE or not BaseDocTemplateClass:
        err_msg = "ERROR (Manual de Usuario): ReportLab no está instalado."
        if registro_output:
            with registro_output:
                print(err_msg)
        return

    filename = "Instrucciones.pdf"
    buffer = io.BytesIO()
    doc = BaseDocTemplateClass(buffer, pagesize=A4_SIZE,
                               leftMargin=2*CM_UNIT, rightMargin=2*CM_UNIT,
                               topMargin=2*CM_UNIT, bottomMargin=2*CM_UNIT)
    frame = FrameClass(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='frame_manual')
    page_template = PageTemplateClass(id='page_tpl_manual', frames=[frame], onPage=_draw_page_number_manual)
    doc.addPageTemplates([page_template])
    styles = _create_pdf_styles_manual()
    story = []

    # --- Bloque 1: Portada, Índice e Introducción ---
    
    # --- PORTADA ---
    story.append(Paragraph("Manual de Usuario", styles['H1_Manual']))
    story.append(SpacerClass(1, 1*CM_UNIT))
    story.append(Paragraph("Programa de Sociograma", styles['H2_Manual']))
    story.append(SpacerClass(1, 0.5*CM_UNIT))
    story.append(Paragraph(f"Versión del documento: {datetime.date.today().strftime('%d de %B de %Y')}", styles['Normal_Manual']))
    story.append(PageBreakClass())

    # --- ÍNDICE ---
    story.append(Paragraph("Índice", styles['H1_Manual']))
    toc_items = [
        "1. Introducción al Programa", "2. Flujo de Trabajo Básico",
        "3. Guía Detallada de la Interfaz",
        "   3.1. Pantalla Principal: Gestión de Instituciones",
        "   3.2. Pantalla de Grupos", "   3.3. Pantalla de Miembros",
        "   3.4. Cuestionario del Miembro y Gestión de Preguntas",
        "4. Herramientas de Análisis",
        "   4.1. El Sociograma Interactivo", "   4.2. La Matriz Sociométrica",
        "   4.3. La Diana de Afinidad",
        "5. Importación y Exportación de Datos (CSV)",
        "   5.1. Configuración de un Formulario de Google",
        "   5.2. Estructura del Archivo CSV",
        "   5.3. Panel de Importación y Exportación en la App"
    ]
    for item in toc_items:
        style = styles['H3_Manual'] if item.strip().startswith(('1.', '2.', '3.', '4.', '5.')) else styles['Normal_Manual']
        if item.strip().startswith(('2.', '3.', '4.', '5.')):
             story.append(SpacerClass(1, 0.2*CM_UNIT))
        story.append(Paragraph(item, style))
    story.append(PageBreakClass())

    # --- SECCIÓN 1 y 2 ---
    story.append(Paragraph("1. Introducción al Programa", styles['H2_Manual']))
    story.append(Paragraph("Este programa está diseñado para facilitar la creación, gestión y análisis de datos sociométricos. Permite definir instituciones, grupos y miembros, registrar respuestas a cuestionarios sociométricos y visualizar las dinámicas grupales a través de sociogramas, matrices y otros reportes.", styles['Normal_Manual']))
    
    story.append(SpacerClass(1, 0.5*CM_UNIT))
    story.append(Paragraph("2. Flujo de Trabajo Básico", styles['H2_Manual']))
    story.append(Paragraph("El uso principal de la aplicación sigue una jerarquía lógica, desde lo más general a lo más específico:", styles['Normal_Manual']))
    workflow_items = [
        ListItemClass(Paragraph("<b>Gestión de Instituciones:</b> El nivel más alto. Aquí puede crear, modificar o eliminar instituciones.", styles['Bullet_Manual'])),
        ListItemClass(Paragraph("<b>Gestión de Grupos:</b> Dentro de cada institución, puede crear y gestionar grupos.", styles['Bullet_Manual'])),
        ListItemClass(Paragraph("<b>Gestión de Miembros:</b> Dentro de cada grupo, se añaden los miembros participantes.", styles['Bullet_Manual'])),
        ListItemClass(Paragraph("<b>Registro de Cuestionarios:</b> Para cada miembro, se puede acceder a un formulario para registrar sus elecciones.", styles['Bullet_Manual'])),
        ListItemClass(Paragraph("<b>Análisis y Reportes:</b> Con los datos cargados, se pueden generar sociogramas, matrices, reportes PDF y la Diana de Afinidad.", styles['Bullet_Manual']))
    ]
    if ListFlowableClass and ListItemClass: story.append(ListFlowableClass(workflow_items, bulletType='bullet'))
    
    story.append(SpacerClass(1, 0.5*CM_UNIT))
    story.append(Paragraph("3. Guía Detallada de la Interfaz", styles['H2_Manual']))
    story.append(Paragraph("<b>3.1. Pantalla Principal: Gestión de Instituciones</b>", styles['H3_Manual']))
    story.append(Paragraph("Esta es la primera pantalla. Muestra una lista de todas las instituciones y sus controles asociados.", styles['Normal_Manual']))
    
    story.append(Paragraph("<u>Componentes de la Pantalla de Instituciones:</u>", styles['H4_Manual']))
    inst_components_items = [
        ListItemClass(Paragraph("<b>Lista de Instituciones:</b> Un cuadro de selección que muestra todas las instituciones existentes. Haga clic en el nombre de una institución para seleccionarla. Esto es necesario para poder modificarla, eliminarla o ver sus grupos.", styles['Bullet_Manual'])),
        ListItemClass(Paragraph("<b>Anotaciones de Institución:</b> Un cuadro de texto a la derecha que muestra las notas guardadas para la institución seleccionada. Es de solo lectura en esta vista.", styles['Bullet_Manual']))
    ]
    if ListFlowableClass and ListItemClass: story.append(ListFlowableClass(inst_components_items, bulletType='bullet'))
    
    story.append(Paragraph("<u>Botones de Acción:</u>", styles['H4_Manual']))
    inst_buttons_items = [
        ListItemClass(Paragraph("<b>Nueva Institución:</b> Muestra un formulario para crear una nueva institución. Deberá proporcionar un nombre único y, opcionalmente, anotaciones.", styles['Bullet_Manual'])),
        ListItemClass(Paragraph("<b>Modificar Institución:</b> (Se habilita al seleccionar una). Permite cambiar el nombre y las anotaciones de la institución seleccionada.", styles['Bullet_Manual'])),
        ListItemClass(Paragraph("<b>Eliminar Institución:</b> (Se habilita al seleccionar una). Borra permanentemente la institución seleccionada y todos sus datos asociados (grupos, miembros, respuestas, etc.). <b>Esta acción es irreversible y requiere confirmación.</b>", styles['Bullet_Manual'])),
        ListItemClass(Paragraph("<b>Ver Grupos:</b> (Se habilita al seleccionar una). Navega a la pantalla de gestión de grupos de la institución seleccionada. Es el paso principal para profundizar en los datos.", styles['Bullet_Manual'])),
        ListItemClass(Paragraph("<b>Importar/Exportar CSV:</b> Despliega el panel para la gestión de datos masivos. Su uso se detalla en la sección 5.", styles['Bullet_Manual'])),
        ListItemClass(Paragraph("<b>Salir App:</b> Cierra la aplicación y finaliza la sesión.", styles['Bullet_Manual']))
    ]
    if ListFlowableClass and ListItemClass: story.append(ListFlowableClass(inst_buttons_items, bulletType='bullet'))
    # --- Bloque 2: Guía de la Pantalla de Grupos ---
    
    story.append(PageBreakClass())
    story.append(Paragraph("<b>3.2. Pantalla de Grupos</b>", styles['H3_Manual']))
    story.append(Paragraph("Tras seleccionar una institución y hacer clic en 'Ver Grupos', llegará aquí. Esta pantalla lista todos los grupos de esa institución. Al seleccionar un grupo, verá sus detalles (coordinador, profesores, etc.) en el panel derecho.", styles['Normal_Manual']))
    
    story.append(Paragraph("<u>Componentes de la Pantalla de Grupos:</u>", styles['H4_Manual']))
    group_components_items = [
        ListItemClass(Paragraph("<b>Lista de Grupos:</b> Cuadro de selección con todos los grupos de la institución. Seleccione uno para habilitar las acciones sobre él.", styles['Bullet_Manual'])),
        ListItemClass(Paragraph("<b>Detalles del Grupo:</b> Muestra información adicional del grupo seleccionado como el coordinador, profesores de apoyo y anotaciones.", styles['Bullet_Manual']))
    ]
    if ListFlowableClass and ListItemClass: story.append(ListFlowableClass(group_components_items, bulletType='bullet'))

    story.append(Paragraph("<u>Botones de Acción Principales:</u>", styles['H4_Manual']))
    group_buttons_items = [
        ListItemClass(Paragraph("<b>Nuevo Grupo:</b> Abre un formulario para crear un nuevo grupo en la institución actual.", styles['Bullet_Manual'])),
        ListItemClass(Paragraph("<b>Modificar Grupo:</b> (Se habilita al seleccionar). Permite editar los detalles del grupo seleccionado.", styles['Bullet_Manual'])),
        ListItemClass(Paragraph("<b>Eliminar Grupo:</b> (Se habilita al seleccionar). Borra el grupo y todos sus miembros y respuestas.", styles['Bullet_Manual'])),
        ListItemClass(Paragraph("<b>Ver Miembros:</b> (Se habilita al seleccionar). Navega a la siguiente pantalla para gestionar los miembros del grupo.", styles['Bullet_Manual'])),
        ListItemClass(Paragraph("<b>Volver a Instituciones:</b> Regresa a la pantalla principal.", styles['Bullet_Manual'])),
    ]
    if ListFlowableClass and ListItemClass: story.append(ListFlowableClass(group_buttons_items, bulletType='bullet'))

    story.append(Paragraph("<u>Botones de Análisis y Reportes:</u>", styles['H4_Manual']))
    group_analysis_items = [
        ListItemClass(Paragraph("<b>Ver Sociograma:</b> (Se habilita al seleccionar). Abre la herramienta de visualización del sociograma para el grupo. Esta herramienta se explica en detalle en la sección 4.1.", styles['Bullet_Manual'])),
        ListItemClass(Paragraph("<b>Reportes del Grupo:</b> (Se habilita al seleccionar). Despliega un sub-menú con tres potentes herramientas de análisis y reporte:", styles['Bullet_Manual'])),
        ListItemClass(Paragraph("<b>Matriz Sociométrica:</b> Navega a una vista de tabla que resume numéricamente las elecciones. Se explica en la sección 4.2.", styles['Bullet_Sub_Manual'])),
        ListItemClass(Paragraph("<b>PDF Datos Cuestionario:</b> Genera y descarga un PDF con todas las respuestas detalladas de cada miembro del grupo.", styles['Bullet_Sub_Manual'])),
        ListItemClass(Paragraph("<b>Diana de Afinidad:</b> Despliega un panel para generar la visualización de la Diana, que muestra la popularidad de los miembros en círculos concéntricos. Se explica en la sección 4.3.", styles['Bullet_Sub_Manual']))
    ]
    if ListFlowableClass and ListItemClass: story.append(ListFlowableClass(group_analysis_items, bulletType='bullet'))
    # --- Bloque 3: Guía de la Pantalla de Miembros y Cuestionario ---
    
    story.append(SpacerClass(1, 0.5*CM_UNIT))
    story.append(Paragraph("<b>3.3. Pantalla de Miembros</b>", styles['H3_Manual']))
    story.append(Paragraph("Muestra la lista de todos los miembros de un grupo. Permite añadir, modificar o eliminar miembros individualmente.", styles['Normal_Manual']))
    
    story.append(Paragraph("<u>Componentes y Botones:</u>", styles['H4_Manual']))
    member_screen_items = [
        ListItemClass(Paragraph("<b>Lista de Miembros:</b> Seleccione un miembro para ver sus detalles (apellido, nombre, iniciales, anotaciones) y activar los botones.", styles['Bullet_Manual'])),
        ListItemClass(Paragraph("<b>Nuevo Miembro:</b> Abre el formulario para añadir un nuevo participante al grupo, donde podrá introducir su nombre, apellido, sexo, fecha de nacimiento y anotaciones.", styles['Bullet_Manual'])),
        ListItemClass(Paragraph("<b>Modificar Miembro:</b> (Se habilita al seleccionar). Permite editar los datos del miembro seleccionado.", styles['Bullet_Manual'])),
        ListItemClass(Paragraph("<b>Eliminar Miembro:</b> (Se habilita al seleccionar). Borra al miembro seleccionado y sus respuestas del cuestionario.", styles['Bullet_Manual'])),
        ListItemClass(Paragraph("<b>Cuestionario:</b> (Se habilita al seleccionar). Abre el formulario de elecciones para el miembro seleccionado. Este es el paso clave para registrar los datos sociométricos.", styles['Bullet_Manual'])),
        ListItemClass(Paragraph("<b>Volver a Grupos:</b> Regresa a la pantalla de gestión de grupos.", styles['Bullet_Manual'])),
    ]
    if ListFlowableClass and ListItemClass: story.append(ListFlowableClass(member_screen_items, bulletType='bullet'))

    story.append(SpacerClass(1, 0.4*CM_UNIT))
    story.append(Paragraph("<b>3.4. Cuestionario y Gestión de Preguntas</b>", styles['H3_Manual']))
    story.append(Paragraph("Este formulario muestra todas las preguntas definidas para el grupo. Para cada pregunta, puede seleccionar a otros miembros de las listas desplegables. Una vez completado, haga clic en <b>'Guardar Respuestas'</b>.", styles['Normal_Manual']))
    
    story.append(Paragraph("<u>Botones del Cuestionario:</u>", styles['H4_Manual']))
    q_buttons_items = [
        ListItemClass(Paragraph("<b>Guardar Respuestas:</b> Guarda las elecciones hechas en el formulario.", styles['Bullet_Manual'])),
        ListItemClass(Paragraph("<b>Generar PDF Cuestionario:</b> Crea un PDF en blanco con las preguntas del grupo, útil para imprimir y aplicar en papel.", styles['Bullet_Manual'])),
        ListItemClass(Paragraph("<b>Salir sin Guardar:</b> Cierra el cuestionario y descarta cualquier cambio no guardado.", styles['Bullet_Manual'])),
        ListItemClass(Paragraph("<b>Gestionar Preguntas:</b> Abre una pantalla avanzada para configurar el cuestionario.", styles['Bullet_Manual']))
    ]
    if ListFlowableClass and ListItemClass: story.append(ListFlowableClass(q_buttons_items, bulletType='bullet'))

    story.append(Paragraph("<u>Pantalla de Gestión de Preguntas:</u>", styles['H4_Manual']))
    story.append(Paragraph("Aquí puede personalizar completamente el cuestionario para cada grupo. Puede añadir, modificar o eliminar preguntas, definiendo para cada una:", styles['Normal_Manual']))
    q_mgmt_items = [
        ListItemClass(Paragraph("<b>ID Único y Clave de Datos:</b> Identificadores internos para la pregunta.", styles['Bullet_Sub_Manual'])),
        ListItemClass(Paragraph("<b>Texto y Tipo:</b> El texto que verá el usuario y una categoría (ej. 'Juego', 'Tarea').", styles['Bullet_Sub_Manual'])),
        ListItemClass(Paragraph("<b>Polaridad:</b> Define si la pregunta es de aceptación (positiva) o de rechazo (negativa).", styles['Bullet_Sub_Manual'])),
        ListItemClass(Paragraph("<b>Orden y Nº de Selecciones:</b> Controla el orden de aparición y cuántas elecciones puede hacer un miembro por pregunta.", styles['Bullet_Sub_Manual'])),
    ]
    if ListFlowableClass and ListItemClass: story.append(ListFlowableClass(q_mgmt_items, bulletType='bullet'))
    # --- Bloque 4: Guía de Herramientas de Análisis ---

    story.append(PageBreakClass())
    story.append(Paragraph("4. Herramientas de Análisis", styles['H2_Manual']))
    story.append(Paragraph("Una vez que los datos han sido ingresados, el programa ofrece varias herramientas para su análisis visual y cuantitativo.", styles['Normal_Manual']))

    story.append(Paragraph("<b>4.1. El Sociograma Interactivo</b>", styles['H3_Manual']))
    story.append(Paragraph("Esta es la visualización principal, que muestra a los miembros como nodos y sus elecciones como flechas. Puede filtrar y colorear la red para destacar patrones. Los controles le permiten:", styles['Normal_Manual']))
    socio_features = [
        ListItemClass(Paragraph("<b>Relaciones a Incluir:</b> Marque las preguntas específicas que desea visualizar en el grafo.", styles['Bullet_Manual'])),
        ListItemClass(Paragraph("<b>Filtro por Sexo de Miembros:</b> Muestra solo nodos de un sexo específico (Masculino, Femenino) o todos.", styles['Bullet_Manual'])),
        ListItemClass(Paragraph("<b>Etiquetas de Nodos:</b> Cambia el texto dentro de cada nodo entre el nombre completo del miembro, sus iniciales o un identificador anónimo.", styles['Bullet_Manual'])),
        ListItemClass(Paragraph("<b>Filtro de Miembros Activos:</b> Si se marca, oculta a los miembros que no han realizado ninguna elección.", styles['Bullet_Manual'])),
        ListItemClass(Paragraph("<b>Opción Nominadores/Aislados:</b> Si está marcada, los nodos que no reciben ninguna elección (aislados) se colorean de un color especial. Si se desmarca, estos nodos se ocultan del grafo.", styles['Bullet_Manual'])),
        ListItemClass(Paragraph("<b>Coloreado Especial:</b> Puede activar checkboxes para resaltar con colores distintivos a los nodos que solo reciben elecciones o a aquellos que participan en relaciones recíprocas (elecciones mutuas).", styles['Bullet_Manual'])),
        ListItemClass(Paragraph("<b>Filtro de Conexión por Sexo:</b> Muestra solo las elecciones entre miembros del mismo sexo, de diferente sexo, o todas.", styles['Bullet_Manual'])),
        ListItemClass(Paragraph("<b>Foco en Participante:</b> Permite seleccionar un miembro de una lista desplegable para ver únicamente sus conexiones (las que hace, las que recibe, o ambas). Esto es muy útil para analizar la perspectiva de un individuo.", styles['Bullet_Manual'])),
        ListItemClass(Paragraph("<b>Resaltar Líderes:</b> Colorea automáticamente los N miembros más elegidos en las preguntas positivas.", styles['Bullet_Manual'])),
        ListItemClass(Paragraph("<b>Botones de Dibujo:</b> 'Redibujar' aplica un layout orgánico, mientras que 'Dibujar en Círculo' organiza los nodos de forma circular. 'Generar PDF' exporta la vista actual.", styles['Bullet_Manual'])),
    ]
    if ListFlowableClass and ListItemClass: story.append(ListFlowableClass(socio_features, bulletType='bullet'))
    
    story.append(SpacerClass(1, 0.4*CM_UNIT))
    story.append(Paragraph("<b>4.2. La Matriz Sociométrica</b>", styles['H3_Manual']))
    story.append(Paragraph("Es una tabla que resume numéricamente quién elige a quién. Las filas representan a los nominadores y las columnas a los elegidos. Permite ver rápidamente los totales de elecciones hechas y recibidas.", styles['Normal_Manual']))
    story.append(Paragraph("<u>Controles de la Matriz:</u>", styles['H4_Manual']))
    matrix_features = [
         ListItemClass(Paragraph("<b>Selección de Preguntas:</b> Utilice los checkboxes para seleccionar las preguntas que desea incluir en el conteo de la matriz.", styles['Bullet_Manual'])),
         ListItemClass(Paragraph("<b>Botones de Selección Rápida:</b> Los botones 'Todas', 'Ninguna', 'Positivas' y 'Negativas' le permiten marcar o desmarcar rápidamente grupos de preguntas según su polaridad.", styles['Bullet_Manual'])),
         ListItemClass(Paragraph("<b>Actualizar Matriz:</b> Este botón regenera la tabla con las preguntas que haya seleccionado.", styles['Bullet_Manual'])),
         ListItemClass(Paragraph("<b>Generar PDF:</b> Exporta la tabla actualmente visible a un archivo PDF.", styles['Bullet_Manual'])),
    ]
    if ListFlowableClass and ListItemClass: story.append(ListFlowableClass(matrix_features, bulletType='bullet'))
    
    story.append(SpacerClass(1, 0.4*CM_UNIT))
    story.append(Paragraph("<b>4.3. La Diana de Afinidad</b>", styles['H3_Manual']))
    story.append(Paragraph("Esta visualización coloca a los miembros en círculos concéntricos. Los miembros con más elecciones recibidas (los 'populares') se sitúan en el centro, mientras que los menos elegidos quedan en la periferia. Permite identificar rápidamente los distintos niveles de integración social.", styles['Normal_Manual']))
    story.append(Paragraph("<u>Controles de la Diana:</u>", styles['H4_Manual']))
    diana_features = [
         ListItemClass(Paragraph("<b>Selección de Preguntas:</b> Al igual que en la matriz, puede seleccionar las preguntas (positivas, negativas o una mezcla) que se usarán para calcular el puntaje de afinidad de cada miembro.", styles['Bullet_Manual'])),
         ListItemClass(Paragraph("<b>Mostrar Líneas de Elección:</b> Este checkbox le permite mostrar u ocultar las flechas de elección en el gráfico para una vista más limpia o más detallada.", styles['Bullet_Manual'])),
         ListItemClass(Paragraph("<b>Generar/Actualizar Diana:</b> Dibuja o redibuja la diana con las opciones seleccionadas.", styles['Bullet_Manual'])),
         ListItemClass(Paragraph("<b>Descargar Diana (PNG):</b> Una vez generada, este botón se habilita para que pueda descargar la imagen de la diana en formato PNG.", styles['Bullet_Manual'])),
    ]
    if ListFlowableClass and ListItemClass: story.append(ListFlowableClass(diana_features, bulletType='bullet'))
    # --- Bloque 5: Guía de Importación/Exportación CSV y Cierre de la Función ---

    story.append(PageBreakClass())
    
    story.append(Paragraph("5. Importación y Exportación de Datos (CSV)", styles['H2_Manual']))
    story.append(Paragraph("Esta funcionalidad, accesible desde la pantalla de Instituciones, es crucial para la carga y descarga masiva de datos, especialmente cuando se utilizan formularios externos como Google Forms.", styles['Normal_Manual']))
    
    story.append(Paragraph("<b>5.1. Configuración de un Formulario de Google</b>", styles['H3_Manual']))
    story.append(Paragraph("Para que el archivo CSV exportado desde Google Forms sea compatible, configure su formulario con los siguientes tipos de pregunta:", styles['Normal_Manual']))
    gforms_items = [
        ListItemClass(Paragraph("<b>Institucion:</b> 'Lista desplegable'.", styles['Bullet_Manual'])),
        ListItemClass(Paragraph("<b>Grupo:</b> 'Lista desplegable'.", styles['Bullet_Manual'])),
        ListItemClass(Paragraph("<b>Nombre y Apellido:</b> 'Lista desplegable'.", styles['Bullet_Manual'])),
        ListItemClass(Paragraph("<b>Sexo:</b> 'Opción múltiple' (con opciones 'Masculino' y 'Femenino').", styles['Bullet_Manual'])),
        ListItemClass(Paragraph("<b>Fecha De Nacimiento:</b> 'Fecha'.", styles['Bullet_Manual'])),
        ListItemClass(Paragraph("<b>Preguntas de Elección (¡MUY IMPORTANTE!):</b>", styles['Bullet_Manual']))]
    if ListFlowableClass and ListItemClass: story.append(ListFlowableClass(gforms_items, bulletType='bullet'))
    story.append(Paragraph("Use el tipo de pregunta <b>'Cuadrícula de opción múltiple'</b>:", styles['Normal_Manual']))
    grid_items = [
        ListItemClass(Paragraph("<b>Pregunta:</b> Coloca una pregunta (ej. '¿Con quién te gustaría jugar?').", styles['Bullet_Manual'])),
        ListItemClass(Paragraph("<b>Filas:</b> Use los identificadores como 'Opcion 1', 'Opcion 2', etc.", styles['Bullet_Manual'])),
        ListItemClass(Paragraph("<b>Columnas:</b> Use los mismos nombres de sus participantes aqui.", styles['Bullet_Manual']))]
    if ListFlowableClass and ListItemClass: story.append(ListFlowableClass(grid_items, bulletType='bullet', start='-', leftIndent=2.5*CM_UNIT))
    
    story.append(SpacerClass(1, 0.5*CM_UNIT))
    story.append(Paragraph("<b>5.2. Estructura del Archivo CSV</b>", styles['H3_Manual']))
    story.append(Paragraph("Si crea el CSV manualmente, debe seguir esta estructura exacta. El orden de las primeras columnas es fundamental.", styles['Normal_Manual']))
    
    id_cols_data = [
        ["<b>Columna CSV</b>", "<b>Descripción</b>"],
        ["Marca temporal", "Generada por G-Forms. Opcional."],
        ["Dirección de correo electrónico", "Opcional."],
        ["Institucion", "<b>Obligatorio</b>. Nombre exacto de la institución."],
        ["Grupo", "<b>Obligatorio</b>. Nombre exacto del grupo."],
        ["Nombre y Apellido", "<b>Obligatorio</b>. Nombre del miembro que responde."],
        ["Sexo", "<b>Obligatorio</b>. Valores: 'Masculino', 'Femenino'."],
        ["Fecha De Nacimiento", "<b>Obligatorio</b>. Formato: DD/MM/YYYY."],
        ["Pregunta [Opcion N]", "<b>Obligatorio para respuestas</b>. El valor debe ser el nombre del miembro elegido."]]
    
    id_table_data_flowable = [[Paragraph(cell, styles['Table_Cell_Manual']) for cell in row] for row in id_cols_data]
    id_table_data_flowable[0] = [Paragraph(cell, styles['Table_Header_Manual']) for cell in id_cols_data[0]]
    
    id_table = TableClass(id_table_data_flowable, colWidths=[6*CM_UNIT, 10*CM_UNIT])
    id_table.setStyle(TableStyleClass([('BACKGROUND',(0,0),(1,0), color_lightgrey),('GRID',(0,0),(-1,-1),0.5, color_grey),('VALIGN',(0,0),(-1,-1),'TOP')]))
    story.append(KeepInFrameClass(doc.width, 12*CM_UNIT, [id_table]))

    story.append(SpacerClass(1, 0.5*CM_UNIT))
    story.append(Paragraph("<b>5.3. Panel de Importación y Exportación en la App</b>", styles['H3_Manual']))
    story.append(Paragraph("<u>Sección de Importación:</u>", styles['H4_Manual']))
    import_panel_items = [
        ListItemClass(Paragraph("<b>Nombre Archivo:</b> Escriba el nombre exacto del archivo CSV que ha subido a la carpeta `/content/` de Colab.", styles['Bullet_Manual'])),
        ListItemClass(Paragraph("<b>Opciones de Importación (Checkboxes):</b> Seleccione qué partes de su CSV desea procesar. Por ejemplo, puede importar solo los miembros y sus datos demográficos sin cargar las respuestas, o viceversa. Esto le da un control total sobre la actualización de datos.", styles['Bullet_Manual'])),
        ListItemClass(Paragraph("<b>Opciones Adicionales:</b> Controle comportamientos específicos, como si se deben crear miembros que son mencionados en las respuestas pero no están en la lista principal.", styles['Bullet_Manual'])),
    ]
    if ListFlowableClass and ListItemClass: story.append(ListFlowableClass(import_panel_items, bulletType='bullet'))
    
    story.append(Paragraph("<u>Sección de Exportación:</u>", styles['H4_Manual']))
    story.append(Paragraph("Esta sección le permite descargar los datos de su proyecto en un formato CSV compatible. Siga los pasos numerados:", styles['Normal_Manual']))
    export_panel_items = [
        ListItemClass(Paragraph("<b>1. Cargar Instituciones:</b> Muestra una lista de todas sus instituciones para que las seleccione.", styles['Bullet_Manual'])),
        ListItemClass(Paragraph("<b>2. Cargar Grupos:</b> Muestra los grupos pertenecientes a las instituciones que marcó en el paso anterior.", styles['Bullet_Manual'])),
        ListItemClass(Paragraph("<b>3. Generar CSV:</b> Crea y ofrece para descargar un archivo CSV que contiene todos los datos (miembros, respuestas, etc.) de los grupos que haya seleccionado.", styles['Bullet_Manual'])),
    ]
    if ListFlowableClass and ListItemClass: story.append(ListFlowableClass(export_panel_items, bulletType='bullet'))

    # --- CIERRE DE LA FUNCIÓN ---
    try:
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        b64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
        html_link = f'<p style="text-align:center; margin-top:10px;"><a download="{filename}" href="data:application/pdf;base64,{b64_pdf}" target="_blank" style="padding:8px 15px; background-color:#5cb85c; color:white;text-decoration:none;border-radius:5px;font-weight:bold;">Descargar Manual de Usuario (PDF)</a></p>'
        if registro_output:
            with registro_output: clear_output(wait=True); print(f"Manual de Usuario '{filename}' listo."); display(HTML(html_link))
        else: display(HTML(html_link))
    except Exception as e:
        err_msg_build_final = f"ERROR generando manual de usuario: {e}\n{traceback.format_exc()}"
        print(err_msg_build_final)
        if registro_output:
            with registro_output:
                print(err_msg_build_final)
        if 'buffer' in locals() and not buffer.closed: buffer.close()                
        
# --- FIN BLOQUE 3 ---
# --- BLOQUE 4: PDF DEL SOCIOGRAMA CON LEYENDA (DESDE IMAGEN PRE-RENDERIZADA) ---

# Funciones helper que faltaban en la respuesta anterior
def _draw_page_number_general(canvas, doc):
    if not REPORTLAB_AVAILABLE: return
    canvas.saveState()
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(color_grey if color_grey else ColorClass(0.5,0.5,0.5))
    margin_adj = 1.5 * CM_UNIT
    doc_width = getattr(doc, 'width', A4_SIZE[0] - 2 * margin_adj)
    canvas.drawRightString(doc_width + 1*CM_UNIT, 1 * CM_UNIT, f"Página {doc.page}")
    canvas.restoreState()

def _create_pdf_styles_general():
    styles = getSampleStyleSheet_actual()
    if not REPORTLAB_AVAILABLE: return styles
    styles.add(ParagraphStyleClass(name='H1_Custom', parent=styles['h1'], alignment=ALIGN_CENTER, fontSize=18, spaceBefore=12, spaceAfter=8, textColor=HexColorFunc("#2c3e50")))
    styles.add(ParagraphStyleClass(name='H2_Custom', parent=styles['h2'], fontSize=14, spaceBefore=10, spaceAfter=5, alignment=ALIGN_LEFT, textColor=HexColorFunc("#34495e")))
    styles.add(ParagraphStyleClass(name='Member_Name_Header', parent=styles['h3'], fontSize=12, spaceBefore=10, spaceAfter=5, alignment=ALIGN_LEFT, textColor=HexColorFunc("#2980b9")))
    styles.add(ParagraphStyleClass(name='Questionnaire_Header', parent=styles['Normal'], alignment=ALIGN_LEFT, fontSize=9, textColor=HexColorFunc("#7f8c8d")))
    styles.add(ParagraphStyleClass(name='Question_Text', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, spaceBefore=6))
    styles.add(ParagraphStyleClass(name='Response_Line', parent=styles['Normal'], leftIndent=1*CM_UNIT, spaceBefore=2))
    styles.add(ParagraphStyleClass(name='Response_Label', parent=styles['Normal'], fontName='Helvetica-Oblique', textColor=color_grey, leftIndent=1*CM_UNIT))
    styles.add(ParagraphStyleClass(name='Small_Info', parent=styles['Normal'], fontSize=8, textColor=color_grey))
    styles.add(ParagraphStyleClass(name='Normal_Custom', parent=styles['Normal'], fontSize=10, leading=14, spaceBefore=3, spaceAfter=3, alignment=ALIGN_JUSTIFY))
    styles.add(ParagraphStyleClass(name='Table_Header', parent=styles['Normal_Custom'], fontName='Helvetica-Bold', fontSize=7, alignment=ALIGN_CENTER, leading=9))
    styles.add(ParagraphStyleClass(name='Table_Cell', parent=styles['Normal_Custom'], fontSize=8, alignment=ALIGN_CENTER, leading=10))
    styles.add(ParagraphStyleClass(name='Table_Cell_Left', parent=styles['Normal_Custom'], fontSize=8, alignment=ALIGN_LEFT, leading=10))
    styles.add(ParagraphStyleClass(name='Legend_MainTitle', parent=styles['h2'], fontSize=11, spaceBefore=6, spaceAfter=4, textColor=HexColorFunc("#333")))
    styles.add(ParagraphStyleClass(name='Legend_Subtitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, spaceBefore=4, spaceAfter=2))
    styles.add(ParagraphStyleClass(name='Legend_Item_Color_Symbol', parent=styles['Normal'], fontSize=12))
    styles.add(ParagraphStyleClass(name='Legend_Item_Width_Symbol', parent=styles['Normal'], fontSize=14, alignment=ALIGN_CENTER))
    styles.add(ParagraphStyleClass(name='Legend_Item_Text', parent=styles['Normal'], fontSize=8, alignment=ALIGN_LEFT))
    return styles

def generate_sociogram_with_legend_pdf(image_bytes, legend_info,
                                         institution_name, group_name,
                                         registro_output,
                                         style_reciprocal_links_active=False,
                                         force_error_message=None):
    if not REPORTLAB_AVAILABLE or not BaseDocTemplateClass:
        err_msg_rl_soc_gen_pdf = "ERROR (PDF Sociograma): ReportLab no está instalado o componentes no disponibles.";
        if registro_output: 
          with registro_output: print(err_msg_rl_soc_gen_pdf); return
        else:
          print(err_msg_rl_soc_gen_pdf); return

    if (not image_bytes or not isinstance(image_bytes, bytes)) and not force_error_message:
        placeholder_message_img = "Imagen del sociograma no disponible."
        if MATPLOTLIB_AVAILABLE and plt:
            try:
                fig_ph_soc_img, ax_ph_soc_img = plt.subplots(figsize=(6,4))
                ax_ph_soc_img.text(0.5, 0.5, placeholder_message_img, ha='center', va='center', fontsize=10, color='grey', wrap=True)
                ax_ph_soc_img.set_axis_off()
                img_buffer_ph_soc_img = io.BytesIO()
                plt.savefig(img_buffer_ph_soc_img, format='png', dpi=75); img_buffer_ph_soc_img.seek(0)
                image_bytes = img_buffer_ph_soc_img.getvalue();
                plt.close(fig_ph_soc_img)
            except Exception as e_placeholder_soc_img_create:
                if registro_output:
                    with registro_output: print(f"  ERROR (PDF Sociograma): No se pudo crear imagen de placeholder: {e_placeholder_soc_img_create}")
                if not force_error_message:
                    return
        elif not force_error_message:
             if registro_output:
                with registro_output: print("ADVERTENCIA (PDF Sociograma): Matplotlib no disponible para crear placeholder. PDF no se generará si no se fuerza mensaje.")
             return

    clean_institution_name_file = re.sub(r'[^\w\s-]', '', institution_name).replace(' ', '_')
    clean_group_name_file = re.sub(r'[^\w\s-]', '', group_name).replace(' ', '_')
    timestamp_file_name = datetime.datetime.now().strftime('%Y%m%d%H%M')
    filename_pdf = f"Sociograma_{clean_institution_name_file}_{clean_group_name_file}_{timestamp_file_name}.pdf"

    buffer_for_pdf = io.BytesIO()
    doc_width_for_pdf, doc_height_for_pdf = LANDSCAPE_FUNC(A4_SIZE)
    doc_for_pdf = BaseDocTemplateClass(buffer_for_pdf, pagesize=(doc_width_for_pdf, doc_height_for_pdf),
                                       leftMargin=1.5*CM_UNIT, rightMargin=1.5*CM_UNIT,
                                       topMargin=1.5*CM_UNIT, bottomMargin=2*CM_UNIT)

    frame_main_for_pdf = FrameClass(doc_for_pdf.leftMargin, doc_for_pdf.bottomMargin, doc_for_pdf.width, doc_for_pdf.height, id='main_frame_sociogram_pdf_v4')
    page_template_for_pdf = PageTemplateClass(id='sociogram_page_pdf_v4', frames=[frame_main_for_pdf], onPage=_draw_page_number_general)
    doc_for_pdf.addPageTemplates([page_template_for_pdf])
    styles_for_pdf = _create_pdf_styles_general()
    story_for_pdf = []

    story_for_pdf.append(Paragraph(f"Sociograma: {institution_name} - {group_name}", styles_for_pdf.get('H1_Custom', styles_for_pdf['h1'])))
    story_for_pdf.append(SpacerClass(1, 0.3*CM_UNIT))

    try:
        if force_error_message and not image_bytes:
             story_for_pdf.append(Paragraph(f"<font color='red'>Error: {force_error_message}</font>", styles_for_pdf.get('Normal_Custom', styles_for_pdf['Normal'])))
        elif image_bytes:
            img_obj_for_pdf = ImageClass(io.BytesIO(image_bytes))
            img_avail_width_for_pdf = frame_main_for_pdf.width
            img_avail_height_for_pdf = frame_main_for_pdf.height * 0.60
            
            aspect_img_pdf = img_obj_for_pdf.drawHeight / float(img_obj_for_pdf.drawWidth) if img_obj_for_pdf.drawWidth > 0 else 1
            new_w_img_pdf = img_avail_width_for_pdf
            new_h_img_pdf = new_w_img_pdf * aspect_img_pdf
            if new_h_img_pdf > img_avail_height_for_pdf:
                new_h_img_pdf = img_avail_height_for_pdf
                new_w_img_pdf = new_h_img_pdf / aspect_img_pdf if aspect_img_pdf > 0 else img_avail_width_for_pdf
            img_obj_for_pdf.drawWidth, img_obj_for_pdf.drawHeight = new_w_img_pdf, new_h_img_pdf
            
            story_for_pdf.append(KeepInFrameClass(frame_main_for_pdf.width, img_avail_height_for_pdf + 0.5*CM_UNIT, [img_obj_for_pdf], hAlign='CENTER'))
            story_for_pdf.append(SpacerClass(1, 0.4*CM_UNIT))
        else:
            story_for_pdf.append(Paragraph("Error: Imagen del sociograma no disponible para el PDF.", styles_for_pdf.get('Normal_Custom', styles_for_pdf['Normal'])))
    except Exception as e_img_add_to_pdf:
        if registro_output: 
          with registro_output: print(f"  ERROR (PDF Sociograma): No se pudo procesar/añadir imagen al PDF: {e_img_add_to_pdf}")
        story_for_pdf.append(Paragraph("Error: No se pudo mostrar la imagen del sociograma en el PDF.", styles_for_pdf.get('Normal_Custom', styles_for_pdf['Normal'])))

    legend_elements_story_list_pdf = []
    if legend_info and isinstance(legend_info, dict):
        legend_elements_story_list_pdf.append(Paragraph("Leyenda:", styles_for_pdf.get('Legend_MainTitle', styles_for_pdf['h2'])))
        
        node_colors_legend = legend_info.get("node_colors", {})
        if node_colors_legend and PILLOW_AVAILABLE:
            legend_elements_story_list_pdf.append(Paragraph("Color de Nodo:", styles_for_pdf.get('Legend_Subtitle', styles_for_pdf['Normal_Custom'])))
            node_color_items = []
            col_widths_node_leg = [1.5*CM_UNIT, frame_main_for_pdf.width - 1.5*CM_UNIT - 2*CM_UNIT]
            for color_h, desc_n in sorted(node_colors_legend.items(), key=lambda item: item[1]):
                img_buf_rect_n = _create_legend_line_image_pil(color_h, "solid", "none", "none", img_width_px=25, img_height_px=12, line_thickness=10)
                rect_img_n = ImageClass(img_buf_rect_n, width=0.8*CM_UNIT, height=0.4*CM_UNIT) if img_buf_rect_n else Paragraph(f"<font color='{color_h}'>■</font>", styles_for_pdf['Legend_Item_Color_Symbol'])
                node_color_items.append([rect_img_n, Paragraph(desc_n, styles_for_pdf['Legend_Item_Text'])])
            if node_color_items:
                node_table_leg = TableClass(node_color_items, colWidths=col_widths_node_leg)
                node_table_leg.setStyle(TableStyleClass([('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),1*MM_UNIT)]))
                legend_elements_story_list_pdf.append(node_table_leg)
            legend_elements_story_list_pdf.append(SpacerClass(1, 0.3*CM_UNIT))

        edge_styles_legend = legend_info.get("edge_styles", {})
        if edge_styles_legend and PILLOW_AVAILABLE:
            legend_elements_story_list_pdf.append(Paragraph("Color/Estilo de Flecha:", styles_for_pdf.get('Legend_Subtitle', styles_for_pdf['Normal_Custom'])))
            edge_style_items = []
            col_widths_edge_leg = [2.0*CM_UNIT, frame_main_for_pdf.width - 2.0*CM_UNIT - 2*CM_UNIT]
            sorted_edge_styles_leg = sorted(edge_styles_legend.items(), key=lambda item: ("A_" if item[1].get('is_focus') else "B_") + item[0] )
            for desc_e_leg, style_attrs_e_leg in sorted_edge_styles_leg:
                color_e_leg = style_attrs_e_leg.get('color', '#000000'); is_focus_e_leg = style_attrs_e_leg.get('is_focus', False)
                can_be_recip_e_leg = style_attrs_e_leg.get('can_be_reciprocal_styled', False)
                line_style1_e_leg = style_attrs_e_leg.get('base_line_style', 'solid')
                arrow_shape1_e_leg = style_attrs_e_leg.get('base_arrow_shape', 'triangle')
                source_arrow_shape1_e_leg = style_attrs_e_leg.get('source_arrow_shape', 'none')
                img_buf1_e_leg = _create_legend_line_image_pil(color_e_leg, line_style1_e_leg, arrow_shape1_e_leg, source_arrow_shape1_e_leg)
                image1_e_leg = ImageClass(img_buf1_e_leg, width=1.8*CM_UNIT, height=0.6*CM_UNIT) if img_buf1_e_leg else Paragraph(" ", styles_for_pdf['Normal_Custom'])
                suffix1_e_leg = " (Doble Foco)" if source_arrow_shape1_e_leg != 'none' and source_arrow_shape1_e_leg == arrow_shape1_e_leg and is_focus_e_leg else ""
                edge_style_items.append([image1_e_leg, Paragraph(f"{desc_e_leg}{suffix1_e_leg}", styles_for_pdf['Legend_Item_Text'])])
                if style_reciprocal_links_active and can_be_recip_e_leg and not is_focus_e_leg:
                    img_buf2_e_leg = _create_legend_line_image_pil(color_e_leg, 'dashed', style_attrs_e_leg.get('base_arrow_shape', 'triangle'), style_attrs_e_leg.get('base_arrow_shape', 'triangle'))
                    img2_e_leg = ImageClass(img_buf2_e_leg, width=1.8*CM_UNIT, height=0.6*CM_UNIT) if img_buf2_e_leg else Paragraph(" ", styles_for_pdf['Normal_Custom'])
                    edge_style_items.append([img2_e_leg, Paragraph(f"<font name='Helvetica-Oblique'>{desc_e_leg} (Doble Recíproca)</font>", styles_for_pdf['Legend_Item_Text'])])
            if edge_style_items:
                edge_table_leg = TableClass(edge_style_items, colWidths=col_widths_edge_leg)
                edge_table_leg.setStyle(TableStyleClass([('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('LEFTPADDING', (0,0),(-1,-1),0), ('BOTTOMPADDING', (0,0),(-1,-1),2*MM_UNIT)]))
                legend_elements_story_list_pdf.append(edge_table_leg)
            legend_elements_story_list_pdf.append(SpacerClass(1,0.3*CM_UNIT))

        width_styles_legend = legend_info.get("widths", {})
        if width_styles_legend and PILLOW_AVAILABLE:
            legend_elements_story_list_pdf.append(Paragraph("Grosor de Flecha (Orden de Elección):", styles_for_pdf.get('Legend_Subtitle', styles_for_pdf['Normal_Custom'])))
            width_items = []
            col_widths_width_leg = [1.5*CM_UNIT, frame_main_for_pdf.width - 1.5*CM_UNIT - 2*CM_UNIT]
            for desc_w_leg, width_px_str_w_leg in sorted(width_styles_legend.items(), key=lambda item: int(item[0].split(" ")[1]) if "Elección" in item[0] and item[0].split(" ")[1].isdigit() else 99 ):
                try: line_thick_w_leg = float(width_px_str_w_leg.replace('px',''))
                except: line_thick_w_leg = 1.0
                img_buf_w_leg = _create_legend_line_image_pil("#000000", "solid", "none", "none", line_thickness=max(1,int(line_thick_w_leg)))
                symbol_w_leg = ImageClass(img_buf_w_leg, width=1.3*CM_UNIT, height=0.5*CM_UNIT) if img_buf_w_leg else Paragraph("━", styles_for_pdf['Legend_Item_Width_Symbol'])
                width_items.append([symbol_w_leg, Paragraph(f"{desc_w_leg} (aprox. {width_px_str_w_leg})", styles_for_pdf['Legend_Item_Text'])])
            if width_items:
                width_table_leg = TableClass(width_items, colWidths=col_widths_width_leg)
                width_table_leg.setStyle(TableStyleClass([('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('LEFTPADDING', (0,0),(-1,-1),0), ('BOTTOMPADDING', (0,0),(-1,-1),1*MM_UNIT)]))
                legend_elements_story_list_pdf.append(width_table_leg)
        
        if legend_elements_story_list_pdf:
            story_for_pdf.append(KeepInFrameClass(frame_main_for_pdf.width, frame_main_for_pdf.height * 0.35, legend_elements_story_list_pdf, hAlign='LEFT'))

    try:
        doc_for_pdf.build(story_for_pdf)
        pdf_bytes_output_gen = buffer_for_pdf.getvalue(); buffer_for_pdf.close()
        b64_pdf_output_gen = base64.b64encode(pdf_bytes_output_gen).decode('utf-8')
        html_link_output_gen = f'<p style="text-align:center; margin-top:10px;"><a download="{filename_pdf}" href="data:application/pdf;base64,{b64_pdf_output_gen}" target="_blank" style="padding:8px 15px; background-color:#007bff; color:white; text-decoration:none; border-radius:5px; font-weight:bold;">Descargar PDF Sociograma: {filename_pdf}</a></p>'
        if registro_output:
            with registro_output: 
                # print(f"ÉXITO: PDF sociograma '{filename_pdf}' listo para descargar."); 
                display(HTML(html_link_output_gen))
        else: display(HTML(html_link_output_gen))
    except Exception as e_build_soc_pdf_gen:
        err_msg_build_soc_pdf_gen_final = f"ERROR construyendo PDF sociograma: {e_build_soc_pdf_gen}\n{traceback.format_exc()}"
        if registro_output: 
          with registro_output: print(err_msg_build_soc_pdf_gen_final)
        else:
          print(err_msg_build_soc_pdf_gen_final)
        if buffer_for_pdf and not buffer_for_pdf.closed: buffer_for_pdf.close()
# --- FIN BLOQUE 4 ---
# --- BLOQUE 5: PDF DESDE JSON DE CYTOSCAPE (RENDERIZANDO CON MATPLOTLIB) ---
def generate_pdf_from_cytoscape_json(graph_json, legend_info,
                                       institution_name, group_name,
                                       registro_output, layout_hint='cose',
                                       style_reciprocal_links_active_param=False,
                                       force_error_message_on_image_fail=None):
    
    # if registro_output and isinstance(registro_output, widgets.Output):
        # with registro_output:
            # print(f"  DEBUG_PDF_JSON_MAIN_V2: Entrando a generate_pdf_from_cytoscape_json para {institution_name}/{group_name}.")

    if not REPORTLAB_AVAILABLE:
        err_msg_rl_json_main_v2 = "ERROR (PDF desde JSON): ReportLab no está instalado.";
        if registro_output: 
          with registro_output: print(err_msg_rl_json_main_v2); return
        else:
          print(err_msg_rl_json_main_v2)
          return

    valid_graph_json_input_main_v2 = False
    if isinstance(graph_json, dict) and 'elements' in graph_json:
        elements_data_json_main_v2 = graph_json.get('elements')
        if isinstance(elements_data_json_main_v2, dict) and \
           (elements_data_json_main_v2.get('nodes') is not None or elements_data_json_main_v2.get('edges') is not None) and \
           (isinstance(elements_data_json_main_v2.get('nodes'), list) or isinstance(elements_data_json_main_v2.get('edges'), list)):
            valid_graph_json_input_main_v2 = True

    if not valid_graph_json_input_main_v2:
        if registro_output:
            with registro_output:
                print(f"ERROR_PDF_JSON_VALIDATION_MAIN_V2: Datos JSON del grafo ('graph_json') no válidos o estructura incorrecta.")
        generate_sociogram_with_legend_pdf(None, legend_info, institution_name, group_name, registro_output,
                                           style_reciprocal_links_active=style_reciprocal_links_active_param,
                                           force_error_message="Datos del grafo (JSON) no válidos para generar imagen.")
        return

    image_bytes_for_pdf_final_json_v2 = None
    
    if not MATPLOTLIB_AVAILABLE or plt is None or not nx:
        if registro_output:
            with registro_output: print("ERROR (PDF desde JSON - Matplotlib/NetworkX): Matplotlib o NetworkX no instalados. No se puede generar imagen desde JSON.")
        current_force_error_msg = force_error_message_on_image_fail if force_error_message_on_image_fail else "Librerías de graficación (Matplotlib/NetworkX) no disponibles."
        image_bytes_for_pdf_final_json_v2 = None
        force_error_message_on_image_fail = current_force_error_msg
    else:
        try:
            # if registro_output:
                # with registro_output: print("  INFO (PDF Gen Matplotlib JSON v2): Intentando generar imagen desde JSON con Matplotlib/NetworkX...")

            G_from_json_render_final_v2 = nx.cytoscape_graph(graph_json)

            if not G_from_json_render_final_v2.nodes():
                # if registro_output: 
                  # with registro_output: print("  INFO (PDF Gen Matplotlib JSON v2): Grafo JSON sin nodos. Creando placeholder 'Sin Nodos'.")
                fig_ph_json_empty_v2, ax_ph_json_empty_v2 = plt.subplots(figsize=(5,3))
                ax_ph_json_empty_v2.text(0.5, 0.5, "Grafo sin nodos para mostrar.", ha='center', va='center', fontsize=10, color='grey', wrap=True)
                ax_ph_json_empty_v2.set_axis_off(); img_buffer_ph_json_empty_v2 = io.BytesIO()
                plt.savefig(img_buffer_ph_json_empty_v2, format='png', dpi=90); img_buffer_ph_json_empty_v2.seek(0)
                image_bytes_for_pdf_final_json_v2 = img_buffer_ph_json_empty_v2.getvalue(); plt.close(fig_ph_json_empty_v2)
            else:
                node_list_mpl_json_render_v2 = list(G_from_json_render_final_v2.nodes())
                is_multigraph_json_render_v2 = G_from_json_render_final_v2.is_multigraph()
                edge_list_data_mpl_json_render_v2 = list(G_from_json_render_final_v2.edges(data=True, keys=is_multigraph_json_render_v2))
                edge_data_dicts_mpl_json_render_v2 = [data_dict for u,v,*key_and_data_dict_render_v2 in edge_list_data_mpl_json_render_v2 for data_dict in (key_and_data_dict_render_v2[-1:],) if isinstance(data_dict, dict)]

                node_colors_mpl_str_json_render_v2 = [G_from_json_render_final_v2.nodes[n].get('node_color', 'lightgrey') for n in node_list_mpl_json_render_v2]
                labels_mpl_json_render_v2 = {n: G_from_json_render_final_v2.nodes[n].get('label_to_display', str(n)[:3].upper()) for n in node_list_mpl_json_render_v2}
                edge_colors_mpl_str_json_render_v2 = [d.get('edge_color', 'grey') for d in edge_data_dicts_mpl_json_render_v2]
                
                def robust_convert_color_for_mpl_json_local_v2(color_input):
                    if not isinstance(color_input, str): color_input = 'grey'
                    if color_input.startswith('#') and (len(color_input) == 7 or len(color_input) == 9) :
                        try: return HexColorFunc(color_input).rgb() if len(color_input) == 7 else HexColorFunc(color_input[:7]).rgb()
                        except: return (0.5, 0.5, 0.5)
                    if color_input == 'lightgrey': return (0.83, 0.83, 0.83)
                    try: return toColorFunc(color_input).rgb()
                    except: return (0.5,0.5,0.5)

                node_colors_mpl_render_final_v2 = [robust_convert_color_for_mpl_json_local_v2(c) for c in node_colors_mpl_str_json_render_v2]
                edge_colors_mpl_render_final_v2 = [robust_convert_color_for_mpl_json_local_v2(c) for c in edge_colors_mpl_str_json_render_v2]
                edge_opacities_mpl_render_final_v2 = [float(d.get('edge_opacity', 1.0)) for d in edge_data_dicts_mpl_json_render_v2]
                edge_widths_mpl_str_render_final_v2 = [str(d.get('edge_width_attr', '1.0px')).replace('px','') for d in edge_data_dicts_mpl_json_render_v2]
                edge_widths_mpl_render_final_v2 = [float(w_str) if w_str else 1.0 for w_str in edge_widths_mpl_str_render_final_v2]
                edge_styles_mpl_internal_render_final_v2 = [d.get('edge_line_style', 'solid') for d in edge_data_dicts_mpl_json_render_v2]
                linestyle_map_render_final_v2 = {'solid': '-', 'dotted': ':', 'dashed': '--'}
                edge_styles_mpl_render_final_v2 = [linestyle_map_render_final_v2.get(s, '-') for s in edge_styles_mpl_internal_render_final_v2]
                node_shapes_map_mpl_render_final_v2 = {'Masculino': 'o', 'Femenino': '^', 'Desconocido': 's', 'Otro': 's', 'ellipse':'o', 'triangle':'^', 'square':'s'}
                node_shapes_list_mpl_render_final_v2 = [node_shapes_map_mpl_render_final_v2.get(G_from_json_render_final_v2.nodes[n].get('sexo_attr', G_from_json_render_final_v2.nodes[n].get('gender','Desconocido')), 's') for n in node_list_mpl_json_render_v2]
                
                positions_mpl_render_final_v2 = {}
                positions_found_in_json_render_ok_v2 = True
                if graph_json.get('elements', {}).get('nodes'):
                    for node_el_data_render_final_v2 in graph_json.get('elements', {}).get('nodes', []):
                        node_id_render_final_v2 = node_el_data_render_final_v2.get('data', {}).get('id')
                        pos_dict_render_final_v2 = node_el_data_render_final_v2.get('position', node_el_data_render_final_v2.get('data', {}).get('position'))
                        if node_id_render_final_v2 and pos_dict_render_final_v2 and isinstance(pos_dict_render_final_v2, dict) and 'x' in pos_dict_render_final_v2 and 'y' in pos_dict_render_final_v2:
                            try: positions_mpl_render_final_v2[node_id_render_final_v2] = (float(pos_dict_render_final_v2['x']), -float(pos_dict_render_final_v2['y']))
                            except (ValueError, TypeError): positions_found_in_json_render_ok_v2 = False; break
                        else: positions_found_in_json_render_ok_v2 = False; break
                else: positions_found_in_json_render_ok_v2 = False
                if not positions_found_in_json_render_ok_v2 or not positions_mpl_render_final_v2 or len(positions_mpl_render_final_v2) != G_from_json_render_final_v2.number_of_nodes():
                    # if registro_output: 
                      # with registro_output: print(f"  INFO (PDF Gen Matplotlib JSON v2): Posiciones no encontradas/completas. Usando layout '{layout_hint}'.")
                    node_count_mpl_render_final_v2 = G_from_json_render_final_v2.number_of_nodes()
                    if layout_hint == 'circle': positions_mpl_render_final_v2 = nx.circular_layout(G_from_json_render_final_v2)
                    elif layout_hint == 'kamada_kawai' and node_count_mpl_render_final_v2 > 0: positions_mpl_render_final_v2 = nx.kamada_kawai_layout(G_from_json_render_final_v2)
                    else: positions_mpl_render_final_v2 = nx.spring_layout(G_from_json_render_final_v2, seed=42, k=(0.7/math.sqrt(node_count_mpl_render_final_v2) if node_count_mpl_render_final_v2>1 else 0.5), iterations=70 if node_count_mpl_render_final_v2 > 2 else 10)

                fig_dims_mpl_json_v2 = (14,10) if G_from_json_render_final_v2.number_of_nodes() > 10 else (12,8)
                fig_mpl_render_final_v2, ax_mpl_render_final_v2 = plt.subplots(figsize=fig_dims_mpl_json_v2)
                node_size_val_render_v2 = 1200 if G_from_json_render_final_v2.number_of_nodes() < 25 else 1000
                font_size_val_render_v2 = 8 if G_from_json_render_final_v2.number_of_nodes() < 25 else 7
                
                unique_shapes_render_v2 = sorted(list(set(node_shapes_list_mpl_render_final_v2)))
                for shape_symbol_item_render_v2 in unique_shapes_render_v2:
                    nodelist_for_shape_render_v2 = [node_list_mpl_json_render_v2[i_shape_node] for i_shape_node, s_node_shape in enumerate(node_shapes_list_mpl_render_final_v2) if s_node_shape == shape_symbol_item_render_v2]
                    node_colors_for_shape_render_v2 = [node_colors_mpl_render_final_v2[i_shape_node_color] for i_shape_node_color, s_node_shape_color in enumerate(node_shapes_list_mpl_render_final_v2) if s_node_shape_color == shape_symbol_item_render_v2]
                    nx.draw_networkx_nodes(G_from_json_render_final_v2, positions_mpl_render_final_v2, nodelist=nodelist_for_shape_render_v2,
                                           node_color=node_colors_for_shape_render_v2, node_shape=shape_symbol_item_render_v2,
                                           node_size=node_size_val_render_v2, alpha=1.0, ax=ax_mpl_render_final_v2,
                                           edgecolors='black', linewidths=0.5)
                
                for i_edge_item_render_v2, edge_render_data_item_v2 in enumerate(edge_list_data_mpl_json_render_v2):
                    u_edge_render_v2, v_edge_render_v2 = edge_render_data_item_v2[0], edge_render_data_item_v2[1]
                    arrow_style_mpl_render_v2 = '-|>' if edge_data_dicts_mpl_json_render_v2[i_edge_item_render_v2].get('target_arrow_shape_attr', 'triangle') != 'none' else '-'
                    source_arrow_shape_mpl_render_v2 = edge_data_dicts_mpl_json_render_v2[i_edge_item_render_v2].get('source_arrow_shape_attr', 'none')
                    if source_arrow_shape_mpl_render_v2 != 'none': arrow_style_mpl_render_v2 = '<|-|>'
                    
                    connection_style_mpl_render_v2 = 'arc3'
                    rad_val_str_mpl_render_v2 = str(edge_data_dicts_mpl_json_render_v2[i_edge_item_render_v2].get('edge_control_point_distances', '0'))
                    rad_val_mpl_render_v2 = 0.0;
                    try: rad_val_mpl_render_v2 = float(rad_val_str_mpl_render_v2) / 100.0
                    except: rad_val_mpl_render_v2 = 0.0
                    if abs(rad_val_mpl_render_v2) > 0.01: connection_style_mpl_render_v2 = f'arc3,rad={rad_val_mpl_render_v2}'
                    
                    nx.draw_networkx_edges(G_from_json_render_final_v2, positions_mpl_render_final_v2, edgelist=[(u_edge_render_v2, v_edge_render_v2)],
                                           width=edge_widths_mpl_render_final_v2[i_edge_item_render_v2],
                                           edge_color=[edge_colors_mpl_render_final_v2[i_edge_item_render_v2]],
                                           style=edge_styles_mpl_render_final_v2[i_edge_item_render_v2],
                                           alpha=edge_opacities_mpl_render_final_v2[i_edge_item_render_v2],
                                           arrowstyle=arrow_style_mpl_render_v2, arrows=True,
                                           connectionstyle=connection_style_mpl_render_v2,
                                           ax=ax_mpl_render_final_v2, node_size=node_size_val_render_v2)

                nx.draw_networkx_labels(G_from_json_render_final_v2, positions_mpl_render_final_v2, labels=labels_mpl_json_render_v2, font_size=font_size_val_render_v2, ax=ax_mpl_render_final_v2)
                ax_mpl_render_final_v2.set_title(f"Sociograma: {institution_name} - {group_name}", fontsize=16)
                ax_mpl_render_final_v2.set_axis_off(); fig_mpl_render_final_v2.tight_layout(pad=1.0)
                
                img_buffer_mpl_json_output_v2 = io.BytesIO()
                plt.savefig(img_buffer_mpl_json_output_v2, format='png', dpi=150)
                img_buffer_mpl_json_output_v2.seek(0)
                image_bytes_for_pdf_final_json_v2 = img_buffer_mpl_json_output_v2.getvalue()
                plt.close(fig_mpl_render_final_v2)
                # if registro_output: 
                  # with registro_output: print("  INFO (PDF Gen Matplotlib JSON v2): Imagen generada desde JSON.")
        
        except Exception as e_render_mpl_from_json_final_v2:
            if registro_output:
                with registro_output:
                    print(f"!!! ERROR (PDF desde JSON - Matplotlib v2) renderizando grafo: {e_render_mpl_from_json_final_v2}")
                    print(traceback.format_exc(limit=2))
            if MATPLOTLIB_AVAILABLE and plt:
                try:
                    fig_err_json_render_v2, ax_err_json_render_v2 = plt.subplots(figsize=(5,3))
                    ax_err_json_render_v2.text(0.5,0.5, "Error al generar\nimagen del grafo\ndesde datos JSON.", ha='center',va='center',color='red', wrap=True)
                    ax_err_json_render_v2.set_axis_off(); err_buf_mpl_json_render_v2 = io.BytesIO()
                    plt.savefig(err_buf_mpl_json_render_v2, format='png', dpi=75); err_buf_mpl_json_render_v2.seek(0)
                    image_bytes_for_pdf_final_json_v2 = err_buf_mpl_json_render_v2.getvalue(); plt.close(fig_err_json_render_v2)
                    # if registro_output: 
                      # with registro_output: print("  INFO (PDF Gen Matplotlib JSON v2): Placeholder de error (render JSON) generado.")
                except Exception as e_placeholder_err_json_final_v2:
                     if registro_output: 
                      with registro_output: print(f"  ERROR (PDF Gen Matplotlib JSON v2): Falló creación de placeholder de error: {e_placeholder_err_json_final_v2}")
                     image_bytes_for_pdf_final_json_v2 = None
            else: image_bytes_for_pdf_final_json_v2 = None

    final_error_message_to_pdf_v2 = force_error_message_on_image_fail
    if image_bytes_for_pdf_final_json_v2 is None and force_error_message_on_image_fail is None:
        final_error_message_to_pdf_v2 = "Error crítico al generar imagen del grafo (Matplotlib o datos JSON)."
                
    generate_sociogram_with_legend_pdf(image_bytes_for_pdf_final_json_v2, legend_info, institution_name, group_name, registro_output,
                                       style_reciprocal_links_active=style_reciprocal_links_active_param,
                                       force_error_message=final_error_message_to_pdf_v2)
# --- FIN BLOQUE 5 ---
# --- BLOQUE 6: OTRAS FUNCIONES DE GENERACIÓN DE PDF ---
def generate_and_download_school_questionnaires_pdf(institution_name, registro_output):
    if not REPORTLAB_AVAILABLE or not BaseDocTemplateClass:
        err_msg_sq_final = "ERROR (PDF Cuestionarios Institución): ReportLab no disponible.";
        if registro_output: 
          with registro_output: print(err_msg_sq_final); return
        else:
          print(err_msg_sq_final); return
    
    filename_sq = f"CuestionariosBlancos_{re.sub(r'[^a-zA-Z0-9_]+', '', institution_name)}.pdf"
    buffer_sq = io.BytesIO()
    doc_sq = BaseDocTemplateClass(buffer_sq, pagesize=A4_SIZE, leftMargin=1.5*CM_UNIT, rightMargin=1.5*CM_UNIT, topMargin=2*CM_UNIT, bottomMargin=2.5*CM_UNIT)
    frame_sq = FrameClass(doc_sq.leftMargin, doc_sq.bottomMargin, doc_sq.width, doc_sq.height, id='frame_institution_q_pdf_v3')
    # La función _draw_page_number_general no está en el código proporcionado, asumiré que es un duplicado o similar a _draw_page_number_manual
    template_sq = PageTemplateClass(id='tpl_institution_q_pdf_v3', frames=[frame_sq], onPage=_draw_page_number_manual)
    doc_sq.addPageTemplates([template_sq]); 
    styles_sq = _create_pdf_styles_manual()
    story_sq = []
    
    institution_groups_list_sq = sociograma_data.classes_data.get(institution_name, [])
    
    if not institution_groups_list_sq:
        story_sq.append(Paragraph(f"Institución: {institution_name}", styles_sq.get('H1_Manual', styles_sq['h1'])))
        story_sq.append(Paragraph("Esta institución no tiene grupos registrados.", styles_sq.get('Normal_Manual', styles_sq['Normal'])))
    else:
        story_sq.append(Paragraph(f"Cuestionarios en Blanco", styles_sq.get('H1_Manual', styles_sq['h1'])))
        story_sq.append(Paragraph(f"Institución: {institution_name}", styles_sq.get('H2_Manual', styles_sq['h2'])))
        story_sq.append(SpacerClass(1, 0.5*CM_UNIT)); first_group_processed_sq = True
        for group_info_sq in institution_groups_list_sq:
            group_name_sq = group_info_sq.get('name')
            if not group_name_sq: continue
            if not first_group_processed_sq: story_sq.append(PageBreakClass())
            first_group_processed_sq = False
            story_sq.append(Paragraph(f"Grupo: {group_name_sq}", styles_sq.get('H2_Manual', styles_sq['h2']))); story_sq.append(SpacerClass(1, 0.3*CM_UNIT))
            
            group_question_defs_sq = sociograma_data.get_class_question_definitions(institution_name, group_name_sq)
            if not group_question_defs_sq:
                story_sq.append(Paragraph("<i>Este grupo no tiene preguntas definidas.</i>", styles_sq.get('Response_Label', styles_sq['Normal']))); story_sq.append(SpacerClass(1, 0.5*CM_UNIT)); continue
            
            sorted_q_items_inst_sq = sorted(group_question_defs_sq.items(), key=lambda item: (item[1].get('order', 99), item[0]))
            questionnaire_model_for_group_sq = []
            for q_id_inst_sq, q_def_inst_sq in sorted_q_items_inst_sq:
                question_text_inst_sq = q_def_inst_sq.get('text', f"Pregunta {q_id_inst_sq}"); max_selections_inst_sq = q_def_inst_sq.get('max_selections', 2)
                questionnaire_model_for_group_sq.append(Paragraph(f"{question_text_inst_sq} (Máximo {max_selections_inst_sq} selecciones):", styles_sq.get('Question_Text', styles_sq['Normal'])))
                for i_inst_sq in range(max_selections_inst_sq): questionnaire_model_for_group_sq.append(Paragraph(f"{i_inst_sq+1}. ___________________________________________________________", styles_sq.get('Response_Line', styles_sq['Normal'])))
                questionnaire_model_for_group_sq.append(SpacerClass(1, 0.2*CM_UNIT))
            
            group_members_list_sq = sociograma_data.members_data.get(institution_name, {}).get(group_name_sq, [])
            if not group_members_list_sq: story_sq.append(Paragraph("<i>Este grupo no tiene miembros registrados.</i>", styles_sq.get('Response_Label', styles_sq['Normal']))); continue
            
            sorted_members_inst_sq = sorted(group_members_list_sq, key=lambda s: (s.get('cognome', '').strip().upper(), s.get('nome', '').strip().upper()))
            first_member_in_this_group_sq = True
            for member_inst_item_sq in sorted_members_inst_sq:
                if not first_member_in_this_group_sq: story_sq.append(PageBreakClass())
                first_member_in_this_group_sq = False
                full_name_mem_inst_item_sq = f"{member_inst_item_sq.get('cognome', '').strip()} {member_inst_item_sq.get('nome', '').strip()}".strip()
                story_sq.append(Paragraph(f"Institución: {institution_name}", styles_sq.get('Questionnaire_Header', styles_sq['Normal'])))
                story_sq.append(Paragraph(f"Grupo: {group_name_sq}", styles_sq.get('Questionnaire_Header', styles_sq['Normal'])))
                story_sq.append(Paragraph(f"Miembro: {full_name_mem_inst_item_sq}", styles_sq.get('Member_Name_Header', styles_sq['h3'])))
                story_sq.append(SpacerClass(1, 0.3*CM_UNIT)); story_sq.extend(questionnaire_model_for_group_sq)
    try:
        doc_sq.build(story_sq); pdf_bytes_inst_q_out_final = buffer_sq.getvalue(); buffer_sq.close()
        b64_pdf_inst_q_out_final = base64.b64encode(pdf_bytes_inst_q_out_final).decode('utf-8')
        html_link_inst_q_out_final = f'<p style="text-align:center; margin-top:10px;"><a download="{filename_sq}" href="data:application/pdf;base64,{b64_pdf_inst_q_out_final}" target="_blank" style="padding:8px 15px; background-color:#007bff; color:white; text-decoration:none; border-radius:5px; font-weight:bold;">Descargar Cuestionarios en Blanco ({institution_name})</a></p>'
        if registro_output: 
          with registro_output: 
              # print(f"ÉXITO: PDF '{filename_sq}' generado."); 
              display(HTML(html_link_inst_q_out_final))
        else: display(HTML(html_link_inst_q_out_final))
    except Exception as e_build_inst_q_final_pdf:
        err_msg_build_inst_q_final_pdf_out = f"ERROR al construir PDF de cuestionarios en blanco para institución: {e_build_inst_q_final_pdf}\n{traceback.format_exc()}"; 
        if registro_output: 
          with registro_output: print(err_msg_build_inst_q_final_pdf_out)
        else:
          print(err_msg_build_inst_q_final_pdf_out)
        if buffer_sq and not buffer_sq.closed: buffer_sq.close()

def generate_and_download_questionnaire_pdf(institution_name, group_name, registro_output):
    if not REPORTLAB_AVAILABLE or not BaseDocTemplateClass:
        err_msg_qpdf_det_final = "ERROR (PDF Respuestas Det.): ReportLab no disponible.";
        if registro_output: 
          with registro_output: print(err_msg_qpdf_det_final); return
        else:
          print(err_msg_qpdf_det_final); return
    filename_q_det_final = f"RespuestasDetalladas_{re.sub(r'[^a-zA-Z0-9_]+','',institution_name)}_{re.sub(r'[^a-zA-Z0-9_]+','',group_name)}.pdf"
    buffer_q_det_final = io.BytesIO(); doc_q_det_final = BaseDocTemplateClass(buffer_q_det_final, pagesize=A4_SIZE, leftMargin=1.5*CM_UNIT, rightMargin=1.5*CM_UNIT, topMargin=2*CM_UNIT, bottomMargin=2.5*CM_UNIT)
    # La función _draw_page_number_general no está en el código proporcionado, asumiré que es un duplicado o similar a _draw_page_number_manual
    frame_q_det_final = FrameClass(doc_q_det_final.leftMargin, doc_q_det_final.bottomMargin, doc_q_det_final.width, doc_q_det_final.height, id='frame_resp_det_pdf_v3')
    template_q_det_final = PageTemplateClass(id='tpl_resp_det_pdf_v3', frames=[frame_q_det_final], onPage=_draw_page_number_manual)
    doc_q_det_final.addPageTemplates([template_q_det_final]);
    styles_q_det_final = _create_pdf_styles_manual()
    story_q_det_final = []
    story_q_det_final.append(Paragraph(f"Respuestas Detalladas del Cuestionario", styles_q_det_final.get('H1_Manual', styles_q_det_final['h1'])))
    story_q_det_final.append(Paragraph(f"Institución: {institution_name}", styles_q_det_final.get('H2_Manual', styles_q_det_final['h2'])))
    story_q_det_final.append(Paragraph(f"Grupo: {group_name}", styles_q_det_final.get('H2_Manual', styles_q_det_final['h2'])))
    story_q_det_final.append(SpacerClass(1, 0.5*CM_UNIT))
    group_question_defs_resp_det_final = sociograma_data.get_class_question_definitions(institution_name, group_name)
    if not group_question_defs_resp_det_final:
        story_q_det_final.append(Paragraph(f"<i>Este grupo ({group_name}) no tiene preguntas definidas.</i>", styles_q_det_final.get('Response_Label', styles_q_det_final['Normal'])))
    else:
        sorted_q_items_resp_det_final = sorted(group_question_defs_resp_det_final.items(), key=lambda item:(item[1].get('order',99),item[0]))
        members_list_resp_det_final = sociograma_data.members_data.get(institution_name,{}).get(group_name,[])
        if not members_list_resp_det_final:
            story_q_det_final.append(Paragraph(f"<i>No hay miembros en el grupo {group_name}.</i>", styles_q_det_final.get('Response_Label', styles_q_det_final['Normal'])))
        else:
            sorted_members_resp_det_final = sorted(members_list_resp_det_final, key=lambda s:(s.get('cognome','').strip().upper(),s.get('nome','').strip().upper()))
            first_mem_page_resp_det_final = True
            for mem_resp_det_item in sorted_members_resp_det_final:
                if not first_mem_page_resp_det_final: story_q_det_final.append(PageBreakClass())
                first_mem_page_resp_det_final = False
                full_n_resp_det_item = f"{mem_resp_det_item.get('cognome','').strip()} {mem_resp_det_item.get('nome','').strip()}".strip()
                story_q_det_final.append(Paragraph(f"Miembro: {full_n_resp_det_item}", styles_q_det_final.get('Member_Name_Header', styles_q_det_final['h3'])))
                mem_resp_key_det_item = (institution_name, group_name, full_n_resp_det_item)
                mem_responses_dict_det_item = sociograma_data.questionnaire_responses_data.get(mem_resp_key_det_item, {})
                if not mem_responses_dict_det_item: story_q_det_final.append(Paragraph("<i>No ha respondido el cuestionario.</i>", styles_q_det_final.get('Response_Label',styles_q_det_final['Normal'])))
                else:
                    any_response_for_this_member_resp_det = False
                    for q_id_resp_det, q_def_resp_det in sorted_q_items_resp_det_final:
                        question_text_resp_det = q_def_resp_det.get('text', f"Pregunta {q_id_resp_det}"); data_key_resp_det = q_def_resp_det.get('data_key', q_id_resp_det)
                        responses_for_q_resp_det = mem_responses_dict_det_item.get(data_key_resp_det, [])
                        story_q_det_final.append(Paragraph(f"{question_text_resp_det}:", styles_q_det_final.get('Question_Text', styles_q_det_final['Normal'])))
                        if responses_for_q_resp_det:
                            any_response_for_this_member_resp_det = True
                            for i_resp_det, resp_name_item_det in enumerate(responses_for_q_resp_det): story_q_det_final.append(Paragraph(f"    {i_resp_det+1}. {resp_name_item_det}", styles_q_det_final.get('Normal_Manual', styles_q_det_final['Normal'])))
                        else: story_q_det_final.append(Paragraph("    - Sin respuesta -", styles_q_det_final.get('Response_Label', styles_q_det_final['Normal'])))
                        story_q_det_final.append(SpacerClass(1, 0.1*CM_UNIT))
                    if not any_response_for_this_member_resp_det and mem_responses_dict_det_item : story_q_det_final.append(Paragraph("<i>(No se encontraron respuestas para las preguntas actuales del cuestionario)</i>", styles_q_det_final.get('Response_Label', styles_q_det_final['Normal'])))
    try:
        doc_q_det_final.build(story_q_det_final); pdf_bytes_q_det_out_final = buffer_q_det_final.getvalue(); buffer_q_det_final.close(); b64_pdf_q_det_out_final = base64.b64encode(pdf_bytes_q_det_out_final).decode('utf-8')
        html_link_q_det_out_final = f'<p style="text-align:center; margin-top:10px;"><a download="{filename_q_det_final}" href="data:application/pdf;base64,{b64_pdf_q_det_out_final}" target="_blank" style="padding:8px 15px; background-color:#17a2b8; color:white;text-decoration:none;border-radius:5px;font-weight:bold;">Descargar Respuestas Detalladas: {filename_q_det_final}</a></p>'
        if registro_output: 
          with registro_output: 
              # print(f"ÉXITO: PDF '{filename_q_det_final}' generado."); 
              display(HTML(html_link_q_det_out_final))
        else: display(HTML(html_link_q_det_out_final))
    except Exception as e_build_q_det_final_pdf:
        err_msg_build_q_det_final_pdf_out = f"ERROR construyendo PDF de respuestas detalladas: {e_build_q_det_final_pdf}\n{traceback.format_exc()}";
        if registro_output: 
          with registro_output: print(err_msg_build_q_det_final_pdf_out)
        else:
          print(err_msg_build_q_det_final_pdf_out)
        if buffer_q_det_final and not buffer_q_det_final.closed: buffer_q_det_final.close()

def generate_class_questionnaire_template_pdf(institution_name, group_name, registro_output):
    if not REPORTLAB_AVAILABLE or not BaseDocTemplateClass:
        err_msg_tpl_grp_final_pdf = "ERROR (PDF Plantilla Grupo): ReportLab no disponible.";
        if registro_output: 
          with registro_output: print(err_msg_tpl_grp_final_pdf); return
        else:
          print(err_msg_tpl_grp_final_pdf); return
    filename_tpl_grp_final_pdf = f"PlantillaCuestionario_{re.sub(r'[^a-zA-Z0-9_]+','',institution_name)}_{re.sub(r'[^a-zA-Z0-9_]+','',group_name)}.pdf"
    buffer_tpl_grp_final_pdf = io.BytesIO(); doc_tpl_grp_final_pdf = BaseDocTemplateClass(buffer_tpl_grp_final_pdf, pagesize=A4_SIZE, leftMargin=1.5*CM_UNIT, rightMargin=1.5*CM_UNIT, topMargin=2*CM_UNIT, bottomMargin=2.5*CM_UNIT)
    frame_tpl_grp_final_pdf = FrameClass(doc_tpl_grp_final_pdf.leftMargin, doc_tpl_grp_final_pdf.bottomMargin, doc_tpl_grp_final_pdf.width, doc_tpl_grp_final_pdf.height, id='frame_tpl_grp_pdf_v3')
    template_tpl_grp_final_pdf = PageTemplateClass(id='tpl_tpl_grp_pdf_v3', frames=[frame_tpl_grp_final_pdf], onPage=_draw_page_number_manual)
    doc_tpl_grp_final_pdf.addPageTemplates([template_tpl_grp_final_pdf]); 
    styles_tpl_grp_final_pdf = _create_pdf_styles_manual()
    story_tpl_grp_final_pdf = []
    story_tpl_grp_final_pdf.append(Paragraph(f"Plantilla del Cuestionario Sociométrico", styles_tpl_grp_final_pdf.get('H1_Manual', styles_tpl_grp_final_pdf['h1'])))
    story_tpl_grp_final_pdf.append(Paragraph(f"Institución: {institution_name}", styles_tpl_grp_final_pdf.get('H2_Manual', styles_tpl_grp_final_pdf['h2'])))
    story_tpl_grp_final_pdf.append(Paragraph(f"Grupo: {group_name}", styles_tpl_grp_final_pdf.get('H2_Manual', styles_tpl_grp_final_pdf['h2'])))
    story_tpl_grp_final_pdf.append(SpacerClass(1,0.3*CM_UNIT)); story_tpl_grp_final_pdf.append(Paragraph("Nombre del Miembro: ____________________________________________", styles_tpl_grp_final_pdf.get('Member_Name_Header',styles_tpl_grp_final_pdf['h3']))); story_tpl_grp_final_pdf.append(SpacerClass(1,0.5*CM_UNIT))
    group_q_defs_tpl_grp_final_pdf = sociograma_data.get_class_question_definitions(institution_name, group_name)
    if not group_q_defs_tpl_grp_final_pdf:
        story_tpl_grp_final_pdf.append(Paragraph(f"<i>Este grupo ({group_name}) no tiene preguntas definidas.</i>", styles_tpl_grp_final_pdf.get('Response_Label',styles_tpl_grp_final_pdf['Normal'])))
    else:
        sorted_q_items_tpl_grp_final_pdf = sorted(group_q_defs_tpl_grp_final_pdf.items(), key=lambda item:(item[1].get('order',99),item[0]))
        for q_id_tpl_grp_final_pdf, q_def_tpl_grp_final_pdf in sorted_q_items_tpl_grp_final_pdf:
            q_text_tpl_grp_final_pdf = q_def_tpl_grp_final_pdf.get('text',f"Pregunta {q_id_tpl_grp_final_pdf}"); max_sel_tpl_grp_final_pdf = q_def_tpl_grp_final_pdf.get('max_selections',2)
            story_tpl_grp_final_pdf.append(Paragraph(f"{q_text_tpl_grp_final_pdf} (Máximo {max_sel_tpl_grp_final_pdf} selecciones):", styles_tpl_grp_final_pdf.get('Question_Text',styles_tpl_grp_final_pdf['Normal'])))
            for i_tpl_grp_final_pdf in range(max_sel_tpl_grp_final_pdf): story_tpl_grp_final_pdf.append(Paragraph(f"{i_tpl_grp_final_pdf+1}. ___________________________________________________________", styles_tpl_grp_final_pdf.get('Response_Line',styles_tpl_grp_final_pdf['Normal'])))
            story_tpl_grp_final_pdf.append(SpacerClass(1,0.2*CM_UNIT))
    try:
        doc_tpl_grp_final_pdf.build(story_tpl_grp_final_pdf); pdf_bytes_tpl_grp_out_final_pdf = buffer_tpl_grp_final_pdf.getvalue(); buffer_tpl_grp_final_pdf.close(); b64_pdf_tpl_grp_out_final_pdf = base64.b64encode(pdf_bytes_tpl_grp_out_final_pdf).decode('utf-8')
        html_link_tpl_grp_out_final_pdf = f'<p style="text-align:center; margin-top:10px;"><a download="{filename_tpl_grp_final_pdf}" href="data:application/pdf;base64,{b64_pdf_tpl_grp_out_final_pdf}" target="_blank" style="padding:8px 15px; background-color:#007bff; color:white;text-decoration:none;border-radius:5px;font-weight:bold;">Descargar Plantilla de Cuestionario</a></p>'
        if registro_output: 
          with registro_output: 
              # print(f"ÉXITO: PDF plantilla '{filename_tpl_grp_final_pdf}' listo."); 
              display(HTML(html_link_tpl_grp_out_final_pdf))
        else: display(HTML(html_link_tpl_grp_out_final_pdf))
    except Exception as e_build_tpl_grp_final_pdf_gen:
        err_msg_build_tpl_grp_final_pdf_gen_out = f"ERROR construyendo PDF plantilla para {group_name}: {e_build_tpl_grp_final_pdf_gen}\n{traceback.format_exc()}";
        if registro_output: 
          with registro_output: print(err_msg_build_tpl_grp_final_pdf_gen_out)
        else:
          print(err_msg_build_tpl_grp_final_pdf_gen_out)
        if buffer_tpl_grp_final_pdf and not buffer_tpl_grp_final_pdf.closed: buffer_tpl_grp_final_pdf.close()

def generate_class_summary_report_pdf(institution_name, group_name, registro_output):
    if not REPORTLAB_AVAILABLE or not BaseDocTemplateClass:
        err_msg_sum_rep_grp_final_pdf = "ERROR (PDF Resumen Grupo): ReportLab no disponible.";
        if registro_output: 
          with registro_output: print(err_msg_sum_rep_grp_final_pdf); return
        else:
          print(err_msg_sum_rep_grp_final_pdf); return
    
    filename_sum_grp_final_pdf = f"ResumenCuestionario_{re.sub(r'[^a-zA-Z0-9_]+','',institution_name)}_{re.sub(r'[^a-zA-Z0-9_]+','',group_name)}_{datetime.datetime.now().strftime('%Y%m%d%H%M')}.pdf"
    buffer_sum_grp_final_pdf = io.BytesIO()
    page_size_sum_rep_final_pdf = LANDSCAPE_FUNC(A4_SIZE)
    doc_sum_grp_final_pdf = BaseDocTemplateClass(buffer_sum_grp_final_pdf, pagesize=page_size_sum_rep_final_pdf,
                                                 leftMargin=1*CM_UNIT, rightMargin=1*CM_UNIT,
                                                 topMargin=1.5*CM_UNIT, bottomMargin=1.5*CM_UNIT)
    
    frame_sum_grp_final_pdf = FrameClass(doc_sum_grp_final_pdf.leftMargin, doc_sum_grp_final_pdf.bottomMargin,
                                         doc_sum_grp_final_pdf.width, doc_sum_grp_final_pdf.height,
                                         id='frame_group_summary_pdf_v_final')
    template_sum_grp_final_pdf = PageTemplateClass(id='tpl_group_summary_pdf_v_final',
                                                   frames=[frame_sum_grp_final_pdf],
                                                   onPage=_draw_page_number_manual)
    doc_sum_grp_final_pdf.addPageTemplates([template_sum_grp_final_pdf])
    styles_sum_grp_final_pdf = _create_pdf_styles_manual()
    story_sum_grp_final_pdf = []

    story_sum_grp_final_pdf.append(Paragraph(f"Institución: {institution_name}", styles_sum_grp_final_pdf.get('Normal_Manual', styles_sum_grp_final_pdf['Normal'])))
    story_sum_grp_final_pdf.append(Paragraph(f"Grupo: {group_name}", styles_sum_grp_final_pdf.get('Normal_Manual', styles_sum_grp_final_pdf['Normal'])))
    story_sum_grp_final_pdf.append(Paragraph(f"<font size='7'>Generado el: {datetime.datetime.now().strftime('%d/%m/%Y %I:%M %p')}</font>", styles_sum_grp_final_pdf.get('Small_Info', styles_sum_grp_final_pdf['Normal'])))
    story_sum_grp_final_pdf.append(SpacerClass(1, 0.5*CM_UNIT))
    story_sum_grp_final_pdf.append(Paragraph("RESUMEN DEL CUESTIONARIO SOCIOMÉTRICO", styles_sum_grp_final_pdf.get('H1_Manual', styles_sum_grp_final_pdf['h1'])))
    story_sum_grp_final_pdf.append(Paragraph("<i>(Conteggio de elecciones recibidas por tipo de pregunta)</i>", styles_sum_grp_final_pdf.get('Questionnaire_Header', styles_sum_grp_final_pdf['Normal'])))
    story_sum_grp_final_pdf.append(SpacerClass(1, 0.5*CM_UNIT))
    
    members_list_summary_rep_final = sociograma_data.members_data.get(institution_name, {}).get(group_name, [])
    group_question_defs_summary_rep_final = sociograma_data.get_class_question_definitions(institution_name, group_name)

    if not members_list_summary_rep_final or not group_question_defs_summary_rep_final:
        msg_no_data_sum_final = "";
        if not members_list_summary_rep_final: msg_no_data_sum_final += "No hay miembros registrados en este grupo. "
        if not group_question_defs_summary_rep_final: msg_no_data_sum_final += "No hay preguntas de cuestionario definidas para este grupo."
        story_sum_grp_final_pdf.append(Paragraph(f"<i>{msg_no_data_sum_final.strip()}</i>", styles_sum_grp_final_pdf.get('Response_Label', styles_sum_grp_final_pdf['Normal'])))
    else:
        positive_questions_summary_list_final = []
        negative_questions_summary_list_final = []
        sorted_q_items_summary_rep_final = sorted(group_question_defs_summary_rep_final.items(), key=lambda item: (item[1].get('order',99),item[0]))
        
        for q_id_sum_rep_final, q_def_sum_rep_final in sorted_q_items_summary_rep_final:
            dk_sum_rep_final = q_def_sum_rep_final.get('data_key', q_id_sum_rep_final)
            q_type_sum_rep_final = q_def_sum_rep_final.get('type','General')[:10]
            if q_def_sum_rep_final.get('polarity')=='positive':
                positive_questions_summary_list_final.append({'data_key':dk_sum_rep_final, 'type':q_type_sum_rep_final})
            elif q_def_sum_rep_final.get('polarity')=='negative':
                negative_questions_summary_list_final.append({'data_key':dk_sum_rep_final, 'type':q_type_sum_rep_final})
        
        header_row_summary_rep_final = [Paragraph("<b>MIEMBRO</b>",styles_sum_grp_final_pdf['Table_Header_Manual'])]
        name_col_w_sum_rep_final=4.5*CM_UNIT
        total_col_w_sum_rep_final=1.5*CM_UNIT
        
        num_pos_q_sum_rep_final=len(positive_questions_summary_list_final)
        num_neg_q_sum_rep_final=len(negative_questions_summary_list_final)
        num_choice_cols_sum_rep_final = num_pos_q_sum_rep_final + num_neg_q_sum_rep_final
        
        available_width_for_choices_sum_rep_final = doc_sum_grp_final_pdf.width - name_col_w_sum_rep_final - (total_col_w_sum_rep_final * 2)
        
        choice_col_w_sum_rep_final = 1.0*CM_UNIT
        if num_choice_cols_sum_rep_final > 0:
            choice_col_w_sum_rep_final = max(choice_col_w_sum_rep_final, available_width_for_choices_sum_rep_final / num_choice_cols_sum_rep_final)
        
        col_widths_summary_rep_final=[name_col_w_sum_rep_final]
        
        for pq_sum_rep_final in positive_questions_summary_list_final:
            header_row_summary_rep_final.append(Paragraph(f"<b>Acep.<br/>{pq_sum_rep_final['type']}</b>",styles_sum_grp_final_pdf['Table_Header_Manual']))
            col_widths_summary_rep_final.append(choice_col_w_sum_rep_final)
        header_row_summary_rep_final.append(Paragraph("<b>TOTAL<br/>Acep.</b>",styles_sum_grp_final_pdf['Table_Header_Manual']))
        col_widths_summary_rep_final.append(total_col_w_sum_rep_final)
        
        for nq_sum_rep_final in negative_questions_summary_list_final:
            header_row_summary_rep_final.append(Paragraph(f"<b>Rech.<br/>{nq_sum_rep_final['type']}</b>",styles_sum_grp_final_pdf['Table_Header_Manual']))
            col_widths_summary_rep_final.append(choice_col_w_sum_rep_final)
        header_row_summary_rep_final.append(Paragraph("<b>TOTAL<br/>Rech.</b>",styles_sum_grp_final_pdf['Table_Header_Manual']))
        col_widths_summary_rep_final.append(total_col_w_sum_rep_final)
        
        table_data_summary_rep_final = [header_row_summary_rep_final]

        nominations_received_summary_rep_final = collections.defaultdict(lambda: collections.defaultdict(int))
        for (resp_inst_sum_final,resp_grp_sum_final,nominator_k_sum_final),responses_val_sum_final in sociograma_data.questionnaire_responses_data.items():
            if resp_inst_sum_final==institution_name and resp_grp_sum_final==group_name:
                for dk_val_sum_final,nominated_l_sum_final in responses_val_sum_final.items():
                    for nominee_k_sum_final in nominated_l_sum_final:
                        nominations_received_summary_rep_final[nominee_k_sum_final][dk_val_sum_final]+=1
        
        sorted_members_for_rows_summary_rep_final = sorted(
            members_list_summary_rep_final,
            key=lambda m_sort_sum:(str(m_sort_sum.get('nome','')).strip().title(),str(m_sort_sum.get('cognome','')).strip().title())
        )
        
        for member_info_sum_row_rep_final in sorted_members_for_rows_summary_rep_final:
            nome_fila_titulo_sum_rep_final = member_info_sum_row_rep_final.get('nome','').strip().title()
            cognome_fila_titulo_sum_rep_final = member_info_sum_row_rep_final.get('cognome','').strip().title()
            full_name_key_display_sum_rep_final = f"{nome_fila_titulo_sum_rep_final} {cognome_fila_titulo_sum_rep_final}".strip()
            
            row_data_sum_rep_final=[Paragraph(full_name_key_display_sum_rep_final,styles_sum_grp_final_pdf['Table_Cell_Manual'])]
            total_pos_rec_sum_rep_final=0
            for pq_sum_data_rep_final in positive_questions_summary_list_final:
                count_sum_rep_final=nominations_received_summary_rep_final[full_name_key_display_sum_rep_final].get(pq_sum_data_rep_final['data_key'],0)
                row_data_sum_rep_final.append(Paragraph(str(count_sum_rep_final),styles_sum_grp_final_pdf['Table_Cell_Manual']))
                total_pos_rec_sum_rep_final+=count_sum_rep_final
            row_data_sum_rep_final.append(Paragraph(f"<b>{total_pos_rec_sum_rep_final}</b>",styles_sum_grp_final_pdf['Table_Cell_Manual']))
            
            total_neg_rec_sum_rep_final=0
            for nq_sum_data_rep_final in negative_questions_summary_list_final:
                count_sum_rep_final=nominations_received_summary_rep_final[full_name_key_display_sum_rep_final].get(nq_sum_data_rep_final['data_key'],0)
                row_data_sum_rep_final.append(Paragraph(str(count_sum_rep_final),styles_sum_grp_final_pdf['Table_Cell_Manual']))
                total_neg_rec_sum_rep_final+=count_sum_rep_final
            row_data_sum_rep_final.append(Paragraph(f"<b>{total_neg_rec_sum_rep_final}</b>",styles_sum_grp_final_pdf['Table_Cell_Manual']))
            
            table_data_summary_rep_final.append(row_data_sum_rep_final)

        if len(table_data_summary_rep_final)>1:
            table_summary_rep_final=TableClass(table_data_summary_rep_final,colWidths=col_widths_summary_rep_final,repeatRows=1)
            table_summary_rep_final.setStyle(TableStyleClass([
                ('BACKGROUND',(0,0),(-1,0),color_lightgrey if color_lightgrey else ColorClass(0.8,0.8,0.8)),
                ('GRID',(0,0),(-1,-1),0.5,color_grey if color_grey else ColorClass(0.5,0.5,0.5)),
                ('ALIGN',(1,0),(-1,-1),'CENTER'),
                ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                ('FONTNAME',(0,1),(0,-1),'Helvetica'),
                ('FONTSIZE',(0,0),(-1,-1),7),
                ('LEFTPADDING',(0,0),(0,-1),2*MM_UNIT),
                ('RIGHTPADDING',(-1,0),(-1,-1),2*MM_UNIT)
            ]))
            story_sum_grp_final_pdf.append(table_summary_rep_final)
        else:
            story_sum_grp_final_pdf.append(Paragraph("<i>No hay datos de elecciones recibidas para mostrar en la tabla de resumen.</i>",styles_sum_grp_final_pdf.get('Response_Label',styles_sum_grp_final_pdf['Normal'])))
    try:
        doc_sum_grp_final_pdf.build(story_sum_grp_final_pdf)
        pdf_bytes_summary_out_final = buffer_sum_grp_final_pdf.getvalue(); buffer_sum_grp_final_pdf.close()
        b64_pdf_summary_out_final = base64.b64encode(pdf_bytes_summary_out_final).decode('utf-8')
        html_link_summary_out_final = f'<p style="text-align:center; margin-top:10px;"><a download="{filename_sum_grp_final_pdf}" href="data:application/pdf;base64,{b64_pdf_summary_out_final}" target="_blank" style="padding:8px 15px; background-color:#28a745; color:white; text-decoration:none; border-radius:5px; font-weight:bold;">Descargar Resumen del Grupo: {filename_sum_grp_final_pdf}</a></p>'
        if registro_output:
            with registro_output:
                # print(f"ÉXITO: PDF resumen del grupo '{filename_sum_grp_final_pdf}' listo para descargar.")
                display(HTML(html_link_summary_out_final))
        else:
            display(HTML(html_link_summary_out_final))
    except Exception as e_build_sum_grp_final_pdf_gen:
        err_msg_build_sum_grp_final_pdf_gen_out = f"ERROR construyendo PDF resumen para grupo {group_name}: {e_build_sum_grp_final_pdf_gen}\n{traceback.format_exc()}";
        if registro_output: 
          with registro_output: print(err_msg_build_sum_grp_final_pdf_gen_out)
        else:
          print(err_msg_build_sum_grp_final_pdf_gen_out)
        if buffer_sum_grp_final_pdf and not buffer_sum_grp_final_pdf.closed: buffer_sum_grp_final_pdf.close()

def generate_pdf_from_html_content(html_string, output_filename_base, registro_output):
    if not XHTML2PDF_AVAILABLE:
        err_msg_xhtml_gen_final_html_pdf = "ERROR (HTML a PDF): xhtml2pdf no instalado.";
        if registro_output: 
          with registro_output: print(err_msg_xhtml_gen_final_html_pdf); display(HTML("<p style='color:red;'>Error: Falta xhtml2pdf.</p>"))
        else:
          print(err_msg_xhtml_gen_final_html_pdf)
        return
    output_filename_final_html_pdf_gen = f"{re.sub(r'[^a-zA-Z0-9_]+', '', output_filename_base)}_{datetime.datetime.now().strftime('%Y%m%d%H%M')}.pdf"
    buffer_final_html_pdf_gen = io.BytesIO()
    full_html_content_final_pdf_gen = html_string
    if not html_string.strip().lower().startswith("<!doctype html>") and not html_string.strip().lower().startswith("<html>"):
        full_html_content_final_pdf_gen = f"<!doctype html><html><head><meta charset='utf-8'/></head><body>{html_string}</body></html>"
    source_html_stream_final_pdf_gen = io.StringIO(full_html_content_final_pdf_gen)
    pdf_result_final_html_gen_create = pisa.CreatePDF(source_html_stream_final_pdf_gen, dest=buffer_final_html_pdf_gen, encoding='utf-8')
    source_html_stream_final_pdf_gen.close()
    if pdf_result_final_html_gen_create.err:
        err_msg_xhtml_gen_final_pdf_create = f"ERROR (HTML a PDF) con xhtml2pdf: {pdf_result_final_html_gen_create.err}";
        if registro_output: 
          with registro_output: print(err_msg_xhtml_gen_final_pdf_create); display(HTML(f"<p style='color:red;'>Error PDF: {pdf_result_final_html_gen_create.err}.</p>"))
        else:
          print(err_msg_xhtml_gen_final_pdf_create)
        buffer_final_html_pdf_gen.close(); return
    pdf_bytes_final_html_out_gen_final = buffer_final_html_pdf_gen.getvalue(); buffer_final_html_pdf_gen.close()
    b64_pdf_final_html_out_gen_final = base64.b64encode(pdf_bytes_final_html_out_gen_final).decode('utf-8')
    html_link_final_html_out_gen_final = f'<p style="text-align:center; margin-top:10px;"><a download="{output_filename_final_html_pdf_gen}" href="data:application/pdf;base64,{b64_pdf_final_html_out_gen_final}" target="_blank" style="padding:8px 15px;background-color:#007bff;color:white;text-decoration:none;border-radius:5px;font-weight:bold;">Descargar PDF: {output_filename_final_html_pdf_gen}</a></p>'
    if registro_output: 
      with registro_output: 
          # print(f"ÉXITO: PDF '{output_filename_final_html_pdf_gen}' desde HTML listo."); 
          display(HTML(html_link_final_html_out_gen_final))
    else: display(HTML(html_link_final_html_out_gen_final))
# --- FIN BLOQUE 6 ---
# --- BLOQUE 7 ---
def generate_affinity_diana_image(
    institution_name,
    group_name,
    members_data_list_detailed,
    edges_data,
    show_lines=True,
    registro_output=None,
    num_zonas_definidas=4,
    labels_zonas=None,
    filename_base="DianaAfinidad"
):
    # if registro_output and hasattr(registro_output, 'append_stdout'):
        # with registro_output:
            # print(f"  DEBUG (gen_diana_img v1.22 - Sexo, Inst/Grp, Miembro): Entrando.")
            # print(f"    Institución: {institution_name}, Grupo: {group_name}")
            # print(f"    Num Miembros Data: {len(members_data_list_detailed) if members_data_list_detailed is not None else 'None'}")
            # print(f"    Num Edges Data: {len(edges_data) if edges_data is not None else 'None'}")

    if not MATPLOTLIB_AVAILABLE or plt is None or mpatches is None or np is None or mlines is None:
        if registro_output and hasattr(registro_output, 'append_stdout'):
            with registro_output: print("ERROR (Diana Afinidad Matplotlib): Matplotlib o componentes no disponibles.")
        return None

    if not members_data_list_detailed:
        # if registro_output and hasattr(registro_output, 'append_stdout'):
            # with registro_output: print("INFO (Diana Afinidad Matplotlib): No hay miembros para generar la diana.")
        fig_placeholder_diana_no_data, ax_placeholder_diana_no_data = plt.subplots(figsize=(8, 8))
        ax_placeholder_diana_no_data.text(0.5, 0.5, "No hay datos de miembros\npara la Diana de Afinidad.",
                ha='center', va='center', transform=ax_placeholder_diana_no_data.transAxes, fontsize=12, color='grey')
        ax_placeholder_diana_no_data.set_xticks([]); ax_placeholder_diana_no_data.set_yticks([]); ax_placeholder_diana_no_data.set_aspect('equal', adjustable='box')
        buffer_placeholder_diana_no_data = io.BytesIO()
        plt.savefig(buffer_placeholder_diana_no_data, format='png', dpi=100)
        plt.close(fig_placeholder_diana_no_data)
        buffer_placeholder_diana_no_data.seek(0)
        return buffer_placeholder_diana_no_data

    members_ordenados_general_diana_func = sorted(
        members_data_list_detailed,
        key=lambda x_sort: (
            x_sort.get('total_recibido', 0), x_sort.get('primeras_opciones', 0),
            x_sort.get('segundas_opciones', 0), x_sort.get('terceras_opciones', 0),
            str(x_sort.get('id_corto', 'Z'))
        ),
        reverse=True
    )

    fig_diana_img, ax_diana_img = plt.subplots(figsize=(10, 10), subplot_kw={'aspect': 'equal'})
    ax_diana_img.set_xlim(-1.35, 1.35); ax_diana_img.set_ylim(-1.35, 1.35); ax_diana_img.axis('off')
    
    n_grad_rings_bg = 100
    color_centro_grad_bg = np.array([1.0, 0.60, 0.0]) 
    color_borde_grad_bg = np.array([1.0, 0.98, 0.80]) 
    for i_grad_bg in range(n_grad_rings_bg, 0, -1):
        radio_grad_bg = i_grad_bg / n_grad_rings_bg
        frac_grad_bg = (n_grad_rings_bg - i_grad_bg) / (n_grad_rings_bg - 1 if n_grad_rings_bg > 1 else 1)
        color_actual_grad_rgb_bg = np.clip(color_borde_grad_bg * (1 - frac_grad_bg) + color_centro_grad_bg * frac_grad_bg, 0, 1)
        ancho_wedge_grad_bg = radio_grad_bg - ((i_grad_bg - 1) / n_grad_rings_bg if i_grad_bg > 1 else 0)
        grad_patch_bg = mpatches.Wedge((0, 0), radio_grad_bg, 0, 360, width=ancho_wedge_grad_bg, facecolor=tuple(color_actual_grad_rgb_bg), edgecolor='none', zorder=0)
        ax_diana_img.add_patch(grad_patch_bg)
    
    puntajes_reales_en_diana_list_func = sorted(list(set(mem.get('total_recibido', 0) for mem in members_ordenados_general_diana_func)), reverse=True)
    min_radio_puntaje_viz_adj_func = 0.15
    max_radio_puntaje_viz_adj_func = 0.98
    radios_de_los_circulos_de_puntaje_func = {} 

    if puntajes_reales_en_diana_list_func:
        max_p_real_diana_func = puntajes_reales_en_diana_list_func[0]
        min_p_real_diana_global_func = puntajes_reales_en_diana_list_func[-1]

        if len(puntajes_reales_en_diana_list_func) == 1:
            radio_unico_calc_func = (min_radio_puntaje_viz_adj_func + max_radio_puntaje_viz_adj_func) / 2.0 if puntajes_reales_en_diana_list_func[0] > 0 else max_radio_puntaje_viz_adj_func
            radios_de_los_circulos_de_puntaje_func[puntajes_reales_en_diana_list_func[0]] = radio_unico_calc_func
            circ_puntaje_func = mpatches.Circle((0,0), radio_unico_calc_func, edgecolor='#333', facecolor='none', lw=0.5, ls=':', zorder=15)
            ax_diana_img.add_patch(circ_puntaje_func)
            ax_diana_img.text(0, radio_unico_calc_func + 0.022, str(puntajes_reales_en_diana_list_func[0]), ha='center', va='bottom', fontsize=6.5, color='#222', zorder=20, bbox=dict(facecolor='white', alpha=0.15, pad=0.01, edgecolor='none'))
        else:
            for puntaje_val_circ_func in puntajes_reales_en_diana_list_func:
                radio_para_este_circ_puntaje_func = 0.0
                if max_p_real_diana_func == min_p_real_diana_global_func: 
                     radio_para_este_circ_puntaje_func = (min_radio_puntaje_viz_adj_func + max_radio_puntaje_viz_adj_func) / 2.0
                elif max_p_real_diana_func > min_p_real_diana_global_func:
                    fraccion_inv_p_func = (max_p_real_diana_func - puntaje_val_circ_func) / (max_p_real_diana_func - min_p_real_diana_global_func)
                    radio_para_este_circ_puntaje_func = min_radio_puntaje_viz_adj_func + fraccion_inv_p_func * (max_radio_puntaje_viz_adj_func - min_radio_puntaje_viz_adj_func)
                
                radios_de_los_circulos_de_puntaje_func[puntaje_val_circ_func] = radio_para_este_circ_puntaje_func
                circ_puntaje_func = mpatches.Circle((0, 0), radio_para_este_circ_puntaje_func,
                                               edgecolor='#333333', facecolor='none', lw=0.5, ls=':', zorder=15)
                ax_diana_img.add_patch(circ_puntaje_func)
                ax_diana_img.text(0, radio_para_este_circ_puntaje_func + 0.022, str(puntaje_val_circ_func),
                        ha='center', va='bottom', fontsize=6.5, color='#222222',
                        zorder=20, bbox=dict(facecolor='white', alpha=0.15, pad=0.01, edgecolor='none'))

    node_positions_diana_func = {}
    min_font_size_n_diana_func, max_font_size_n_diana_func = 5.2, 6.8
    node_size_base_n_diana_func = 1200

    members_agrupados_por_su_puntaje_real_diana_func = collections.defaultdict(list)
    for mem_data_grp_diana_func in members_ordenados_general_diana_func:
        members_agrupados_por_su_puntaje_real_diana_func[mem_data_grp_diana_func.get('total_recibido', 0)].append(mem_data_grp_diana_func)

    for puntaje_circ_actual_diana_func, lista_members_de_este_puntaje_diana_func in members_agrupados_por_su_puntaje_real_diana_func.items():
        n_members_en_este_circ_de_puntaje_diana_func = len(lista_members_de_este_puntaje_diana_func)
        if n_members_en_este_circ_de_puntaje_diana_func == 0: continue

        radio_nominal_de_este_circulo_de_puntaje_diana_func = radios_de_los_circulos_de_puntaje_func.get(
            puntaje_circ_actual_diana_func, max_radio_puntaje_viz_adj_func 
        )

        members_sub_ordenados_en_circulo_puntaje_diana_func = sorted(
            lista_members_de_este_puntaje_diana_func,
            key=lambda x_sub: (-x_sub.get('primeras_opciones',0), 
                           -x_sub.get('segundas_opciones',0), 
                           -x_sub.get('terceras_opciones',0), 
                           str(x_sub.get('id_corto','Z'))),
            reverse=False
        )
        
        angulo_inicial_para_este_circulo_puntaje_diana_func = np.random.uniform(
            0, np.pi / (n_members_en_este_circ_de_puntaje_diana_func + 0.5 if n_members_en_este_circ_de_puntaje_diana_func > 0 else 1)
        ) * (puntaje_circ_actual_diana_func + 2.0)

        for j_idx_mem_sub_orden_diana_func, member_dict_diana_func in enumerate(members_sub_ordenados_en_circulo_puntaje_diana_func):
            nombre_completo_mem_diana_func = member_dict_diana_func.get('nombre_completo')
            id_corto_mem_diana_func = member_dict_diana_func.get('id_corto')
            sexo_mem_diana_func = member_dict_diana_func.get('sexo', 'Desconocido')
            if not all([nombre_completo_mem_diana_func, id_corto_mem_diana_func, sexo_mem_diana_func]): continue
            
            radio_final_colocacion_nodo_diana_func = radio_nominal_de_este_circulo_de_puntaje_diana_func
            
            if n_members_en_este_circ_de_puntaje_diana_func > 1:
                fraccion_sub_prioridad_diana_func = j_idx_mem_sub_orden_diana_func / (n_members_en_este_circ_de_puntaje_diana_func - 1)
                
                idx_puntaje_actual_en_lista_diana_func = puntajes_reales_en_diana_list_func.index(puntaje_circ_actual_diana_func) if puntaje_circ_actual_diana_func in puntajes_reales_en_diana_list_func else -1
                radio_limite_interno_para_ajuste_diana_func = 0.0
                if idx_puntaje_actual_en_lista_diana_func > 0:
                    puntaje_inmediatamente_superior_diana_func = puntajes_reales_en_diana_list_func[idx_puntaje_actual_en_lista_diana_func - 1]
                    radio_limite_interno_para_ajuste_diana_func = radios_de_los_circulos_de_puntaje_func.get(puntaje_inmediatamente_superior_diana_func, 0.0)
                
                espacio_max_para_ajuste_hacia_adentro_diana_func = radio_nominal_de_este_circulo_de_puntaje_diana_func - radio_limite_interno_para_ajuste_diana_func
                factor_dispersion_en_banda_diana_func = 0.75
                delta_total_dispersion_radial_diana_func = espacio_max_para_ajuste_hacia_adentro_diana_func * factor_dispersion_en_banda_diana_func
                ajuste_radial_calculado_diana_func = - (1 - fraccion_sub_prioridad_diana_func) * delta_total_dispersion_radial_diana_func
                radio_final_colocacion_nodo_diana_func = radio_nominal_de_este_circulo_de_puntaje_diana_func + ajuste_radial_calculado_diana_func
            
            if puntaje_circ_actual_diana_func == (puntajes_reales_en_diana_list_func[0] if puntajes_reales_en_diana_list_func else 0) and \
               n_members_en_este_circ_de_puntaje_diana_func == 1 and radio_nominal_de_este_circulo_de_puntaje_diana_func < 0.05:
                 radio_final_colocacion_nodo_diana_func = 0.0
            
            radio_final_colocacion_nodo_diana_func = max(0.0, radio_final_colocacion_nodo_diana_func)

            angulo_mem_actual_pos_diana_func = angulo_inicial_para_este_circulo_puntaje_diana_func + (j_idx_mem_sub_orden_diana_func * (2 * np.pi / n_members_en_este_circ_de_puntaje_diana_func if n_members_en_este_circ_de_puntaje_diana_func > 0 else 1))
            
            x_node_final_pos_diana_func, y_node_final_pos_diana_func = 0, 0
            if radio_final_colocacion_nodo_diana_func > 0.0001 or n_members_en_este_circ_de_puntaje_diana_func > 1 :
                 x_node_final_pos_diana_func = radio_final_colocacion_nodo_diana_func * np.cos(angulo_mem_actual_pos_diana_func)
                 y_node_final_pos_diana_func = radio_final_colocacion_nodo_diana_func * np.sin(angulo_mem_actual_pos_diana_func)
            node_positions_diana_func[nombre_completo_mem_diana_func] = (x_node_final_pos_diana_func, y_node_final_pos_diana_func)

            marker_s_diana_func, fc_s_diana_func = ('^', '#FFC0CB') if sexo_mem_diana_func.lower() == 'femenino' else \
                                                 ('o', '#ADD8E6') if sexo_mem_diana_func.lower() == 'masculino' else \
                                                 ('s', '#A0E0A0')
            node_sz_reduct_diana_func = (n_members_en_este_circ_de_puntaje_diana_func / 7.0) + (radio_final_colocacion_nodo_diana_func * 0.6)
            node_actual_sz_diana_func = max(38, node_size_base_n_diana_func / (node_sz_reduct_diana_func + 1.5) )
            ax_diana_img.scatter(x_node_final_pos_diana_func, y_node_final_pos_diana_func, s=node_actual_sz_diana_func, marker=marker_s_diana_func, 
                                 edgecolor='#101010', facecolor=fc_s_diana_func, zorder=25, lw=0.45)
            font_actual_sz_diana_func = max(min_font_size_n_diana_func, max_font_size_n_diana_func - (n_members_en_este_circ_de_puntaje_diana_func / 8.0) - (radio_final_colocacion_nodo_diana_func * 1.0))
            ax_diana_img.text(x_node_final_pos_diana_func, y_node_final_pos_diana_func, id_corto_mem_diana_func, 
                              ha='center', va='center', fontsize=font_actual_sz_diana_func, 
                              color='#000000', zorder=28, weight='normal')

    if show_lines and edges_data:
        direct_election_pairs_diana_func = set((e_tuple[0],e_tuple[1]) for e_tuple in edges_data if e_tuple[0]!=e_tuple[1])
        edge_instance_counts_diana_func = collections.defaultdict(int)
        drawn_bi_directional_arrows_pairs_diana_func = set()

        for nominator_diana_func, nominee_diana_func, q_key_edge_diana_func, _ in edges_data:
            if nominator_diana_func == nominee_diana_func or nominator_diana_func not in node_positions_diana_func or nominee_diana_func not in node_positions_diana_func:
                continue
            x1_diana_func, y1_diana_func = node_positions_diana_func[nominator_diana_func]
            x2_diana_func, y2_diana_func = node_positions_diana_func[nominee_diana_func]
            is_reciprocal_this_pair_diana_func = (nominee_diana_func, nominator_diana_func) in direct_election_pairs_diana_func
            sorted_pair_key_diana_func = tuple(sorted((nominator_diana_func, nominee_diana_func)))
            
            line_style_arrow_diana_func, arrow_color_val_diana_func, alpha_val_diana_func, lw_val_diana_func, z_order_arrow_diana_func = ('-', '#404040', 0.55, 0.65, 5)
            if is_reciprocal_this_pair_diana_func:
                line_style_arrow_diana_func, arrow_color_val_diana_func, alpha_val_diana_func, lw_val_diana_func = ('--', '#606060', 0.38, 0.50)
            
            dx_arrow_diana_func, dy_arrow_diana_func = x2_diana_func - x1_diana_func, y2_diana_func - y1_diana_func
            dist_arrow_diana_func = math.hypot(dx_arrow_diana_func, dy_arrow_diana_func)
            if dist_arrow_diana_func < 0.001: continue
            
            node_marker_effective_radius_approx_diana_func = 0.030 
            offset_factor_arrow_diana_func = min(node_marker_effective_radius_approx_diana_func, dist_arrow_diana_func * 0.18)
            
            x_start_arrow_diana_func = x1_diana_func + dx_arrow_diana_func * offset_factor_arrow_diana_func / dist_arrow_diana_func
            y_start_arrow_diana_func = y1_diana_func + dy_arrow_diana_func * offset_factor_arrow_diana_func / dist_arrow_diana_func
            x_end_arrow_diana_func = x2_diana_func - dx_arrow_diana_func * offset_factor_arrow_diana_func / dist_arrow_diana_func
            y_end_arrow_diana_func = y2_diana_func - dy_arrow_diana_func * offset_factor_arrow_diana_func / dist_arrow_diana_func
            
            connection_style_val_diana_func = "arc3,rad=0"

            if is_reciprocal_this_pair_diana_func:
                if sorted_pair_key_diana_func in drawn_bi_directional_arrows_pairs_diana_func: continue
                rad_recip_curve_diana_func = 0.12
                ax_diana_img.annotate("", xy=(x_end_arrow_diana_func, y_end_arrow_diana_func), xytext=(x_start_arrow_diana_func, y_start_arrow_diana_func),
                                      arrowprops=dict(arrowstyle="-|>", mutation_scale=6.5, color=arrow_color_val_diana_func,
                                                      shrinkA=0.5, shrinkB=0.5, connectionstyle=f"arc3,rad={rad_recip_curve_diana_func}",
                                                      linestyle=line_style_arrow_diana_func, linewidth=lw_val_diana_func, alpha=alpha_val_diana_func),
                                      zorder=z_order_arrow_diana_func)
                ax_diana_img.annotate("", xy=(x_start_arrow_diana_func, y_start_arrow_diana_func), xytext=(x_end_arrow_diana_func, y_end_arrow_diana_func),
                                      arrowprops=dict(arrowstyle="-|>", mutation_scale=6.5, color=arrow_color_val_diana_func,
                                                      shrinkA=0.5, shrinkB=0.5, connectionstyle=f"arc3,rad={rad_recip_curve_diana_func}",
                                                      linestyle=line_style_arrow_diana_func, linewidth=lw_val_diana_func, alpha=alpha_val_diana_func),
                                      zorder=z_order_arrow_diana_func)
                drawn_bi_directional_arrows_pairs_diana_func.add(sorted_pair_key_diana_func)
            else:
                instance_count_this_edge_diana_func = edge_instance_counts_diana_func[(nominator_diana_func, nominee_diana_func)]
                rad_multi_edge_curve_diana_func = instance_count_this_edge_diana_func * 0.055 * (1 if instance_count_this_edge_diana_func % 2 == 0 else -1)
                if abs(rad_multi_edge_curve_diana_func) > 0.18: rad_multi_edge_curve_diana_func = 0.18 * np.sign(rad_multi_edge_curve_diana_func)
                connection_style_val_diana_func = f"arc3,rad={rad_multi_edge_curve_diana_func}"
                edge_instance_counts_diana_func[(nominator_diana_func, nominee_diana_func)] += 1
                ax_diana_img.annotate("", xy=(x_end_arrow_diana_func, y_end_arrow_diana_func), xytext=(x_start_arrow_diana_func, y_start_arrow_diana_func),
                                      arrowprops=dict(arrowstyle="-|>", mutation_scale=6.5, color=arrow_color_val_diana_func,
                                                      shrinkA=0.5, shrinkB=0.5, connectionstyle=connection_style_val_diana_func,
                                                      linestyle=line_style_arrow_diana_func, linewidth=lw_val_diana_func, alpha=alpha_val_diana_func),
                                      zorder=z_order_arrow_diana_func)

    ax_diana_img.set_title(f"Diana de Afinidad: {group_name}\n({institution_name})", fontsize=14, pad=20, weight='bold')
    
    legend_handles_grad_diana_func = [
        mpatches.Patch(facecolor=tuple(np.clip(color_centro_grad_bg*0.9 + color_borde_grad_bg*0.1,0,1)), edgecolor='black', lw=0.5, label="Puntaje Mayor (Centro Conceptual)"),
        mpatches.Patch(facecolor=tuple(np.clip(color_borde_grad_bg*0.9 + color_centro_grad_bg*0.1,0,1)), edgecolor='black', lw=0.5, label="Puntaje Menor (Periferia Conceptual)")
    ]
    ax_diana_img.legend(handles=legend_handles_grad_diana_func, title="Gradiente Popularidad",
                        loc='lower center', bbox_to_anchor=(0.5, -0.09), ncol=2,
                        fontsize='xx-small', title_fontsize='x-small', frameon=True, facecolor='#FFFFFFE8',
                        edgecolor='#BBBBBB', borderpad=0.35, labelspacing=0.55, handletextpad=0.35, columnspacing=1.0)
    
    legend_shapes_lines_diana_func = [
        mlines.Line2D([], [], color='black', marker='o', ls='None', ms=7, mfc='#ADD8E6', mec='#101010', label='Masculino'),
        mlines.Line2D([], [], color='black', marker='^', ls='None', ms=7, mfc='#FFC0CB', mec='#101010', label='Femenino'),
        mlines.Line2D([], [], color='black', marker='s', ls='None', ms=6, mfc='#A0E0A0', mec='#101010', label='Desconocido/Otro')
    ]
    if show_lines:
        legend_shapes_lines_diana_func.append(mlines.Line2D([0], [0], color='#404040', lw=0.65, ls='-', label='Elec. Unidireccional'))
        legend_shapes_lines_diana_func.append(mlines.Line2D([0], [0], color='#606060', lw=0.50, ls='--', label='Elec. Recíproca'))
    
    ax_legend2_diana_func = ax_diana_img.legend(handles=legend_shapes_lines_diana_func, title="Símbolos",
                                                loc='upper right', bbox_to_anchor=(1.14, 1.02),
                                                fontsize='xx-small', title_fontsize='x-small', frameon=True, facecolor='#FFFFF7E8',
                                                edgecolor='#BBBBBB', borderpad=0.35, labelspacing=0.55, handletextpad=0.35)
    ax_diana_img.add_artist(ax_legend2_diana_func)

    fig_diana_img.tight_layout(rect=[0, 0.06, 0.98, 0.92])

    buffer_diana_final_output = io.BytesIO()
    try:
        plt.savefig(buffer_diana_final_output, format='png', dpi=150)
        plt.close(fig_diana_img)
        buffer_diana_final_output.seek(0)
        # if registro_output and hasattr(registro_output, 'append_stdout'):
            # with registro_output: print(f"INFO (Diana Afinidad Matplotlib v1.22 - Sexo, Inst/Grp, Miembro): Imagen generada para {institution_name}/{group_name}.")
        return buffer_diana_final_output
    except Exception as e_save_img_diana_final_func:
        if registro_output and hasattr(registro_output, 'append_stdout'):
            with registro_output: print(f"ERROR (Diana Afinidad Matplotlib v1.22 - Sexo, Inst/Grp, Miembro): Al guardar imagen: {e_save_img_diana_final_func}\n{traceback.format_exc(limit=2)}")
        if 'fig_diana_img' in locals() and fig_diana_img is not None and plt is not None:
             try: plt.close(fig_diana_img)
             except Exception: pass
        return None
# --- FIN BLOQUE 7 ---