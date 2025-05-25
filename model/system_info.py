"""
System Info - Modelo responsável pela coleta de informações do sistema
Coleta dados de CPU e memória através dos arquivos /proc/stat e /proc/meminfo
"""

# caminhos dos arquivos de sistema no Linux
CPU_PATH = "/proc/stat"  # arquivo com estatísticas da CPU
MEM_PATH = "/proc/meminfo"  # arquivo com informações de memória


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
        with open("/proc/stat", "r") as f:
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


# teste
if __name__ == "__main__":
    mem_info_obj = MemoryInfo()
    mem_info = mem_info_obj.mem_info
    mem_usage = mem_info_obj.mem_usage
    cpu_usage = mem_info_obj.cpu_usage

    print("Memory Info:")
    for key, value in mem_info.items():
        print(f"{key}: {value} kB")

    print("\nMemory Usage:")
    for key, value in mem_usage.items():
        print(f"{key}: {value} kB")

    print("\nCPU Usage:")
    print(f"Usage: {cpu_usage['usage']:.2f}%")
    print(f"Total Time: {cpu_usage['total']} ticks")
    print(f"Idle Time: {cpu_usage['idle']} ticks")
