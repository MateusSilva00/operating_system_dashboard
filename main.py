from controller.monitor_controller import MonitorController


def main():
    try:
        controller = MonitorController(refresh_interval=1)
        controller.start()
    except KeyboardInterrupt:
        print("Exiting dashboard...")
        controller.stop()


if __name__ == "__main__":
    main()
