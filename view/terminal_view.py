import os

from .utils import kb_to_gb


def clear():
    os.system("clear")


def print_dashboard(
    cpu_usage: dict,
    memory_info: dict,
    total_processes: int,
    total_threads: int,
    processes: list,
):
    clear()
    print("===================== System Monitor ====================")

    print(f"CPU Usage Estimada: {cpu_usage['usage']:.2f}%")

    print(f"Memória Total: {kb_to_gb(memory_info['MemTotal'])} GB")
    print(f"Memória Livre: {kb_to_gb(memory_info['MemFree'])} GB")
    print(f"Memória Disponível: {kb_to_gb(memory_info['MemAvailable'])} GB")

    print(f"Buffers: {kb_to_gb(memory_info['Buffers'])} GB")
    print(f"Cached: {kb_to_gb(memory_info['Cached'])} GB")
    print(f"Memória Ativa: {kb_to_gb(memory_info['Active'])} GB")
    print(f"Memória Inativa: {kb_to_gb(memory_info['Inactive'])} GB")
    print(f"Swap Total: {kb_to_gb(memory_info['SwapTotal'])} GB")
    print(f"Swap Livre: {kb_to_gb(memory_info['SwapFree'])} GB")

    print(f"Total de Processos: {total_processes}")
    print(f"Total de Threads: {total_threads}")

    print("Top 5 Processos por Uso de Memória:")
    print(f"{'PID':>6} {'Nome':<15} {'Threads':<10} {'Memória (MB)':<15}")
    print("=" * 70)
    for proc in processes:
        mem_mb = round(proc["memory_kb"] / 1024, 2)
        print(
            f"{proc['pid']:>6} {proc['name']:<20}{proc['threads']:<10} {mem_mb:>10.2f}"
        )

    print(*"=" * 70, sep="")
    print("Press Ctrl+C to exit")
    print(*"=" * 70, sep="")


def print_process_details(process: dict):
    clear()
    if not process:
        print("❌ Processo não encontrado ou já terminou.")
        return

    print(f"=== Detalhes do Processo PID {process['PID']} ===\n")
    print(f"Nome         : {process['Name']}")
    print(f"Estado       : {process['State']}")
    print(f"UID          : {process['UID']}")
    print(f"Threads      : {process['Threads']}")
    print(f"Comando      : {process['Command']}")
    print(f"Memória Total: {process['VmSize']}")
    print(f"Mem. Residente: {process['VmRSS']}")
    print(
        f"Memória statm: {process['Statm']['resident']} KB residente | {process['Statm']['shared']} KB compartilhada"
    )
    print("\n[Pressione ENTER para voltar ao dashboard]")
    input()
