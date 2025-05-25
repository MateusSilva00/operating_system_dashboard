import asyncio

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.reactive import reactive
from textual.widgets import DataTable, Footer, Header, Static

from model.process_info import (count_processes_and_threads, get_process_info,
                                get_top_processes_by_memory)
from model.system_info import get_cpu_usage, get_memory_info
from view.utils import kb_to_gb


class DashboardApp(App):
    CSS_PATH = None  # Se quiser usar CSS depois
    BINDINGS = [("q", "quit", "Sair")]

    cpu_usage = reactive(0.0)
    total_mem = reactive(0.0)
    free_mem = reactive(0.0)
    avail_mem = reactive(0.0)
    total_proc = reactive(0)
    total_threads = reactive(0)
    top_procs = reactive([])

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield Container(
            Static("CPU / Memória", id="sysinfo"),
            DataTable(id="proctable"),
        )

    async def on_mount(self):
        self.query_one("DataTable").add_columns("PID", "Nome", "Memória (MB)")

        async def update_loop():
            while True:
                cpu = get_cpu_usage()
                mem = get_memory_info()
                plist = get_process_info()
                processes_threads = count_processes_and_threads(plist)
                self.total_proc = processes_threads["total_processes"]
                self.total_threads = processes_threads["total_threads"]
                self.cpu_usage = cpu["usage"]
                self.total_mem = kb_to_gb(mem["MemTotal"])
                self.free_mem = kb_to_gb(mem["MemFree"])
                self.avail_mem = kb_to_gb(mem["MemAvailable"])
                self.top_procs = get_top_processes_by_memory(plist)

                self.refresh_dashboard()
                await asyncio.sleep(1)

        self.run_worker(update_loop, exclusive=True)

    def refresh_dashboard(self):
        sysinfo = self.query_one("#sysinfo", Static)
        sysinfo.update(
            f"CPU Uso: {self.cpu_usage:.2f}%\n"
            f"RAM Total: {self.total_mem:.2f} GB\n"
            f"RAM Livre: {self.free_mem:.2f} GB\n"
            f"RAM Disponível: {self.avail_mem:.2f} GB\n"
            f"Processos: {self.total_proc} | Threads: {self.total_threads}"
        )

        table = self.query_one("DataTable")
        table.clear()
        for proc in self.top_procs:
            table.add_row(
                str(proc["pid"]), proc["name"], f"{round(proc['memory_kb'] / 1024, 2)}"
            )
