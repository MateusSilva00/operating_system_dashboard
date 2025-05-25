import os

PROC_DIR = "/proc"


class ProcessInfo:
    def __init__(self):
        self._uid_cache = self._build_uid_cache()

    def _build_uid_cache(self):
        """Constrói cache de mapeamento UID para username"""
        uid_to_username = {}
        try:
            with open('/etc/passwd', 'r') as passwd_file:
                for line in passwd_file:
                    parts = line.strip().split(':')
                    if len(parts) >= 3:
                        uid_to_username[parts[2]] = parts[0]
        except FileNotFoundError:
            pass
        return uid_to_username

    def _get_proc_entries(self):
        """Obtém lista de PIDs válidos em /proc"""
        try:
            return [entry for entry in os.listdir(PROC_DIR) if entry.isdigit()]
        except (FileNotFoundError, PermissionError):
            return []

    def _parse_process_status(self, pid):
        """Extrai informações do arquivo status de um processo"""
        process_data = {
            'user': 'Unknown',
            'name': 'Unknown', 
            'status': 'Unknown',
            'memory_kb': 0,
            'thread_count': 1
        }
        
        try:
            with open(f"{PROC_DIR}/{pid}/status", "r") as file:
                for line in file:
                    if line.startswith("Uid:"):
                        uid_parts = line.split()
                        if len(uid_parts) > 1:
                            uid = uid_parts[1]
                            process_data['user'] = self._uid_cache.get(uid, f"UID:{uid}")
                    elif line.startswith("Name:"):
                        process_data['name'] = line.split(":", 1)[1].strip()
                    elif line.startswith("State:"):
                        process_data['status'] = line.split(":", 1)[1].strip()
                    elif line.startswith("VmRSS:"):
                        try:
                            process_data['memory_kb'] = int(line.split()[1])
                        except (ValueError, IndexError):
                            pass
                    elif line.startswith("Threads:"):
                        try:
                            process_data['thread_count'] = int(line.split()[1])
                        except (ValueError, IndexError):
                            pass
        except (FileNotFoundError, PermissionError, ValueError):
            pass
            
        return process_data

    def _collect_threads_for_process(self, pid, process_data, max_threads=5):
        """Coleta informações de threads para um processo específico"""
        threads = []
        try:
            task_dir = f'/proc/{pid}/task'
            if os.path.exists(task_dir):
                task_entries = [t for t in os.listdir(task_dir) if t.isdigit()]
                for tid in task_entries[:max_threads]:  # Aumentar de 3 para 5 threads por processo
                    thread_status = process_data['status']
                    try:
                        with open(f'/proc/{pid}/task/{tid}/status', 'r') as tf:
                            for tline in tf:
                                if tline.startswith('State:'):
                                    thread_status = tline.split(':', 1)[1].strip()
                                    break
                    except (FileNotFoundError, PermissionError):
                        pass
                    
                    threads.append({
                        'TID': tid,
                        'PID': pid,
                        'User': process_data['user'],
                        'Name': process_data['name'],
                        'Status': thread_status
                    })
        except (FileNotFoundError, PermissionError):
            pass
        return threads

    def get_process_info(self):
        """Obtém informações de todos os processos e threads do sistema"""
        processes = []
        threads = []
        proc_entries = self._get_proc_entries()

        for pid in proc_entries:
            process_data = self._parse_process_status(pid)
            
            processes.append({
                "PID": pid,
                "User": process_data['user'],
                "Name": process_data['name'],
                "Status": process_data['status'],
                "Memory": process_data['memory_kb'],
                "Threads": process_data['thread_count']
            })

            # Aumentar limite total de threads coletadas
            if len(threads) < 400:  # Aumentar de 200 para 400 threads
                thread_list = self._collect_threads_for_process(pid, process_data)
                threads.extend(thread_list)
            
        return processes, threads

    def count_processes(self):
        return len(self._get_proc_entries())

    def count_threads(self):
        total_threads = 0
        for pid in self._get_proc_entries():
            try:
                with open(f'{PROC_DIR}/{pid}/status', 'r') as f:
                    for line in f:
                        if line.startswith('Threads:'):
                            try:
                                total_threads += int(line.split()[1])
                            except (ValueError, IndexError):
                                total_threads += 1
                            break
            except (FileNotFoundError, PermissionError):
                continue
        return total_threads

    def get_top_processes_by_memory(self, limit=15):
        processes, _ = self.get_process_info()
        
        valid_processes = [p for p in processes 
                         if isinstance(p.get('Memory', 0), (int, float)) and p.get('Memory', 0) > 0]
        
        sorted_processes = sorted(valid_processes, 
                                key=lambda x: x.get('Memory', 0), 
                                reverse=True)
        
        return sorted_processes[:limit]

    def get_process_by_pid(self, pid):
        try:
            with open(os.path.join(PROC_DIR, str(pid), 'status')) as f:
                for line in f:
                    if line.startswith('VmRSS:'):
                        return int(line.split()[1])
        except (FileNotFoundError, ValueError):
            pass
        return None

    def get_page_usage_by_pid(self, pid):
        page_usage = {'total': 0, 'code': 0, 'heap': 0, 'stack': 0}
        try:
            with open(f'/proc/{pid}/smaps', 'r') as f:
                for line in f:
                    if 'Size:' in line:
                        page_usage['total'] += int(line.split()[1])
                    elif '[heap]' in line:
                        page_usage['heap'] += int(next(f).split()[1])
                    elif '[stack]' in line:
                        page_usage['stack'] += int(next(f).split()[1])
                    elif '.text' in line:
                        page_usage['code'] += int(next(f).split()[1])
        except (FileNotFoundError, PermissionError, ValueError, StopIteration):
            pass
        return page_usage

    def get_process_details(self, pid):
        process_details = {}
        try:
            with open(os.path.join(PROC_DIR, str(pid), 'cmdline'), 'rb') as f:
                cmdline = f.read().decode().replace('\x00', ' ').strip()
                process_details['Command Line'] = cmdline if cmdline else None
                
            with open(os.path.join(PROC_DIR, str(pid), 'status'), 'r') as f:
                for line in f:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        process_details[key.strip()] = value.strip()
        except (FileNotFoundError, UnicodeDecodeError):
            pass
        return process_details

    def get_all_page_usage(self):
        all_page_usage = {}
        for pid in self._get_proc_entries():
            page_usage = self.get_page_usage_by_pid(pid)
            if page_usage and any(page_usage.values()):
                all_page_usage[pid] = page_usage
        return all_page_usage

    def get_all_process_details(self):
        all_process_details = {}
        for pid in self._get_proc_entries():
            process_details = self.get_process_details(pid)
            if process_details:
                all_process_details[pid] = process_details
        return all_process_details


if __name__ == "__main__":
    process = ProcessInfo()
    processes, threads = process.get_process_info()
    print(f"Processos: {len(processes)}, Threads: {len(threads)}")
