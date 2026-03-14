import networkx as nx
import matplotlib.pyplot as plt
from brain_parser.codebase_walker import load_brain
from pyvis.network import Network

def build_graph(brain):
    G = nx.DiGraph()

    for filepath, data in brain.items():
        # Add node for each file
        G.add_node(filepath)

        # Add edges from imports
        for imp in data['imports']:
            module = imp.get('name') or imp.get('module', '')
            for other_file in brain.keys():
                if module in other_file:
                    G.add_edge(filepath, other_file)

    return G


def visualize_graph(G):
    risk = calculate_risk(G)

    color_map = {
        "HIGH": "red",
        "MEDIUM": "orange",
        "LOW": "lightgreen"
    }

    node_colors = [color_map[risk[node]] for node in G.nodes()]

    plt.figure(figsize=(10, 7))
    pos = nx.spring_layout(G)

    nx.draw(G, pos,
            with_labels=True,
            node_color=node_colors,
            node_size=2000,
            font_size=8,
            arrows=True,
            edge_color='gray',
            font_weight='bold'
            )

    plt.title("Live Codebase Brain - Risk Map")
    plt.savefig("brain_graph.png")
    plt.show()


def calculate_risk(G):
    risk = {}

    for node in G.nodes():
        in_degree = G.in_degree(node)

        if in_degree >= 2:
            risk[node] = "HIGH"
        elif in_degree == 1:
            risk[node] = "MEDIUM"
        else:
            risk[node] = "LOW"

    return risk


def visualize_interactive(G):
    risk = calculate_risk(G)\

    color_map = {
        "HIGH": "#ff4444",
        "MEDIUM": "#ffa500",
        "LOW": "#44cc44"
    }

    net = Network(
        height="750px",
        width="100%",
        bgcolor="#1a1a2e",
        font_color="white",
        directed=True
    )

    for node in G.nodes():
        risk_level = risk[node]
        color = color_map[risk_level]
        label = node.split("\\")[-1].split("/")[-1]

        net.add_node(
            node,
            label=label,
            color=color,
            size=20 + (G.in_degree(node) * 3),
            title=f"File: {label}\nRisk: {risk_level}\nConnections: {G.in_degree(node)}"
        )

    for edge in G.edges():
        net.add_edge(edge[0], edge[1])

    net.set_options("""
    {
      "nodes": {
        "borderWidth": 2,
        "shadow": true
      },
      "edges": {
        "smooth": {
          "type": "dynamic"
        },
        "shadow": true
      },
      "interaction": {
        "hover": true,
        "navigationButtons": true,
        "hideEdgesOnDrag": true
      },
      "physics": {
        "stabilization": true,
        "barnesHut": {
          "gravitationalConstant": -8000,
          "springLength": 200,
          "springConstant": 0.02
        }
      }
    }
    """)

    net.save_graph("brain_map.html")
    print(f"Nodes in graph: {len(G.nodes())}")
    print(f"Edges in graph: {len(G.edges())}")
    import webbrowser
    webbrowser.open("brain_map.html")
    print("Interactive graph saved to brain_map.html")


if __name__ == "__main__":
    brain = load_brain()
    G = build_graph(brain)
    visualize_interactive(G)

    print("\nRisk Report:")
    for node, level in calculate_risk(G).items():
        print(f"  {node.split(chr(92))[-1]}: {level}")

