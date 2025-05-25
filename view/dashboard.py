import tkinter as tk
from tkinter import ttk

from controller.monitor_controller import MonitorController


class Dashboard(tk.Tk):
    def __init__(self, controller: MonitorController):
        super().__init__()
        self.title("Dashboard do Sistema Operacional")
        self.geometry("800x600")
        self.controller = controller


        self.tab_control = ttk.Notebook(self)

        self.global_tab = ttk.Frame(self.tab_control)
        self.process_tab = ttk.Frame(self.tab_control)
        self.memory_tab = ttk.Frame(self.tab_control)

        self.tab_control.add(self.global_tab, text="Dados Globais")
        self.tab_control.add(self.process_tab, text="Processos")
        self.tab_control.add(self.memory_tab, text="Memória")

        self.tab_control.pack(expand=1, fill="both")

        self.create_global_tab()
        self.create_process_tab()
        self.create_memory_tab()

        self.update_data()
    
    def create_global_tab(self):
        self.cpu_label = ttk.Label(self.global_tab, text="Uso da CPU: ")
        self.cpu_label.pack(pady=10)

        self.mem_total_label = ttk.Label(self.global_tab, text="Memória Total: ")
        self.mem_total_label.pack(pady=10)

        self.mem_used_label = ttk.Label(self.global_tab, text="Memória Usada: ")
        self.mem_used_label.pack(pady=10)

        self.mem_free_label = ttk.Label(self.global_tab, text="Memória Livre: ")
        self.mem_free_label.pack(pady=10)

        self.mem_available_label = ttk.Label(self.global_tab, text="Memória Disponível: ")
        self.mem_available_label.pack(pady=10)

    def create_process_tab(self):
        columns = ("PID", "Nome do Processo", "Memória (kB)", "Threads")
        self.process_tree = ttk.Treeview(self.process_tab, columns=columns, show="headings")

        for col in columns:
            self.process_tree.heading(col, text=col)
            self.process_tree.column(col, anchor=tk.CENTER)
        
        self.process_tree.pack(expand=True, fill="both")
    

    def create_memory_tab(self):
        columns = ("Propriedade", "Valor")
        self.memory_tree = ttk.Treeview(self.memory_tab, columns=columns, show="headings")

        for col in columns:
            self.memory_tree.heading(col, text=col)
            self.memory_tree.column(col, anchor=tk.CENTER)
        self.memory_tree.pack(expand=True, fill="both")


    def update_data(self):
        data = self.controller.get_data()

        if data:
            self.cpu_label.config(text=f"Uso da CPU: {data['cpu']['usage']:.2f}%")
            self.mem_total_label.config(text=f"Memória Total: {data['memory']['total_memory']} kB")
            self.mem_used_label.config(text=f"Memória Usada: {data['memory']['used_memory']} kB")
            self.mem_available_label.config(text=f"Memória Disponível: {data['memory']['available_memory']} kB")

            for i in self.process_tree.get_children():
                self.process_tree.delete(i)
            for proc in data['top_procs']:
                self.process_tree.insert("", tk.END, values=(proc["pid"], proc["name"], proc["memory_kb"], proc["threads"]))

            for i in self.memory_tree.get_children():
                self.memory_tree.delete(i)
            mem_info = self.controller.memory_info.get_memory_info()
            for key, value in mem_info.items():
                self.memory_tree.insert("", tk.END, values=(key, value))

        self.after(1000, self.update_data)