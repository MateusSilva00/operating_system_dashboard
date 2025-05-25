from controller.monitor_controller import MonitorController
from view.dashboard import Dashboard


def main():
    controller = MonitorController(refresh_interval=1)
    controller.start()

    app = Dashboard(controller)
    app.mainloop()

    controller.stop()
    
if __name__ == "__main__":
    main()