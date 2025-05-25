import os

PROC_DIR = "/proc"


class ProcessInfo:
    def __init__(self):
        self.processes = self.get_process_info()
        # self.total_processes = self.count_processes()
        # self.total_threads = self.count_threads()
        # self.top_processes = self.get_top_processes_by_memory()

    def get_process_info(self):
        processes = []
        threads = []

        # Cache do mapeamento UID para username para melhor performance
        uid_to_username = {}
        try:
            with open('/etc/passwd', 'r') as passwd_file:
                for line in passwd_file:
                    parts = line.strip().split(':')
                    if len(parts) >= 3:
                        uid = parts[2]
                        username = parts[0]
                        uid_to_username[uid] = username
        except FileNotFoundError:
            pass

        try:
            proc_entries = [entry for entry in os.listdir(PROC_DIR) if entry.isdigit()]
        except (FileNotFoundError, PermissionError):
            return processes, threads

        for entry in proc_entries:
            pid = entry
            user, name, status = "Unknown", "Unknown", "Unknown"
            memory_kb = 0
            thread_count = 0

            try:
                # Ler informações do processo
                with open(f"{PROC_DIR}/{pid}/status", "r") as file:
                    for line in file:
                        if line.startswith("Uid:"):
                            uid_parts = line.split()
                            if len(uid_parts) > 1:
                                uid = uid_parts[1]
                                user = uid_to_username.get(uid, f"UID:{uid}")
                        elif line.startswith("Name:"):
                            name = line.split(":", 1)[1].strip()
                        elif line.startswith("State:"):
                            status = line.split(":", 1)[1].strip()
                        elif line.startswith("VmRSS:"):
                            try:
                                memory_kb = int(line.split()[1])
                            except (ValueError, IndexError):
                                memory_kb = 0
                        elif line.startswith("Threads:"):
                            try:
                                thread_count = int(line.split()[1])
                            except (ValueError, IndexError):
                                thread_count = 1
            except (FileNotFoundError, PermissionError, ValueError):
                continue
                
            processes.append({
                "PID": pid,
                "User": user,
                "Name": name,
                "Status": status,
                "Memory": memory_kb,
                "Threads": thread_count
            })

            # Coletar threads apenas para alguns processos (para performance)
            if len(threads) < 100:  # Limitar coleta de threads
                try:
                    task_dir = f'/proc/{pid}/task'
                    if os.path.exists(task_dir):
                        task_entries = [t for t in os.listdir(task_dir) if t.isdigit()]
                        for tid in task_entries[:5]:  # Limitar a 5 threads por processo
                            threads.append({
                                'TID': tid,
                                'PID': pid,
                                'User': user,
                                'Name': name,
                                'Status': status
                            })
                except (FileNotFoundError, PermissionError):
                    pass
            
        return processes, threads

    def get_process_by_pid(self, pid):
        process_memory = None 
        try:
            with open(os.path.join(PROC_DIR, pid, 'status')) as f:
                for line in f:
                    if line.startswith('VmRSS:'):
                        memory = line.split()[1] # Memória em kB
                        process_memory = int(memory)
                        break
        except FileNotFoundError:
            pass 
        return process_memory

    def get_all_page_usage(self):
        all_page_usage = {}
        try:
            # Itera sobre todos os diretórios em /proc
            for pid_dir in os.listdir(PROC_DIR):
                if pid_dir.isdigit(): 
                    pid = pid_dir
                    page_usage = self.get_page_usage_by_pid(pid)
                    if page_usage is not None:
                        all_page_usage[pid] = page_usage
        except FileNotFoundError:
            pass 
        return all_page_usage
    
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
        except FileNotFoundError:
            pass  
        except PermissionError:
            pass
        except Exception as e:
            print(f"Erro com a quantidade de páginas para o processo {pid}: {e}")
        return page_usage
    
    def get_process_details(self, pid):
        process_details = {}
        try:
            # Lê vários arquivos dentro do diretório /proc/{pid} para obter os detalhes do processo
            with open(os.path.join(PROC_DIR, pid, 'cmdline'), 'rb') as f:
                # Lê a linha de comando do processo
                cmdline = f.read().decode().replace('\x00', ' ').strip()
                process_details['Command Line'] = cmdline if cmdline else None
                
            with open(os.path.join(PROC_DIR, pid, 'status'), 'r') as f:
                # Lê a informação do status do processo
                for line in f:
                    key, value = line.split(':', 1)
                    process_details[key.strip()] = value.strip()
        except FileNotFoundError:
            pass  
        return process_details
    
    def get_all_process_details(self):
        all_process_details = {}
        try:
            for pid_dir in os.listdir(PROC_DIR):
                if pid_dir.isdigit(): 
                    pid = pid_dir
                    process_details = self.get_process_details(pid)
                    if process_details:
                        all_process_details[pid] = process_details
        except Exception as e:
            pass
        return all_process_details

    def count_processes(self):
        """Conta o total de processos de forma otimizada"""
        try:
            return len([entry for entry in os.listdir(PROC_DIR) if entry.isdigit()])
        except (FileNotFoundError, PermissionError):
            return 0

    def count_threads(self):
        """Conta o total de threads de forma otimizada"""
        total_threads = 0
        try:
            proc_entries = [entry for entry in os.listdir(PROC_DIR) if entry.isdigit()]
            for entry in proc_entries[:50]:  # Limitar para performance
                try:
                    with open(f'{PROC_DIR}/{entry}/status', 'r') as f:
                        for line in f:
                            if line.startswith('Threads:'):
                                try:
                                    total_threads += int(line.split()[1])
                                except (ValueError, IndexError):
                                    total_threads += 1
                                break
                except (FileNotFoundError, PermissionError):
                    continue
        except (FileNotFoundError, PermissionError):
            pass
        return total_threads

    def get_top_processes_by_memory(self, limit=15):
        """Retorna os processos que mais consomem memória"""
        processes, _ = self.get_process_info()
        
        # Filtrar processos válidos e ordenar por memória
        valid_processes = []
        for proc in processes:
            memory = proc.get('Memory', 0)
            if isinstance(memory, (int, float)) and memory > 0:
                valid_processes.append(proc)
        
        # Ordenar por memória (decrescente)
        sorted_processes = sorted(valid_processes, 
                                key=lambda x: x.get('Memory', 0), 
                                reverse=True)
        
        return sorted_processes[:limit]


if __name__ == "__main__":
    process = ProcessInfo()
    # print(process.processes)
