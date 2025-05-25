"""
Process Info - Modelo responsável pela coleta de informações de processos e threads
Utiliza o sistema de arquivos /proc para obter dados detalhados de todos os processos
"""

import os

# diretório raiz do sistema de arquivos /proc
PROC_DIR = "/proc"


class ProcessInfo:
    """
    Classe responsável por coletar e processar informações de processos e threads
    Navega pelo /proc para extrair dados de cada processo do sistema
    """

    def __init__(self):
        # Cache para mapear UIDs para nomes de usuário (evita múltiplas leituras do /etc/passwd)
        self._uid_cache = self._build_uid_cache()

    def _build_uid_cache(self) -> dict:
        """
        constrói cache de mapeamento UID para username
        lê o arquivo /etc/passwd uma única vez para mapear IDs de usuário para nomes
        """
        uid_to_username = {}
        try:
            with open("/etc/passwd", "r") as passwd_file:
                for line in passwd_file:
                    # Formato: username:x:uid:gid:info:home:shell
                    parts = line.strip().split(":")
                    if len(parts) >= 3:
                        uid_to_username[parts[2]] = parts[0]  # uid -> username
        except FileNotFoundError:
            pass
        return uid_to_username

    def _get_proc_entries(self) -> list:
        """
        obtém lista de PIDs válidos em /proc
        filtra apenas diretórios com nomes numéricos
        """
        try:
            # lista todos os entries em /proc que são números (PIDs)
            return [entry for entry in os.listdir(PROC_DIR) if entry.isdigit()]
        except (FileNotFoundError, PermissionError):
            return []

    def _parse_process_status(self, pid: str) -> dict:
        """
        extrai informações do arquivo /proc/PID/status de um processo

        arquivo status contém informações como:
        - Name: nome do processo
        - State: estado atual (R=running, S=sleeping, etc.)
        - Uid: ID do usuário proprietário
        - VmRSS: memória residente (RAM física usada)
        - Threads: número de threads do processo
        """
        process_data = {
            "user": "Unknown",
            "name": "Unknown",
            "status": "Unknown",
            "memory_kb": 0,
            "thread_count": 1,
        }

        try:
            with open(f"{PROC_DIR}/{pid}/status", "r") as file:
                for line in file:
                    if line.startswith("Uid:"):
                        # Extrai UID e converte para nome de usuário
                        uid_parts = line.split()
                        if len(uid_parts) > 1:
                            uid = uid_parts[1]
                            process_data["user"] = self._uid_cache.get(
                                uid, f"UID:{uid}"
                            )
                    elif line.startswith("Name:"):
                        process_data["name"] = line.split(":", 1)[1].strip()
                    elif line.startswith("State:"):
                        process_data["status"] = line.split(":", 1)[1].strip()
                    elif line.startswith("VmRSS:"):
                        # Memória residente em kB (RAM física usada)
                        try:
                            process_data["memory_kb"] = int(line.split()[1])
                        except (ValueError, IndexError):
                            pass
                    elif line.startswith("Threads:"): # número de threads do processo
                        try:
                            process_data["thread_count"] = int(line.split()[1])
                        except (ValueError, IndexError):
                            pass
        except (FileNotFoundError, PermissionError, ValueError):
            # caso não conseguir ler o arquivo, mantém valores padrão
            pass

        return process_data

    def _collect_threads_for_process(
        self, pid: str, process_data: dict, max_threads: int = 5
    ) -> list:
        """
        coleta informações de threads para um processo específico

        cada processo pode ter múltiplas threads listadas em /proc/PID/task/
        coleta informações detalhadas de até max_threads por processo
        """
        threads = []
        try:
            task_dir = f"/proc/{pid}/task"
            if os.path.exists(task_dir):
                # lista todas as threads (TIDs) do processo
                task_entries = [t for t in os.listdir(task_dir) if t.isdigit()]

                # limita o número de threads coletadas por processo (performance)
                for tid in task_entries[:max_threads]:
                    thread_status = process_data["status"]

                    try:
                        # tenta ler status específico da thread
                        with open(f"/proc/{pid}/task/{tid}/status", "r") as tf:
                            for tline in tf:
                                if tline.startswith("State:"):
                                    thread_status = tline.split(":", 1)[1].strip()
                                    break
                    except (FileNotFoundError, PermissionError):
                        # se não conseguir ler, usa status do processo pai
                        pass

                    threads.append(
                        {
                            "TID": tid,  # thread ID
                            "PID": pid,  # process ID pai
                            "User": process_data["user"],  # usuário proprietário
                            "Name": process_data["name"],  # nome do processo
                            "Status": thread_status,  # estado da thread
                        }
                    )
        except (FileNotFoundError, PermissionError):
            pass
        return threads

    def get_process_info(self) -> tuple:
        """
        obtém informações de todos os processos e threads do sistema

        percorre todos os diretórios em /proc que representam processos,
        extrai informações de cada um e coleta dados de suas threads
        """
        processes = []
        threads = []
        proc_entries = self._get_proc_entries()

        for pid in proc_entries:
            process_data = self._parse_process_status(pid)

            # adiciona processo à lista
            processes.append(
                {
                    "PID": pid,
                    "User": process_data["user"],
                    "Name": process_data["name"],
                    "Status": process_data["status"],
                    "Memory": process_data["memory_kb"],
                    "Threads": process_data["thread_count"],
                }
            )

            # coleta threads do processo
            if len(threads) < 400:  # limite de threads coletadas
                thread_list = self._collect_threads_for_process(pid, process_data)
                threads.extend(thread_list)

        return processes, threads

    def count_processes(self) -> int:
        return len(self._get_proc_entries())

    def count_threads(self) -> int:
        total_threads = 0
        for pid in self._get_proc_entries():
            try:
                with open(f"{PROC_DIR}/{pid}/status", "r") as f:
                    for line in f:
                        if line.startswith("Threads:"):
                            try:
                                total_threads += int(line.split()[1])
                            except (ValueError, IndexError):
                                total_threads += 1  # assume pelo menos 1 thread
                            break
            except (FileNotFoundError, PermissionError):
                continue
        return total_threads

    def get_top_processes_by_memory(self, limit=15) -> list:
        # Retorna os processos que mais consomem memória
        processes, _ = self.get_process_info()

        # filtra apenas processos com memória válida (> 0)
        valid_processes = [
            p
            for p in processes
            if isinstance(p.get("Memory", 0), (int, float)) and p.get("Memory", 0) > 0
        ]

        # ordena por memória em ordem decrescente
        sorted_processes = sorted(
            valid_processes, key=lambda x: x.get("Memory", 0), reverse=True
        )

        return sorted_processes[:limit]

    def get_process_by_pid(self, pid: str) -> int:
        # obtém uso de memória de um processo específico
        try:
            with open(os.path.join(PROC_DIR, str(pid), "status")) as f:
                for line in f:
                    if line.startswith("VmRSS:"):
                        return int(line.split()[1])
        except (FileNotFoundError, ValueError):
            pass
        return None

    def get_page_usage_by_pid(self, pid: str) -> dict:
        """
        obtém uso detalhado de páginas de memória por processo

        lê o arquivo /proc/PID/smaps que contém mapeamento detalhado
        de memória do processo, incluindo heap, stack, código, etc.
        """
        page_usage = {"total": 0, "code": 0, "heap": 0, "stack": 0}
        try:
            with open(f"/proc/{pid}/smaps", "r") as f:
                for line in f:
                    if "Size:" in line:
                        # soma tamanho total de todas as regiões
                        page_usage["total"] += int(line.split()[1])
                    elif "[heap]" in line:
                        # região de heap
                        page_usage["heap"] += int(next(f).split()[1])
                    elif "[stack]" in line:
                        # região de stack
                        page_usage["stack"] += int(next(f).split()[1])
                    elif ".text" in line:
                        # região de código executável
                        page_usage["code"] += int(next(f).split()[1])
        except (FileNotFoundError, PermissionError, ValueError, StopIteration):
            pass
        return page_usage

    def get_process_details(self, pid: str) -> dict:
        """
        obtém detalhes completos de um processo

        combina informações do /proc/PID/status e /proc/PID/cmdline
        para fornecer visão completa do processo
        """
        process_details = {}
        try:
            # lê linha de comando do processo
            with open(os.path.join(PROC_DIR, str(pid), "cmdline"), "rb") as f:
                cmdline = f.read().decode().replace("\x00", " ").strip()
                process_details["Command Line"] = cmdline if cmdline else None

            # lê todas as informações do status
            with open(os.path.join(PROC_DIR, str(pid), "status"), "r") as f:
                for line in f:
                    if ":" in line:
                        key, value = line.split(":", 1)
                        process_details[key.strip()] = value.strip()
        except (FileNotFoundError, UnicodeDecodeError):
            pass
        return process_details

    def get_all_page_usage(self) -> dict:
        # obtém uso de páginas para todos os processos
        all_page_usage = {}
        for pid in self._get_proc_entries():
            page_usage = self.get_page_usage_by_pid(pid)
            if page_usage and any(page_usage.values()):
                all_page_usage[pid] = page_usage
        return all_page_usage

    def get_all_process_details(self) -> dict:
        # obtém detalhes de todos os processos
        all_process_details = {}
        for pid in self._get_proc_entries():
            process_details = self.get_process_details(pid)
            if process_details:
                all_process_details[pid] = process_details
        return all_process_details


# teste 
if __name__ == "__main__":
    process = ProcessInfo()
    processes, threads = process.get_process_info()
    print(f"Processos: {len(processes)}, Threads: {len(threads)}")
