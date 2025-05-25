import tkinter as tk
from tkinter import ttk
from typing import Any, Dict, List, Optional

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
    
    # Cores do tema
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
        
        # Referências para widgets que serão atualizados
        self.metric_labels: Dict[str, ttk.Label] = {}
        self.trees: Dict[str, ttk.Treeview] = {}
        
        self._setup_window()
        self._setup_matplotlib()
        self._setup_styles()
        self._create_interface()
        self._start_updates()

    def _setup_window(self):
        """Configura janela principal"""
        self.title(self.WINDOW_TITLE)
        self.geometry(self.WINDOW_SIZE)
        self.configure(bg=self.BACKGROUND_COLOR)

    def _setup_matplotlib(self):
        """Configura matplotlib para tema escuro"""
        plt.style.use("dark_background")

    def _setup_styles(self):
        """Configura todos os estilos do ttk"""
        style = ttk.Style(self)
        style.theme_use("clam")

        # Definições de estilos centralizadas
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

        # Aplicar configurações
        for style_name, config in style_configs.items():
            style.configure(style_name, **config)

        # Mapeamentos especiais
        style.map(
            "TNotebook.Tab",
            background=[("selected", self.COLORS['primary'])],
            foreground=[("selected", self.BACKGROUND_COLOR)],
        )
        style.map("Futuristic.Treeview", 
                 background=[("selected", f"{self.COLORS['primary']}33")])

    def _create_interface(self):
        """Cria interface principal"""
        self._create_header()
        self._create_tabs()

    def _create_header(self):
        """Cria cabeçalho da aplicação"""
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
        """Cria sistema de abas"""
        self.tab_control = ttk.Notebook(self)
        self.tab_control.pack(expand=1, fill="both", padx=20, pady=(0, 20))

        # Definir abas
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
        """Factory method para criar cards de métricas"""
        card = ttk.Frame(parent, style="Card.TFrame")
        card.pack(fill="x", pady=8, padx=5)

        title_label = ttk.Label(card, text=title, style="Info.TLabel")
        title_label.pack(anchor="w", padx=15, pady=(10, 5))

        value_label = ttk.Label(card, text=f"-- {unit}", style="Metric.TLabel")
        value_label.pack(anchor="w", padx=15, pady=(0, 10))

        # Armazenar referência para atualizações
        self.metric_labels[key] = value_label
        return value_label

    def _create_treeview(self, parent: tk.Widget, columns: List[str], 
                        key: str) -> ttk.Treeview:
        """Factory method para criar treeviews"""
        tree_frame = tk.Frame(parent, bg=self.BACKGROUND_COLOR)
        tree_frame.pack(fill="both", expand=True)

        tree = ttk.Treeview(
            tree_frame, 
            columns=columns, 
            show="headings", 
            style="Futuristic.Treeview"
        )

        # Configurar colunas
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, anchor=tk.CENTER, width=150)

        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Armazenar referência
        self.trees[key] = tree
        return tree

    def _create_global_tab(self, tab_frame: ttk.Frame):
        """Cria aba global"""
        container = tk.Frame(tab_frame, bg=self.BACKGROUND_COLOR)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        metrics_frame = tk.Frame(container, bg=self.BACKGROUND_COLOR)
        metrics_frame.pack(fill="x", pady=(0, 20))

        # CPU Section
        cpu_frame = self._create_section_frame(metrics_frame, "left", "🔥 PROCESSADOR")
        self._create_metric_card(cpu_frame, "Uso da CPU", "cpu_usage", "%")

        # Memory Section
        memory_frame = self._create_section_frame(metrics_frame, "right", "💾 MEMÓRIA RÁPIDA")
        memory_metrics = [
            ("Total", "mem_total", "GB"),
            ("Em Uso", "mem_used", "GB"),
            ("Livre", "mem_free", "GB"),
            ("Disponível", "mem_available", "GB")
        ]
        
        for title, key, unit in memory_metrics:
            self._create_metric_card(memory_frame, title, key, unit)

    def _create_section_frame(self, parent: tk.Widget, side: str, title: str) -> tk.Frame:
        """Cria frame de seção com título"""
        frame = tk.Frame(parent, bg=self.BACKGROUND_COLOR)
        pack_config = {"side": side, "fill": "both", "expand": True}
        
        if side == "left":
            pack_config["padx"] = (0, 10)
        elif side == "right":
            pack_config["padx"] = (10, 0)
            
        frame.pack(**pack_config)

        title_label = ttk.Label(frame, text=title, style="Title.TLabel")
        title_label.pack(anchor="w", pady=(0, 15))
        
        return frame

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
        """Painel de métricas otimizado e responsivo"""
        metrics_frame = ttk.Frame(parent, style="Card.TFrame")
        metrics_frame.pack(side="left", fill="both", padx=(0, 8))
        metrics_frame.configure(width=350)
        metrics_frame.pack_propagate(False)

        # Header do painel
        header = ttk.Label(metrics_frame, text="📊 MÉTRICAS PRINCIPAIS", style="Info.TLabel")
        header.pack(anchor="w", padx=15, pady=15)

        # Container scrollável para métricas
        metrics_scroll = tk.Frame(metrics_frame, bg=self.COLORS['card'])
        metrics_scroll.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # Métricas organizadas por grupos
        self._create_metric_groups(metrics_scroll)

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

    def _create_memory_chart_panel(self, parent: tk.Widget):
        """Painel do gráfico otimizado e responsivo"""
        chart_frame = ttk.Frame(parent, style="Card.TFrame")
        chart_frame.pack(side="right", fill="both", expand=True, padx=(8, 0))

        # Header do gráfico
        chart_header = tk.Frame(chart_frame, bg=self.COLORS['card'])
        chart_header.pack(fill="x", padx=15, pady=15)

        chart_title = ttk.Label(chart_header, text="📈 MONITOR EM TEMPO REAL", style="Info.TLabel")
        chart_title.pack(side="left")

        # Container do gráfico responsivo
        graph_container = tk.Frame(chart_frame, bg=self.COLORS['card'])
        graph_container.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # Configuração do matplotlib responsivo
        self.fig, self.ax = plt.subplots(figsize=(9, 6), facecolor=self.COLORS['card'])
        self.ax.set_facecolor(self.COLORS['dark'])
        
        # Estilo do gráfico otimizado
        self._configure_chart_style()

        # Canvas responsivo
        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_container)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def _configure_chart_style(self):
        """Configura estilo do gráfico de forma otimizada"""
        self.ax.set_title("USO DE MEMÓRIA RAM (%)", 
                         color=self.COLORS['primary'], 
                         fontsize=16, fontweight="bold", pad=20)
        
        self.ax.set_ylim(0, 100)
        self.ax.set_xlabel("Tempo (s)", color=self.COLORS['text'], fontsize=12)
        self.ax.set_ylabel("Uso (%)", color=self.COLORS['text'], fontsize=12)
        self.ax.tick_params(colors=self.COLORS['text'], labelsize=10)
        self.ax.grid(True, alpha=0.2, color=self.COLORS['grid'], linestyle=':')

        # Linha principal otimizada
        self.line, = self.ax.plot([], [], color=self.COLORS['secondary'], 
                                 linewidth=2.5, alpha=0.9, antialiased=True)

        # Zonas de alerta
        self.ax.axhspan(80, 90, alpha=0.1, color='orange', label='Atenção')
        self.ax.axhspan(90, 100, alpha=0.1, color='red', label='Crítico')

        # Legenda otimizada
        self.ax.legend(['Uso da Memória', 'Zona de Atenção', 'Zona Crítica'],
                      loc='upper left', fontsize=9, framealpha=0.8)

    # Remover métodos obsoletos e simplificar atualizações
    def _update_memory_chart(self, data: Dict[str, Any]):
        """Atualização otimizada do gráfico e métricas"""
        try:
            mem_data = data.get('mem', {})
            mem_percent = mem_data.get('mem_percent_usage', 0)

            # Atualizar métricas de forma unificada
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

        except Exception as e:
            print(f"Erro ao atualizar gráfico de memória: {e}")

    def _update_all_metrics(self, metrics_data: Dict[str, float]):
        """Atualiza todas as métricas de forma otimizada"""
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
        """Atualização otimizada do gráfico"""
        self.mem_usage_history.append(mem_percent)
        if len(self.mem_usage_history) > self.MAX_HISTORY_POINTS:
            self.mem_usage_history.pop(0)

        if len(self.mem_usage_history) > 1:
            x_data = range(len(self.mem_usage_history))
            self.line.set_data(x_data, self.mem_usage_history)
            self.ax.set_xlim(0, max(self.MAX_HISTORY_POINTS, len(self.mem_usage_history)))

            # Limpar preenchimentos anteriores
            for collection in self.ax.collections[:]:
                if hasattr(collection, '_original_facecolor'):
                    collection.remove()

            # Preenchimento suave
            self.ax.fill_between(x_data, self.mem_usage_history, alpha=0.3, 
                               color=self.COLORS['secondary'])

            # Redesenho eficiente
            self.canvas.draw_idle()

    def _update_global_metrics(self, data: Dict[str, Any]):
        """Atualiza métricas da aba global"""
        try:
            cpu_usage = data.get('cpu', {}).get('usage', 0)
            if 'cpu_usage' in self.metric_labels:
                self.metric_labels['cpu_usage'].config(text=f"{cpu_usage:.1f} %")

            mem_data = data.get('mem', {})
            total = mem_data.get('total_memory', 0)
            used = mem_data.get('used_memory', 0)
            available = mem_data.get('available_memory', 0)
            free = total - used

            memory_values = [
                ('mem_total', total),
                ('mem_used', used),
                ('mem_free', free),
                ('mem_available', available)
            ]

            for key, value in memory_values:
                if key in self.metric_labels:
                    formatted_value = format_memory_value_only(value)
                    unit = get_memory_unit(value)
                    self.metric_labels[key].config(text=f"{formatted_value} {unit}")

        except (KeyError, ValueError, TypeError) as e:
            print(f"Erro ao atualizar métricas globais: {e}")

    def _update_process_list(self, data: Dict[str, Any]):
        """Atualiza lista de processos"""
        try:
            tree = self.trees.get('processes')
            if not tree:
                return

            # Limpar dados anteriores
            for item in tree.get_children():
                tree.delete(item)

            # Inserir novos dados
            processes = data.get("top_processes", [])[:self.MAX_PROCESSES_DISPLAY]
            for proc in processes:
                tree.insert("", tk.END, values=(
                    proc.get("pid", "N/A"),
                    proc.get("name", "N/A")[:20],
                    format_memory_size(proc.get("memory_kb", 0)),
                    proc.get("threads", "N/A"),
                ))

        except (KeyError, TypeError) as e:
            print(f"Erro ao atualizar lista de processos: {e}")

    def _update_memory_details(self):
        """Atualiza detalhes da memória (se necessário)"""
        try:
            tree = self.trees.get('memory_details')
            if not tree:
                return

            # Limpar dados anteriores
            for item in tree.get_children():
                tree.delete(item)

            # Obter informações de memória
            mem_info = self.controller.system_info.get_memory_info()
            items = list(mem_info.items())[:self.MAX_MEMORY_ITEMS]
            
            for key, value in items:
                tree.insert("", tk.END, values=(key, format_memory_size(value)))

        except Exception as e:
            print(f"Erro ao atualizar detalhes da memória: {e}")

    def _update_data(self):
        """Atualiza todos os dados da interface"""
        try:
            data = self.controller.get_data()
            if not data:
                return

            self._update_global_metrics(data)
            self._update_process_list(data)
            self._update_memory_details()  # Restaurado para compatibilidade
            self._update_memory_chart(data)

        except Exception as e:
            print(f"Erro geral na atualização de dados: {e}")
        finally:
            self.after(self.UPDATE_INTERVAL, self._update_data)

    def _start_updates(self):
        """Inicia ciclo de atualizações"""
        self._update_data()
