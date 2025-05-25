import os

PROC_DIR = "/proc"

class ProcessInfo:
    def __init__(self):
        self.processes = self.get_process_info()
        self.total_processes = self.count_processes()
        self.total_threads = self.count_threads()
        self.top_processes = self.get_top_processes_by_memory()


    def get_process_info(self) -> list:
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

    def count_processes(self) -> int:
        total_processes = len(self.processes)
        return total_processes
    
    def count_threads(self) -> int:
        total_threads = sum(proc["threads"] for proc in self.processes)
        return total_threads


    def get_top_processes_by_memory(self, top_n: int = 5) -> list:
        sorted_processes = sorted(self.processes, key=lambda x: x["memory_kb"], reverse=True)
        return sorted_processes[:top_n]


    def get_process_details(self, pid: str) -> dict:
        try:
            with open(f"{PROC_DIR}/{pid}/status", "r") as file:
                status_lines = file.read().splitlines()
                status_data = {
                    line.split(":")[0]: line.split(":", 1)[1].strip()
                    for line in status_lines
                }

            with open(f"{PROC_DIR}/{pid}/cmdline", "r") as file:
                cmd = file.read().replace("\0", " ").strip()

            with open(f"{PROC_DIR}/{pid}/statm", "r") as file:
                statm = file.read().split()

            return {
                "PID": pid,
                "Name": status_data.get("Name", "?"),
                "State": status_data.get("State", "?"),
                "UID": status_data.get("Uid", "?").split()[0],
                "Threads": status_data.get("Threads", "0"),
                "VmSize": status_data.get("VmSize", "0 kB"),
                "VmRSS": status_data.get("VmRSS", "0 kB"),
                "Command": cmd,
                "Statm": {
                    "size": int(statm[0]) * 4,
                    "resident": int(statm[1]) * 4,
                    "shared": int(statm[2]) * 4,
                },
            }

        except (FileNotFoundError, ValueError):
            return {"PID": pid, "Error": "Process not found or inaccessible"}


if __name__ == "__main__":
    process = ProcessInfo()
    print(f"Total Processes: {process.total_processes}")
    print(f"Total Threads: {process.total_threads}")
    top_processes = process.get_top_processes_by_memory()
    print("Top Processes by Memory Usage:")
    for proc in top_processes:
        print(f"PID: {proc['pid']}, Name: {proc['name']}, Memory: {proc['memory_kb']} KB")
