import threading
import time

from model.process_info import (
    count_processes_and_threads,
    get_process_details,
    get_process_info,
    get_top_processes_by_memory,
)
from model.system_info import get_cpu_usage, get_memory_info
from view.terminal_view import print_dashboard, print_process_details


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
            processes = get_process_info()
            process_thrads = count_processes_and_threads(processes)
            top_procs = get_top_processes_by_memory(processes, 5)

            print_dashboard(
                cpu_usage=cpu,
                memory_info=memory,
                total_processes=process_thrads["total_processes"],
                total_threads=process_thrads["total_threads"],
                processes=top_procs,
            )

            print(
                "\nDigite um PID para ver detalhes ou pressione ENTER para atualizar:"
            )
            user_input = input("PID > ").strip()

            if user_input.isdigit():
                pid = int(user_input)
                proc_details = get_process_details(pid)
            print_process_details(proc_details)

            time.sleep(self.refresh_interval)
