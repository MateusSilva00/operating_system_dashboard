import tkinter as tk
from tkinter import ttk

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from controller.monitor_controller import MonitorController
from view.utils import kb_to_gb


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
        self.memory_tree.pack(side=tk.LEFT, expand=True, fill="both")

        # Frame para informações adicionais e gráfico
        right_frame = ttk.Frame(self.memory_tab)
        right_frame.pack(side=tk.RIGHT, expand=True, fill="both")

        # Labels para porcentagem e memória livre em GB
        self.mem_percent_label = ttk.Label(right_frame, text="Uso de Memória: ")
        self.mem_percent_label.pack(pady=10)

        self.mem_free_gb_label = ttk.Label(right_frame, text="Memória Livre (GB): ")
        self.mem_free_gb_label.pack(pady=10)

        # Gráfico de uso de memória
        self.mem_usage_history = []
        self.fig, self.ax = plt.subplots(figsize=(4, 3))
        self.ax.set_title("Uso de Memória (%)")
        self.ax.set_ylim(0, 100)
        self.ax.set_xlabel("Tempo (s)")
        self.ax.set_ylabel("Uso (%)")
        self.line, = self.ax.plot([], [], color='blue')

        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas.get_tk_widget().pack(expand=True, fill="both")


    def update_data(self):
        data = self.controller.get_data()

        if data:
            self.cpu_label.config(text=f"Uso da CPU: {data['cpu']['usage']:.2f}%")
            self.mem_total_label.config(text=f"Memória Total: {data['mem']['total_memory']} kB")
            self.mem_used_label.config(text=f"Memória Usada: {data['mem']['used_memory']} kB")
            self.mem_available_label.config(text=f"Memória Disponível: {data['mem']['available_memory']} kB")

            for i in self.memory_tree.get_children():
                self.memory_tree.delete(i)

            mem_info = self.controller.system_info.get_memory_info()
            for key, value in mem_info.items():
                self.memory_tree.insert("", tk.END, values=(key, f"{value} kB"))

            # Calcula porcentagem de uso e memória livre em GB
            mem_total = data['mem']['total_memory']
            mem_used = data['mem']['used_memory']
            mem_free = mem_total - mem_used
            mem_percent = (mem_used / mem_total) * 100

            self.mem_percent_label.config(text=f"Uso de Memória: {mem_percent:.2f}%")
            self.mem_free_gb_label.config(text=f"Memória Livre (GB): {kb_to_gb(mem_free)} GB")

            # Atualiza gráfico
            self.mem_usage_history.append(mem_percent)
            if len(self.mem_usage_history) > 60:
                self.mem_usage_history.pop(0)

            self.line.set_data(range(len(self.mem_usage_history)), self.mem_usage_history)
            self.ax.set_xlim(0, max(60, len(self.mem_usage_history)))
            self.canvas.draw()


            self.after(1000, self.update_data)