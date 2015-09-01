import signal
import os


# TODO code logic
def stop_process(pid):
    os.kill(pid, signal.SIGTERM)
