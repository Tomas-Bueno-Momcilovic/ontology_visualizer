from rdflib import Graph
import networkx as nx
import matplotlib.pyplot as plt
from pyvis.network import Network
from graphviz import Digraph


# Load ontology
def load_ontology(file_path, format="xml"):
    try:
        g = Graph()
        g.parse(file_path, format=format)
        print("Ontology loaded successfully!")
    except Exception as e:
        print(f"Failed to parse ontology: {e}")
        exit(1)
    return g


# Normalize URIs for readability
def normalize_uri(uri):
    """Extract a human-readable label from a URI."""
    if isinstance(uri, str):  # Ensure we're handling strings
        # Remove the namespace and keep the local part
        if "#" in uri:
            return uri.split("#")[-1]  # After the hash
        elif "/" in uri:
            return uri.split("/")[-1]  # After the last slash
    return str(uri)  # Convert any other type to string


# Build NetworkX graph
def build_graph(graph):
    G = nx.DiGraph()

    for s, p, o in graph.triples((None, None, None)):
        # Add normalized nodes and edges
        G.add_node(normalize_uri(s))
        G.add_node(normalize_uri(o))
        G.add_edge(normalize_uri(s), normalize_uri(o), label=normalize_uri(p))

    return G


# Visualization with Matplotlib
def visualize_with_matplotlib(G):
    print("Visualizing with Matplotlib...")
    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, node_size=1500, font_size=10)
    edge_labels = nx.get_edge_attributes(G, "label")
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
    plt.title("Ontology Visualization (Matplotlib)")
    plt.show()


# Interactive visualization with PyVis
def visualize_with_pyvis(G):
    print("Visualizing with PyVis...")
    net = Network(notebook=False)
    for node in G.nodes:
        net.add_node(node, label=node)
    for edge in G.edges:
        label = G.edges[edge].get("label", "")
        net.add_edge(edge[0], edge[1], title=label)
    net.toggle_physics(True)

    with open("ontology_pyvis.html", "w") as f:
        f.write(net.generate_html())

    print("PyVis visualization saved to ontology_pyvis.html.")


# Visualization with Graphviz
def visualize_with_graphviz(G):
    print("Visualizing with Graphviz...")
    dot = Digraph(comment="Ontology Graph", format="png")

    # Set layout and size
    dot.attr(rankdir="LR")  # Left-to-right layout
    dot.attr(size="10,5")  # Set a fixed graph size

    # Add nodes with normalized labels
    for node in G.nodes:
        dot.node(node, label=node)

    # Add edges with normalized labels and style
    for edge in G.edges:
        label = G.edges[edge].get("label", "")
        dot.edge(edge[0], edge[1], label=label, color="blue", fontcolor="red", penwidth="1.5")

    dot.render("ontology_graphviz", format="png", cleanup=True)
    print("Graphviz visualization saved to ontology_graphviz.png.")


# Main testing function
def test_visualizations(file_path):
    ontology = load_ontology(file_path)
    nx_graph = build_graph(ontology)

    # Test all visualization options
    visualize_with_matplotlib(nx_graph)
    visualize_with_pyvis(nx_graph)
    visualize_with_graphviz(nx_graph)


# Run the tests
file_path = "example.owl"  # Replace with your ontology file path
test_visualizations(file_path)
