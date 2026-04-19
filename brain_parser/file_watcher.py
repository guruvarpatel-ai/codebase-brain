import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from brain_parser.universal_parser import parse_file
from brain_parser.codebase_walker import walk_codebase, save_brain, load_brain

class BrainEventHandler(FileSystemEventHandler):
    def __init__(self):
        self.brain = load_brain() or {}

    SKIP_WATCH = {'.git', '.idea', '__pycache__', 'node_modules', 'lib'}

    def should_skip(path):
        # skip git, ide, temp files
        if path.endswith('~'):
            return True
        for skip in SKIP_WATCH:
            if skip in path.replace('\\', '/'):
                return True
        return False

    def on_modified(self, event):
        if event.is_directory:
            return
        if should_skip(event.src_path):
            return
        # skip brain output files

        if event.src_path.endswith('brain.json') or event.src_path.endswith('brain_map.html'):
            return
        print(f"Modified: {event.src_path}")
        result = parse_file(event.src_path)
        if result and result['language'] != 'unknown':
            self.brain[event.src_path] = result
            save_brain(self.brain)

    def on_created(self, event):
        if should_skip(event.src_path):
            return
        if not event.is_directory:
            print(f"New file: {event.src_path}")
            result = parse_file(event.src_path)
            if result and result['language'] != 'unknown':
                self.brain[event.src_path] = result
                save_brain(self.brain)

    def on_deleted(self, event):
        if should_skip(event.src_path):
            return
        if not event.is_directory:
            print(f"Deleted: {event.src_path}")
            if event.src_path in self.brain:
                del self.brain[event.src_path]
                save_brain(self.brain)


def start_watching(path="."):
    brain = load_brain() or {}
    if not brain:
        print("No brain found. Building first...")
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