import tkinter as tk
from tkinter import ttk
from typing import Any, Dict, List

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from controller.monitor_controller import MonitorController
from view.utils import (format_memory_size, format_memory_value_only,
                        get_memory_unit)


class Dashboard(tk.Tk):
    # Constantes de configuração
    WINDOW_TITLE = "⚡ OS DASHBOARD"
    WINDOW_SIZE = "1200x800"
    BACKGROUND_COLOR = "#0a0a0a"
    UPDATE_INTERVAL = 1000
    MAX_PROCESSES_DISPLAY = 15
    MAX_MEMORY_ITEMS = 20
    MAX_HISTORY_POINTS = 60
    
    COLORS = {
        'primary': '#00d4ff',
        'secondary': '#00ff88',
        'background': '#0a0a0a',
        'card': '#1a1a1a',
        'dark': '#111111',
        'text': '#ffffff',
        'grid': '#333333'
    }

    def __init__(self, controller: MonitorController):
        super().__init__()
        self.controller = controller
        self.mem_usage_history: List[float] = []
        self.show_all_memory_details = False  # Estado do botão "Exibir Mais"
        
        self.metric_labels: Dict[str, ttk.Label] = {}
        self.trees: Dict[str, ttk.Treeview] = {}
        
        self._setup_window()
        self._setup_matplotlib()
        self._setup_styles()
        self._create_interface()
        self._start_updates()

    def _setup_window(self):
        self.title(self.WINDOW_TITLE)
        self.geometry(self.WINDOW_SIZE)
        self.configure(bg=self.BACKGROUND_COLOR)

    def _setup_matplotlib(self):
        plt.style.use("dark_background")

    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style_configs = {
            "TNotebook": {
                "background": self.BACKGROUND_COLOR,
                "borderwidth": 0,
                "tabmargins": [5, 5, 5, 0]
            },
            "TNotebook.Tab": {
                "background": self.COLORS['card'],
                "foreground": self.COLORS['primary'],
                "padding": [20, 12],
                "font": ("JetBrains Mono", 11, "bold"),
                "borderwidth": 0,
            },
            "Title.TLabel": {
                "background": self.BACKGROUND_COLOR,
                "foreground": self.COLORS['primary'],
                "font": ("JetBrains Mono", 16, "bold"),
            },
            "Info.TLabel": {
                "background": self.BACKGROUND_COLOR,
                "foreground": self.COLORS['text'],
                "font": ("JetBrains Mono", 12),
            },
            "Metric.TLabel": {
                "background": self.COLORS['card'],
                "foreground": self.COLORS['secondary'],
                "font": ("JetBrains Mono", 14, "bold"),
                "relief": "flat",
                "borderwidth": 1,
            },
            "Card.TFrame": {
                "background": self.COLORS['card'],
                "relief": "flat",
                "borderwidth": 1
            },
            "Futuristic.Treeview": {
                "background": self.COLORS['dark'],
                "foreground": self.COLORS['text'],
                "fieldbackground": self.COLORS['dark'],
                "font": ("JetBrains Mono", 10),
                "borderwidth": 0,
                "rowheight": 25,
            },
            "Futuristic.Treeview.Heading": {
                "background": self.COLORS['primary'],
                "foreground": self.BACKGROUND_COLOR,
                "font": ("JetBrains Mono", 11, "bold"),
                "borderwidth": 0,
            }
        }

        for style_name, config in style_configs.items():
            style.configure(style_name, **config)

        style.map(
            "TNotebook.Tab",
            background=[("selected", self.COLORS['primary'])],
            foreground=[("selected", self.BACKGROUND_COLOR)],
        )
        style.map("Futuristic.Treeview", 
                 background=[("selected", f"{self.COLORS['primary']}33")])

    def _create_interface(self):
        self._create_header()
        self._create_tabs()

    def _create_header(self):
        header_frame = tk.Frame(self, bg=self.BACKGROUND_COLOR, height=60)
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        header_frame.pack_propagate(False)

        title_label = ttk.Label(
            header_frame, 
            text="⚡ SISTEMA OPERACIONAL DASHBOARD", 
            style="Title.TLabel"
        )
        title_label.pack(side="left", pady=15)

    def _create_tabs(self):
        self.tab_control = ttk.Notebook(self)
        self.tab_control.pack(expand=1, fill="both", padx=20, pady=(0, 20))

        tabs_config = [
            ("global", "🌐 GLOBAL", self._create_global_tab),
            ("process", "⚙️ PROCESSOS", self._create_process_tab),
            ("memory", "💾 MEMÓRIA", self._create_memory_tab)
        ]

        self.tabs = {}
        for tab_key, tab_text, create_func in tabs_config:
            tab_frame = ttk.Frame(self.tab_control)
            self.tabs[tab_key] = tab_frame
            self.tab_control.add(tab_frame, text=tab_text)
            create_func(tab_frame)

    def _create_metric_card(self, parent: tk.Widget, title: str, 
                           key: str, unit: str = "") -> ttk.Label:
        card = ttk.Frame(parent, style="Card.TFrame")
        card.pack(fill="x", pady=8, padx=5)

        title_label = ttk.Label(card, text=title, style="Info.TLabel")
        title_label.pack(anchor="w", padx=15, pady=(10, 5))

        value_label = ttk.Label(card, text=f"-- {unit}", style="Metric.TLabel")
        value_label.pack(anchor="w", padx=15, pady=(0, 10))

        self.metric_labels[key] = value_label
        return value_label

    def _create_treeview(self, parent: tk.Widget, columns: List[str], 
                        key: str) -> ttk.Treeview:
        tree_frame = tk.Frame(parent, bg=self.BACKGROUND_COLOR)
        tree_frame.pack(fill="both", expand=True)

        tree = ttk.Treeview(
            tree_frame, 
            columns=columns, 
            show="headings", 
            style="Futuristic.Treeview"
        )

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, anchor=tk.CENTER, width=150)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.trees[key] = tree
        return tree

    def _create_global_tab(self, tab_frame: ttk.Frame):
        container = tk.Frame(tab_frame, bg=self.BACKGROUND_COLOR)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        metrics_frame = tk.Frame(container, bg=self.BACKGROUND_COLOR)
        metrics_frame.pack(fill="x", pady=(0, 20))

        cpu_metrics = [
            ("Uso da CPU", "cpu_usage", "%"),
            ("Tempo Ocioso", "cpu_idle", "%"),
            ("Processos", "process_count", ""),
            ("Threads", "thread_count", "")
        ]

        for title, key, unit in cpu_metrics:
            self._create_metric_card(metrics_frame, title, key, unit)

        chart_frame = ttk.Frame(container, style="Card.TFrame")
        chart_frame.pack(fill="both", expand=True, pady=(10, 0))

        self.cpu_fig, self.cpu_ax = plt.subplots(figsize=(8, 4), facecolor=self.COLORS['card'])
        self.cpu_ax.set_facecolor(self.COLORS['dark'])
        self.cpu_ax.set_title("Uso da CPU (%)", color=self.COLORS['primary'], fontsize=14, fontweight="bold")
        self.cpu_ax.set_ylim(0, 100)
        self.cpu_ax.set_xlabel("Tempo (s)", color=self.COLORS['text'])
        self.cpu_ax.set_ylabel("Uso (%)", color=self.COLORS['text'])
        self.cpu_ax.tick_params(colors=self.COLORS['text'])
        self.cpu_ax.grid(True, alpha=0.2, color=self.COLORS['grid'], linestyle=':')

        self.cpu_line, = self.cpu_ax.plot([], [], color=self.COLORS['secondary'], linewidth=2.5)

        self.cpu_usage_history: List[float] = []

        self.cpu_canvas = FigureCanvasTkAgg(self.cpu_fig, master=chart_frame)
        self.cpu_canvas.get_tk_widget().pack(fill="both", expand=True)

    def _create_process_tab(self, tab_frame: ttk.Frame):
        """Cria aba de processos"""
        container = tk.Frame(tab_frame, bg=self.BACKGROUND_COLOR)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        title = ttk.Label(container, text="⚙️ PROCESSOS ATIVOS", style="Title.TLabel")
        title.pack(anchor="w", pady=(0, 20))

        columns = ("PID", "PROCESSO", "MEMÓRIA", "THREADS")
        self._create_treeview(container, columns, "processes")

    def _create_memory_tab(self, tab_frame: ttk.Frame):
        """Cria aba de memória responsiva e otimizada"""
        container = tk.Frame(tab_frame, bg=self.BACKGROUND_COLOR)
        container.pack(fill="both", expand=True, padx=15, pady=15)

        # Header da aba
        header_frame = tk.Frame(container, bg=self.BACKGROUND_COLOR)
        header_frame.pack(fill="x", pady=(0, 15))
        
        title = ttk.Label(header_frame, text="💾 ANÁLISE DE MEMÓRIA", style="Title.TLabel")
        title.pack(side="left")

        # Layout principal responsivo
        main_layout = tk.Frame(container, bg=self.BACKGROUND_COLOR)
        main_layout.pack(fill="both", expand=True)

        # Painel esquerdo: Métricas (35% da largura)
        self._create_memory_metrics_panel(main_layout)
        
        # Painel direito: Gráfico (65% da largura)
        self._create_memory_chart_panel(main_layout)

    def _create_memory_metrics_panel(self, parent: tk.Widget):
        metrics_frame = ttk.Frame(parent, style="Card.TFrame")
        metrics_frame.pack(side="left", fill="both", padx=(0, 8))
        metrics_frame.configure(width=350)
        metrics_frame.pack_propagate(False)

        header_frame = tk.Frame(metrics_frame, bg=self.COLORS['card'])
        header_frame.pack(fill="x", padx=15, pady=15)

        header = ttk.Label(header_frame, text="📊 MÉTRICAS PRINCIPAIS", style="Info.TLabel")
        header.pack(side="left")

        self.toggle_button = tk.Button(
            header_frame,
            text="Exibir Mais",
            command=self._toggle_memory_details,
            bg=self.COLORS['primary'],
            fg=self.COLORS['background'],
            font=("JetBrains Mono", 9, "bold"),
            relief="flat",
            padx=10,
            pady=5,
            cursor="hand2"
        )
        self.toggle_button.pack(side="right")

        main_scroll_container = tk.Frame(metrics_frame, bg=self.COLORS['card'])
        main_scroll_container.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.main_canvas = tk.Canvas(main_scroll_container, bg=self.COLORS['card'], highlightthickness=0)
        main_scrollbar = ttk.Scrollbar(main_scroll_container, orient="vertical", command=self.main_canvas.yview)
        self.main_scrollable_frame = tk.Frame(self.main_canvas, bg=self.COLORS['card'])

        self.main_scrollable_frame.bind("<Configure>", lambda e: self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all")))
        self.main_canvas.create_window((0, 0), window=self.main_scrollable_frame, anchor="nw")
        self.main_canvas.configure(yscrollcommand=main_scrollbar.set)

        self.main_canvas.bind("<Enter>", lambda e: self.main_canvas.bind_all('<Button-4>', self._on_mousewheel_linux))
        self.main_canvas.bind("<Leave>", lambda e: self.main_canvas.unbind_all('<Button-4>'))
        self.main_canvas.bind("<Enter>", lambda e: self.main_canvas.bind_all('<Button-5>', self._on_mousewheel_linux))
        self.main_canvas.bind("<Leave>", lambda e: self.main_canvas.unbind_all('<Button-5>'))

        self.main_canvas.pack(side="left", fill="both", expand=True)
        main_scrollbar.pack(side="right", fill="y")

        self.main_metrics_frame = tk.Frame(self.main_scrollable_frame, bg=self.COLORS['card'])
        self.main_metrics_frame.pack(fill="x", pady=(0, 10))

        self.extra_details_frame = tk.Frame(self.main_scrollable_frame, bg=self.COLORS['card'])

        self._create_metric_groups(self.main_metrics_frame)
        self._create_extra_memory_details()

    def _create_metric_groups(self, parent: tk.Widget):
        """Cria grupos de métricas organizados"""
        groups = {
            "💽 MEMÓRIA FÍSICA": [
                ("Total", "mem_total_chart"),
                ("Em Uso", "mem_used_chart"), 
                ("Livre", "mem_free_chart"),
                ("% Uso", "mem_percent")
            ],
            "🔄 CACHE/BUFFER": [
                ("Cache", "mem_cache"),
                ("Buffers", "mem_buffers")
            ],
            "💿 SWAP": [
                ("Swap Total", "mem_virtual")
            ]
        }

        for group_name, metrics in groups.items():
            # Título do grupo
            group_frame = tk.Frame(parent, bg=self.COLORS['card'])
            group_frame.pack(fill="x", pady=(5, 10))
            
            group_label = ttk.Label(group_frame, text=group_name, 
                                  font=("JetBrains Mono", 11, "bold"),
                                  foreground=self.COLORS['primary'],
                                  background=self.COLORS['card'])
            group_label.pack(anchor="w", pady=(0, 5))

            # Métricas do grupo
            for label, key in metrics:
                self._create_compact_metric(group_frame, label, key)

    def _create_compact_metric(self, parent: tk.Widget, title: str, key: str):
        """Cria métrica compacta e responsiva"""
        metric_frame = tk.Frame(parent, bg=self.COLORS['dark'])
        metric_frame.pack(fill="x", pady=2, padx=5)

        # Layout flex
        content_frame = tk.Frame(metric_frame, bg=self.COLORS['dark'])
        content_frame.pack(fill="x", padx=8, pady=6)

        title_label = ttk.Label(content_frame, text=title,
                               font=("JetBrains Mono", 10),
                               foreground=self.COLORS['text'],
                               background=self.COLORS['dark'])
        title_label.pack(side="left")

        value_label = ttk.Label(content_frame, text="--",
                               font=("JetBrains Mono", 10, "bold"),
                               foreground=self.COLORS['secondary'],
                               background=self.COLORS['dark'])
        value_label.pack(side="right")

        self.metric_labels[key] = value_label

    def _create_extra_memory_details(self):
        """Cria seção de detalhes extras de memória"""
        # Título da seção
        details_title = ttk.Label(
            self.extra_details_frame, 
            text="🔍 DETALHES COMPLETOS", 
            font=("JetBrains Mono", 11, "bold"),
            foreground=self.COLORS['primary'],
            background=self.COLORS['card']
        )
        details_title.pack(anchor="w", pady=(10, 5))

        # Container para os detalhes (sem scroll separado, usa o scroll principal)
        details_container = tk.Frame(self.extra_details_frame, bg=self.COLORS['card'])
        details_container.pack(fill="both", expand=True)

        # Frame scrollável simples (o scroll principal cuidará disso)
        self.scrollable_frame = tk.Frame(details_container, bg=self.COLORS['card'])
        self.scrollable_frame.pack(fill="both", expand=True)

        # Armazenar referências para atualização
        self.memory_details_labels = {}

    def _toggle_memory_details(self):
        self.show_all_memory_details = not self.show_all_memory_details
        if self.show_all_memory_details:
            self.extra_details_frame.pack(fill="both", expand=True, pady=(10, 0))
            self.toggle_button.config(text="Exibir Menos")
            self._populate_memory_details()
        else:
            self.extra_details_frame.pack_forget()
            self.toggle_button.config(text="Exibir Mais")
        self.main_canvas.update_idletasks()
        self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))

    def _populate_memory_details(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.memory_details_labels.clear()

        mem_info = self.controller.system_info.get_memory_info()
        for key, value in mem_info.items():
            detail_frame = tk.Frame(self.scrollable_frame, bg=self.COLORS['dark'])
            detail_frame.pack(fill="x", pady=1, padx=2)

            content_frame = tk.Frame(detail_frame, bg=self.COLORS['dark'])
            content_frame.pack(fill="x", padx=6, pady=3)

            name_label = ttk.Label(
                content_frame, 
                text=key.replace('_', ' ').title(),
                font=("JetBrains Mono", 8),
                foreground=self.COLORS['text'],
                background=self.COLORS['dark']
            )
            name_label.pack(side="left")

            value_label = ttk.Label(
                content_frame, 
                text=format_memory_size(value),
                font=("JetBrains Mono", 8, "bold"),
                foreground=self.COLORS['secondary'],
                background=self.COLORS['dark']
            )
            value_label.pack(side="right")

            self.memory_details_labels[key] = value_label

        self.main_canvas.update_idletasks()
        self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))

    def _update_memory_details_if_visible(self):
        if self.show_all_memory_details and self.memory_details_labels:
            mem_info = self.controller.system_info.get_memory_info()
            for key, value in mem_info.items():
                if key in self.memory_details_labels:
                    formatted_value = format_memory_size(value)
                    self.memory_details_labels[key].config(text=formatted_value)

    def _create_memory_chart_panel(self, parent: tk.Widget):
        chart_frame = ttk.Frame(parent, style="Card.TFrame")
        chart_frame.pack(side="right", fill="both", expand=True, padx=(8, 0))

        chart_header = tk.Frame(chart_frame, bg=self.COLORS['card'])
        chart_header.pack(fill="x", padx=15, pady=15)

        chart_title = ttk.Label(chart_header, text="MONITOR EM TEMPO REAL", style="Info.TLabel")
        chart_title.pack(side="left")

        graph_container = tk.Frame(chart_frame, bg=self.COLORS['card'])
        graph_container.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.fig, self.ax = plt.subplots(figsize=(9, 6), facecolor=self.COLORS['card'])
        self.ax.set_facecolor(self.COLORS['dark'])
        
        self._configure_chart_style()

        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_container)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def _configure_chart_style(self):
        self.ax.set_title("USO DE MEMÓRIA RAM (%)", 
                         color=self.COLORS['primary'], 
                         fontsize=16, fontweight="bold", pad=20)
        
        self.ax.set_ylim(0, 100)
        self.ax.set_xlabel("Tempo (s)", color=self.COLORS['text'], fontsize=12)
        self.ax.set_ylabel("Uso (%)", color=self.COLORS['text'], fontsize=12)
        self.ax.tick_params(colors=self.COLORS['text'], labelsize=10)
        self.ax.grid(True, alpha=0.2, color=self.COLORS['grid'], linestyle=':')

        self.line, = self.ax.plot([], [], color=self.COLORS['secondary'], 
                                 linewidth=2.5, alpha=0.9, antialiased=True)

        self.ax.axhspan(80, 90, alpha=0.1, color='orange', label='Atenção')
        self.ax.axhspan(90, 100, alpha=0.1, color='red', label='Crítico')

        self.ax.legend(['Uso da Memória', 'Zona de Atenção', 'Zona Crítica'],
                      loc='upper left', fontsize=9, framealpha=0.8)

    def _update_memory_chart(self, data: Dict[str, Any]):
        mem_data = data.get('mem', {})
        mem_percent = mem_data.get('mem_percent_usage', 0)

        metrics_data = {
            'mem_total_chart': mem_data.get('total_memory', 0),
            'mem_used_chart': mem_data.get('used_memory', 0),
            'mem_free_chart': mem_data.get('free_memory', 0),
            'mem_percent': mem_percent,
            'mem_cache': mem_data.get('cached_memory', 0),
            'mem_buffers': mem_data.get('buffers', 0),
            'mem_virtual': mem_data.get('swap_total', 0)
        }

        self._update_all_metrics(metrics_data)
        self._update_chart_optimized(mem_percent)


    def _update_all_metrics(self, metrics_data: Dict[str, float]):
        for key, value in metrics_data.items():
            if key in self.metric_labels:
                if key == 'mem_percent':
                    text = f"{value:.1f}%"
                else:
                    formatted_value = format_memory_value_only(value)
                    unit = get_memory_unit(value)
                    text = f"{formatted_value} {unit}"
                
                self.metric_labels[key].config(text=text)

    def _update_chart_optimized(self, mem_percent: float):
        self.mem_usage_history.append(mem_percent)
        if len(self.mem_usage_history) > self.MAX_HISTORY_POINTS:
            self.mem_usage_history.pop(0)

        if len(self.mem_usage_history) > 1:
            x_data = range(len(self.mem_usage_history))
            self.line.set_data(x_data, self.mem_usage_history)
            self.ax.set_xlim(0, max(self.MAX_HISTORY_POINTS, len(self.mem_usage_history)))

            for collection in self.ax.collections[:]:
                if hasattr(collection, '_original_facecolor'):
                    collection.remove()

            self.ax.fill_between(x_data, self.mem_usage_history, alpha=0.3, 
                               color=self.COLORS['secondary'])

            self.canvas.draw_idle()

    def _update_global_metrics(self, data: Dict[str, Any]):
        cpu_usage = data.get('cpu', {}).get('usage', 0)
        process_count = len(data.get('processes', []))
        thread_count = sum(proc.get('threads', 0) for proc in data.get('processes', []))

        metrics = {
            'cpu_usage': f"{cpu_usage:.1f}%",
            'cpu_idle': f"{100 - cpu_usage:.1f}%",  # Corrigido aqui
            'process_count': f"{process_count}",
            'thread_count': f"{thread_count}"
        }

        for key, value in metrics.items():
            if key in self.metric_labels:
                self.metric_labels[key].config(text=value)

        self.cpu_usage_history.append(cpu_usage)
        if len(self.cpu_usage_history) > self.MAX_HISTORY_POINTS:
            self.cpu_usage_history.pop(0)

        x_data = range(len(self.cpu_usage_history))
        self.cpu_line.set_data(x_data, self.cpu_usage_history)
        self.cpu_ax.set_xlim(0, max(self.MAX_HISTORY_POINTS, len(self.cpu_usage_history)))

        for collection in self.cpu_ax.collections[:]:
            collection.remove()

        self.cpu_ax.fill_between(x_data, self.cpu_usage_history, alpha=0.3, color=self.COLORS['secondary'])

        self.cpu_canvas.draw_idle()

    def _update_process_list(self, data: Dict[str, Any]):
        tree = self.trees.get('processes')
        if not tree:
            return

        for item in tree.get_children():
            tree.delete(item)

        processes = data.get("top_processes", [])[:self.MAX_PROCESSES_DISPLAY]
        for proc in processes:
            tree.insert("", tk.END, values=(
                proc.get("pid", "N/A"),
                proc.get("name", "N/A")[:20],
                format_memory_size(proc.get("memory_kb", 0)),
                proc.get("threads", "N/A"),
            ))


    def _update_memory_details(self):
        tree = self.trees.get('memory_details')
        if tree:
            for item in tree.get_children():
                tree.delete(item)

            mem_info = self.controller.system_info.get_memory_info()
            items = list(mem_info.items())[:self.MAX_MEMORY_ITEMS]
            
            for key, value in items:
                tree.insert("", tk.END, values=(key, format_memory_size(value)))

        # Atualizar detalhes extras se visíveis
        self._update_memory_details_if_visible()


    def _update_data(self):
        data = self.controller.get_data()
        if not data:
            return

        self._update_global_metrics(data)
        self._update_process_list(data)
        self._update_memory_details() 
        self._update_memory_chart(data)

        self.after(self.UPDATE_INTERVAL, self._update_data)

    def _start_updates(self):
        self._update_data()

    def _on_mousewheel_linux(self, event):
        direction = -1 if event.num == 4 else 1
        self.main_canvas.yview_scroll(direction, "units")
