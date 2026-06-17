import json
import os
from brain_parser.codebase_walker import load_brain
from dotenv import load_dotenv


def get_client():
    from brain_parser.llm_router import call_llm
    # returns a wrapper so existing code doesn't break
    load_dotenv()
    model = os.getenv("LLM_MODEL") or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    return None, model


def find_relevant_context(brain, question):
    from brain_parser.graph_builder import build_graph, calculate_risk

    # build graph and get risk scores
    G = build_graph(brain)
    risk = calculate_risk(G)

    scores = {}
    question_lower = question.lower()
    question_words = set(question_lower.split())

    for filepath, data in brain.items():
        score = 0

        filename = filepath.lower()
        for word in question_words:
            if word in filename:
                score += 3

        for func in data.get('functions', []):
            if func['name'].lower() in question_lower:
                score += 3

        for cls in data.get('classes', []):
            if cls['name'].lower() in question_lower:
                score += 3

        for imp in data.get('imports', []):
            name = imp.get('name', '').lower()
            if any(word in name for word in question_words):
                score += 2

        summary = data.get('summary', '').lower()
        for word in question_words:
            if word in summary:
                score += 1

        # boost score for HIGH risk files when question is about risk
        if risk.get(filepath) == 'HIGH':
            score += 2

        scores[filepath] = score

    sorted_files = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    # build context with risk scores included
    top_5 = {}
    for f, s in sorted_files[:5]:
        if f in brain:
            file_data = dict(brain[f])
            file_data['risk'] = risk.get(f, 'LOW')
            file_data['dependents'] = len(list(G.predecessors(f)))
            file_data.pop('content', None)  # strip raw content — too many tokens
            top_5[f] = file_data

    if not top_5:
        for f, s in sorted_files[:5]:
            if f in brain:
                file_data = dict(brain[f])
                file_data['risk'] = risk.get(f, 'LOW')
                file_data['dependents'] = len(list(G.predecessors(f)))
                file_data.pop('content', None)
                top_5[f] = file_data

    return top_5


def ask_brain(question):
    from brain_parser.llm_router import call_llm

    brain = load_brain()
    if not brain:
        return "Brain is empty. Run walker first."

    context = find_relevant_context(brain, question)
    if len(context) > 5:
        context = dict(list(context.items())[:5])
    context_str = json.dumps(context, indent=2)

    prompt = f"""You are an intelligent codebase brain.
You have deep knowledge of this codebase structure.
Here is what you know:

{context_str}

Answer this question precisely and clearly:
{question}"""

    return call_llm(prompt, max_tokens=500)

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


if __name__ == "__main__":
    while True:
        question = input("\nAsk your brain: ")
        if question == "exit":
            break
        answer = ask_brain(question)
        print(f"\nBrain: {answer}")