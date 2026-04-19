import networkx as nx
import os
from brain_parser.codebase_walker import load_brain
from brain_parser.graph_builder import build_graph



def detect_circular_dependencies(brain):
    # build graph from brain → find cycles → report files involved
    G = build_graph(brain)

    bugs = []

    try:
        cycles = list(nx.simple_cycles(G))
        for cycle in cycles:
            bugs.append({
                'type': 'circular_dependency',
                'severity': 'HIGH',
                'files': cycle,
                'message': f"Circular dependency detected: {' → '.join(cycle)} → {cycle[0]}",
                'fix': 'Extract shared logic into a separate file that both can import from.'
            })
    except Exception as e:
        print(f"Cycle detection error: {e}")

    return bugs


def detect_unused_imports(brain):
    # compare imports list against function/class names used in file
    bugs = []

    for filepath, data in brain.items():
        # skip non-python files until we support body reading
        if data.get('language') != 'python':
            continue
        imports = data.get('imports', [])
        functions = [f['name'].lower() for f in data.get('functions', [])]
        classes = [c['name'].lower() for c in data.get('classes', [])]
        summary = data.get('summary', '').lower()

        for imp in imports:
            imp_name = imp.get('name', '').lower()
            # extract just the module name
            imp_name = imp.get('name', '').lower()

            # handle "from x import y" → extract x
            if imp_name.startswith('from '):
                module = imp_name.split('from ')[1].split(' import')[0].strip()
            # handle "import x" → extract x
            elif imp_name.startswith('import '):
                module = imp_name.replace('import ', '').split(' as ')[0].strip()
            else:
                continue

            if not module:
                continue

            # check if module appears anywhere in file context
            used = (
                    any(module in f for f in functions) or
                    any(module in c for c in classes) or
                    module in summary
            )

            if not used:
                bugs.append({
                    'type': 'unused_import',
                    'severity': 'LOW',
                    'file': filepath,
                    'import': imp.get('name', ''),
                    'line': imp.get('line', 0),
                    'message': f"Possibly unused import '{module}' in {filepath}",
                    'fix': f"Remove 'import {module}' if not needed."
                })

    return bugs

def detect_bugs_with_llm(brain, G):
    # calculate risk → filter HIGH risk files → send to Groq → find bugs
    from brain_parser.graph_builder import calculate_risk
    from groq import Groq
    from dotenv import load_dotenv
    load_dotenv()

    risk = calculate_risk(G)
    high_risk_files = [f for f, r in risk.items() if r == "HIGH"]

    if not high_risk_files:
        return []

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    bugs = []

    for filepath in high_risk_files:
        data = brain.get(filepath)
        if not data:
            continue

        summary = data.get('summary', '')
        functions = [f['name'] for f in data.get('functions', [])]
        imports = [i['name'] for i in data.get('imports', [])]

        prompt = f"""You are a senior code reviewer. Analyze this file for bugs.

        File: {filepath}
        Summary: {summary}
        Functions: {functions}
        Imports: {imports}

        Rules:
        - Only report bugs you can prove from the information given
        - Every bug must reference a specific function name from the functions list
        - Do not invent bugs that are not evident from the summary
        - If no provable bugs exist respond with exactly: NO BUGS

        Format each bug exactly like this:
        BUG: [function_name] description of specific problem
        FIX: specific code change needed"""

        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature = 0
            )
            result = response.choices[0].message.content.strip()

            if "NO BUGS" not in result:
                bugs.append({
                    'type': 'llm_detected_bug',
                    'severity': 'HIGH',
                    'file': filepath,
                    'message': result,
                    'fix': 'See details above'
                })
        except Exception as e:
            print(f"LLM bug detection error for {filepath}: {e}")

    return bugs


def run_all_detectors(brain=None, G=None):
    if not brain:
        brain = load_brain()
    if not brain:
        return []

    bugs = []
    bugs.extend(detect_circular_dependencies(brain))
    # TODO: Week 4 - LLM bug detection needs function bodies for accuracy
    # bugs.extend(detect_bugs_with_llm(brain, G))

    return bugs

if __name__ == "__main__":
    bugs = run_all_detectors()
    print(f"\nFound {len(bugs)} potential bugs:\n")
    for bug in bugs:
        print(f"[{bug['severity']}] {bug['type']}")
        print(f"  {bug['message']}")
        print(f"  Fix: {bug['fix']}\n")