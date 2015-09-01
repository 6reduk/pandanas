# -*- coding: utf-8 -*-
# system
import traceback
import os
# my
from pandanas.daemon.core import DaemonBase
from pandanas.daemon.core.mixins import WorkerUnitManagerMixin


class SingleProcessDaemon(DaemonBase):
    def __init__(self):
        super(SingleProcessDaemon, self).__init__()


class MultiprocessDaemon(WorkerUnitManagerMixin, DaemonBase):

    def __init__(self, *args, **kwargs):
        super(MultiprocessDaemon, self).__init__(*args, **kwargs)

    def handle_terminate(self, signal_number, stack_frame):
        self.log_info('Got SIGTERM signal. Try graceful terminate child processes')
        stoped_worker = []
        for worker in [w for w in self.worker_pool if w.is_alive()]:
            try:
                self.log_debug('worker: {}'.format(worker))
                worker.terminate()
                stoped_worker.append(worker)
            except Exception as e:
                self.log_error("{cls}: Can't terminate worker[{pid}]! Error: {err}, traceback: {traceback}.".format(
                    cls=self.__class__, pid=worker.pid, err=e, traceback=traceback.format_exc()
                ))
        for worker in stoped_worker:
            worker.join()
        self.terminate()

    def handle_reload(self, signal_number, stack_frame):
        self.log_debug('Got signal: {signal_number}. Reload daemon not implemented.'.format(signal_number=signal_number))

    def handle_child(self, signal_number, stack_frame):
        self.log_debug('Got signal: {signal_number}. Process child errors not implemented.'.format(signal_number=signal_number))