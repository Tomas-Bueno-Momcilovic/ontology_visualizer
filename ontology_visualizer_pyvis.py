from rdflib import Graph, RDF, RDFS, OWL
import rdflib
from rdflib.namespace import RDFS, RDF
from pyvis.network import Network
import networkx as nx

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
    # Remove label truncation
    return label


def extract_labels(ontology):
    labels = {}
    for s, _, o in ontology.triples((None, RDFS.label, None)):
        labels[str(s)] = str(o)
    return labels

def get_entity_info(ontology, entity, labels):
    """
    Retrieve annotations and data properties for the given entity.
    """
    info = []
    # Get rdfs:comment annotations
    comments = ontology.objects(entity, RDFS.comment)
    for comment in comments:
        info.append(f"Comment: {str(comment)}")
    # Get other annotations and data properties
    for p, o in ontology.predicate_objects(entity):
        if p not in [RDF.type, RDFS.label, RDFS.comment] and isinstance(o, rdflib.Literal):
            prop_label = normalize_uri(p, labels)
            info.append(f"{prop_label}: {str(o)}")
    if info:
        return "<br>".join(info)
    else:
        return "No additional information available."

def visualize_taxonomy(ontology, labels):
    net = Network(height='750px', width='100%', directed=True)
    net.toggle_physics(True)
    classes = set()
    for cls in ontology.subjects(RDF.type, OWL.Class):
        classes.add(str(cls))

    if len(classes) == 0:
        net.add_node('NoClasses', label='No classes found in the ontology.', shape='box', color='red')
        return net

    for subclass, _, superclass in ontology.triples((None, RDFS.subClassOf, None)):
        subclass_str = str(subclass)
        superclass_str = str(superclass)
        if subclass_str in classes and superclass_str in classes:
            superclass_label = normalize_uri(superclass_str, labels)
            subclass_label = normalize_uri(subclass_str, labels)
            superclass_info = get_entity_info(ontology, superclass, labels)
            subclass_info = get_entity_info(ontology, subclass, labels)
            superclass_title = f"<b>{superclass_label}</b><br>{superclass_info}"
            subclass_title = f"<b>{subclass_label}</b><br>{subclass_info}"

            net.add_node(superclass_str, label=superclass_label, title=superclass_title, shape='box', color='lightblue')
            net.add_node(subclass_str, label=subclass_label, title=subclass_title, shape='box', color='lightblue')
            net.add_edge(superclass_str, subclass_str, label='subClassOf', color='black', title='subClassOf')
    return net

def visualize_concept_map(ontology, labels, included_properties=None):
    net = Network(height='750px', width='100%', directed=True)
    net.toggle_physics(True)

    # Map individuals to their classes
    ind_to_class = {}
    individuals = set()
    for ind in ontology.subjects(RDF.type, None):
        if not any((ind, RDF.type, t) in ontology for t in [
            OWL.Class, RDF.Property, OWL.ObjectProperty, OWL.DatatypeProperty, OWL.AnnotationProperty]):
            types = list(ontology.objects(ind, RDF.type))
            ind_to_class[str(ind)] = [str(t) for t in types]
            individuals.add(ind)

    # Add individuals to the network with data properties in tooltips
    for ind in individuals:
        ind_str = str(ind)
        ind_label = normalize_uri(ind_str, labels)
        ind_info = get_entity_info(ontology, ind, labels)
        ind_title = f"<b>{ind_label}</b><br>{ind_info}"
        net.add_node(ind_str, label=ind_label, title=ind_title, color='orange', shape='ellipse')

    # Add classes to the network
    classes = set()
    for cls in ontology.subjects(RDF.type, OWL.Class):
        cls_str = str(cls)
        classes.add(cls_str)
        cls_label = normalize_uri(cls_str, labels)
        cls_info = get_entity_info(ontology, cls, labels)
        cls_title = f"<b>{cls_label}</b><br>{cls_info}"
        net.add_node(cls_str, label=cls_label, title=cls_title, color='lightgreen', shape='box')

    # Add edges based on object properties
    for s, p, o in ontology.triples((None, None, None)):
        if p not in [RDF.type, RDFS.subClassOf] and not isinstance(o, rdflib.Literal):
            if included_properties and str(p) not in included_properties:
                continue
            s_str = str(s)
            o_str = str(o)
            property_label = normalize_uri(p, labels)
            property_info = get_entity_info(ontology, p, labels)
            edge_title = f"<b>{property_label}</b><br>{property_info}"
            net.add_edge(s_str, o_str, label=property_label, color='blue', title=edge_title)
    return net

def visualize_node_to_node(ontology, labels, start_node, end_node, included_properties='Any'):
    net = Network(height='750px', width='100%', directed=False)
    net.toggle_physics(True)
    G = nx.Graph()
    for s, p, o in ontology.triples((None, None, None)):
        if p == RDF.type:
            continue
        if included_properties != 'Any' and str(p) not in included_properties:
            continue
        s_str = str(s)
        o_str = str(o)
        if not isinstance(o, rdflib.Literal):
            edge_label = normalize_uri(p, labels)
            edge_title = get_entity_info(ontology, p, labels)
            G.add_edge(s_str, o_str, label=edge_label, title=edge_title)

    start_node_str = str(start_node)
    end_node_str = str(end_node)
    try:
        path = nx.shortest_path(G, source=start_node_str, target=end_node_str)
        path_edges = list(zip(path, path[1:]))

        for node in path:
            node_label = normalize_uri(node, labels)
            node_info = get_entity_info(ontology, rdflib.URIRef(node), labels)
            node_title = f"<b>{node_label}</b><br>{node_info}"
            net.add_node(node, label=node_label, title=node_title, color='lightblue')

        for edge in path_edges:
            s = edge[0]
            t = edge[1]
            edge_data = G.edges[edge]
            label = edge_data.get('label', '')
            title = edge_data.get('title', '')
            net.add_edge(s, t, label=label, color='black', title=title)

        return net
    except nx.NetworkXNoPath:
        net.add_node('NoPath', label=f'No path found between {normalize_uri(start_node, labels)} and {normalize_uri(end_node, labels)}.', shape='box', color='red')
        return net
