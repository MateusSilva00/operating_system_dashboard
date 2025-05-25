import os

from .utils import kb_to_gb


def clear():
    os.system('clear')

def print_dashboard(cpu_usage: dict, memory_info: dict):
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
    print("=========================================================")
    print("Press Ctrl+C to exit")
    print("=========================================================")
