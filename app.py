import streamlit as st
from rdflib import Graph, RDF, RDFS, OWL
import rdflib
import os

# Import visualization functions
import ontology_visualizer_graphviz as viz_graphviz
import ontology_visualizer_pyvis as viz_pyvis

def display_pyvis_network(net):
    import streamlit.components.v1 as components
    try:
        html = net.generate_html()
        components.html(html, height=750, scrolling=True)
    except Exception as e:
        st.error(f"An error occurred while displaying the PyVis network: {e}")

def get_ontology_format(file_name):
    if file_name.endswith('.ttl'):
        return 'ttl'
    elif file_name.endswith('.rdf') or file_name.endswith('.xml'):
        return 'xml'
    elif file_name.endswith('.owl'):
        # OWL files are often in RDF/XML format
        return 'xml'
    elif file_name.endswith('.nt'):
        return 'nt'
    elif file_name.endswith('.n3'):
        return 'n3'
    else:
        # Default to RDF/XML if format is unknown
        return 'xml'


def main():
    st.set_page_config(page_title="OntoViz", page_icon="ontoviz.ico", layout="centered")
    st.title("Ontology Visualizer")

    st.sidebar.header("Select Ontology")

    ONTOLOGY_DIR = 'ontologies'
    if not os.path.exists(ONTOLOGY_DIR):
        os.makedirs(ONTOLOGY_DIR)

    ontology_files = [f for f in os.listdir(ONTOLOGY_DIR) if os.path.isfile(os.path.join(ONTOLOGY_DIR, f))]
    ontology_options = ['Upload new ontology file'] + ontology_files
    selected_option = st.sidebar.selectbox("Select an ontology file", ontology_options)

    if selected_option == 'Upload new ontology file':
        uploaded_file = st.sidebar.file_uploader("Choose an ontology file", type=["owl", "rdf", "xml", "ttl", "nt", "n3"])
        if uploaded_file is not None:
            file_name = uploaded_file.name
            save_path = os.path.join(ONTOLOGY_DIR, file_name)
            with open(save_path, 'wb') as f:
                f.write(uploaded_file.getbuffer())
            st.sidebar.success(f"Saved file: {file_name}")
            selected_option = file_name
        else:
            st.info("Please upload an ontology file to get started.")
            return
    else:
        save_path = os.path.join(ONTOLOGY_DIR, selected_option)
        st.sidebar.info(f"Using ontology file: {selected_option}")

    visualization_library = st.sidebar.selectbox("Select Visualization Library", ['Graphviz', 'PyVis'])

    ontology_format = get_ontology_format(save_path)

    ontology = Graph()
    try:
        ontology.parse(save_path, format=ontology_format)
        st.success("Ontology loaded successfully!")
    except Exception as e:
        st.error(f"Failed to parse ontology: {e}")
        return

    if visualization_library == 'Graphviz':
        labels = viz_graphviz.extract_labels(ontology)
        normalize_uri = viz_graphviz.normalize_uri
    else:
        labels = viz_pyvis.extract_labels(ontology)
        normalize_uri = viz_pyvis.normalize_uri

    st.header("Visualization Options")

    if st.checkbox("Show Taxonomy Visualization"):
        st.subheader("Taxonomy (Classes and Subclasses)")
        if visualization_library == 'Graphviz':
            try:
                image_path = viz_graphviz.visualize_taxonomy(ontology, labels)
                if image_path and os.path.exists(image_path):
                    st.image(image_path)
                else:
                    st.warning("No classes or subclass relationships found.")
            except Exception as e:
                st.error(f"An error occurred with Graphviz visualization: {e}")
        else:
            try:
                net = viz_pyvis.visualize_taxonomy(ontology, labels)
                if net:
                    display_pyvis_network(net)
                else:
                    st.warning("No classes or subclass relationships found.")
            except Exception as e:
                st.error(f"An error occurred with PyVis visualization: {e}")

    if st.checkbox("Show Concept Map Visualization"):
        st.subheader("Concept Map (Classes and Their Relationships Based on Individuals)")
        object_properties = set()
        for _, p, _ in ontology.triples((None, None, None)):
            if isinstance(p, rdflib.term.URIRef) and p not in [RDF.type, RDFS.subClassOf]:
                object_properties.add(str(p))

        property_labels = [normalize_uri(p, labels) for p in object_properties]
        selected_properties = st.multiselect("Select properties to include in the concept map", property_labels, default=property_labels)
        selected_properties_uris = [p for p in object_properties if normalize_uri(p, labels) in selected_properties]

        if visualization_library == 'Graphviz':
            try:
                image_path = viz_graphviz.visualize_concept_map(ontology, labels, included_properties=selected_properties_uris)
                if image_path and os.path.exists(image_path):
                    st.image(image_path)
                else:
                    st.warning("No relationships to display with the selected properties.")
            except Exception as e:
                st.error(f"An error occurred with Graphviz visualization: {e}")
        else:
            try:
                net = viz_pyvis.visualize_concept_map(ontology, labels, included_properties=selected_properties_uris)
                if net:
                    display_pyvis_network(net)
                else:
                    st.warning("No relationships to display with the selected properties.")
            except Exception as e:
                st.error(f"An error occurred with PyVis visualization: {e}")

    if st.checkbox("Show Node-to-Node Visualization"):
        st.subheader("Node-to-Node Shortest Path")
        individuals = set()
        for s in ontology.subjects(RDF.type, None):
            if not any((s, RDF.type, t) in ontology for t in [OWL.Class, RDF.Property, OWL.ObjectProperty, OWL.DatatypeProperty, OWL.AnnotationProperty]):
                individuals.add(str(s))

        if individuals:
            individual_labels = [normalize_uri(ind, labels) for ind in individuals]
            start_label = st.selectbox("Select Start Node", individual_labels, key="start_node")
            end_label = st.selectbox("Select End Node", individual_labels, key="end_node")
            start_node = [ind for ind in individuals if normalize_uri(ind, labels) == start_label][0]
            end_node = [ind for ind in individuals if normalize_uri(ind, labels) == end_label][0]
            use_all_properties = st.checkbox("Use all object properties (Any)", value=True)

            if not use_all_properties:
                object_properties = set()
                for _, p, _ in ontology.triples((None, None, None)):
                    if isinstance(p, rdflib.term.URIRef) and p != RDF.type:
                        object_properties.add(str(p))
                property_labels = [normalize_uri(p, labels) for p in object_properties]
                selected_properties = st.multiselect("Select object properties to consider", property_labels, default=property_labels)
                selected_properties_uris = [p for p in object_properties if normalize_uri(p, labels) in selected_properties]
                included_properties = selected_properties_uris
            else:
                included_properties = 'Any'

            if visualization_library == 'Graphviz':
                try:
                    image_path = viz_graphviz.visualize_node_to_node(ontology, labels, start_node, end_node, included_properties=included_properties)
                    if image_path and os.path.exists(image_path):
                        st.image(image_path)
                    else:
                        st.warning(f"No path found between {start_label} and {end_label}.")
                except Exception as e:
                    st.error(f"An error occurred with Graphviz visualization: {e}")
            else:
                try:
                    net = viz_pyvis.visualize_node_to_node(ontology, labels, start_node, end_node, included_properties=included_properties)
                    if net:
                        display_pyvis_network(net)
                    else:
                        st.warning(f"No path found between {start_label} and {end_label}.")
                except Exception as e:
                    st.error(f"An error occurred with PyVis visualization: {e}")
        else:
            st.warning("No individuals found in the ontology.")

    st.header("RDF Mapping Visualization")
    st.markdown("Upload a `.mapping` JSON file to visualize the RDF mapping using Graphviz.")

    mapping_file = st.file_uploader("Upload a mapping JSON file", type=["json"])
    if mapping_file is not None:
        # Save the mapping file
        mapping_path = os.path.join("ontologies", mapping_file.name)
        with open(mapping_path, 'wb') as f:
            f.write(mapping_file.getbuffer())
        st.success(f"Mapping file {mapping_file.name} saved.")
        if st.button("Visualize Mapping"):
            # Call visualize_rdf_mapping from viz_graphviz
            try:
                image_path = viz_graphviz.visualize_rdf_mapping(mapping_path)
                if image_path and os.path.exists(image_path):
                    st.image(image_path)
                else:
                    st.warning("No mapping visualization generated.")
            except Exception as e:
                st.error(f"An error occurred while visualizing the mapping: {e}")


if __name__ == "__main__":
    main()
