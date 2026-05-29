import re
import os
from brain_parser.codebase_walker import load_brain
from brain_parser.graph_builder import build_graph, calculate_risk


# Patterns for each language stacktrace format
TRACE_PATTERNS = [
    # JavaScript/Node: at functionName (file.js:34:12)
    r'at\s+(?:\S+\s+)?\((.+?\.(?:js|ts)):(\d+)',
    # Python: File "file.py", line 34
    r'File\s+"(.+?\.py)",\s+line\s+(\d+)',
    # Java: at com.example.Class(File.java:34)
    r'at\s+[\w.]+\((\w+\.java):(\d+)\)',
]


def extract_frames(stacktrace):
    """Extract (filepath, line_number) pairs from any stacktrace."""
    frames = []
    for pattern in TRACE_PATTERNS:
        matches = re.findall(pattern, stacktrace)
        for filepath, line in matches:
            frames.append({
                'file': filepath.strip(),
                'line': int(line)
            })
    # deduplicate preserving order
    seen = set()
    unique = []
    for f in frames:
        key = (f['file'], f['line'])
        if key not in seen:
            seen.add(key)
            unique.append(f)
    return unique


def match_frame_to_graph(frame_file, G):
    """Match a short filename from stacktrace to full path in graph."""
    frame_norm = frame_file.replace('\\', '/')
    candidates = []

    for node in G.nodes():
        node_norm = node.replace('\\', '/')
        # exact suffix match — auth/middleware.js matches ./src/auth/middleware.js
        if node_norm.endswith(frame_norm):
            candidates.append(node)

    if not candidates:
        return None
    # prefer shortest path — most specific match
    return min(candidates, key=len)


def find_root_cause(stacktrace):
    """Main function — paste stacktrace, get root cause analysis."""
    brain = load_brain()
    if not brain:
        return {"error": "No brain found. Run 'brain start' first."}

    G = build_graph(brain)
    risk = calculate_risk(G)

    frames = extract_frames(stacktrace)
    if not frames:
        return {"error": "No file references found in stacktrace. Paste the full error including file paths."}

    results = []
    for frame in frames:
        matched_node = match_frame_to_graph(frame['file'], G)
        if not matched_node:
            continue

        # walk backwards — what files feed into this file
        import networkx as nx
        predecessors = list(G.predecessors(matched_node))
        ancestors = list(nx.ancestors(G, matched_node))

        # find functions in this file near the error line
        file_data = brain.get(matched_node, {})
        functions = file_data.get('functions', [])
        nearby_functions = [
            f for f in functions
            if abs(f['line'] - frame['line']) <= 10
        ]

        results.append({
            'file': matched_node,
            'line': frame['line'],
            'risk': risk.get(matched_node, 'LOW'),
            'nearby_functions': nearby_functions,
            'direct_causes': predecessors,
            'all_causes': ancestors,
        })

    if not results:
        return {"error": "Files in stacktrace not found in brain. Run 'brain start' to rebuild."}

    return _format_result(results, risk)


def _format_result(results, risk):
    lines = []
    lines.append("ROOT CAUSE ANALYSIS")
    lines.append("=" * 50)

    for i, r in enumerate(results, 1):
        lines.append(f"\n[{i}] {r['file']}  line {r['line']}  [{r['risk']}]")

        if r['nearby_functions']:
            lines.append("    Functions at error site:")
            for f in r['nearby_functions']:
                lines.append(f"      → {f['name']}() line {f['line']}")

        if r['direct_causes']:
            lines.append("    Direct causes (files that feed this):")
            for f in r['direct_causes']:
                lines.append(f"      ← {f}  [{risk.get(f, 'LOW')}]")

        if r['all_causes']:
            lines.append(f"    Full cause chain: {len(r['all_causes'])} files upstream")

    # Add Groq explanation
    lines.append("\n" + "=" * 50)
    lines.append("BRAIN DIAGNOSIS")
    lines.append("=" * 50)
    lines.append(_ask_groq_diagnosis(results, risk))

    return "\n".join(lines)


def _ask_groq_diagnosis(results, risk):
    try:
        from groq import Groq
        from dotenv import load_dotenv
        load_dotenv()
        import os

        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        context = ""
        for r in results:
            context += f"\nFile: {r['file']} (line {r['line']}, risk: {r['risk']})\n"
            if r['nearby_functions']:
                context += f"Functions: {[f['name'] for f in r['nearby_functions']]}\n"
            if r['direct_causes']:
                context += f"Fed by: {r['direct_causes']}\n"

        prompt = f"""You are a senior developer doing root cause analysis.
Given this dependency chain from a production error:
{context}

In 3 sentences max:
1. Which file is most likely the root cause and why
2. What the developer should check first
3. What likely went wrong

Be specific. Name the files and functions."""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0
        )
        return response.choices[0].message.content

    except Exception as e:
        return f"Could not get AI diagnosis: {str(e)}"