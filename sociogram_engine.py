# sociogram_engine.py
# (v1.9 - MultiDiGraph, corrección q_def en B1, Bloque 2 corregido, "miembro")

# --- Importaciones ---
import io
import base64 
import traceback
import collections
import json
import sys
import time 
import math

from IPython.display import display, clear_output, HTML as IPHTML, Javascript
from ipywidgets import widgets, Layout 

try:
    import ipycytoscape
    import networkx as nx 
    IPYCYTOSCAPE_AVAILABLE = True
except ImportError:
    print("ERROR CRÍTICO (sociogram_engine): ipycytoscape y/o networkx no están instalados.")
    ipycytoscape = None; nx = None
    IPYCYTOSCAPE_AVAILABLE = False

try:
    import pdf_generator 
except ImportError:
    print("ADVERTENCIA (sociogram_engine): No se pudo importar pdf_generator. Leyenda de flechas podría no tener imágenes.")
    pdf_generator = None

def draw_sociogramma(
    school_name, class_name,
    app_data_ref, 
    node_gender_filter='Todos',
    label_display_mode='nombre_apellido',
    selected_data_keys_from_checkboxes=None,
    connection_gender_type='todas',
    active_members_filter=False,
    nominators_option=False,
    nominators_color_filter=False, 
    received_color_filter=False,
    reciprocal_nodes_color_filter=False,
    style_reciprocal_links=False,
    selected_participant_focus=None,
    connection_focus_mode='all',
    ui_sociogramma_dict_ref=None,
    registro_output=None,
    layout_to_use='cose',
    highlight_mode='none',
    highlight_value=1
):
    # --- VALIDACIONES INICIALES Y CONFIGURACIÓN DE WIDGETS DE SALIDA ---
    if not ui_sociogramma_dict_ref or not isinstance(ui_sociogramma_dict_ref, dict):
        if registro_output and isinstance(registro_output, widgets.Output):
            with registro_output: print("ERROR (draw_sociogramma engine): ui_sociogramma_dict_ref no válido.")
        return None, None, None 
        
    sociogram_graph_output_widget = ui_sociogramma_dict_ref.get("graph_output")
    sociogram_legend_output_widget = ui_sociogramma_dict_ref.get("legend_output")

    if not sociogram_graph_output_widget or not isinstance(sociogram_graph_output_widget, widgets.Output):
        if registro_output and isinstance(registro_output, widgets.Output):
            with registro_output: print("ERROR (draw_sociogramma engine): graph_output widget no válido.")
        return None, None, None
        
    if not ui_sociogramma_dict_ref.get('_keep_output_for_pdf_prep', False):
        with sociogram_graph_output_widget: clear_output(wait=True)
        if sociogram_legend_output_widget and isinstance(sociogram_legend_output_widget, widgets.Output):
            with sociogram_legend_output_widget: clear_output(wait=True)

    if not IPYCYTOSCAPE_AVAILABLE or not ipycytoscape or not nx:
        if registro_output and isinstance(registro_output, widgets.Output):
            with registro_output: print("ERROR (draw_sociogramma engine): ipycytoscape o NetworkX no cargado.")
        if sociogram_graph_output_widget and isinstance(sociogram_graph_output_widget, widgets.Output):
             with sociogram_graph_output_widget: display(IPHTML("<p style='color:red;'>Error: Librerías de sociograma (ipycytoscape/NetworkX) no disponibles.</p>"))
        return None, None, None
        
    if not registro_output or not isinstance(registro_output, widgets.Output):
        registro_output = widgets.Output() 

    # with registro_output:
        # version_str = "Engine_v1.9_MultiDiGraph_Miembro"
        # print(f"\n--- DEBUG DRAW_SOCIOGRAMMA ({version_str}) ---")
        # print(f"  Parámetros Recibidos:")
        # print(f"    Institución: {school_name}, Grupo: {class_name}")
        # print(f"    Foco Participante: '{selected_participant_focus}', Modo Foco: '{connection_focus_mode}'")
        # print(f"    Selected Data Keys: {selected_data_keys_from_checkboxes}")

    cytoscape_widget_instance = None
    legend_info_final_for_display = {}
    graph_json_for_cytoscape = {'elements': {'nodes': [], 'edges': []}}

# === INICIO BLOQUE 1: OBTENCIÓN DE DATOS INICIALES Y CREACIÓN DE G_base ===
    if not app_data_ref or not hasattr(app_data_ref, 'members_data'):
        if registro_output:
            with registro_output: print("ERROR CRÍTICO (draw_sociogramma engine B1): app_data_ref o app_data_ref.members_data no accesible.")
        return None, None, None

    if not app_data_ref.members_data.get(school_name, {}).get(class_name):
        # if registro_output:
            # with registro_output: print(f"  INFO (draw_sociogramma engine B1): No hay datos de miembros para {school_name}/{class_name}.")
        return None, None, None
    
    members_list_for_class_base = app_data_ref.members_data[school_name][class_name]
    
    member_details_map = {}
    for m_detail_node in members_list_for_class_base:
        m_nome_titulo_node = m_detail_node.get('nome','').strip().title()
        m_cognome_titulo_node = m_detail_node.get('cognome','').strip().title()
        node_id_key_para_mapa_y_grafo = f"{m_nome_titulo_node} {m_cognome_titulo_node}".strip()
        if node_id_key_para_mapa_y_grafo:
             member_details_map[node_id_key_para_mapa_y_grafo] = m_detail_node
    
    if not member_details_map:
        # if registro_output:
            # with registro_output: print(f"  INFO (draw_sociogramma engine B1): member_details_map vacío para {school_name}/{class_name}.")
        return None, None, None

    G_base = nx.MultiDiGraph()
    nodes_added_to_gbase = 0

    for node_id_nombre_apellido, member_detail_data in member_details_map.items():
        sexo_val = member_detail_data.get('sexo', 'Desconocido')
        
        passes_filter = False
        if node_gender_filter == 'Todos': passes_filter = True
        elif node_gender_filter == 'Masculino' and sexo_val == 'Masculino': passes_filter = True
        elif node_gender_filter == 'Femenino' and sexo_val == 'Femenino': passes_filter = True
        elif node_gender_filter == 'Desconocido' and sexo_val not in ['Masculino', 'Femenino']: passes_filter = True
        
        if passes_filter:
            G_base.add_node(
                node_id_nombre_apellido,
                id=node_id_nombre_apellido,
                sexo_attr=sexo_val,
                iniz=member_detail_data.get('iniz', 'N/A'),
                original_nome=member_detail_data.get('nome','').strip(),
                original_cognome=member_detail_data.get('cognome','').strip()
            )
            nodes_added_to_gbase += 1

    if not G_base.nodes():
        # if registro_output:
            # with registro_output: print(f"  INFO (draw_sociogramma engine B1): Grafo base (G_base) sin nodos después del filtro. Nodos procesados: {nodes_added_to_gbase}")
        return None, None, None
    # with registro_output:
        # print(f"  DEBUG ENGINE B1: G_base ({type(G_base)}) creado con {nodes_added_to_gbase} nodos (ID: \"Nombre Apellido\").")

    G_nodes_pre_activity_filter = G_base.copy()
    if active_members_filter:
        temp_G_edges_for_activity = nx.MultiDiGraph()
        for n_act_filter, d_act_filter in G_base.nodes(data=True):
            temp_G_edges_for_activity.add_node(n_act_filter, **d_act_filter)

        for nominator_fn_active in G_base.nodes():
            responses_for_activity_check = app_data_ref.questionnaire_responses_data.get((school_name, class_name, nominator_fn_active), {})
            for iter_q_data_key_active, nominated_list_active in responses_for_activity_check.items():
                if not selected_data_keys_from_checkboxes or iter_q_data_key_active not in selected_data_keys_from_checkboxes:
                    continue
                for nominated_n_active in nominated_list_active:
                    if nominated_n_active in G_base.nodes():
                        temp_G_edges_for_activity.add_edge(nominator_fn_active, nominated_n_active)
        
        active_member_nodes = set()
        if temp_G_edges_for_activity.nodes():
            active_member_nodes = {
                n_a for n_a in G_base.nodes()
                if temp_G_edges_for_activity.out_degree(n_a) > 0 and \
                   any(n_a != t for _, t in temp_G_edges_for_activity.out_edges(n_a))
            }
        nodes_to_remove_activity = [n_r for n_r in list(G_nodes_pre_activity_filter.nodes()) if n_r not in active_member_nodes]
        G_nodes_pre_activity_filter.remove_nodes_from(nodes_to_remove_activity)
        # with registro_output:
            # print(f"  DEBUG ENGINE B1: Filtro de miembros activos aplicado. Nodos restantes en G_nodes_pre_activity_filter: {len(G_nodes_pre_activity_filter.nodes())}")

    if not G_nodes_pre_activity_filter.nodes():
        # if registro_output:
            # with registro_output: print(f"  INFO (draw_sociogramma engine B1): Grafo sin nodos después del filtro de miembros activos.")
        return None, None, None

    G_with_edges_full = G_nodes_pre_activity_filter.copy()
    actual_edges_added_count = 0
    
    if selected_data_keys_from_checkboxes:
        class_questions_local_b1 = app_data_ref.get_class_question_definitions(school_name, class_name)
        
        for nominator_full_name_main_loop in list(G_with_edges_full.nodes()):
            member_responses_for_current_nominator = app_data_ref.questionnaire_responses_data.get(
                (school_name, class_name, nominator_full_name_main_loop), {}
            )
            if not member_responses_for_current_nominator: continue
            
            for current_question_data_key, nominated_names_list in member_responses_for_current_nominator.items():
                if current_question_data_key not in selected_data_keys_from_checkboxes: continue
                
                q_def_for_edge_b1 = {}
                if class_questions_local_b1:
                    for qid_lookup, q_def_lookup in class_questions_local_b1.items():
                        if q_def_lookup.get('data_key') == current_question_data_key:
                            q_def_for_edge_b1 = q_def_lookup; break
                
                for election_index, nominated_name in enumerate(nominated_names_list):
                    if nominated_name in G_with_edges_full.nodes():
                        nominator_node_data = G_with_edges_full.nodes[nominator_full_name_main_loop]
                        nominated_node_data = G_with_edges_full.nodes[nominated_name]
                        
                        nominator_sexo_val = nominator_node_data.get('sexo_attr', 'Desconocido')
                        nominated_sexo_val = nominated_node_data.get('sexo_attr', 'Desconocido')
                        
                        passes_conn_sexo = (connection_gender_type == 'todas') or \
                                             (connection_gender_type == 'mismo_genero' and nominator_sexo_val != 'Desconocido' and nominator_sexo_val == nominated_sexo_val) or \
                                             (connection_gender_type == 'diferente_genero' and nominator_sexo_val != 'Desconocido' and nominated_sexo_val != 'Desconocido' and nominator_sexo_val != nominated_sexo_val)
                        if passes_conn_sexo:
                            G_with_edges_full.add_edge(
                                nominator_full_name_main_loop, nominated_name,
                                relation_data_key=current_question_data_key,
                                election_index=election_index,
                                polarity=q_def_for_edge_b1.get('polarity', 'neutral')
                            )
                            actual_edges_added_count += 1
    # else:
        # if registro_output:
            # with registro_output: print("  INFO (draw_sociogramma engine B1): No hay data_keys seleccionados, no se añadirán aristas.")

    G = G_with_edges_full.copy()
    # with registro_output:
        # print(f"  DEBUG ENGINE B1 (FINAL): G_base ({type(G_base)}) tiene {len(G_base.nodes())}N.")
        # print(f"  DEBUG ENGINE B1 (FINAL): G_nodes_pre_activity_filter tiene {len(G_nodes_pre_activity_filter.nodes())}N.")
        # print(f"  DEBUG ENGINE B1 (FINAL): G_with_edges_full (y G inicial) ({type(G)}) tiene {len(G.nodes())}N, {len(G.edges())}A (Contador aristas: {actual_edges_added_count}).")
        # if len(G.edges()) > 0:
            # first_edge_example_data = list(G.edges(keys=True, data=True))[0] if G.is_multigraph() else list(G.edges(data=True))[0]
            # print(f"    DEBUG ENGINE B1 (FINAL): Ejemplo primera arista en G: {first_edge_example_data}")
        # elif actual_edges_added_count == 0 and selected_data_keys_from_checkboxes :
             # print(f"    ADVERTENCIA ENGINE B1 (FINAL): Se seleccionaron data_keys pero no se añadieron aristas.")
# === FIN BLOQUE 1 ===
# === INICIO BLOQUE 2: LÓGICA DE FOCO Y RECIPROCIDAD ===
    focus_participant_node = None
    focus_connected_nodes_overall = set()
    specific_focus_target_nodes = set()
    focus_outgoing_edges_tuples = set()
    focus_incoming_edges_tuples = set()
    is_focus_active = bool(selected_participant_focus and selected_participant_focus in G.nodes())

    if is_focus_active:
        focus_participant_node = selected_participant_focus
        for u_focus, target_node_focus, k_focus, data_focus in G.out_edges(selected_participant_focus, keys=True, data=True):
            focus_outgoing_edges_tuples.add((u_focus, target_node_focus))
            focus_connected_nodes_overall.add(target_node_focus)
        for source_node_focus, v_focus, k_focus, data_focus in G.in_edges(selected_participant_focus, keys=True, data=True):
            focus_incoming_edges_tuples.add((source_node_focus, v_focus))
            focus_connected_nodes_overall.add(source_node_focus)
        if connection_focus_mode == 'outgoing':
            specific_focus_target_nodes.update(t for _, t in focus_outgoing_edges_tuples)
        elif connection_focus_mode == 'incoming':
            specific_focus_target_nodes.update(s for s, _ in focus_incoming_edges_tuples)
        elif connection_focus_mode == 'all':
            specific_focus_target_nodes = focus_connected_nodes_overall.copy()
        
        # if registro_output and isinstance(registro_output, widgets.Output):
            # with registro_output:
                # print(f"  DEBUG ENGINE B2 (FOCO): Foco activo en '{focus_participant_node}'.")
                # print(f"    Tuplas de aristas salientes del Foco (pares u,v únicos): {len(focus_outgoing_edges_tuples)}")
                # print(f"    Tuplas de aristas entrantes al Foco (pares u,v únicos): {len(focus_incoming_edges_tuples)}")
                # print(f"    Nodos objetivo específicos para modo foco '{connection_focus_mode}': {len(specific_focus_target_nodes)}")

    edges_processed_for_reciprocity = 0
    for u_attr, v_attr, key_attr, data_attr in G.edges(keys=True, data=True):
        relation_uv_attr = data_attr.get('relation_data_key')
        is_truly_reciprocal_in_full_attr = False
        idx_vu_for_style_calc = float('inf')
        if G_with_edges_full.has_edge(v_attr, u_attr):
            for _, target_node_of_v, key_vu_full, data_vu_full_attr in G_with_edges_full.out_edges(v_attr, keys=True, data=True):
                if target_node_of_v == u_attr:
                    if data_vu_full_attr and data_vu_full_attr.get('relation_data_key') == relation_uv_attr:
                        is_truly_reciprocal_in_full_attr = True
                        idx_vu_for_style_calc = data_vu_full_attr.get('election_index', float('inf'))
                        break
        G.edges[u_attr, v_attr, key_attr]['is_truly_reciprocal_in_full'] = is_truly_reciprocal_in_full_attr
        if is_truly_reciprocal_in_full_attr:
            idx_uv_attr = data_attr.get('election_index', float('inf'))
            G.edges[u_attr, v_attr, key_attr]['election_index_for_style'] = max(idx_uv_attr, idx_vu_for_style_calc)
        else:
            G.edges[u_attr, v_attr, key_attr]['election_index_for_style'] = data_attr.get('election_index', 0)
        edges_processed_for_reciprocity +=1
    
    # if registro_output and isinstance(registro_output, widgets.Output):
        # with registro_output:
            # print(f"  DEBUG ENGINE B2 (RECIPROCIDAD): {edges_processed_for_reciprocity} aristas individuales procesadas para atributos de reciprocidad.")

    nodes_before_isolate_filter = len(G.nodes())
    if not nominators_option:
        isolated_nodes = list(nx.isolates(G)) 
        nodes_to_remove_isolated_final = [n for n in isolated_nodes if not (is_focus_active and n == focus_participant_node)]
        if nodes_to_remove_isolated_final:
            G.remove_nodes_from(nodes_to_remove_isolated_final)
            # if registro_output and isinstance(registro_output, widgets.Output):
                 # with registro_output: print(f"  DEBUG ENGINE B2 (AISLADOS): Filtro Aislados (nominators_option=False) quitó {len(nodes_to_remove_isolated_final)} nodos. Nodos restantes en G: {len(G.nodes())}.")
        # else:
            # if registro_output and isinstance(registro_output, widgets.Output):
                 # with registro_output: print(f"  DEBUG ENGINE B2 (AISLADOS): Filtro Aislados (nominators_option=False) no quitó nodos. Nodos en G: {len(G.nodes())}.")
        if is_focus_active:
            specific_focus_target_nodes.difference_update(nodes_to_remove_isolated_final)
            focus_connected_nodes_overall.difference_update(nodes_to_remove_isolated_final)
    # else:
        # if registro_output and isinstance(registro_output, widgets.Output):
            # with registro_output: print(f"  DEBUG ENGINE B2 (AISLADOS): nominators_option=True, no se aplica filtro de aislados. Nodos en G: {len(G.nodes())}.")

    if not G.nodes(): 
      if registro_output and isinstance(registro_output, widgets.Output):
          with registro_output: print(f"  INFO (draw_sociogramma engine B2): Grafo G sin nodos después de filtro de nominators/aislados.");
      return None, None, None 
# === FIN BLOQUE 2 ===

# === INICIO BLOQUE 3: CÁLCULO DE LÍDERES Y ROLES DE NODOS PARA COLOREADO ===
    if not hasattr(app_data_ref, 'get_class_question_definitions'):
        if registro_output and isinstance(registro_output, widgets.Output): 
            with registro_output: print("ERROR CRÍTICO (draw_sociogramma engine B3): app_data_ref.get_class_question_definitions no accesible.")
        class_questions = {} 
    else:
        class_questions = app_data_ref.get_class_question_definitions(school_name, class_name)
    
    # if registro_output and isinstance(registro_output, widgets.Output):
        # with registro_output:
            # print(f"  DEBUG ENGINE B3 (LIDERES): Obtenidas {len(class_questions)} definiciones de preguntas para {school_name}/{class_name}.")

    positive_data_keys = {
        q_def.get('data_key')
        for q_id, q_def in class_questions.items() 
        if q_def.get('polarity') == 'positive' and q_def.get('data_key')
    }
    # if registro_output and isinstance(registro_output, widgets.Output):
        # with registro_output:
            # print(f"  DEBUG ENGINE B3 (LIDERES): Data keys positivos identificados: {positive_data_keys}")

    leader_scores = collections.defaultdict(int)
    first_choice_counts = collections.defaultdict(int)
    
    for u_leader_score, v_leader_score, data_leader_score_dict in G_with_edges_full.edges(data=True):
        if v_leader_score not in G.nodes(): 
            continue
        relation_key_leader = data_leader_score_dict.get('relation_data_key')
        election_idx_leader = data_leader_score_dict.get('election_index')
        if relation_key_leader in positive_data_keys:
            leader_scores[v_leader_score] += 1
            if election_idx_leader == 0: 
                first_choice_counts[v_leader_score] += 1
    
    processed_leader_scores_list = [
        {'name': n_name, 'score': leader_scores.get(n_name, 0), 'first_choices': first_choice_counts.get(n_name, 0)}
        for n_name in G.nodes() 
    ]
    sorted_leaders_details_list = sorted(
        processed_leader_scores_list,
        key=lambda item: (item['score'], item['first_choices']),
        reverse=True
    )

    leaders_to_highlight_names_list = []
    if highlight_mode == 'top_n' and highlight_value > 0:
        leaders_to_highlight_names_list = [ld['name'] for ld in sorted_leaders_details_list[:int(highlight_value)]]
    elif highlight_mode == 'k_th' and 1 <= int(highlight_value) <= len(sorted_leaders_details_list):
        leaders_to_highlight_names_list = [sorted_leaders_details_list[int(highlight_value)-1]['name']]
    
    # if registro_output and isinstance(registro_output, widgets.Output):
        # with registro_output:
            # print(f"  DEBUG ENGINE B3 (LIDERES): Líderes a resaltar (highlight_mode='{highlight_mode}', value={highlight_value}): {leaders_to_highlight_names_list}")

    color_leader_val = 'gold'
    color_not_chosen_val = 'silver'
    color_gender_male = 'skyblue'
    color_gender_female = 'lightcoral'
    color_gender_unknown = 'limegreen'
    highlight_focus_participant_color_val = 'darkorange' 
    highlight_focus_connected_color_val = '#FFDB58'    
    opacity_default_val = 1.0
    opacity_dimmed_node_val = 0.15 
    opacity_dimmed_edge_val = 0.08 

    nodes_not_chosen_role_set = set()
    nominators_active_role_set = set() 
    receivers_only_or_self_role_set = set()
    nodes_in_reciprocal_relation_role_set = set()

    if G_with_edges_full.nodes(): 
        in_degrees_for_roles_full = dict(G_with_edges_full.in_degree(weight=None)) 
        nodes_not_chosen_role_set = {
            n_role for n_role, deg_role in in_degrees_for_roles_full.items()
            if deg_role == 0 and n_role in G.nodes() 
        }
        for node_role_iter in G.nodes(): 
            if node_role_iter not in G_with_edges_full.nodes(): continue 
            
            if G_with_edges_full.out_degree(node_role_iter) > 0 and \
               any(node_role_iter != target_role for _, target_role in G_with_edges_full.out_edges(node_role_iter)): 
                nominators_active_role_set.add(node_role_iter)
            
            is_receiver_only_or_self_in_full = True
            if G_with_edges_full.out_degree(node_role_iter) > 0:
                is_receiver_only_or_self_in_full = all(node_role_iter == target_role for _, target_role in G_with_edges_full.out_edges(node_role_iter))
            
            if is_receiver_only_or_self_in_full: 
                receivers_only_or_self_role_set.add(node_role_iter)

        temp_processed_recip_nodes_for_coloring_set = set()
        for u_r_recip, v_r_recip, k_r_recip, data_uv_r_recip_dict in G_with_edges_full.edges(keys=True, data=True):
            if u_r_recip not in G.nodes() or v_r_recip not in G.nodes(): 
                continue 
            
            rel_uv_r_recip = data_uv_r_recip_dict.get('relation_data_key')
            pair_key_r_recip_tuple = tuple(sorted((u_r_recip,v_r_recip))) + (rel_uv_r_recip,) 
            if pair_key_r_recip_tuple in temp_processed_recip_nodes_for_coloring_set:
                continue 

            if G_with_edges_full.has_edge(v_r_recip, u_r_recip):
                for _, target_node_of_v_recip, key_vu_full_recip, data_vu_full_recip_dict in G_with_edges_full.out_edges(v_r_recip, keys=True, data=True):
                    if target_node_of_v_recip == u_r_recip:
                        if data_vu_full_recip_dict and data_vu_full_recip_dict.get('relation_data_key') == rel_uv_r_recip:
                            nodes_in_reciprocal_relation_role_set.add(u_r_recip)
                            nodes_in_reciprocal_relation_role_set.add(v_r_recip)
                            temp_processed_recip_nodes_for_coloring_set.add(pair_key_r_recip_tuple)
                            break
    
    # if registro_output and isinstance(registro_output, widgets.Output):
        # with registro_output:
            # print(f"  DEBUG ENGINE B3 (ROLES): Nodos 'No Elegidos' (en G): {len(nodes_not_chosen_role_set)}")
            # print(f"  DEBUG ENGINE B3 (ROLES): Nodos 'Solo Reciben/AutoNomina' (en G): {len(receivers_only_or_self_role_set)}")
            # print(f"  DEBUG ENGINE B3 (ROLES): Nodos 'En Relación Recíproca' (en G): {len(nodes_in_reciprocal_relation_role_set)}")

# === FIN BLOQUE 3 ===
# === INICIO BLOQUE 4: APLICACIÓN DE ESTILOS A NODOS ===
    nodes_styled_count = 0
    # if registro_output and isinstance(registro_output, widgets.Output):
        # with registro_output:
            # print(f"  DEBUG ENGINE B4 (STYLE_NODE_PRE): Iniciando estilos para {len(G.nodes())} nodos.")

    for node_name_final_style, node_data_dict_style in G.nodes(data=True):
        sexo_estilo = node_data_dict_style.get('sexo_attr', 'Desconocido')
        
        base_node_color_style = color_gender_unknown
        node_shape_style = 'square'
        if sexo_estilo == 'Masculino':
            base_node_color_style = color_gender_male
            node_shape_style = 'ellipse'
        elif sexo_estilo == 'Femenino':
            base_node_color_style = color_gender_female
            node_shape_style = 'triangle'

        current_node_color_style = base_node_color_style
        node_opacity_style = opacity_default_val
        node_classes_cytoscape_list = []
        is_styled_by_priority_rule = False

        if is_focus_active:
            if node_name_final_style == focus_participant_node:
                current_node_color_style = highlight_focus_participant_color_val
                node_classes_cytoscape_list.append('focus_node_selected')
                is_styled_by_priority_rule = True
            elif node_name_final_style in specific_focus_target_nodes:
                current_node_color_style = highlight_focus_connected_color_val
                node_classes_cytoscape_list.append('focus_node_connected')
                is_styled_by_priority_rule = True
            else:
                node_opacity_style = opacity_dimmed_node_val
                node_classes_cytoscape_list.append('dimmed_node')
        
        if not is_styled_by_priority_rule and leaders_to_highlight_names_list and node_name_final_style in leaders_to_highlight_names_list:
            current_node_color_style = color_leader_val
            node_opacity_style = opacity_default_val
            if 'dimmed_node' in node_classes_cytoscape_list:
                node_classes_cytoscape_list.remove('dimmed_node')
            node_classes_cytoscape_list.append('leader_node')
            is_styled_by_priority_rule = True
        
        if not is_styled_by_priority_rule:
            applied_role_color_this_node = False
            if nominators_option and node_name_final_style in nodes_not_chosen_role_set:
                current_node_color_style = color_not_chosen_val
                applied_role_color_this_node = True
            if received_color_filter and node_name_final_style in receivers_only_or_self_role_set:
                current_node_color_style = 'lightsalmon'
                applied_role_color_this_node = True
            if reciprocal_nodes_color_filter and node_name_final_style in nodes_in_reciprocal_relation_role_set:
                current_node_color_style = 'mediumpurple'
                applied_role_color_this_node = True
            if applied_role_color_this_node and 'dimmed_node' not in node_classes_cytoscape_list:
                 node_opacity_style = opacity_default_val

        G.nodes[node_name_final_style]['node_color'] = current_node_color_style
        G.nodes[node_name_final_style]['node_opacity'] = node_opacity_style
        G.nodes[node_name_final_style]['node_shape_attr'] = node_shape_style
        G.nodes[node_name_final_style]['classes_cytoscape'] = ' '.join(node_classes_cytoscape_list) if node_classes_cytoscape_list else ''

        label_text_node = node_name_final_style
        original_nome_from_node = node_data_dict_style.get('original_nome', '')
        original_cognome_from_node = node_data_dict_style.get('original_cognome', '')

        if label_display_mode == 'nombre_apellido':
            label_text_node = f"{original_nome_from_node[:1]}. {original_cognome_from_node.title()}"
        elif label_display_mode == 'iniciales':
            label_text_node = node_data_dict_style.get('iniz', 'N/A')
        elif label_display_mode == 'anonimo':
            try:
                node_idx_val_label = list(G.nodes()).index(node_name_final_style) + 1
            except ValueError:
                node_idx_val_label = "?"
            label_text_node = f"ID {node_idx_val_label}"
        
        G.nodes[node_name_final_style]['label_to_display'] = label_text_node.strip()
        nodes_styled_count +=1

    # if registro_output and isinstance(registro_output, widgets.Output):
        # with registro_output:
            # print(f"  DEBUG ENGINE B4 (STYLE_NODE_POST): Estilos aplicados a {nodes_styled_count} nodos.")
            # if G.nodes() and nodes_styled_count > 0:
                # first_node_name_b4_post = list(G.nodes())[0]
            # elif not G.nodes():
                # print(f"    INFO ENGINE B4 (STYLE_NODE_POST): No hay nodos en G para estilizar.")
# === FIN BLOQUE 4 ===

# === INICIO BLOQUE 5: DEFINICIÓN DE COLORES/ESTILOS PARA ARISTAS Y LEYENDA ===
    legend_info_final_for_display = {"node_colors": {}, "edge_styles": {}, "widths": {}}
    max_possible_width = 3.5
    min_possible_width = 1.0
    width_decrement = 1.0
    legend_widths_count = 0
    for i_w in range(int(max_possible_width / width_decrement) if width_decrement > 0 else 1):
         w_val = max(min_possible_width, max_possible_width - (i_w * width_decrement))
         if w_val >= min_possible_width :
             legend_info_final_for_display["widths"][f"Elección {i_w+1}"] = f"{w_val:.1f}px"
             legend_widths_count +=1
    # if registro_output and isinstance(registro_output, widgets.Output):
        # with registro_output:
            # print(f"  DEBUG ENGINE B5 (LEGEND_WIDTHS): {legend_widths_count} entradas de grosor generadas para la leyenda.")

    selected_question_details_for_legend_list = []
    current_selected_data_keys_for_legend_calc = selected_data_keys_from_checkboxes if selected_data_keys_from_checkboxes is not None else []
    if current_selected_data_keys_for_legend_calc:
        for data_key_leg_iter in current_selected_data_keys_for_legend_calc:
            q_def_dict_leg_iter = None
            if class_questions and isinstance(class_questions, dict):
                q_def_dict_leg_iter = next(
                    (qd_dict for qid, qd_dict in class_questions.items() if qd_dict.get('data_key') == data_key_leg_iter), None
                )
            if q_def_dict_leg_iter:
                label_for_legend_val_iter = data_key_leg_iter 
                if hasattr(app_data_ref, 'sociogram_relation_options_map'):
                    label_for_legend_val_iter = app_data_ref.sociogram_relation_options_map.get(data_key_leg_iter, data_key_leg_iter)
                elif registro_output and isinstance(registro_output, widgets.Output):
                    with registro_output: print(f"ADVERTENCIA (draw_sociogramma engine B5 LEGEND): app_data_ref.sociogram_relation_options_map no accesible para data_key {data_key_leg_iter}")
                
                selected_question_details_for_legend_list.append({
                    'data_key': data_key_leg_iter,
                    'polarity': q_def_dict_leg_iter.get('polarity', 'neutral'),
                    'label_for_legend': label_for_legend_val_iter
                })
            elif registro_output and isinstance(registro_output, widgets.Output):
                 with registro_output: print(f"ADVERTENCIA (draw_sociogramma engine B5 LEGEND): No se encontró q_def para data_key {data_key_leg_iter} en class_questions.")
    
    # if registro_output and isinstance(registro_output, widgets.Output):
        # with registro_output:
            # print(f"  DEBUG ENGINE B5 (SELECTED_Q_DETAILS): {len(selected_question_details_for_legend_list)} detalles de preguntas seleccionadas para leyenda.")

    special_positive_color = '#28a745'; special_negative_color = '#dc3545'
    edge_color_palette = ['#007bff','#6c757d','#17a2b8','#ffc107','#fd7e14','#6610f2','#e83e8c']
    focus_outgoing_edge_color_val = '#32CD32'; focus_incoming_edge_color_val = '#1E90FF'; focus_reciprocal_edge_color_val = '#FF8C00'
    focus_outgoing_arrow_shape_val = 'chevron'; focus_incoming_arrow_shape_val = 'triangle'; focus_reciprocal_arrow_shape_val = 'diamond'
    
    data_key_to_color_map_edges = {}
    is_special_pos_neg_case_legend = False
    if len(selected_question_details_for_legend_list) == 2:
        polarities_in_selection_legend = {details['polarity'] for details in selected_question_details_for_legend_list}
        if 'positive' in polarities_in_selection_legend and 'negative' in polarities_in_selection_legend and len(polarities_in_selection_legend) == 2:
            is_special_pos_neg_case_legend = True
    
    # if registro_output and isinstance(registro_output, widgets.Output):
        # with registro_output:
            # print(f"  DEBUG ENGINE B5 (EDGE_COLORS): is_special_pos_neg_case_legend = {is_special_pos_neg_case_legend}")

    edge_styles_for_legend_dict = legend_info_final_for_display["edge_styles"]

    if is_special_pos_neg_case_legend:
        for details_leg_item in selected_question_details_for_legend_list:
            data_key_leg_color = details_leg_item['data_key']
            polarity_leg_color = details_leg_item['polarity']
            label_legend_color = details_leg_item['label_for_legend']
            color_to_assign_leg_map = special_positive_color if polarity_leg_color == 'positive' else special_negative_color
            data_key_to_color_map_edges[data_key_leg_color] = color_to_assign_leg_map
            edge_styles_for_legend_dict[label_legend_color] = {
                'color': color_to_assign_leg_map, 'base_line_style': 'solid',
                'base_arrow_shape': 'triangle', 'can_be_reciprocal_styled': True, 'is_focus': False
            }
    else:
        color_idx_leg_map = 0
        palette_to_use_leg_map = [c for c in edge_color_palette if c not in [special_positive_color, special_negative_color]]
        if not palette_to_use_leg_map: palette_to_use_leg_map = edge_color_palette
        
        for details_leg_item in selected_question_details_for_legend_list:
            data_key_leg_color = details_leg_item['data_key']
            label_legend_color = details_leg_item['label_for_legend']
            assigned_color_leg_map = palette_to_use_leg_map[color_idx_leg_map % len(palette_to_use_leg_map)]
            data_key_to_color_map_edges[data_key_leg_color] = assigned_color_leg_map
            edge_styles_for_legend_dict[label_legend_color] = {
                'color': assigned_color_leg_map, 'base_line_style': 'solid',
                'base_arrow_shape': 'triangle', 'can_be_reciprocal_styled': True, 'is_focus': False
            }
            color_idx_leg_map += 1
    
    if is_focus_active:
        edge_styles_for_legend_dict["Saliente de Foco"] = {
            'color': focus_outgoing_edge_color_val, 'base_line_style': 'dotted',
            'base_arrow_shape': focus_outgoing_arrow_shape_val, 'can_be_reciprocal_styled': False, 'is_focus': True
        }
        edge_styles_for_legend_dict["Entrante a Foco"] = {
            'color': focus_incoming_edge_color_val, 'base_line_style': 'dotted',
            'base_arrow_shape': focus_incoming_arrow_shape_val, 'can_be_reciprocal_styled': False, 'is_focus': True
        }
        if connection_focus_mode == 'all':
            edge_styles_for_legend_dict["Recíproca con Foco"] = {
                'color': focus_reciprocal_edge_color_val, 'base_line_style': 'dotted',
                'base_arrow_shape': focus_reciprocal_arrow_shape_val,
                'source_arrow_shape': focus_reciprocal_arrow_shape_val,
                'can_be_reciprocal_styled': False, 'is_focus': True
            }
            
    # if registro_output and isinstance(registro_output, widgets.Output):
        # with registro_output:
            # print(f"  DEBUG ENGINE B5 (LEGEND_FINAL): data_key_to_color_map_edges: {data_key_to_color_map_edges}")
            # print(f"  DEBUG ENGINE B5 (LEGEND_FINAL): {len(edge_styles_for_legend_dict)} estilos de arista definidos para la leyenda.")
# === FIN BLOQUE 5 ===

# === INICIO BLOQUE 6: APLICACIÓN DE ESTILOS A ARISTAS ===
    edges_styled_count = 0
    for u_edge_style, v_edge_style, key_edge_style, edge_data_style_dict in G.edges(keys=True, data=True):
        edge_tuple_style = (u_edge_style, v_edge_style)
        current_election_index_for_width = edge_data_style_dict.get('election_index_for_style', 0)
        edge_width_px_value = max(min_possible_width, max_possible_width - (current_election_index_for_width * width_decrement))
        G.edges[u_edge_style, v_edge_style, key_edge_style]['edge_width_attr'] = f"{edge_width_px_value:.1f}px"
        edge_relation_key_style = edge_data_style_dict.get('relation_data_key')
        final_edge_color_style = data_key_to_color_map_edges.get(edge_relation_key_style, '#AAAAAA') 
        final_edge_opacity_style = opacity_default_val 
        final_line_style_edge = 'solid' 
        final_target_arrow_style = 'triangle' 
        final_source_arrow_style = 'none' 
        final_edge_classes_list = []
        is_truly_reciprocal_edge_style = edge_data_style_dict.get('is_truly_reciprocal_in_full', False) 
        is_styled_by_focus_this_edge = False 
        if is_focus_active: 
            is_outgoing_direct_this_edge = edge_tuple_style in focus_outgoing_edges_tuples 
            is_incoming_direct_this_edge = edge_tuple_style in focus_incoming_edges_tuples 
            is_reciprocal_with_focus_this_edge = False
            if is_truly_reciprocal_edge_style:
                if u_edge_style == focus_participant_node and (v_edge_style, u_edge_style) in focus_incoming_edges_tuples:
                    is_reciprocal_with_focus_this_edge = True
                elif v_edge_style == focus_participant_node and (u_edge_style, v_edge_style) in focus_incoming_edges_tuples:
                     if (v_edge_style, u_edge_style) in focus_outgoing_edges_tuples:
                        is_reciprocal_with_focus_this_edge = True
            if connection_focus_mode == 'all':
                if is_reciprocal_with_focus_this_edge:
                    final_edge_color_style = focus_reciprocal_edge_color_val 
                    final_line_style_edge = 'dotted'
                    final_target_arrow_style = focus_reciprocal_arrow_shape_val 
                    final_source_arrow_style = focus_reciprocal_arrow_shape_val 
                    final_edge_classes_list.append('focus_edge_reciprocal')
                    is_styled_by_focus_this_edge = True
                elif is_outgoing_direct_this_edge:
                    final_edge_color_style = focus_outgoing_edge_color_val 
                    final_line_style_edge = 'dotted'
                    final_target_arrow_style = focus_outgoing_arrow_shape_val 
                    final_edge_classes_list.append('focus_edge_outgoing')
                    is_styled_by_focus_this_edge = True
                elif is_incoming_direct_this_edge:
                    final_edge_color_style = focus_incoming_edge_color_val 
                    final_line_style_edge = 'dotted'
                    final_target_arrow_style = focus_incoming_arrow_shape_val 
                    final_edge_classes_list.append('focus_edge_incoming')
                    is_styled_by_focus_this_edge = True
            elif connection_focus_mode == 'outgoing' and is_outgoing_direct_this_edge:
                    final_edge_color_style = focus_outgoing_edge_color_val
                    final_line_style_edge = 'dotted'
                    final_target_arrow_style = focus_outgoing_arrow_shape_val
                    final_edge_classes_list.append('focus_edge_outgoing')
                    is_styled_by_focus_this_edge = True
            elif connection_focus_mode == 'incoming' and is_incoming_direct_this_edge:
                    final_edge_color_style = focus_incoming_edge_color_val
                    final_line_style_edge = 'dotted'
                    final_target_arrow_style = focus_incoming_arrow_shape_val
                    final_edge_classes_list.append('focus_edge_incoming')
                    is_styled_by_focus_this_edge = True
            if not is_styled_by_focus_this_edge:
                final_edge_opacity_style = opacity_dimmed_edge_val 
                final_edge_classes_list.append('dimmed_edge')
                if style_reciprocal_links and is_truly_reciprocal_edge_style and connection_focus_mode == 'all':
                     final_source_arrow_style = 'triangle' 
                     final_line_style_edge = 'dashed' 
        elif style_reciprocal_links and is_truly_reciprocal_edge_style: 
            final_source_arrow_style = 'triangle' 
            final_line_style_edge = 'dashed' 
        G.edges[u_edge_style, v_edge_style, key_edge_style]['edge_color'] = final_edge_color_style
        G.edges[u_edge_style, v_edge_style, key_edge_style]['edge_opacity'] = final_edge_opacity_style
        G.edges[u_edge_style, v_edge_style, key_edge_style]['edge_line_style'] = final_line_style_edge
        G.edges[u_edge_style, v_edge_style, key_edge_style]['target_arrow_shape_attr'] = final_target_arrow_style
        G.edges[u_edge_style, v_edge_style, key_edge_style]['source_arrow_shape_attr'] = final_source_arrow_style
        G.edges[u_edge_style, v_edge_style, key_edge_style]['classes_cytoscape'] = ' '.join(final_edge_classes_list) if final_edge_classes_list else ''
        edges_styled_count +=1
    # if registro_output and isinstance(registro_output, widgets.Output):
        # with registro_output:
            # print(f"  DEBUG ENGINE B6 (STYLE_EDGE_POST): Estilos aplicados a {edges_styled_count} aristas individuales.")
# === FIN BLOQUE 6 ===
# === INICIO BLOQUE 7: PREPARACIÓN DE G_to_render Y CREACIÓN DEL WIDGET CYTOSCAPE ===
    G_to_render = G.copy() 
    if is_focus_active and connection_focus_mode in ['outgoing', 'incoming']:
        # if registro_output and isinstance(registro_output, widgets.Output):
            # with registro_output:
                # print(f"  DEBUG ENGINE B7 (G_TO_RENDER_PRE): Modo foco direccional '{connection_focus_mode}' activo. Filtrando G_to_render...")
        G_focus_strict = nx.MultiDiGraph() if isinstance(G, nx.MultiDiGraph) else nx.DiGraph()
        nodes_for_strict_focus_view = {focus_participant_node}.union(specific_focus_target_nodes)
        nodes_added_to_focus_strict = 0
        for node_id_strict, node_data_strict in G.nodes(data=True):
            if node_id_strict in nodes_for_strict_focus_view:
                G_focus_strict.add_node(node_id_strict, **node_data_strict)
                G_focus_strict.nodes[node_id_strict]['node_opacity'] = opacity_default_val 
                if 'dimmed_node' in G_focus_strict.nodes[node_id_strict].get('classes_cytoscape', ''):
                    G_focus_strict.nodes[node_id_strict]['classes_cytoscape'] = G_focus_strict.nodes[node_id_strict]['classes_cytoscape'].replace('dimmed_node', '').strip()
                nodes_added_to_focus_strict += 1
            else: 
                G_focus_strict.add_node(node_id_strict, **node_data_strict) 
                G_focus_strict.nodes[node_id_strict]['node_opacity'] = opacity_dimmed_node_val 
                G_focus_strict.nodes[node_id_strict]['node_color'] = "lightgrey" 
                G_focus_strict.nodes[node_id_strict]['label_to_display'] = "" 
                nodes_added_to_focus_strict += 1
        # if registro_output and isinstance(registro_output, widgets.Output):
            # with registro_output:
                # print(f"    DEBUG ENGINE B7 (G_FOCUS_STRICT_NODES): {nodes_added_to_focus_strict} nodos añadidos a G_focus_strict para foco '{connection_focus_mode}'.")
        edges_that_are_direct_focus_connections = set()
        if connection_focus_mode == 'outgoing':
            edges_that_are_direct_focus_connections.update(focus_outgoing_edges_tuples)
        elif connection_focus_mode == 'incoming':
            edges_that_are_direct_focus_connections.update(focus_incoming_edges_tuples)
        edges_added_to_focus_strict = 0
        edge_iterator_for_g_to_render = G.edges(keys=True, data=True) if G.is_multigraph() else G.edges(data=True)
        for edge_data_tuple_render in edge_iterator_for_g_to_render:
            key_g_render_edge_current = None 
            if G.is_multigraph():
                u_g_render_edge, v_g_render_edge, key_g_render_edge_current, data_g_render_edge_dict = edge_data_tuple_render
            else:
                u_g_render_edge, v_g_render_edge, data_g_render_edge_dict = edge_data_tuple_render
            is_direct_focus_edge_for_render = (u_g_render_edge, v_g_render_edge) in edges_that_are_direct_focus_connections
            if is_direct_focus_edge_for_render: 
                if u_g_render_edge in G_focus_strict.nodes() and v_g_render_edge in G_focus_strict.nodes():
                    attrs_to_add_strict = data_g_render_edge_dict.copy()
                    attrs_to_add_strict['edge_opacity'] = opacity_default_val 
                    if 'dimmed_edge' in attrs_to_add_strict.get('classes_cytoscape',''):
                        attrs_to_add_strict['classes_cytoscape'] = attrs_to_add_strict['classes_cytoscape'].replace('dimmed_edge','').strip()
                    if G_focus_strict.is_multigraph(): 
                        G_focus_strict.add_edge(u_g_render_edge, v_g_render_edge, key=key_g_render_edge_current, **attrs_to_add_strict)
                    else: 
                        G_focus_strict.add_edge(u_g_render_edge, v_g_render_edge, **attrs_to_add_strict)
                    edges_added_to_focus_strict +=1
        # if registro_output and isinstance(registro_output, widgets.Output):
            # with registro_output:
                # print(f"    DEBUG ENGINE B7 (G_FOCUS_STRICT_EDGES): {edges_added_to_focus_strict} aristas de foco directo añadidas a G_focus_strict.")
        G_to_render = G_focus_strict
    # else:
        # if registro_output and isinstance(registro_output, widgets.Output):
            # with registro_output:
                # print(f"  DEBUG ENGINE B7 (G_TO_RENDER_PRE): No se aplica filtro de foco direccional. G_to_render ({type(G_to_render)}) es copia de G ({type(G)}).")

    if isinstance(G_to_render, nx.MultiDiGraph) and G_to_render.edges():
        # if registro_output and isinstance(registro_output, widgets.Output):
            # with registro_output:
                # print(f"  DEBUG ENGINE B7 (EdgeCurve MultiDiGraph): Aplicando lógica de curvatura a G_to_render ({len(G_to_render.edges())} aristas).")
        base_distance_curve = 20 
        unique_directed_pairs_to_render = set((u_temp,v_temp) for u_temp, v_temp, _ in G_to_render.edges(keys=True))
        for u_curve, v_curve in unique_directed_pairs_to_render:
            specific_edges_between_uv = []
            for source_node_iter, target_node_iter, key_edge_iter, data_edge_iter in G_to_render.out_edges(u_curve, keys=True, data=True):
                if target_node_iter == v_curve: 
                    specific_edges_between_uv.append({'key': key_edge_iter, 'data': data_edge_iter})
            num_edges_in_group_curve = len(specific_edges_between_uv)
            if num_edges_in_group_curve > 1:
                for i_curve, edge_info in enumerate(specific_edges_between_uv):
                    key_edge_to_modify = edge_info['key']
                    data_edge_to_modify = G_to_render.edges[u_curve, v_curve, key_edge_to_modify]
                    distance_curve_val = 0
                    is_this_a_focus_outgoing_edge = False
                    if 'classes_cytoscape' in data_edge_to_modify and 'focus_edge_outgoing' in data_edge_to_modify['classes_cytoscape']:
                        is_this_a_focus_outgoing_edge = True
                    if is_this_a_focus_outgoing_edge and connection_focus_mode == 'outgoing':
                        distance_curve_val = 0 
                    else:
                        slot_curve = i_curve - (num_edges_in_group_curve - 1) / 2.0
                        distance_curve_val = slot_curve * base_distance_curve
                    data_edge_to_modify['edge_control_point_distances'] = str(distance_curve_val)
                    data_edge_to_modify['edge_control_point_weights'] = "0.5"
            elif num_edges_in_group_curve == 1:
                key_edge_single_curve = specific_edges_between_uv[0]['key']
                data_edge_single_curve = G_to_render.edges[u_curve, v_curve, key_edge_single_curve]
                distance_single_curve = 0
                is_this_a_focus_outgoing_single_edge = False
                if 'classes_cytoscape' in data_edge_single_curve and 'focus_edge_outgoing' in data_edge_single_curve['classes_cytoscape']:
                    is_this_a_focus_outgoing_single_edge = True
                if G_to_render.has_edge(v_curve, u_curve) and not (is_this_a_focus_outgoing_single_edge and connection_focus_mode == 'outgoing'): 
                    distance_single_curve = base_distance_curve / 3 
                data_edge_single_curve['edge_control_point_distances'] = str(distance_single_curve)
                data_edge_single_curve['edge_control_point_weights'] = "0.5"

    if not G_to_render.nodes():
        if registro_output and isinstance(registro_output, widgets.Output):
            with registro_output: print(f"  INFO (draw_sociogramma engine B7): Grafo G_to_render sin nodos. No se dibujará.")
        if sociogram_graph_output_widget and isinstance(sociogram_graph_output_widget, widgets.Output):
            with sociogram_graph_output_widget: display(IPHTML("<p style='color:grey;text-align:center;'>No hay nodos/aristas que mostrar.</p>"))
        return None, None, None

    graph_json_for_cytoscape = nx.cytoscape_data(G_to_render)
    # if registro_output and isinstance(registro_output, widgets.Output):
        # with registro_output:
            # print(f"  DEBUG ENGINE B7 (CYTOSCAPE_JSON): G_to_render ({type(G_to_render)}) tiene {len(G_to_render.nodes())}N, {len(G_to_render.edges())}A.")
            # num_nodes_in_json = len(graph_json_for_cytoscape.get('elements', {}).get('nodes', []))
            # num_edges_in_json = len(graph_json_for_cytoscape.get('elements', {}).get('edges', []))
            # print(f"    JSON para Cytoscape contiene {num_nodes_in_json} nodos y {num_edges_in_json} aristas.")

    cytoscape_widget_instance = ipycytoscape.CytoscapeWidget()
    graph_output_container_height_str_val = '600px'
    if sociogram_graph_output_widget and hasattr(sociogram_graph_output_widget, 'layout') and \
       sociogram_graph_output_widget.layout and \
       hasattr(sociogram_graph_output_widget.layout, 'height') and \
       sociogram_graph_output_widget.layout.height not in ['auto', None, '']:
        graph_output_container_height_str_val = sociogram_graph_output_widget.layout.height
    cytoscape_widget_instance.layout.height = graph_output_container_height_str_val
    cytoscape_widget_instance.layout.width = '100%'

    if graph_json_for_cytoscape.get('elements') and \
       (graph_json_for_cytoscape['elements'].get('nodes') or graph_json_for_cytoscape['elements'].get('edges')):
        cytoscape_widget_instance.graph.add_graph_from_json(graph_json_for_cytoscape['elements'])
    else:
        if registro_output and isinstance(registro_output, widgets.Output):
            with registro_output: print("  INFO (draw_sociogramma engine B7 CYTOSCAPE): JSON sin elementos. No se dibujará.");
        if sociogram_graph_output_widget and isinstance(sociogram_graph_output_widget, widgets.Output):
             with sociogram_graph_output_widget: display(IPHTML("<p style='color:grey;text-align:center;'>No hay elementos para dibujar.</p>"))
        return None, None, None

    cytoscape_style_rules = [
        {'selector': 'node', 'style': {
            'background-color': 'data(node_color)', 'label': 'data(label_to_display)', 'width': '50px', 'height': '50px', 'font-size': '10px',
            'color': '#333', 'text-valign': 'center', 'text-halign': 'center', 'border-width': '1px', 'border-color': '#666',
            'shape': 'data(node_shape_attr)', 'opacity': 'data(node_opacity)', 'z-index': 10, 'classes': 'data(classes_cytoscape)'}},
        {'selector': 'node[classes_cytoscape*="focus_node_selected"]', 'style': {'border-width': '3px', 'border-color': 'black', 'z-index': 100, 'opacity': opacity_default_val}},
        {'selector': 'node[classes_cytoscape*="focus_node_connected"]', 'style': {'border-width': '2px', 'border-color': '#333', 'z-index': 90, 'opacity': opacity_default_val}},
        {'selector': 'node[classes_cytoscape*="leader_node"]', 'style': {'border-width': '2px', 'border-color': 'darkgoldenrod', 'z-index': 80}},
        {'selector': 'node:selected', 'style': {'background-color': 'cyan', 'border-color': 'blue', 'border-width': '3px', 'opacity': opacity_default_val, 'z-index': 200}},
        {'selector': 'edge', 'style': {
            'line-color': 'data(edge_color)', 'target-arrow-shape': 'data(target_arrow_shape_attr)', 'target-arrow-color': 'data(edge_color)',
            'source-arrow-shape': 'data(source_arrow_shape_attr)', 'source-arrow-color': 'data(edge_color)', 'width': 'data(edge_width_attr)',
            'curve-style': 'unbundled-bezier', 'control-point-distances': 'data(edge_control_point_distances)', 'control-point-weights': 'data(edge_control_point_weights)',
            'line-style': 'data(edge_line_style)', 'opacity': 'data(edge_opacity)', 'z-index': 1, 'classes': 'data(classes_cytoscape)',
            'arrow-scale': 1.2, 'target-distance-from-node': '0px', 'source-distance-from-node': '0px'}},
        {'selector': 'edge[classes_cytoscape*="dimmed_edge"]', 'style': {'z-index': 5 }},
        {'selector': 'edge[classes_cytoscape*="focus_edge_outgoing"]', 'style': {'opacity': opacity_default_val, 'z-index': 50 }},
        {'selector': 'edge[classes_cytoscape*="focus_edge_incoming"]', 'style': {'opacity': opacity_default_val, 'z-index': 50 }},
        {'selector': 'edge[classes_cytoscape*="focus_edge_reciprocal"]', 'style': {'opacity': opacity_default_val, 'z-index': 55 }}
    ]
    cytoscape_widget_instance.set_style(cytoscape_style_rules)

    layout_options_dict_final = { 'animate': False, 'fit': True, 'padding': 30 }
    if layout_to_use == 'circle':
        num_nodes_for_layout_val_final = len(G_to_render.nodes()); target_max_radius_val_final = 140; radius_factor_val_final = 6; min_radius_val_final = 50
        calculated_radius_val_final = num_nodes_for_layout_val_final * radius_factor_val_final if num_nodes_for_layout_val_final > 0 else min_radius_val_final
        final_radius_to_use = max(min_radius_val_final, min(calculated_radius_val_final, target_max_radius_val_final)); circle_spacing_factor_final = 1.1
        layout_options_dict_final.update({'name': 'circle', 'radius': final_radius_to_use, 'spacingFactor': circle_spacing_factor_final, 'clockwise': False})
    elif layout_to_use == 'preset':
        layout_options_dict_final.update({'name': 'preset'})
        # if registro_output and isinstance(registro_output, widgets.Output):
            # with registro_output: print(f"  DEBUG ENGINE B7 (LAYOUT): Usando layout 'preset'.")
    else: 
        layout_options_dict_final.update({'name': 'cose', 'nodeSpacing': 70, 'idealEdgeLength': 140, 'numIter': 1000, 'edgeElasticity': 100, 'randomize': False })
    
    # if registro_output and isinstance(registro_output, widgets.Output):
        # with registro_output:
            # print(f"  DEBUG ENGINE B7 (LAYOUT): Aplicando layout: {layout_options_dict_final['name']}")

    cytoscape_widget_instance.set_layout(**layout_options_dict_final)
    cytoscape_widget_instance.user_zooming_enabled = True
    cytoscape_widget_instance.wheel_sensitivity = 0.2
# === FIN BLOQUE 7 ===

# === INICIO BLOQUE 8: MOSTRAR WIDGET, LEYENDA HTML Y RETORNAR ===
    if not ui_sociogramma_dict_ref.get('_keep_output_for_pdf_prep', False):
        if sociogram_graph_output_widget and isinstance(sociogram_graph_output_widget, widgets.Output):
            with sociogram_graph_output_widget:
                 display(cytoscape_widget_instance)
                 if 'google.colab' in sys.modules:
                     display(Javascript('google.colab.output.setIframeHeight(0, true, {maxHeight: 1200})'))
        elif registro_output and isinstance(registro_output, widgets.Output):
            with registro_output: print("ADVERTENCIA (draw_sociogramma engine B8): sociogram_graph_output_widget no es válido, no se puede mostrar el grafo.")

    final_node_colors_for_html_legend = collections.OrderedDict()
    if is_focus_active:
        final_node_colors_for_html_legend[highlight_focus_participant_color_val] = "Participante en Foco"
        if any(n_node_conn in specific_focus_target_nodes for n_node_conn in G.nodes() if n_node_conn != focus_participant_node):
            final_node_colors_for_html_legend[highlight_focus_connected_color_val] = "Conectado al Foco (Directo)"
    if leaders_to_highlight_names_list:
        final_node_colors_for_html_legend[color_leader_val] = "Líder(es) Resaltado(s)"
    if nominators_option and any(n_node_role in nodes_not_chosen_role_set for n_node_role in G.nodes()):
        final_node_colors_for_html_legend[color_not_chosen_val] = "No Elegido (por otros)"
    if received_color_filter and any(n_node_role in receivers_only_or_self_role_set for n_node_role in G.nodes()):
        final_node_colors_for_html_legend['lightsalmon'] = "Solo Recibe / Auto-nomina"
    if reciprocal_nodes_color_filter and any(n_node_role in nodes_in_reciprocal_relation_role_set for n_node_role in G.nodes()):
        final_node_colors_for_html_legend['mediumpurple'] = "En Relación Recíproca"

    genders_in_graph_display_for_base_colors = set()
    for n_name_leg_html_b8, n_data_leg_html_dict_b8 in G.nodes(data=True):
        node_color_in_graph_html_b8 = n_data_leg_html_dict_b8.get('node_color')
        is_base_gender_color_for_legend_b8 = node_color_in_graph_html_b8 in [color_gender_male, color_gender_female, color_gender_unknown]
        if is_base_gender_color_for_legend_b8:
            genders_in_graph_display_for_base_colors.add(n_data_leg_html_dict_b8.get('sexo_attr', n_data_leg_html_dict_b8.get('gender')))

    if 'Masculino' in genders_in_graph_display_for_base_colors: final_node_colors_for_html_legend[color_gender_male] = "Masculino (Elipse)"
    if 'Femenino' in genders_in_graph_display_for_base_colors: final_node_colors_for_html_legend[color_gender_female] = "Femenino (Triángulo)"
    if 'Desconocido' in genders_in_graph_display_for_base_colors or \
       any(g_leg_b8 not in ['Masculino', 'Femenino'] for g_leg_b8 in genders_in_graph_display_for_base_colors if g_leg_b8 is not None):
        final_node_colors_for_html_legend[color_gender_unknown] = "Sexo Desconocido/Otro (Cuadrado)"
    legend_info_final_for_display["node_colors"] = final_node_colors_for_html_legend

    if sociogram_legend_output_widget and isinstance(sociogram_legend_output_widget, widgets.Output) and \
       not ui_sociogramma_dict_ref.get('_keep_output_for_pdf_prep', False) :
        advertencia_html_str = ""
        if selected_data_keys_from_checkboxes and len(selected_data_keys_from_checkboxes) > 1:
            advertencia_html_str = (
                "<div style='margin-bottom: 10px; padding: 8px; border: 1px solid #ffcc00; "
                "background-color: #fff9e6; color: #856404; font-size: 0.8em; border-radius: 4px; text-align: center;'>"
                "<strong>Advertencia:</strong> Si se analiza más de 1 pregunta a la vez, "
                "el gráfico podría no representar de manera completamente fidedigna las interacciones individuales "
                "debido a la agregación de elecciones. Considere analizar preguntas individualmente para mayor detalle."
                "</div>"
            )
        legend_html_str_final = advertencia_html_str
        legend_html_str_final += "<div style='margin-top: 0px; padding: 10px; border: 1px solid #ddd; font-size: 0.85em; background-color: #f9f9f9;'>"
        legend_html_str_final += "<h4 style='margin-top:0; margin-bottom: 8px; color: #333;'>Leyenda:</h4>"
        if legend_info_final_for_display.get("node_colors"):
            legend_html_str_final += "<div style='margin-bottom: 7px;'><strong>Color de Nodo:</strong><ul style='list-style-type:none; padding-left:5px; margin-top:3px;'>"
            for color_val_leg_html_disp, desc_leg_html_disp in legend_info_final_for_display["node_colors"].items():
                legend_html_str_final += f"<li style='margin-bottom:2px;'><span style='display:inline-block; width:18px; height:10px; background-color:{color_val_leg_html_disp}; margin-right:6px; border:1px solid #aaa; vertical-align:middle;'></span> {desc_leg_html_disp}</li>"
            legend_html_str_final += "</ul></div>"
        edge_styles_legend_html_display = legend_info_final_for_display.get("edge_styles", {})
        if edge_styles_legend_html_display:
            legend_html_str_final += "<div style='margin-bottom: 7px;'><strong>Color/Estilo de Flecha:</strong><ul style='list-style-type:none; padding-left:5px; margin-top:3px;'>"
            sorted_edge_styles_html_display = sorted(edge_styles_legend_html_display.items(), key=lambda item: ("A_" if item[1].get('is_focus') else "B_") + item[0] )
            for desc_leg_edge_html_disp, style_attrs_leg_edge_html_disp in sorted_edge_styles_html_display:
                color_for_img = style_attrs_leg_edge_html_disp.get('color', '#333333')
                base_line_style = style_attrs_leg_edge_html_disp.get('base_line_style', 'solid')
                base_arrow_shape = style_attrs_leg_edge_html_disp.get('base_arrow_shape', 'triangle')
                base_source_arrow_shape = style_attrs_leg_edge_html_disp.get('source_arrow_shape', 'none')
                img_tag_html_base = ""
                can_generate_img = pdf_generator and hasattr(pdf_generator, '_create_legend_line_image_pil')
                if can_generate_img:
                    img_buffer_base = pdf_generator._create_legend_line_image_pil(
                        color_hex=color_for_img, line_style_name=base_line_style,
                        arrow_shape_name=base_arrow_shape, source_arrow_shape_name=base_source_arrow_shape,
                        img_width_px=50, img_height_px=15, line_thickness=2
                    )
                    if img_buffer_base:
                        img_b64_base = base64.b64encode(img_buffer_base.getvalue()).decode('utf-8')
                        img_tag_html_base = f"<img src='data:image/png;base64,{img_b64_base}' style='vertical-align:middle; margin-right:6px; height:12px; object-fit:contain;' alt='{base_line_style} line'/>"
                if not img_tag_html_base:
                    img_tag_html_base = f"<span style='display:inline-block; width:18px; height:10px; background-color:{color_for_img}; margin-right:6px; border:1px solid #aaa; vertical-align:middle;'></span>"
                legend_html_str_final += f"<li style='margin-bottom:2px;'>{img_tag_html_base} {desc_leg_edge_html_disp}</li>"
                can_be_reciprocal_html_disp = style_attrs_leg_edge_html_disp.get('can_be_reciprocal_styled', False)
                is_focus_style_html_disp = style_attrs_leg_edge_html_disp.get('is_focus', False)
                if style_reciprocal_links and can_be_reciprocal_html_disp and not is_focus_style_html_disp:
                    reciprocal_line_style_html_disp = 'dashed'
                    reciprocal_source_arrow_html_disp = base_arrow_shape
                    img_tag_html_recip = ""
                    if can_generate_img:
                        img_buffer_recip = pdf_generator._create_legend_line_image_pil(
                            color_hex=color_for_img, line_style_name=reciprocal_line_style_html_disp,
                            arrow_shape_name=base_arrow_shape, source_arrow_shape_name=reciprocal_source_arrow_html_disp,
                            img_width_px=50, img_height_px=15, line_thickness=2
                        )
                        if img_buffer_recip:
                            img_b64_recip = base64.b64encode(img_buffer_recip.getvalue()).decode('utf-8')
                            img_tag_html_recip = f"<img src='data:image/png;base64,{img_b64_recip}' style='vertical-align:middle; margin-right:6px; height:12px; object-fit:contain;' alt='reciprocal line'/>"
                    if not img_tag_html_recip:
                        img_tag_html_recip = f"<span style='display:inline-block; width:18px; height:1px; border-top: 2px dashed {color_for_img}; margin-right:6px; vertical-align:middle;'></span>"
                    desc_text_recip_html_disp = f"<i>↳ {desc_leg_edge_html_disp} (recíproca)</i>"
                    legend_html_str_final += f"<li style='margin-bottom:2px; padding-left:15px;'>{img_tag_html_recip} {desc_text_recip_html_disp}</li>"
            legend_html_str_final += "</ul></div>"
        widths_legend_html_display = legend_info_final_for_display.get("widths", {})
        if widths_legend_html_display:
            legend_html_str_final += "<div><strong>Grosor de Flecha (Orden de Elección):</strong><ul style='list-style-type:none; padding-left:5px; margin-top:3px;'>"
            sorted_widths_html_legend_display = sorted(widths_legend_html_display.items(), key=lambda item: int(item[0].split(" ")[1]) if "Elección" in item[0] and item[0].split(" ")[1].isdigit() else 99)
            for desc_w_html_disp, width_val_px_str_html_disp in sorted_widths_html_legend_display:
                line_height_for_legend_val_html_disp = width_val_px_str_html_disp.replace('px','');
                try: line_display_height_val_html_disp = max(1, float(line_height_for_legend_val_html_disp))
                except ValueError: line_display_height_val_html_disp = 2
                legend_html_str_final += f"<li style='margin-bottom:2px;'><span style='display:inline-block; width:25px; height:{line_display_height_val_html_disp}px; background-color:black; margin-right:6px; vertical-align:middle;'></span> {desc_w_html_disp} (aprox. {width_val_px_str_html_disp})</li>"
            legend_html_str_final += "</ul></div>"
        legend_html_str_final += "</div>"
        with sociogram_legend_output_widget:
            clear_output(wait=True); display(IPHTML(legend_html_str_final))
    elif sociogram_legend_output_widget and isinstance(sociogram_legend_output_widget, widgets.Output):
        with sociogram_legend_output_widget: clear_output(wait=True)

    if isinstance(ui_sociogramma_dict_ref, dict):
        ui_sociogramma_dict_ref['_current_cytoscape_widget'] = cytoscape_widget_instance
        ui_sociogramma_dict_ref['_current_legend_info'] = legend_info_final_for_display.copy()
        ui_sociogramma_dict_ref['_last_drawn_graph_G'] = G.copy()
        ui_sociogramma_dict_ref['_last_graph_elements_json'] = graph_json_for_cytoscape.get('elements', {'nodes':[], 'edges':[]})
        ui_sociogramma_dict_ref['_last_layout_used'] = layout_to_use
    elif registro_output and isinstance(registro_output, widgets.Output):
        with registro_output: print("ADVERTENCIA (draw_sociogramma engine B8): ui_sociogramma_dict_ref no es dict, no se guarda estado para PDF.")

    # if registro_output and isinstance(registro_output, widgets.Output):
        # with registro_output: print(f"DEBUG (draw_sociogramma Engine v1.9 - Miembro): Sociograma dibujado y estado guardado para layout '{layout_to_use}'.")

    return cytoscape_widget_instance, legend_info_final_for_display.copy(), graph_json_for_cytoscape
    # === FIN BLOQUE 8 ===