import threading
import time

from model.system_info import get_cpu_usage, get_memory_info
from view.terminal_view import print_dashboard


class MonitorController:
    def __init__(self, refresh_interval: int = 1):
        self.refresh_interval = refresh_interval
        self._running = False
        self.thread = threading.Thread(target=self.run, daemon=True)

    def start(self):
        self._running = True
        self.thread.start()
        while self._running:
            time.sleep(0.1)  # Keep the main thread alive
        
    
    def stop(self):
        self._running = False
    
    def run(self):
        while self._running:
            cpu = get_cpu_usage()
            memory = get_memory_info()
            print_dashboard(cpu, memory)
            time.sleep(self.refresh_interval)
