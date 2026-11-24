import sys
import time
import subprocess
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class RestartHandler(FileSystemEventHandler):
    def __init__(self, script_path):
        self.script_path = script_path
        self.process = None
        self.start_bot()

    def start_bot(self):
        if self.process:
            self.process.terminate()
            self.process.wait()
        print("Starting bot...")
        self.process = subprocess.Popen([sys.executable, self.script_path])

    def check_process(self):
        if self.process and self.process.poll() is not None:
            print("Bot process died, restarting...")
            self.start_bot()

    def on_modified(self, event):
        if event.src_path.endswith('.py') and not event.src_path.endswith('auto_restart.py'):
            print(f"File changed: {event.src_path}")
            self.start_bot()

if __name__ == "__main__":
    script_path = "your_bot.py"
    event_handler = RestartHandler(script_path)
    observer = Observer()
    observer.schedule(event_handler, path='.', recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
            event_handler.check_process()
    except KeyboardInterrupt:
        observer.stop()
        if event_handler.process:
            event_handler.process.terminate()
    observer.join()