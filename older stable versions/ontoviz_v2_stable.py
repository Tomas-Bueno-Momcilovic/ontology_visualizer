from rdflib import Graph
import networkx as nx
from graphviz import Digraph
from pyvis.network import Network
import matplotlib.pyplot as plt


# Normalize URIs for readability
def normalize_uri(uri):
    """Extract a human-readable label or shorten specific URIs."""
    if isinstance(uri, str):
        if "#" in uri:
            local_name = uri.split("#")[-1]
        elif "/" in uri:
            local_name = uri.split("/")[-1]
        else:
            local_name = uri

        # Shorten specific terms
        label_map = {
            "type": "Type",
            "subClassOf": "⊆",
            "hasChild": "⤷",
            "hasGrandchild": "⤵",
            "worksFor": "→"
        }
        return label_map.get(local_name, local_name)

    return str(uri)


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
    pos = nx.spring_layout(G, k=0.5, iterations=50)  # Adjust 'k' for better spacing
    plt.figure(figsize=(12, 10))
    nx.draw(G, pos, with_labels=True, node_size=2000, font_size=10, edge_color="blue", font_color="black")
    edge_labels = nx.get_edge_attributes(G, "label")
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8, font_color="red")
    plt.title("Ontology Visualization (Matplotlib)")
    plt.savefig("matplotlib_ontology.png", dpi=300)  # Save as a PNG file
    print("Matplotlib visualization saved as 'matplotlib_ontology.png'.")


# Interactive visualization with PyVis
def visualize_with_pyvis(G):
    print("Visualizing with PyVis...")
    net = Network(notebook=False)
    for node in G.nodes:
        node_type = "Class" if "Class" in node else "Property" if "Property" in node else "Individual"
        net.add_node(node, label=node, title=f"Type: {node_type}", color="blue" if node_type == "Class" else "green")

    for edge in G.edges:
        label = G.edges[edge].get("label", "")
        net.add_edge(edge[0], edge[1], title=f"Relation: {label}", label=label, color="red")

    net.toggle_physics(True)

    # Write the HTML manually
    html_content = net.generate_html()
    with open("ontology_pyvis.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    print("PyVis visualization saved as 'ontology_pyvis.html'.")


# Visualization with Graphviz
def visualize_with_graphviz(G):
    print("Visualizing with Graphviz...")
    dot = Digraph(comment="Ontology Graph", format="png")
    dot.attr(rankdir="LR")  # Left-to-right layout
    dot.attr(size="10,5")  # Set a fixed graph size

    # Add nodes with normalized labels
    for node in G.nodes:
        dot.node(node, label=node, shape="ellipse", color="blue")

    # Add edges with normalized labels and style
    for edge in G.edges:
        label = G.edges[edge].get("label", "")
        dot.edge(edge[0], edge[1], label=label, color="blue", fontcolor="red", penwidth="1.5")

    dot.render("ontology_graphviz", format="png", cleanup=True)
    dot.render("ontology_graphviz", format="pdf", cleanup=True)
    dot.render("ontology_graphviz", format="svg", cleanup=True)
    print("Graphviz visualization saved as 'ontology_graphviz.png', 'ontology_graphviz.pdf', and 'ontology_graphviz.svg'.")


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
