import time

CPU_PATH = "/proc/stat"
MEM_PATH = "/proc/meminfo"


class MemoryInfo:
    def __init__(self):
        self._last_cpu_usage = None
        self.mem_info = self.get_memory_info()
        self.mem_usage = self.get_mem_usage()
        self.cpu_usage = self.get_cpu_usage()

    def get_cpu_usage(self) -> dict:
        with open("/proc/stat", "r") as f:
            lines = f.readlines()
            parts = lines[0].split()
            total_time = sum(map(int, parts[1:]))
            idle_time = int(parts[4])

        if self._last_cpu_usage is None:
            self._last_cpu_usage = (total_time, idle_time)
            return {"usage": 0, "total": total_time, "idle": idle_time}

        last_total, last_idle = self._last_cpu_usage
        delta_total = total_time - last_total
        delta_idle = idle_time - last_idle

        self._last_cpu_usage = (total_time, idle_time)

        if delta_total == 0:
            return {"usage": 0, "total": total_time, "idle": idle_time}

        usage = (delta_total - delta_idle) / delta_total * 100

        return {"usage": usage, "total": total_time, "idle": idle_time}

    def get_memory_info(self) -> dict:
        info = {}
        with open(MEM_PATH, "r") as f:
            for line in f:
                key, value = line.split(":")
                info[key.strip()] = int(value.strip().split()[0])

        return info

    def get_mem_usage(self) -> dict:
        mem_info = self.get_memory_info()

        mem_total = self.mem_info["MemTotal"]
        mem_free = self.mem_info["MemFree"]
        mem_available = self.mem_info["MemAvailable"]
        buffers = self.mem_info["Buffers"]
        cached = self.mem_info["Cached"]

        used_memory = mem_total - mem_free - buffers - cached
        cached_memory = buffers + cached

        return {
            "used_memory": used_memory,
            "cached_memory": cached_memory,
            "available_memory": mem_available,
            "total_memory": mem_total,
            "free_memory": mem_free,
            "buffers": buffers,
            "cached": cached,
        }


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
