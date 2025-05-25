import os

PROC_DIR = "/proc"


def get_process_info() -> list:
    processes = []

    for pid in os.listdir(PROC_DIR):
        if not pid.isdigit():
            continue

        try:
            with open(f"{PROC_DIR}/{pid}/status", "r") as file:
                info = file.read().splitlines()
                data = {
                    line.split(":")[0]: line.split(":", 1)[1].strip() for line in info
                }

                processes.append(
                    {
                        "pid": pid,
                        "name": data.get("Name", "Unknown"),
                        "uid": data.get("Uid", "?"),
                        "threads": int(data.get("Threads", "0")),
                        "memory_kb": int(data.get("VmRSS", "0").split()[0]),
                    }
                )

        except (FileNotFoundError, ValueError):
            continue

    return processes


def count_processes_and_threads(processes: list) -> dict:
    total_processes = len(processes)
    total_threads = sum(proc["threads"] for proc in processes)

    return {"total_processes": total_processes, "total_threads": total_threads}


def get_top_processes_by_memory(processes: list, top_n: int = 5) -> list:
    sorted_processes = sorted(processes, key=lambda x: x["memory_kb"], reverse=True)
    return sorted_processes[:top_n]


if __name__ == "__main__":
    processes = get_process_info()
    a, b = count_processes_and_threads(processes)
    top_processes = get_top_processes_by_memory(processes)
