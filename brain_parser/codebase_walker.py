import os
import json
from brain_parser.ast_parser import analyze_file

def walk_codebase(root_path):
    brain = {}

    for folder, subfolders, files in os.walk(root_path):
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(folder, file)
                result = analyze_file(full_path)
                if result is not None:
                    brain[full_path] = result

    return brain
def save_brain(brain, output_path="brain.json"):
    with open(output_path, "w") as f:
        json.dump(brain, f, indent=4)
    print(f"Brain saved to {output_path}")

def load_brain(input_path="brain.json"):
    if not os.path.exists(input_path):
        print("No brain found. Run walker first.")
        return None
    with open(input_path, "r") as f:
        return json.load(f)


if __name__ == "__main__":
    brain = walk_codebase("../flask/src/flask")
    save_brain(brain)

    loaded = load_brain()
    print(f"Brain loaded with {len(loaded)} files")