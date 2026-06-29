import networkx as nx
import matplotlib.pyplot as plt
from brain_parser.codebase_walker import load_brain
from pyvis.network import Network


def build_graph(brain):
    G = nx.DiGraph()

    for filepath, data in brain.items():
        G.add_node(filepath)

        for imp in data.get('imports', []):
            raw = imp.get('name', '')

            # extract module from "from x import y" or "import x"
            if raw.startswith('from '):
                module = raw.split('from ')[1].split(' import')[0].strip()
            elif raw.startswith('import '):
                module = raw.replace('import ', '').split(' as ')[0].strip()
            else:
                continue

            # convert module path to file path format
            # tests.circular_test.file_b → tests/circular_test/file_b
            module_as_path = module.replace('.', '/').lower()

            for other_file in brain.keys():
                other_normalized = other_file.replace('\\', '/').lower()
                # match whole filename not partial
                filename = other_normalized.split('/')[-1].replace('.py', '').replace('.js', '').replace('.java',
                                                                                                         '').replace(
                    '.ts', '')
                if module_as_path == filename or other_normalized.endswith(module_as_path + '.py'):
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
    from pyvis.network import Network
    import os

    risk = calculate_risk(G)

    net = Network(
        height="100vh",
        width="100%",
        bgcolor="#0d0d0d",
        font_color="#ffffff",
        directed=True,
        cdn_resources='in_line'
    )

    color_map = {
        "HIGH": "#ff3860",
        "MEDIUM": "#ffdd57",
        "LOW": "#23d160"
    }

    # build node map first — ensures consistent keys for edges
    node_map = {}
    for node in G.nodes():
        node_map[node] = str(node)

    for node, node_id in node_map.items():
        risk_level = risk.get(node, 'LOW')
        color = color_map[risk_level]
        label = node.replace('\\', '/').split('/')[-1]
        size = 18 + (G.in_degree(node) * 5)

        net.add_node(
            node_id,
            label=label,
            color={
                'background': color,
                'border': color,
                'highlight': {'background': '#ffffff', 'border': color}
            },
            size=size,
            font={'size': 14, 'color': '#ffffff', 'face': 'monospace'},
            borderWidth=2,
            shadow=True,
             title=f"File: {label}\nRisk: {risk_level}\nConnections: {G.in_degree(node)}"
        )

    for edge in G.edges():
        src = node_map.get(edge[0], str(edge[0]))
        dst = node_map.get(edge[1], str(edge[1]))
        if src in net.get_nodes() and dst in net.get_nodes():
            net.add_edge(
                src, dst,
                color={'color': '#ffffff33'},
                width=1.5,
                arrows={'to': {'enabled': True, 'scaleFactor': 0.6}}
            )

    net.set_options("""
    {
      "nodes": {
        "borderWidth": 2,
        "shadow": {
          "enabled": true,
          "color": "rgba(0,0,0,0.8)",
          "size": 15,
          "x": 0,
          "y": 0
        }
      },
      "edges": {
        "smooth": {
          "type": "curvedCW",
          "roundness": 0.2
        },
        "shadow": false
      },
      "interaction": {
        "hover": true,
        "navigationButtons": false,
        "hideEdgesOnDrag": true,
        "tooltipDelay": 100
      },
      "physics": {
        "stabilization": {
          "enabled": true,
          "iterations": 200
        },
        "barnesHut": {
          "gravitationalConstant": -12000,
          "centralGravity": 0.1,
          "springLength": 250,
          "springConstant": 0.02,
          "damping": 0.09
        }
      }
    }
    """)

    output_path = os.path.join(os.getcwd(), 'brain_map.html')

    html_content = net.generate_html()
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    with open(output_path, 'r', encoding='utf-8') as f:
        html = f.read()

    custom_style = """
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { background: #0d0d0d; font-family: 'Courier New', monospace; }
#mynetwork {
    background: radial-gradient(ellipse at center, #1a1a2e 0%, #0d0d0d 100%);
    border: none !important;
}
.legend {
    position: fixed;
    top: 20px;
    left: 20px;
    background: rgba(13,13,13,0.9);
    border: 1px solid #333;
    border-radius: 12px;
    padding: 16px 20px;
    color: #fff;
    font-family: monospace;
    font-size: 13px;
    z-index: 1000;
    backdrop-filter: blur(10px);
}
.legend-title {
    color: #888;
    font-size: 11px;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 12px;
}
.legend-item { display: flex; align-items: center; gap: 10px; margin: 8px 0; }
.dot { width: 12px; height: 12px; border-radius: 50%; box-shadow: 0 0 8px currentColor; }
.high { background: #ff3860; color: #ff3860; }
.medium { background: #ffdd57; color: #ffdd57; }
.low { background: #23d160; color: #23d160; }
.brain-title {
    position: fixed;
    top: 20px;
    right: 20px;
    color: #444;
    font-family: monospace;
    font-size: 12px;
    letter-spacing: 3px;
    text-transform: uppercase;
    z-index: 1000;
}
div.vis-tooltip {
    background: #1a1a2e !important;
    border: 1px solid #ff3860 !important;
    border-radius: 8px !important;
    color: #fff !important;
    font-family: monospace !important;
    font-size: 12px !important;
    padding: 10px 14px !important;
}
</style>
<div class="legend">
    <div class="legend-title">Risk Level</div>
    <div class="legend-item"><div class="dot high"></div><span>High Risk</span></div>
    <div class="legend-item"><div class="dot medium"></div><span>Medium Risk</span></div>
    <div class="legend-item"><div class="dot low"></div><span>Low Risk</span></div>
</div>
<div class="brain-title">Codebase Brain</div>
"""

    html = html.replace('<body>', '<body>' + custom_style)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"Nodes in graph: {len(G.nodes())}")
    print(f"Edges in graph: {len(G.edges())}")
    print(f"Graph saved to {output_path}")


def get_impact(G, filepath):
    import networkx as nx
    import os

    # Normalize incoming path
    target_norm = os.path.abspath(filepath).replace('\\', '/')
    target_rel = filepath.replace('\\', '/').lstrip('./')

    # Find matching node — handles both absolute and relative keys
    matched = None

    for node in G.nodes():
        node_norm = os.path.abspath(node).replace('\\', '/')
        if node_norm == target_norm:
            matched = node
            break

    if not matched:
        return None

    direct = list(G.predecessors(matched))
    all_affected = nx.ancestors(G, matched)
    indirect = [f for f in all_affected if f not in direct]

    return {
        'target': matched,
        'direct': direct,
        'indirect': indirect,
        'total_affected': len(direct) + len(indirect)
    }

if __name__ == "__main__":
    brain = load_brain()
    G = build_graph(brain)
    visualize_interactive(G)

    print("\nRisk Report:")
    for node, level in calculate_risk(G).items():
        print(f"  {node.split(chr(92))[-1]}: {level}")
