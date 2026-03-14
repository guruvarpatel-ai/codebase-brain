import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from brain_parser.ast_parser import analyze_file
from brain_parser.codebase_walker import walk_codebase, save_brain, load_brain

class BrainEventHandler(FileSystemEventHandler):
    def __init__(self):
        self.brain = load_brain() or {}

    def on_modified(self, event):
        if event.src_path.endswith(".py"):
            print(f"Modified: {event.src_path}")
            result = analyze_file(event.src_path)
            if result:
                self.brain[event.src_path] = result
                save_brain(self.brain)

    def on_created(self, event):
        if event.src_path.endswith(".py"):
            print(f"New file: {event.src_path}")
            result = analyze_file(event.src_path)
            if result:
                self.brain[event.src_path] = result
                save_brain(self.brain)

    def on_deleted(self, event):
        if event.src_path.endswith(".py"):
            print(f"Deleted: {event.src_path}")
            if event.src_path in self.brain:
                del self.brain[event.src_path]
                save_brain(self.brain)


def start_watching(path="."):
    brain = load_brain() or {}
    if not brain:
        print("No brain found. Building first...")
        from codebase_walker import walk_codebase
        brain = walk_codebase(path)
        save_brain(brain)

    event_handler = BrainEventHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    print(f"Brain is watching: {path}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("Brain stopped.")
    observer.join()


if __name__ == "__main__":
    start_watching(".")