import threading
import time

from model.process_info import ProcessInfo
from model.system_info import MemoryInfo


class MonitorController:
    def __init__(self, refresh_interval: int = 1):
        self.refresh_interval = refresh_interval
        self._running = False
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.system_info = MemoryInfo()
        self.process_info = ProcessInfo()
        self.data: dict = {}

    def start(self):
        self._running = True
        self.thread.start()

    def stop(self):
        self._running = False

    def run(self):
        while self._running:
            cpu = self.system_info.get_cpu_usage()
            mem = self.system_info.get_mem_usage()
            processes = self.process_info.get_process_info()
            total_processes = self.process_info.count_processes()
            total_threads = self.process_info.count_threads()
            top_processes = self.process_info.get_top_processes_by_memory()

            self.data = {
                "cpu": cpu,
                "mem": mem,
                "processes": processes,
                "total_processes": total_processes,
                "total_threads": total_threads,
                "top_processes": top_processes,
            }
            time.sleep(self.refresh_interval)

    def get_data(self) -> dict:
        return self.data
