import threading
import time
import sched
from threading import Timer

class CallbackTimer(Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)

# def start_timer(callback: function):
#     s = sched.scheduler.enterabs