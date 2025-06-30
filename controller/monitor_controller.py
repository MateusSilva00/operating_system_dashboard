"""
Monitor Controller - Controlador principal do dashboard
Responsável pela coleta de dados do sistema e disponibilizá-los para a interface
"""

import threading
import time

from model.file_info import FileInfo
from model.process_info import ProcessInfo
from model.system_info import MemoryInfo


class MonitorController:
    """
    Executa em thread separada para não bloquear a interface gráfica
    """

    def __init__(self, refresh_interval: int = 1):
        self.refresh_interval = refresh_interval  # Frequência de atualização dos dados
        self._running = False  # Flag para controlar execução da thread

        # Thread daemon para coleta de dados em background
        self.thread = threading.Thread(target=self.run, daemon=True)

        # Lock para proteger acesso concorrente aos dados
        self._data_lock = threading.Lock()

        # Instâncias dos modelos de dados
        self.system_info = MemoryInfo()
        self.process_info = ProcessInfo()
        self.file_info = FileInfo()

        self.data: dict = {}

    def start(self):
        self._running = True
        self.thread.start()

    def stop(self):
        # para a thread de coleta de dados aguarda até 2 segundos para a thread terminar

        self._running = False
        if self.thread.is_alive():
            self.thread.join(timeout=2)

    def run(self):
        """
        loop principal de coleta de dados
        executa continuamente enquanto _running for True
        """
        while self._running:
            try:
                # coleta dados de uso da CPU (/proc/stat)
                cpu = self.system_info.get_cpu_usage()

                # coleta dados de uso da memória (/proc/meminfo)
                mem = self.system_info.get_mem_usage()

                # coleta informações de processos e threads (/proc/*/status, /proc/*/task)
                processes = self.process_info.get_process_info()

                # Conta total de processos no sistema
                total_processes = self.process_info.count_processes()

                # Conta total de threads no sistema
                total_threads = self.process_info.count_threads()

                # obtém os processos que mais consomem memória (top 50)
                top_processes = self.process_info.get_top_processes_by_memory(limit=50)

                with self._data_lock:
                    self.data = {
                        "cpu": cpu,  # dados de CPU (uso, tempo total, tempo ocioso)
                        "mem": mem,  # dados de memória (total, usado, livre, cache, etc.)
                        "processes": processes,
                        "total_processes": total_processes,
                        "total_threads": total_threads,
                        "top_processes": top_processes,
                    }

            except Exception:
                import traceback

                traceback.print_exc()

            time.sleep(self.refresh_interval)

    def get_data(self) -> dict:
        # retorna os dados mais recentes coletados pelo monitor
        with self._data_lock:
            return self.data.copy()
