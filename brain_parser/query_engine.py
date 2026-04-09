import json
import os
from groq import Groq
from brain_parser.codebase_walker import load_brain
from dotenv import load_dotenv

def get_client():
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    if not api_key:
        raise ValueError("No API key found. Run 'brain init' first.")
    return Groq(api_key=api_key), model

def get_client():
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    if not api_key:
        raise ValueError("No API key found. Run 'brain init' first.")
    return Groq(api_key=api_key), model


def find_relevant_context(brain, question):
    scores = {}
    question_lower = question.lower()
    question_words = set(question_lower.split())

    for filepath, data in brain.items():
        score = 0

        # filename match → high value
        filename = filepath.lower()
        for word in question_words:
            if word in filename:
                score += 3

        # function name match → high value
        for func in data.get('functions', []):
            if func['name'].lower() in question_lower:
                score += 3

        # class name match → high value
        for cls in data.get('classes', []):
            if cls['name'].lower() in question_lower:
                score += 3

        # import match → medium value
        for imp in data.get('imports', []):
            name = imp.get('name', '').lower()
            if any(word in name for word in question_words):
                score += 2

        # summary match → medium value
        summary = data.get('summary', '').lower()
        for word in question_words:
            if word in summary:
                score += 1

        scores[filepath] = score

    # sort by score → take top 5
    sorted_files = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_5 = dict([(f, brain[f]) for f, s in sorted_files[:5] if s > 0])

    # if nothing scored → fall back to top 5 by score anyway
    if not top_5:
        top_5 = dict([(f, brain[f]) for f, s in sorted_files[:5]])

    return top_5


def ask_brain(question):
    client, model = get_client()
    brain = load_brain()
    if not brain:
        return "Brain is empty. Run walker first."

    context = find_relevant_context(brain, question)
    # Limit to 5 most relevant files maximum
    if len(context) > 5:
        context = dict(list(context.items())[:5])
    context_str = json.dumps(context, indent=2)

    prompt = f"""You are an intelligent codebase brain.
You have deep knowledge of this codebase structure.
Here is what you know:

{context_str}

Answer this question precisely and clearly:
{question}"""

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content


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