import signal
import sys

from controller.monitor_controller import MonitorController
from view.dashboard import Dashboard


def main():
    """Função principal da aplicação"""
    controller = None
    dashboard = None

    try:
        # Criar e iniciar o controller
        controller = MonitorController(refresh_interval=1)
        controller.start()

        # Criar e executar o dashboard
        dashboard = Dashboard(controller)

        dashboard.mainloop()

    except KeyboardInterrupt:
        print("\nCtrl+C detectado. Finalizando...")
    finally:
        # Limpeza final
        if controller:
            controller.stop()

        if dashboard:
            try:
                dashboard.destroy()
            except:
                pass
        sys.exit(0)


if __name__ == "__main__":
    main()
