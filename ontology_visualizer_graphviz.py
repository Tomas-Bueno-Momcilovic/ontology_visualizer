import os
from rdflib import Graph, RDF, RDFS, OWL
import rdflib
import networkx as nx
from graphviz import Digraph
import json

# Normalize URIs for readability
def normalize_uri(uri, labels):
    uri_str = str(uri)
    if uri_str in labels:
        label = labels[uri_str]
    else:
        if "#" in uri_str:
            local_name = uri_str.split("#")[-1]
        elif "/" in uri_str:
            local_name = uri_str.split("/")[-1]
        else:
            local_name = uri_str
        label = local_name
    return label

def extract_labels(ontology):
    labels = {}
    for s, _, o in ontology.triples((None, RDFS.label, None)):
        labels[str(s)] = str(o)
    return labels

def generate_safe_node_ids(nodes):
    node_id_map = {}
    for idx, node in enumerate(nodes):
        safe_id = f"node{idx}"
        node_id_map[node] = safe_id
    return node_id_map

def visualize_taxonomy(ontology, labels, output_file_prefix="ontology_taxonomy"):
    G = nx.DiGraph()
    classes = set()
    for cls in ontology.subjects(RDF.type, OWL.Class):
        cls_str = str(cls)
        classes.add(cls_str)
        G.add_node(cls_str)

    for subclass, _, superclass in ontology.triples((None, RDFS.subClassOf, None)):
        subclass_str = str(subclass)
        superclass_str = str(superclass)
        if subclass_str in classes and superclass_str in classes:
            G.add_edge(superclass_str, subclass_str)

    if len(G.nodes) == 0:
        return None

    node_id_map = generate_safe_node_ids(G.nodes)
    dot = Digraph(comment="Ontology Taxonomy", format="png", engine='dot')
    dot.attr(rankdir="BT", ranksep='1.0', nodesep='0.5')

    for node in G.nodes:
        node_id = node_id_map[node]
        label = normalize_uri(node, labels)
        dot.node(node_id, label=label, shape="box", style="filled", fillcolor="lightblue", fontcolor="black")

    for edge in G.edges:
        src_id = node_id_map[edge[0]]
        tgt_id = node_id_map[edge[1]]
        dot.edge(src_id, tgt_id, label="subClassOf", color="black", fontsize="10")

    output_path = output_file_prefix + ".png"
    dot.render(output_file_prefix, format="png", cleanup=True)
    return output_path

def visualize_concept_map(ontology, labels, included_properties=None, output_file_prefix="filtered_ontology_concept_map"):
    G = nx.DiGraph()
    ind_to_class = {}
    for ind in ontology.subjects(RDF.type, None):
        if not any((ind, RDF.type, t) in ontology for t in [OWL.Class, RDF.Property, OWL.ObjectProperty, OWL.DatatypeProperty, OWL.AnnotationProperty]):
            types = list(ontology.objects(ind, RDF.type))
            ind_to_class[str(ind)] = [str(t) for t in types]

    class_relations = set()
    for s, p, o in ontology.triples((None, None, None)):
        if p not in [RDF.type, RDFS.subClassOf] and not isinstance(o, rdflib.Literal):
            if included_properties and str(p) not in included_properties:
                continue
            s_str = str(s)
            o_str = str(o)
            if s_str in ind_to_class and o_str in ind_to_class:
                classes_s = ind_to_class[s_str]
                classes_o = ind_to_class[o_str]
                for class_s in classes_s:
                    for class_o in classes_o:
                        class_relations.add((class_s, str(p), class_o))

    if len(class_relations) == 0:
        return None

    for class_s, p, class_o in class_relations:
        G.add_node(class_s)
        G.add_node(class_o)
        G.add_edge(class_s, class_o, label=normalize_uri(p, labels))

    node_id_map = generate_safe_node_ids(G.nodes)
    dot = Digraph(comment="Filtered Ontology Concept Map", format="png", engine='dot')
    dot.attr(rankdir="LR", ranksep='1.0', nodesep='0.5')

    for node in G.nodes:
        node_id = node_id_map[node]
        label = normalize_uri(node, labels)
        dot.node(node_id, label=label, shape="ellipse", style="filled", fillcolor="lightgreen", fontcolor="black")

    for edge in G.edges:
        src_id = node_id_map[edge[0]]
        tgt_id = node_id_map[edge[1]]
        label = G.edges[edge].get("label", "")
        dot.edge(src_id, tgt_id, label=label, color="blue", fontcolor="red", fontsize="10")

    output_path = output_file_prefix + ".png"
    dot.render(output_file_prefix, format="png", cleanup=True)
    return output_path

def visualize_node_to_node(ontology, labels, start_node, end_node, included_properties='Any', output_file_prefix="ontology_node_to_node"):
    G = nx.Graph()
    for s, p, o in ontology.triples((None, None, None)):
        if p == RDF.type:
            continue
        if included_properties != 'Any' and str(p) not in included_properties:
            continue
        s_str = str(s)
        o_str = str(o)
        if not isinstance(o, rdflib.Literal):
            G.add_edge(s_str, o_str, label=normalize_uri(p, labels))

    start_node_str = str(start_node)
    end_node_str = str(end_node)

    try:
        path = nx.shortest_path(G, source=start_node_str, target=end_node_str)
        node_id_map = generate_safe_node_ids(path)
        dot = Digraph(comment=f"Shortest Path from {normalize_uri(start_node, labels)} to {normalize_uri(end_node, labels)}", format="png")
        dot.attr(rankdir="LR")

        for node in path:
            node_id = node_id_map[node]
            label = normalize_uri(node, labels)
            dot.node(node_id, label=label, shape="ellipse", style="filled", fillcolor="lightblue", fontcolor="black")

        path_edges = list(zip(path, path[1:]))
        for edge in path_edges:
            src_id = node_id_map[edge[0]]
            tgt_id = node_id_map[edge[1]]
            label = G.edges[edge].get("label", "")
            dot.edge(src_id, tgt_id, label=label, color="black", fontsize="10")

        output_path = output_file_prefix + ".png"
        dot.render(output_file_prefix, format="png", cleanup=True)
        return output_path
    except nx.NetworkXNoPath:
        return None

def visualize_rdf_mapping(mapping_file, output_file_prefix="mapping_visualization"):
    # Create images directory if not exists
    if not os.path.exists("images"):
        os.makedirs("images")

    with open(mapping_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    subjectMappings = data.get("subjectMappings", [])

    dot = Digraph(comment="RDF Mapping Visualization", format="png", engine='dot')
    dot.attr(rankdir="LR", ranksep='1.0', nodesep='0.5')

    # Initialize node counter for unique node IDs
    node_counter = 0

    def new_id():
        nonlocal node_counter
        node_id = f"node{node_counter}"
        node_counter += 1
        return node_id

    # Iterate over each subject mapping
    for sm in subjectMappings:
        subj = sm.get("subject", {})
        subj_transformation = subj.get("transformation", {})
        subj_value_source = subj.get("valueSource", {})
        subj_constant = subj_value_source.get("constant")
        subj_col = subj_value_source.get("columnName")

        # Determine subject label
        if subj_constant:
            subject_label = f"Subject: {subj_constant}"
        elif subj_col:
            subject_label = f"@{subj_col}"
        else:
            subject_label = "Subject (Unknown)"

        subject_id = new_id()
        dot.node(subject_id, label=subject_label, shape="box", color="lightblue")

        # Handle typeMappings (rdf:type)
        typeMappings = sm.get("typeMappings", [])
        for tm in typeMappings:
            tm_constant = tm.get("valueSource", {}).get("constant")
            if tm_constant:
                # Add a node for type?
                type_id = new_id()
                dot.node(type_id, label=f"Class: {tm_constant}", shape="box", color="lightgreen")
                dot.edge(subject_id, type_id, label="rdf:type", color="green")

        # Handle propertyMappings
        for pm in sm.get("propertyMappings", []):
            property_def = pm.get("property", {})
            p_transformation = property_def.get("transformation", {})
            p_value_source = property_def.get("valueSource", {})
            p_constant = p_value_source.get("constant")
            if p_constant:
                prop_label = p_constant
            else:
                prop_label = "Property"

            # Each value is a separate node
            for val in pm.get("values", []):
                val_source = val.get("valueSource", {})
                val_constant = val_source.get("constant")
                val_col = val_source.get("columnName")
                val_label = ""
                if val_constant:
                    val_label = f"Value: {val_constant}"
                elif val_col:
                    val_label = f"@{val_col}"
                else:
                    val_label = "Value (Unknown)"

                # Check if there's a transformation
                transformation = val.get("transformation")
                if transformation and transformation.get("expression"):
                    val_label += f" [Transform: {transformation['expression']}]"

                # Check valueType
                value_type = val.get("valueType", {})
                vtype = value_type.get("type", "literal")

                if vtype == "datatype_literal":
                    # Extract datatype information
                    datatype_info = value_type.get("datatype", {})
                    datatype_transformation = datatype_info.get("transformation", {})
                    datatype_expr = datatype_transformation.get("expression", "")
                    datatype_lang = datatype_transformation.get("language", "")
                    datatype_constant = datatype_info.get("valueSource", {}).get("constant", "")
                    if datatype_expr and datatype_constant:
                        datatype_full = f"^^{datatype_expr}:{datatype_constant}"
                        val_label += f" {datatype_full}"
                elif vtype == "language_literal":
                    # Extract language tag information
                    language_info = value_type.get("language", {})
                    lang_value_source = language_info.get("valueSource", {})
                    lang_constant = lang_value_source.get("constant", "")
                    if lang_constant:
                        language_tag = f"@{lang_constant}"
                        val_label += f" {language_tag}"

                # Determine node color based on value type
                if vtype == "iri":
                    value_color = "orange"
                else:
                    value_color = "yellow"

                value_id = new_id()
                dot.node(value_id, label=val_label, shape="ellipse", style="filled", fillcolor=value_color)
                dot.edge(subject_id, value_id, label=prop_label, color="blue", fontsize="10")

    output_path = os.path.join("images", output_file_prefix + ".png")
    dot.render(os.path.join("images", output_file_prefix), format="png", cleanup=True)
    return output_path
