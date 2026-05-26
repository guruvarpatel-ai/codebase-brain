import argparse
import os
import threading
import subprocess
import stat
from brain_parser.codebase_walker import walk_codebase, save_brain
from brain_parser.file_watcher import start_watching
from brain_parser.graph_builder import build_graph, visualize_interactive
from brain_parser.query_engine import ask_brain


def cmd_start(path):
    print(" Codebase Brain starting...")
    print(f" Reading codebase at: {path}")
    brain = walk_codebase(path)
    save_brain(brain)
    print(f"Brain built: {len(brain)} files analyzed")

    print(" Building dependency graph...")
    G = build_graph(brain)
    visualize_interactive(G)
    print("Graph ready: brain_map.html")

    print("\n Scanning for bugs...")
    from brain_parser.bug_detector import run_all_detectors
    bugs = run_all_detectors(brain, G)
    if bugs:
        print(f"\n Found {len(bugs)} potential bugs:\n")
        for bug in bugs:
            print(f"  [{bug['severity']}] {bug['type'].replace('_', ' ').upper()}")
            print(f"  {bug['message']}")
            print(f"  Fix: {bug['fix']}\n")
    else:
        print(" No bugs detected. Codebase looks clean.\n")

    print("Starting live file watcher...")
    watcher_thread = threading.Thread(
        target=start_watching,
        args=(path,),
        daemon=True
    )
    watcher_thread.start()
    print("Watching for changes...")

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


def cmd_impact(filepath=None, staged=False):
    from brain_parser.codebase_walker import load_brain
    from brain_parser.graph_builder import build_graph, get_impact, calculate_risk

    brain = load_brain()
    if not brain:
        print("No brain found. Run 'brain start' first.")
        return

    G = build_graph(brain)
    risk = calculate_risk(G)

    root = os.path.abspath('.').replace('\\', '/')
    def clean(path):
        return path.replace('\\', '/').replace(root + '/', '')

    if staged:
        result = subprocess.run(
            ["git", "diff", "--name-only", "--cached"],
            capture_output=True, text=True
        )
        staged_files = [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]

        if not staged_files:
            print("No staged files found.")
            return

        print(f"\n Staged files: {', '.join(staged_files)}\n")
        for f in staged_files:
            print(f"{'='*50}")
            _print_impact(G, risk, f, clean)
        return

    if not filepath:
        print("Provide --file or --staged.")
        return

    _print_impact(G, risk, filepath, clean)


def _print_impact(G, risk, filepath, clean):
    from brain_parser.graph_builder import get_impact
    result = get_impact(G, filepath)

    if not result:
        print(f"File not found in brain: {filepath}")
        return

    print(f"\n Change Impact: {filepath}")
    print(f"   Risk Level: {risk.get(result['target'], 'LOW')}\n")
    print(f"DIRECT IMPACT ({len(result['direct'])} files):")
    for f in result['direct']:
        print(f"  → {clean(f)}")
    print(f"\nINDIRECT IMPACT ({len(result['indirect'])} files):")
    for f in result['indirect']:
        print(f"  → {clean(f)}")
    print(f"\nTotal files affected: {result['total_affected']}\n")


def install_hook(repo_path="."):
    hook_dir = os.path.join(repo_path, ".git", "hooks")
    hook_path = os.path.join(hook_dir, "pre-commit")

    if not os.path.exists(hook_dir):
        print("Not a git repository. Run this inside your project folder.")
        return

    hook_script = """#!/bin/sh
# Codebase Brain — Pre-commit Impact Check
# https://github.com/guruvarpatel-ai/codebase-brain

STAGED=$(git diff --name-only --cached)

if [ -z "$STAGED" ]; then
  exit 0
fi

echo ""
echo "Codebase Brain — Checking blast radius..."
echo ""

brain impact --staged

echo ""
echo "Powered by Codebase Brain"
echo ""
"""

    with open(hook_path, "w", newline='\n') as f:  # newline='\n' fixes Windows CRLF
        f.write(hook_script)

    os.chmod(hook_path, os.stat(hook_path).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    print(f"Brain hook installed at {hook_path}")
    print("Every commit now shows blast radius automatically.")


def cmd_init():
    print("Initializing Codebase Brain...\n")
    api_key = input("Enter your Groq API key: ").strip()
    model = input("Enter model name (press Enter for default): ").strip()
    if not model:
        model = "llama-3.3-70b-versatile"
    with open(".env", "w") as f:
        f.write(f"GROQ_API_KEY={api_key}\n")
        f.write(f"GROQ_MODEL={model}\n")
    print("\nBrain initialized successfully.")
    print("Run 'brain start' to begin.\n")


def main():
    parser = argparse.ArgumentParser(
        description="Codebase Brain - AI layer over your codebase"
    )
    # ← "install-hook" added here
    parser.add_argument("command", choices=["start", "init", "impact", "install-hook"])
    parser.add_argument("--path", default=".", help="Path to codebase")
    parser.add_argument("--file", default="", help="File to analyze impact")
    parser.add_argument("--staged", action="store_true", help="Analyze all staged files")  # ← new
    args = parser.parse_args()

    if args.command == "init":
        cmd_init()
    elif args.command == "start":
        cmd_start(args.path)
    elif args.command == "impact":
        cmd_impact(filepath=args.file or None, staged=args.staged)
    elif args.command == "install-hook":
        install_hook()


if __name__ == "__main__":
    main()