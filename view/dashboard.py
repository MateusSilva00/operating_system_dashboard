import signal
import sys
import tkinter as tk
from tkinter import ttk
from typing import Any, Dict, List

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from controller.monitor_controller import MonitorController
from view.utils import format_memory_size, format_memory_value_only, get_memory_unit


class Dashboard(tk.Tk):
    # Constantes de configuração
    WINDOW_TITLE = "OS DASHBOARD"
    WINDOW_SIZE = "1200x800"
    BACKGROUND_COLOR = "#0a0a0a"
    UPDATE_INTERVAL = 1000
    MAX_PROCESSES_DISPLAY = 15
    MAX_MEMORY_ITEMS = 20
    MAX_HISTORY_POINTS = 60

    COLORS = {
        "primary": "#00d4ff",
        "secondary": "#00ff88",
        "background": "#0a0a0a",
        "card": "#1a1a1a",
        "dark": "#111111",
        "text": "#ffffff",
        "grid": "#333333",
    }

    def __init__(self, controller: MonitorController):
        super().__init__()
        self.controller = controller
        self.mem_usage_history: List[float] = []
        self.show_all_memory_details = False

        self.metric_labels: Dict[str, ttk.Label] = {}
        self.trees: Dict[str, ttk.Treeview] = {}

        # Configurar tratamento de sinais
        self._setup_signal_handlers()

        self._setup_window()
        self._setup_matplotlib()
        self._setup_styles()
        self._create_interface()
        self._start_updates()

    def _setup_signal_handlers(self):
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Bind para ESC e Ctrl+C na interface
        self.bind("<Control-c>", self._on_exit_keypress)
        self.bind("<Escape>", self._on_exit_keypress)
        self.focus_set()  # Necessário para capturar eventos de teclado

    def _signal_handler(self, signum, frame):
        """Handler para sinais do sistema (Ctrl+C, etc.)"""
        self._cleanup_and_exit()

    def _on_exit_keypress(self, event=None):
        """Handler para teclas de saída (Ctrl+C, ESC)"""
        self._cleanup_and_exit()

    def _cleanup_and_exit(self):
        # Parar o controller
        if hasattr(self, "controller"):
            self.controller.stop()

        # Fechar figuras matplotlib
        if hasattr(self, "cpu_fig"):
            plt.close(self.cpu_fig)
        if hasattr(self, "fig"):
            plt.close(self.fig)

        self.quit()
        self.destroy()
        sys.exit(0)

    def _setup_window(self):
        self.title(self.WINDOW_TITLE)
        self.geometry(self.WINDOW_SIZE)
        self.configure(bg=self.BACKGROUND_COLOR)

        # Configurar comportamento ao fechar janela
        self.protocol("WM_DELETE_WINDOW", self._cleanup_and_exit)

    def _setup_matplotlib(self):
        plt.style.use("dark_background")

    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style_configs = {
            "TNotebook": {
                "background": self.BACKGROUND_COLOR,
                "borderwidth": 0,
                "tabmargins": [5, 5, 5, 0],
            },
            "TNotebook.Tab": {
                "background": self.COLORS["card"],
                "foreground": self.COLORS["primary"],
                "padding": [20, 12],
                "font": ("JetBrains Mono", 11, "bold"),
                "borderwidth": 0,
            },
            "Title.TLabel": {
                "background": self.BACKGROUND_COLOR,
                "foreground": self.COLORS["primary"],
                "font": ("JetBrains Mono", 16, "bold"),
            },
            "Info.TLabel": {
                "background": self.BACKGROUND_COLOR,
                "foreground": self.COLORS["text"],
                "font": ("JetBrains Mono", 12),
            },
            "Metric.TLabel": {
                "background": self.COLORS["card"],
                "foreground": self.COLORS["secondary"],
                "font": ("JetBrains Mono", 14, "bold"),
                "relief": "flat",
                "borderwidth": 1,
            },
            "Card.TFrame": {
                "background": self.COLORS["card"],
                "relief": "flat",
                "borderwidth": 1,
            },
            "Futuristic.Treeview": {
                "background": self.COLORS["dark"],
                "foreground": self.COLORS["text"],
                "fieldbackground": self.COLORS["dark"],
                "font": ("JetBrains Mono", 10),
                "borderwidth": 0,
                "rowheight": 25,
            },
            "Futuristic.Treeview.Heading": {
                "background": self.COLORS["primary"],
                "foreground": self.BACKGROUND_COLOR,
                "font": ("JetBrains Mono", 11, "bold"),
                "borderwidth": 0,
            },
            # Estilo para threads
            "Thread.Treeview": {
                "background": "#222a33",
                "foreground": "#00ff88",
                "font": ("JetBrains Mono", 10, "italic"),
            },
        }

        for style_name, config in style_configs.items():
            style.configure(style_name, **config)

        # Tag para threads: cor de fundo e texto diferente
        style.map(
            "TNotebook.Tab",
            background=[("selected", self.COLORS["primary"])],
            foreground=[("selected", self.BACKGROUND_COLOR)],
        )
        style.map(
            "Futuristic.Treeview",
            background=[("selected", f"{self.COLORS['primary']}33")],
        )
        # Aplica cor de fundo para threads
        style.configure("thread", background="#222a33", foreground="#00ff88", font=("JetBrains Mono", 10, "italic"))

    def _create_interface(self):
        self._create_header()
        self._create_tabs()

    def _create_header(self):
        header_frame = tk.Frame(self, bg=self.BACKGROUND_COLOR, height=60)
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        header_frame.pack_propagate(False)

        title_label = ttk.Label(
            header_frame, text="SISTEMA OPERACIONAL DASHBOARD", style="Title.TLabel"
        )
        title_label.pack(side="left", pady=15)

    def _create_tabs(self):
        self.tab_control = ttk.Notebook(self)
        self.tab_control.pack(expand=1, fill="both", padx=20, pady=(0, 20))

        tabs_config = [
            ("global", "GLOBAL", self._create_global_tab),
            ("process", "PROCESSOS", self._create_process_tab),
            ("memory", "MEMÓRIA", self._create_memory_tab),
            ("filesystem", "SISTEMA DE ARQUIVOS", self._create_filesystem_tab),
        ]

        self.tabs = {}
        for tab in tabs_config:
            tab_key = tab[0]
            tab_text = tab[1]
            create_func = tab[2]
            tab_frame = ttk.Frame(self.tab_control)
            self.tab_control.add(tab_frame, text=tab_text)
            self.tabs[tab_key] = tab_frame
            if callable(create_func):
                create_func(tab_frame)

    def _create_metric_card(
        self, parent: tk.Widget, title: str, key: str, unit: str = ""
    ) -> ttk.Label:
        card = ttk.Frame(parent, style="Card.TFrame")
        card.pack(fill="x", pady=5, padx=3)

        title_label = ttk.Label(card, text=title, style="Info.TLabel")
        title_label.pack(anchor="w", padx=12, pady=(8, 3))

        value_label = ttk.Label(card, text=f"-- {unit}", style="Metric.TLabel")
        value_label.pack(anchor="w", padx=12, pady=(0, 8))

        self.metric_labels[key] = value_label
        return value_label

    def _create_treeview(
        self, parent: tk.Widget, columns: List[str], key: str
    ) -> ttk.Treeview:
        tree_frame = tk.Frame(parent, bg=self.BACKGROUND_COLOR)
        tree_frame.pack(fill="both", expand=True)

        tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings", style="Futuristic.Treeview"
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
            ("Threads", "thread_count", ""),
        ]

        for title, key, unit in cpu_metrics:
            self._create_metric_card(metrics_frame, title, key, unit)

        chart_frame = ttk.Frame(container, style="Card.TFrame")
        chart_frame.pack(fill="both", expand=True, pady=(10, 0))

        self.cpu_fig, self.cpu_ax = plt.subplots(
            figsize=(8, 4), facecolor=self.COLORS["card"]
        )
        self.cpu_ax.set_facecolor(self.COLORS["dark"])
        self.cpu_ax.set_title(
            "Uso da CPU (%)",
            color=self.COLORS["primary"],
            fontsize=14,
            fontweight="bold",
        )
        self.cpu_ax.set_ylim(0, 100)
        self.cpu_ax.set_xlabel("Tempo (s)", color=self.COLORS["text"])
        self.cpu_ax.set_ylabel("Uso (%)", color=self.COLORS["text"])
        self.cpu_ax.tick_params(colors=self.COLORS["text"])
        self.cpu_ax.grid(True, alpha=0.2, color=self.COLORS["grid"], linestyle=":")

        (self.cpu_line,) = self.cpu_ax.plot(
            [], [], color=self.COLORS["secondary"], linewidth=2.5
        )

        self.cpu_usage_history: List[float] = []

        self.cpu_canvas = FigureCanvasTkAgg(self.cpu_fig, master=chart_frame)
        self.cpu_canvas.get_tk_widget().pack(fill="both", expand=True)

    def _create_process_tab(self, tab_frame: ttk.Frame):
        """Cria aba de processos simplificada"""
        container = tk.Frame(tab_frame, bg=self.BACKGROUND_COLOR)
        container.pack(fill="both", expand=True, padx=12, pady=12)

        metrics_container = tk.Frame(container, bg=self.BACKGROUND_COLOR)
        metrics_container.pack(fill="x", pady=(0, 10))

        process_card = ttk.Frame(metrics_container, style="Card.TFrame")
        process_card.pack(side="left", fill="x", expand=True, padx=(0, 5))

        thread_card = ttk.Frame(metrics_container, style="Card.TFrame")
        thread_card.pack(side="right", fill="x", expand=True, padx=(5, 0))

        proc_title = ttk.Label(process_card, text="PROCESSOS", style="Info.TLabel")
        proc_title.pack(anchor="w", padx=12, pady=(8, 3))

        self.metric_labels["total_processes"] = ttk.Label(process_card, text="-- processos", style="Metric.TLabel")
        self.metric_labels["total_processes"].pack(anchor="w", padx=12, pady=(0, 8))

        thread_title = ttk.Label(thread_card, text="THREADS", style="Info.TLabel")
        thread_title.pack(anchor="w", padx=12, pady=(8, 3))

        self.metric_labels["total_threads"] = ttk.Label(thread_card, text="-- threads", style="Metric.TLabel")
        self.metric_labels["total_threads"].pack(anchor="w", padx=12, pady=(0, 8))

        self.process_tab_control = ttk.Notebook(container)
        self.process_tab_control.pack(expand=1, fill="both")

        processes_frame = ttk.Frame(self.process_tab_control)
        self.process_tab_control.add(processes_frame, text="PROCESSOS ATIVOS")

        proc_container = tk.Frame(processes_frame, bg=self.BACKGROUND_COLOR)
        proc_container.pack(fill="both", expand=True, padx=8, pady=8)

        proc_columns = ("Num", "PID", "USUÁRIO", "PROCESSO", "STATUS", "MEMÓRIA", "THREADS")
        tree = ttk.Treeview(proc_container, columns=proc_columns, show="headings", style="Futuristic.Treeview")
        tree.heading("Num", text="")
        tree.column("Num", width=30, anchor="w")
        for col in proc_columns[1:]:
            tree.heading(col, text=col)
            tree.column(col, anchor=tk.CENTER, width=100 if col != "PROCESSO" else 180)

        scrollbar = ttk.Scrollbar(proc_container, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.trees["processes"] = tree
        self._expanded_process = None
        self._thread_items = []

        # Bind para clique na Treeview (seta e detalhes)
        tree.bind("<Button-1>", self._on_process_arrow_click)

        # Sub-aba de detalhes
        details_frame = ttk.Frame(self.process_tab_control)
        self.process_tab_control.add(details_frame, text="DETALHES")

        details_container = tk.Frame(details_frame, bg=self.BACKGROUND_COLOR)
        details_container.pack(fill="both", expand=True, padx=8, pady=8)

        details_header = ttk.Label(details_container, text="DETALHES DO PROCESSO", style="Info.TLabel")
        details_header.pack(anchor="w", pady=(0, 8))

        details_text_frame = tk.Frame(details_container, bg=self.BACKGROUND_COLOR)
        details_text_frame.pack(fill="both", expand=True)

        self.details_text = tk.Text(details_text_frame, bg=self.COLORS["dark"], fg=self.COLORS["text"], 
                                   font=("JetBrains Mono", 9), wrap=tk.WORD, state=tk.DISABLED)

        details_scrollbar = ttk.Scrollbar(details_text_frame, orient="vertical", command=self.details_text.yview)
        self.details_text.configure(yscrollcommand=details_scrollbar.set)

        self.details_text.pack(side="left", fill="both", expand=True)
        details_scrollbar.pack(side="right", fill="y")

    def _on_process_arrow_click(self, event):
        """Expande/collapse threads ao clicar na seta OU mostra recursos ao clicar no PID/TID."""
        tree = self.trees["processes"]
        col = tree.identify_column(event.x)
        row_id = tree.identify_row(event.y)
        if not row_id:
            return
        # Só reage à coluna da seta
        if col == "#1":
            current_value = tree.set(row_id, "Num")
            if current_value == "▶":
                self._expand_threads_custom(row_id)
            elif current_value == "▼":
                self._collapse_threads_custom(row_id)
        elif col == "#2":
            # Clique no PID/TID: mostra recursos em nova janela E detalhes na aba
            values = tree.item(row_id, "values")
            if values and len(values) > 1:
                pid_tid = str(values[1]).strip()
                # Se for thread (TID), extrai apenas o número
                if pid_tid.startswith("↳ TID:"):
                    tid = pid_tid.replace("↳ TID:", "").strip()
                    self._show_process_resources_window(tid, is_thread=True)
                    # Para threads, mostra detalhes do processo pai
                    # Busca o processo pai na árvore
                    parent_item = tree.parent(row_id)
                    if parent_item:
                        parent_values = tree.item(parent_item, "values")
                        if parent_values and len(parent_values) > 1:
                            parent_pid = str(parent_values[1]).strip()
                            self._show_process_details(parent_pid)
                else:
                    self._show_process_resources_window(pid_tid, is_thread=False)
                    self._show_process_details(pid_tid)

    def _show_process_resources_window(self, pid_tid, is_thread=False):
        """Abre uma nova janela com os recursos do processo ou thread."""
        pid = pid_tid
        if is_thread:
            msg = f"Recursos para TID {pid_tid}.\n\nThreads compartilham recursos do processo principal.\n\n"
        else:
            msg = f"Recursos para PID {pid_tid}.\n\n"
        
        try:
            resources = self.controller.system_info.get_process_resources(int(pid))
        except Exception as e:
            resources = None
            msg += f"Erro: {e}"

        win = tk.Toplevel(self)
        win.title(f"Recursos - {pid_tid}")
        win.geometry("600x400")
        win.configure(bg=self.BACKGROUND_COLOR)
        
        close_btn = tk.Button(win, text="Fechar", command=win.destroy, 
                             bg=self.COLORS["primary"], fg=self.COLORS["background"], 
                             font=("JetBrains Mono", 10, "bold"), relief="flat", 
                             padx=8, pady=4)
        close_btn.pack(side="bottom", pady=8)
        
        text = tk.Text(win, bg=self.COLORS["dark"], fg=self.COLORS["text"], 
                      font=("JetBrains Mono", 9), wrap=tk.WORD)
        text.pack(fill="both", expand=True, padx=12, pady=12)
        text.insert("end", msg)
        
        if resources:
            open_files = resources.get("open_files", [])
            text.insert("end", f"Arquivos abertos ({len(open_files)}):\n")
            for f in open_files:
                text.insert("end", f"  [fd {f['fd']}] {f['target']}\n")
            if not open_files:
                text.insert("end", "  Nenhum arquivo encontrado.\n")
            
            sockets = resources.get("sockets", [])
            text.insert("end", f"\nSockets ({len(sockets)}):\n")
            for s in sockets:
                text.insert("end", f"  [fd {s['fd']}] {s['target']}\n")
            if not sockets:
                text.insert("end", "  Nenhum socket encontrado.\n")
            
            semaphores = resources.get("semaphores", [])
            text.insert("end", f"\nSemáforos/Mutexes ({len(semaphores)}):\n")
            for sem in semaphores:
                info_preview = sem['info'][:50].replace("\n", " ")
                text.insert("end", f"  [fd {sem['fd']}] {info_preview}...\n")
            if not semaphores:
                text.insert("end", "  Nenhum semáforo/mutex encontrado.\n")
        text.config(state="disabled")

    def _expand_threads_custom(self, item_id):
        tree = self.trees["processes"]
        # Colapsa qualquer outro processo expandido
        if self._expanded_process and self._expanded_process != item_id:
            self._collapse_threads_custom(self._expanded_process)
        # Busca threads do processo
        values = tree.item(item_id, "values")
        data = self.controller.get_data()
        process = None
        for proc in data.get("top_processes", []):
            if str(proc.get("PID")) == str(values[1]):
                process = proc
                break
        if not process:
            return
        threads = process.get("Threads", [])
        self._thread_items = []
        for thread in threads:
            thread_id = tree.insert(
                item_id,
                tk.END,
                values=(
                    "",
                    f"↳ TID: {thread.get('TID', '-')} ",
                    thread.get("User", "-"),
                    f"↳ {thread.get('Name', '-')} ",
                    thread.get("Status", "-"),
                    "-",  # Memória não detalhada por thread
                    "-",  # Threads por thread não faz sentido
                ),
                tags=("thread",)
            )
            self._thread_items.append(thread_id)
        tree.set(item_id, "Num", value="▼")
        tree.item(item_id, open=True)  # Garante que as threads fiquem visíveis
        self._expanded_process = item_id

    def _collapse_threads_custom(self, item_id):
        tree = self.trees["processes"]
        # Remove todos os filhos threads
        children = tree.get_children(item_id)
        for child in children:
            if "thread" in tree.item(child, "tags"):
                tree.delete(child)
        tree.set(item_id, "Num", value="▶")
        tree.item(item_id, open=False)  # Garante que o processo fique fechado
        self._expanded_process = None
        self._thread_items = []

    def _on_process_select(self, event):
        """Exibe detalhes do processo selecionado e expande/collapse threads"""
        tree = self.trees["processes"]
        selection = tree.selection()
        if not selection:
            return

        item_id = selection[0]
        item = tree.item(item_id)
        values = item["values"]
        if not values:
            return
        pid = str(values[0])
        self._show_process_details(pid)

        # Collapse threads se já estiver expandido
        if self._expanded_process == item_id:
            for tid in self._thread_items:
                tree.delete(tid)
            self._expanded_process = None
            self._thread_items = []
            return
        # Remove threads de expansão anterior
        if self._thread_items:
            for tid in self._thread_items:
                tree.delete(tid)
            self._thread_items = []

        # Buscar threads do processo
        process = None
        data = self.controller.get_data()
        for proc in data.get("top_processes", []):
            if str(proc.get("PID")) == pid:
                process = proc
                break
        if not process:
            return
        threads = process.get("Threads", [])
        # Inserir threads como filhos
        for thread in threads:
            thread_id = tree.insert(
                item_id,
                tk.END,
                values=(
                    f"↳ TID: {thread.get('TID', '-')} ",
                    thread.get("User", "-"),
                    f"↳ {thread.get('Name', '-')} ",
                    thread.get("Status", "-"),
                    "-",  # Memória não detalhada por thread
                    "-",  # Threads por thread não faz sentido
                ),
                tags=("thread",)
            )
            self._thread_items.append(thread_id)
        self._expanded_process = item_id

        # Expandir visualmente
        tree.item(item_id, open=True)

    def _show_process_details(self, pid):
        """Mostra detalhes do processo de forma mais compacta"""
        details = self.controller.process_info.get_process_details(pid)
        page_usage = self.controller.process_info.get_page_usage_by_pid(pid)

        self.details_text.config(state=tk.NORMAL)
        self.details_text.delete(1.0, tk.END)

        if details:
            output = f"PROCESSO {pid}\n"
            output += "=" * 30 + "\n\n"

            basic_info = [
                ("Nome", details.get("Name", "N/A")),
                ("Estado", details.get("State", "N/A")),
                ("PPID", details.get("PPid", "N/A")),
                ("Usuário ID", details.get("Uid", "N/A")),
            ]

            for label, value in basic_info:
                output += f"{label}: {value}\n"

            if any(key.startswith("Vm") for key in details.keys()):
                output += "\nMEMÓRIA:\n"
                memory_keys = ["VmSize", "VmRSS", "VmData", "VmStk"]
                for key in memory_keys:
                    if key in details:
                        output += f"  {key}: {details[key]}\n"

            if page_usage and any(page_usage.values()):
                output += f"\nPÁGINAS: {page_usage.get('total', 0)} kB\n"

            if "Command Line" in details and details["Command Line"]:
                output += f"\nComando: {details['Command Line']}\n"
                
            # Mudar automaticamente para a aba de detalhes
            self.process_tab_control.select(1)  # Seleciona a segunda aba (DETALHES)
        else:
            output = f"Erro: Não foi possível obter detalhes do processo {pid}"

        self.details_text.insert(tk.END, output)
        self.details_text.config(state=tk.DISABLED)

    def _create_memory_tab(self, tab_frame: ttk.Frame):
        """Cria aba de memória simplificada"""
        container = tk.Frame(tab_frame, bg=self.BACKGROUND_COLOR)
        container.pack(fill="both", expand=True, padx=12, pady=12)

        main_layout = tk.Frame(container, bg=self.BACKGROUND_COLOR)
        main_layout.pack(fill="both", expand=True)

        self._create_memory_metrics_panel(main_layout)
        self._create_memory_chart_panel(main_layout)

    def _create_memory_metrics_panel(self, parent: tk.Widget):
        metrics_frame = ttk.Frame(parent, style="Card.TFrame")
        metrics_frame.pack(side="left", fill="both", padx=(0, 6))
        metrics_frame.configure(width=320)
        metrics_frame.pack_propagate(False)

        header_frame = tk.Frame(metrics_frame, bg=self.COLORS["card"])
        header_frame.pack(fill="x", padx=12, pady=12)

        header = ttk.Label(header_frame, text="MÉTRICAS", style="Info.TLabel")
        header.pack(side="left")

        self.toggle_button = tk.Button(header_frame, text="Mais", command=self._toggle_memory_details,
                                     bg=self.COLORS["primary"], fg=self.COLORS["background"], 
                                     font=("JetBrains Mono", 8, "bold"), relief="flat", 
                                     padx=8, pady=3, cursor="hand2")
        self.toggle_button.pack(side="right")

        main_scroll_container = tk.Frame(metrics_frame, bg=self.COLORS["card"])
        main_scroll_container.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.main_canvas = tk.Canvas(main_scroll_container, bg=self.COLORS["card"], highlightthickness=0)
        main_scrollbar = ttk.Scrollbar(main_scroll_container, orient="vertical", command=self.main_canvas.yview)
        self.main_scrollable_frame = tk.Frame(self.main_canvas, bg=self.COLORS["card"])

        self.main_scrollable_frame.bind("<Configure>", 
                                       lambda e: self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all")))
        self.main_canvas.create_window((0, 0), window=self.main_scrollable_frame, anchor="nw")
        self.main_canvas.configure(yscrollcommand=main_scrollbar.set)

        self.main_canvas.bind("<Enter>", lambda e: self.main_canvas.bind_all("<Button-4>", self._on_mousewheel_linux))
        self.main_canvas.bind("<Leave>", lambda e: self.main_canvas.unbind_all("<Button-4>"))
        self.main_canvas.bind("<Enter>", lambda e: self.main_canvas.bind_all("<Button-5>", self._on_mousewheel_linux))
        self.main_canvas.bind("<Leave>", lambda e: self.main_canvas.unbind_all("<Button-5>"))

        self.main_canvas.pack(side="left", fill="both", expand=True)
        main_scrollbar.pack(side="right", fill="y")

        self.main_metrics_frame = tk.Frame(self.main_scrollable_frame, bg=self.COLORS["card"])
        self.main_metrics_frame.pack(fill="x", pady=(0, 8))

        self.extra_details_frame = tk.Frame(self.main_scrollable_frame, bg=self.COLORS["card"])

        self._create_metric_groups(self.main_metrics_frame)
        self._create_extra_memory_details()

    def _create_metric_groups(self, parent: tk.Widget):
        """Cria grupos de métricas organizados"""
        groups = {
            "MEMÓRIA FÍSICA": [
                ("Total", "mem_total_chart"),
                ("Em Uso", "mem_used_chart"),
                ("Livre", "mem_free_chart"),
                ("% Uso", "mem_percent"),
            ],
            "CACHE/BUFFER": [("Cache", "mem_cache"), ("Buffers", "mem_buffers")],
            "SWAP": [("Swap Total", "mem_virtual")],
        }

        for group_name, metrics in groups.items():
            # Título do grupo
            group_frame = tk.Frame(parent, bg=self.COLORS["card"])
            group_frame.pack(fill="x", pady=(5, 10))

            group_label = ttk.Label(
                group_frame,
                text=group_name,
                font=("JetBrains Mono", 11, "bold"),
                foreground=self.COLORS["primary"],
                background=self.COLORS["card"],
            )
            group_label.pack(anchor="w", pady=(0, 5))

            # Métricas do grupo
            for label, key in metrics:
                self._create_compact_metric(group_frame, label, key)

    def _create_compact_metric(self, parent: tk.Widget, title: str, key: str):
        """Cria métrica compacta e responsiva"""
        metric_frame = tk.Frame(parent, bg=self.COLORS["dark"])
        metric_frame.pack(fill="x", pady=2, padx=5)

        # Layout flex
        content_frame = tk.Frame(metric_frame, bg=self.COLORS["dark"])
        content_frame.pack(fill="x", padx=8, pady=6)

        title_label = ttk.Label(
            content_frame,
            text=title,
            font=("JetBrains Mono", 10),
            foreground=self.COLORS["text"],
            background=self.COLORS["dark"],
        )
        title_label.pack(side="left")

        value_label = ttk.Label(
            content_frame,
            text="--",
            font=("JetBrains Mono", 10, "bold"),
            foreground=self.COLORS["secondary"],
            background=self.COLORS["dark"],
        )
        value_label.pack(side="right")

        self.metric_labels[key] = value_label

    def _create_extra_memory_details(self):
        """Cria seção de detalhes extras de memória"""
        # Título da seção
        details_title = ttk.Label(
            self.extra_details_frame,
            text="DETALHES COMPLETOS",
            font=("JetBrains Mono", 11, "bold"),
            foreground=self.COLORS["primary"],
            background=self.COLORS["card"],
        )
        details_title.pack(anchor="w", pady=(10, 5))

        # Container para os detalhes (sem scroll separado, usa o scroll principal)
        details_container = tk.Frame(self.extra_details_frame, bg=self.COLORS["card"])
        details_container.pack(fill="both", expand=True)

        # Frame scrollável simples (o scroll principal cuidará disso)
        self.scrollable_frame = tk.Frame(details_container, bg=self.COLORS["card"])
        self.scrollable_frame.pack(fill="both", expand=True)

        # Armazenar referências para atualização
        self.memory_details_labels = {}

    def _toggle_memory_details(self):
        self.show_all_memory_details = not self.show_all_memory_details
        if self.show_all_memory_details:
            self.extra_details_frame.pack(fill="both", expand=True, pady=(8, 0))
            self.toggle_button.config(text="Menos")
            self._populate_memory_details()
        else:
            self.extra_details_frame.pack_forget()
            self.toggle_button.config(text="Mais")
        self.main_canvas.update_idletasks()
        self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))

    def _populate_memory_details(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.memory_details_labels.clear()

        mem_info = self.controller.system_info.get_memory_info()
        for key, value in mem_info.items():
            detail_frame = tk.Frame(self.scrollable_frame, bg=self.COLORS["dark"])
            detail_frame.pack(fill="x", pady=1, padx=2)

            content_frame = tk.Frame(detail_frame, bg=self.COLORS["dark"])
            content_frame.pack(fill="x", padx=6, pady=3)

            name_label = ttk.Label(
                content_frame,
                text=key.replace("_", " ").title(),
                font=("JetBrains Mono", 8),
                foreground=self.COLORS["text"],
                background=self.COLORS["dark"],
            )
            name_label.pack(side="left")

            value_label = ttk.Label(
                content_frame,
                text=format_memory_size(value),
                font=("JetBrains Mono", 8, "bold"),
                foreground=self.COLORS["secondary"],
                background=self.COLORS["dark"],
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

        chart_header = tk.Frame(chart_frame, bg=self.COLORS["card"])
        chart_header.pack(fill="x", padx=15, pady=15)

        chart_title = ttk.Label(
            chart_header, text="MONITOR EM TEMPO REAL", style="Info.TLabel"
        )
        chart_title.pack(side="left")

        graph_container = tk.Frame(chart_frame, bg=self.COLORS["card"])
        graph_container.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.fig, self.ax = plt.subplots(figsize=(9, 6), facecolor=self.COLORS["card"])
        self.ax.set_facecolor(self.COLORS["dark"])

        self._configure_chart_style()

        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_container)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def _configure_chart_style(self):
        self.ax.set_title(
            "USO DE MEMÓRIA RAM (%)",
            color=self.COLORS["primary"],
            fontsize=16,
            fontweight="bold",
            pad=20,
        )

        self.ax.set_ylim(0, 100)
        self.ax.set_xlabel("Tempo (s)", color=self.COLORS["text"], fontsize=12)
        self.ax.set_ylabel("Uso (%)", color=self.COLORS["text"], fontsize=12)
        self.ax.tick_params(colors=self.COLORS["text"], labelsize=10)
        self.ax.grid(True, alpha=0.2, color=self.COLORS["grid"], linestyle=":")

        (self.line,) = self.ax.plot(
            [],
            [],
            color=self.COLORS["secondary"],
            linewidth=2.5,
            alpha=0.9,
            antialiased=True,
        )

        self.ax.axhspan(80, 90, alpha=0.1, color="orange", label="Atenção")
        self.ax.axhspan(90, 100, alpha=0.1, color="red", label="Crítico")

        self.ax.legend(
            ["Uso da Memória", "Zona de Atenção", "Zona Crítica"],
            loc="upper left",
            fontsize=9,
            framealpha=0.8,
        )

    def _update_memory_chart(self, data: Dict[str, Any]):
        mem_data = data.get("mem", {})
        if not isinstance(mem_data, dict):
            return

        mem_percent = mem_data.get("mem_percent_usage", 0)
        if not isinstance(mem_percent, (int, float)):
            mem_percent = 0

        metrics_data = {
            "mem_total_chart": mem_data.get("total_memory", 0),
            "mem_used_chart": mem_data.get("used_memory", 0),
            "mem_free_chart": mem_data.get("free_memory", 0),
            "mem_percent": mem_percent,
            "mem_cache": mem_data.get("cached_memory", 0),
            "mem_buffers": mem_data.get("buffers", 0),
            "mem_virtual": mem_data.get("swap_total", 0),
        }

        self._update_all_metrics(metrics_data)
        self._update_chart_optimized(mem_percent)

    def _update_all_metrics(self, metrics_data: Dict[str, float]):
        for key, value in metrics_data.items():
            if key in self.metric_labels:
                if key == "mem_percent":
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
            self.ax.set_xlim(
                0, max(self.MAX_HISTORY_POINTS, len(self.mem_usage_history))
            )

            for collection in self.ax.collections[:]:
                if hasattr(collection, "_original_facecolor"):
                    collection.remove()

            self.ax.fill_between(
                x_data,
                self.mem_usage_history,
                alpha=0.3,
                color=self.COLORS["secondary"],
            )

            self.canvas.draw_idle()

    def _update_global_metrics(self, data: Dict[str, Any]):
        cpu_data = data.get("cpu", {})
        cpu_usage = cpu_data.get("usage", 0) if isinstance(cpu_data, dict) else 0

        # Usar os totais calculados pelo controller
        total_processes = data.get("total_processes", 0)
        total_threads = data.get("total_threads", 0)

        metrics = {
            "cpu_usage": f"{cpu_usage:.1f}%",
            "cpu_idle": f"{100 - cpu_usage:.1f}%",
            "process_count": f"{total_processes}",
            "thread_count": f"{total_threads}",
        }

        for key, value in metrics.items():
            if key in self.metric_labels:
                self.metric_labels[key].config(text=value)

        # Atualizar gráfico da CPU
        if isinstance(cpu_usage, (int, float)):
            self.cpu_usage_history.append(cpu_usage)
            if len(self.cpu_usage_history) > self.MAX_HISTORY_POINTS:
                self.cpu_usage_history.pop(0)

            if len(self.cpu_usage_history) > 1:
                x_data = range(len(self.cpu_usage_history))
                self.cpu_line.set_data(x_data, self.cpu_usage_history)
                self.cpu_ax.set_xlim(
                    0, max(self.MAX_HISTORY_POINTS, len(self.cpu_usage_history))
                )

                # Limpar preenchimentos anteriores
                for collection in self.cpu_ax.collections[:]:
                    collection.remove()

                self.cpu_ax.fill_between(
                    x_data,
                    self.cpu_usage_history,
                    alpha=0.3,
                    color=self.COLORS["secondary"],
                )
                self.cpu_canvas.draw_idle()

    def _update_process_list(self, data: Dict[str, Any]):
        # Atualizar métricas de resumo
        total_processes = data.get("total_processes", 0)
        total_threads = data.get("total_threads", 0)

        if "total_processes" in self.metric_labels:
            self.metric_labels["total_processes"].config(
                text=f"{total_processes} processos"
            )
        if "total_threads" in self.metric_labels:
            self.metric_labels["total_threads"].config(text=f"{total_threads} threads")

        # --- Preservar expansão ---
        proc_tree = self.trees.get("processes")
        expanded_pid = None
        if self._expanded_process:
            # Tentar obter o PID do processo expandido antes de limpar
            try:
                values = proc_tree.item(self._expanded_process, "values")
                if values and len(values) > 1:
                    expanded_pid = str(values[1])
            except Exception:
                expanded_pid = None

        # Atualizar tabela de processos
        if proc_tree:
            # Limpar dados anteriores
            for item in proc_tree.get_children():
                proc_tree.delete(item)
            self._expanded_process = None
            self._thread_items = []
            # Inserir novos dados
            top_processes = data.get("top_processes", [])
            pid_to_item = {}
            if isinstance(top_processes, list):
                for proc in top_processes:
                    try:
                        memory_kb = proc.get("Memory", 0)
                        if isinstance(memory_kb, (int, float)) and memory_kb > 0:
                            memory_formatted = format_memory_size(memory_kb)
                        else:
                            memory_formatted = "0 KB"
                        item_id = proc_tree.insert(
                            "",
                            tk.END,
                            values=(
                                "▶",
                                str(proc.get("PID", "N/A")),
                                str(proc.get("User", "N/A"))[:15],
                                str(proc.get("Name", "N/A"))[:25],
                                str(proc.get("Status", "N/A")),
                                memory_formatted,
                                str(proc.get("Threads Count", "N/A")),
                            ),
                        )
                        pid_to_item[str(proc.get("PID", "N/A"))] = item_id
                    except Exception as e:
                        print(f"Erro ao inserir processo: {e}")
                        continue

            # --- Restaurar expansão se possível ---
            if expanded_pid and expanded_pid in pid_to_item:
                self._expand_threads_custom(pid_to_item[expanded_pid])

    def _update_memory_details(self):
        tree = self.trees.get("memory_details")
        if tree:
            for item in tree.get_children():
                tree.delete(item)

            mem_info = self.controller.system_info.get_memory_info()
            items = list(mem_info.items())[: self.MAX_MEMORY_ITEMS]

            for key, value in items:
                tree.insert("", tk.END, values=(key, format_memory_size(value)))

        # Atualizar detalhes extras se visíveis
        self._update_memory_details_if_visible()

    def _create_filesystem_tab(self, tab_frame: ttk.Frame):
        """Cria aba do sistema de arquivos simplificada"""
        container = tk.Frame(tab_frame, bg=self.BACKGROUND_COLOR)
        container.pack(fill="both", expand=True, padx=12, pady=12)

        columns = ("Partição", "Montagem", "Total", "Usado", "Livre", "% Usado")
        tree = self._create_treeview(container, columns, "filesystem")

        for idx, col in enumerate(columns):
            tree.column(col, width=100 if idx > 1 else 80, anchor="center")
            tree.heading(col, text=col)

        self._update_filesystem_tab()

    def _update_filesystem_tab(self):
        """Atualiza as informações do sistema de arquivos na aba"""
        from view.utils import format_memory_size
        tree = self.trees.get("filesystem")
        if not tree:
            return
        for item in tree.get_children():
            tree.delete(item)
        partition_usages = self.controller.system_info.get_disk_partition_usage()
        for usage in partition_usages:
            total_str = format_memory_size(usage["total_size"] // 1024)
            used_str = format_memory_size(usage["used_size"] // 1024)
            free_str = format_memory_size(usage["free_size"] // 1024)
            percent = f'{usage["percent_usage"]:.2f}%'
            tree.insert("", "end", values=(
                usage["partition"],
                usage["mount_path"],
                total_str,
                used_str,
                free_str,
                percent
            ))

    def _update_data(self):
        try:
            data = self.controller.get_data()
            self._update_global_metrics(data)
            self._update_process_list(data)
            self._update_memory_details()
            self._update_memory_chart(data)
            self._update_filesystem_tab()

        except Exception as e:
            print(f"Erro ao atualizar dados: {e}")
        finally:
            self.after(self.UPDATE_INTERVAL, self._update_data)

    def _start_updates(self):
        self._update_data()

    def _on_mousewheel_linux(self, event):
        direction = -1 if event.num == 4 else 1
        self.main_canvas.yview_scroll(direction, "units")
