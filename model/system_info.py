"""
System Info - Modelo responsável pela coleta de informações do sistema
Coleta dados de CPU e memória através dos arquivos /proc/stat e /proc/meminfo
"""

import os
from typing import Dict, List, Optional

# caminhos dos arquivos de sistema no Linux
CPU_PATH = "/proc/stat"  # arquivo com estatísticas da CPU
MEM_PATH = "/proc/meminfo"  # arquivo com informações de memória
MOUNTS_PATH = "/proc/mounts"  # arquivo com informações de partições montadas


class MemoryInfo:
    def __init__(self):
        # armazena o último estado da CPU para calcular percentual de uso
        self._last_cpu_usage = None

        # inicializa as propriedades com dados atuais
        self.mem_info = self.get_memory_info()
        self.mem_usage = self.get_mem_usage()
        self.cpu_usage = self.get_cpu_usage()

    def get_cpu_usage(self) -> dict:
        """
        Calcula o percentual de uso da CPU comparando com a leitura anterior

        O arquivo /proc/stat contém:
        - user: tempo em modo usuário
        - nice: tempo em modo usuário com prioridade baixa
        - system: tempo em modo kernel
        - idle: tempo ocioso
        - iowait: tempo aguardando I/O
        - irq: tempo servindo interrupções
        - softirq: tempo servindo interrupções de software
        """

        # Lê a primeira linha do /proc/stat que contém estatísticas globais da CPU
        with open(CPU_PATH, "r") as f:
            lines = f.readlines()
            parts = lines[0].split()  # Separa os valores da linha 'cpu'

            # soma todos os tempos para obter tempo total (exceto o primeiro elemento 'cpu')
            total_time = sum(map(int, parts[1:]))

            # O 5º campo (índice 4) é o tempo ocioso
            idle_time = int(parts[4])

        # se é a primeira leitura, armazena os valores e retorna 0%
        if self._last_cpu_usage is None:
            self._last_cpu_usage = (total_time, idle_time)
            return {"usage": 0, "total": total_time, "idle": idle_time}

        # obtém os valores da leitura anterior
        last_total, last_idle = self._last_cpu_usage

        # calcula as diferenças entre leituras
        delta_total = total_time - last_total
        delta_idle = idle_time - last_idle

        # atualiza para próxima comparação
        self._last_cpu_usage = (total_time, idle_time)

        # evita divisão por zero
        if delta_total == 0:
            return {"usage": 0, "total": total_time, "idle": idle_time}

        # calcula percentual: (tempo_trabalhando / tempo_total) * 100
        usage = (delta_total - delta_idle) / delta_total * 100

        return {"usage": usage, "total": total_time, "idle": idle_time}

    def get_memory_info(self) -> dict:
        """
        Lê todas as informações de memória do arquivo /proc/meminfo
        - MemTotal: memória total do sistema
        - MemFree: memória livre
        - MemAvailable: memória disponível para novos processos
        - Buffers: memória usada para buffers
        - Cached: memória usada para cache
        - SwapTotal: espaço total de swap
        """

        info = {}
        with open(MEM_PATH, "r") as f:
            for line in f:
                key, value = line.split(":")
                # extrai apenas o valor numérico (remove 'kB' se presente)
                info[key.strip()] = int(value.strip().split()[0])

        return info

    def get_mem_usage(self) -> dict:
        """
        processa as informações brutas de memória para calcular métricas úteis

        calcula:
        - memória realmente em uso (total - livre - buffers - cache)
        - percentual de uso da memória
        - organiza informações para fácil consumo pela interface
        """

        self.mem_info = self.get_memory_info()

        # extrai valores principais (todos em kB)
        mem_total = self.mem_info["MemTotal"]
        mem_free = self.mem_info["MemFree"]  # memória completamente livre
        mem_available = self.mem_info["MemAvailable"]  # memória disponível para uso
        buffers = self.mem_info["Buffers"]
        cached = self.mem_info["Cached"]
        swap_total = self.mem_info["SwapTotal"]  # espaço total de swap

        # calcula memória realmente em uso pelos processos
        used_memory = mem_total - mem_free - buffers - cached

        # calcula percentual de uso da memória
        mem_percent_usage = (used_memory / mem_total) * 100

        return {
            "used_memory": used_memory,
            "cached_memory": cached,
            "available_memory": mem_available,
            "total_memory": mem_total,
            "swap_total": swap_total,
            "free_memory": mem_free,
            "buffers": buffers,
            "cached": cached,
            "mem_percent_usage": mem_percent_usage,
        }

    def get_disk_partitions(self) -> list:
        partitions = []
        with open("/proc/partitions", "r") as files:
            lines = files.readlines()[2:]
            for line in lines:
                parts = line.split()
                if len(parts) >= 4:
                    device = parts[3]
                    partitions.append(device)
        return partitions

    def get_partition_usage(self, partition_name) -> Optional[Dict[str, float]]:
        """
        Obtém informações de uso de uma partição específica
        """
        with open(MOUNTS_PATH, "r") as f:
            mounts = f.readlines()
            for mount in mounts:
                if partition_name in mount:
                    mount_info = mount.split()
                    mount_path = mount_info[1]
                    break
            else:
                mount_path = None

        if mount_path:
            usage = os.statvfs(mount_path)
            total = usage.f_frsize * usage.f_blocks
            free = usage.f_frsize * usage.f_bfree
            used = total - free
            percent_usage = (used / total) * 100 if total > 0 else 0

            return {
                "partition": partition_name,
                "mount_path": mount_path,
                "total_size": total,
                "used_size": used,
                "free_size": free,
                "percent_usage": percent_usage,
            }

        return None  # partição não montada ou não encontrada

    def get_process_open_files(self, pid: int) -> List[dict]:
        """
        Retorna uma lista de arquivos abertos pelo processo (fd)
        """
        files = []
        fd_path = f"/proc/{pid}/fd"
        if not os.path.exists(fd_path):
            return files
        try:
            for fd in os.listdir(fd_path):
                file_info = {}
                fd_full_path = os.path.join(fd_path, fd)
                try:
                    target = os.readlink(fd_full_path)
                    file_info["fd"] = fd
                    file_info["target"] = target
                    files.append(file_info)
                except Exception:
                    continue
        except Exception:
            pass
        return files

    def get_process_sockets(self, pid: int) -> List[dict]:
        """
        Retorna uma lista de sockets abertos pelo processo
        """
        sockets = []
        fd_path = f"/proc/{pid}/fd"
        if not os.path.exists(fd_path):
            return sockets
        try:
            for fd in os.listdir(fd_path):
                fd_full_path = os.path.join(fd_path, fd)
                try:
                    target = os.readlink(fd_full_path)
                    if "socket:[" in target:
                        sockets.append({"fd": fd, "target": target})
                except Exception:
                    continue
        except Exception:
            pass
        return sockets

    def get_process_semaphores(self, pid: int) -> List[dict]:
        """
        Retorna uma lista de semáforos/mutexes abertos pelo processo (Linux: /proc/[pid]/fdinfo)
        """
        semaphores = []
        fdinfo_path = f"/proc/{pid}/fdinfo"
        if not os.path.exists(fdinfo_path):
            return semaphores
        try:
            for fd in os.listdir(fdinfo_path):
                fdinfo_file = os.path.join(fdinfo_path, fd)
                try:
                    with open(fdinfo_file, "r") as f:
                        content = f.read()
                        if "sem" in content or "mutex" in content:
                            semaphores.append({"fd": fd, "info": content})
                except Exception:
                    continue
        except Exception:
            pass
        return semaphores

    def get_process_resources(self, pid: int) -> dict:
        """
        Retorna um dicionário com todos os recursos abertos/alocados pelo processo:
        arquivos, sockets, semáforos/mutexes
        """
        return {
            "open_files": self.get_process_open_files(pid),
            "sockets": self.get_process_sockets(pid),
            "semaphores": self.get_process_semaphores(pid),
        }

    def get_disk_partition_usage(self) -> List[Dict[str, float]]:
        """
        Obtém informações de uso de todas as partições montadas
        """
        partitions = self.get_disk_partitions()
        partition_usages = []

        for partition in partitions:
            usage = self.get_partition_usage(partition)
            if usage:
                partition_usages.append(usage)

        return partition_usages


# teste
if __name__ == "__main__":
    mem_info_obj = MemoryInfo()
    # Exemplo: mostrar recursos do processo atual
    import os

    pid = os.getpid()
    print(f"Recursos do processo {pid}:")
    print(mem_info_obj.get_process_resources(pid))
    partition_usages = mem_info_obj.get_disk_partition_usage()
    for usage in partition_usages:
        print(usage)
