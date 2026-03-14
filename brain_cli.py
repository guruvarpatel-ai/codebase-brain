import argparse
import os
import threading
from brain_parser.codebase_walker import walk_codebase, save_brain
from brain_parser.file_watcher import start_watching
from brain_parser.graph_builder import build_graph, visualize_interactive
from brain_parser.query_engine import ask_brain


def cmd_start(path):
    print(" Codebase Brain starting...")

    # Step 1: Walk and build memory
    print(f" Reading codebase at: {path}")
    brain = walk_codebase(path)
    save_brain(brain)
    print(f"Brain built: {len(brain)} files analyzed")

    # Step 2: Build graph
    print(" Building dependency graph...")
    G = build_graph(brain)
    visualize_interactive(G)
    print("Graph ready: brain_map.html")

    # Step 3: Start file watcher in background
    print("Starting live file watcher...")
    watcher_thread = threading.Thread(
        target=start_watching,
        args=(path,),
        daemon=True
    )
    watcher_thread.start()
    print("Watching for changes...")

    # Step 4: Start query loop
    print("\n Brain is live. Ask anything.")
    print("Type 'exit' to stop query mode.")
    print("Press CTRL+C anytime to shut down completely.\n")
    while True:
        question = input("Ask your brain: ")
        if question == "exit":
            print("Brain shutting down.")
            break
        answer = ask_brain(question)
        print(f"\nBrain: {answer}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Codebase Brain - AI layer over your codebase"
    )
    parser.add_argument("command", choices=["start", "init"])
    parser.add_argument("--path", default=".", help="Path to codebase")
    args = parser.parse_args()

    if args.command == "init":
        cmd_init()
    elif args.command == "start":
        cmd_start(args.path)

def cmd_init():
    print("Initializing Codebase Brain...\n")

    api_key = input("Enter your Groq API key: ").strip()

    model = input(
        "Enter model name (press Enter for default): "
    ).strip()

    if not model:
        model = "llama-3.3-70b-versatile"

    with open(".env", "w") as f:
        f.write(f"GROQ_API_KEY={api_key}\n")
        f.write(f"GROQ_MODEL={model}\n")

    print("\nBrain initialized successfully.")
    print("Run 'brain start' to begin.\n")


if __name__ == "__main__":
    main()