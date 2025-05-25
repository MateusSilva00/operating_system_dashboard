import time

CPU_PATH = "/proc/stat"
MEM_PATH = "/proc/meminfo"

_last_cpu_usage = None # to store the last CPU usage for comparison

def get_cpu_usage():
    global _last_cpu_usage
    
    with open("/proc/stat", "r") as f:
        lines = f.readlines()
        parts = lines[0].split()
        total_time = sum(map(int, parts[1:]))
        idle_time = int(parts[4])
    
    if _last_cpu_usage is None:
        _last_cpu_usage = (total_time, idle_time)
        time.sleep(0.1)  # wait for a short time to get a new reading

        return {"usage": 0}

    last_total, last_idle = _last_cpu_usage
    delta_total = total_time - last_total
    delta_idle = idle_time - last_idle

    _last_cpu_usage = (total_time, idle_time)

    if delta_total == 0:
        return {"usage": 0}    
        
    usage = (delta_total - delta_idle) / delta_total * 100
    return {"usage": usage, "total": total_time, "idle": idle_time}

def get_memory_info():
    info = {}
    with open(MEM_PATH, "r") as f:
        for line in f:
            key, value = line.split(":")
            info[key.strip()] = int(value.strip().split()[0])
    

    return {
        "MemTotal": info.get("MemTotal", 0),
        "MemFree": info.get("MemFree", 0),
        "MemAvailable": info.get("MemAvailable", 0),
        "Buffers": info.get("Buffers", 0),
        "Cached": info.get("Cached", 0),
        "Active": info.get("Active", 0),
        "Inactive": info.get("Inactive", 0),
        "SwapTotal": info.get("SwapTotal", 0),
        "SwapFree": info.get("SwapFree", 0),
    }