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
            try:
                # print("Coletando dados do sistema...")  # Debug

                cpu = self.system_info.get_cpu_usage()
                # print(f"CPU: {cpu}")  # Debug

                mem = self.system_info.get_mem_usage()
                # print(f"Memória: {type(mem)}")  # Debug

                processes, threads = self.process_info.get_process_info()
                # print(f"Processos: {len(processes)}, Threads: {len(threads)}")  # Debug

                total_processes = self.process_info.count_processes()
                total_threads = self.process_info.count_threads()
                # print(f"Total processos: {total_processes}, Total threads: {total_threads}")  # Debug

                top_processes = self.process_info.get_top_processes_by_memory()
                # print(f"Top processos: {len(top_processes)}")  # Debug

                self.data = {
                    "cpu": cpu,
                    "mem": mem,
                    "processes": processes,
                    "threads": threads,
                    "total_processes": total_processes,
                    "total_threads": total_threads,
                    "top_processes": top_processes,
                }

                # print("Dados atualizados com sucesso")  # Debug

            except Exception as e:
                # print(f"Erro na coleta de dados: {e}")
                import traceback

                traceback.print_exc()

            time.sleep(self.refresh_interval)

    def get_data(self) -> dict:
        return self.data
