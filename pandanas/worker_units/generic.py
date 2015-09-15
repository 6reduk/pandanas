import traceback
import os
import sys
from pandanas.core.mixins import LoggerMixin, SignalHandleMixin, QueueJobHandleMixin
from pandanas.worker_units.core import UnitBase


class WorkerUnit(UnitBase, LoggerMixin, SignalHandleMixin, QueueJobHandleMixin):

    def __init__(self, config, *args, **kwargs):
        super(WorkerUnit, self).__init__(*args, **kwargs)
        self.config = config

    def get_logger_name(self):
        return '{worker_name}_{pid}'.format(worker_name=self.name, pid=os.getpid())

    def get_logfile_name(self):
        return 'downloader.log'

    def handle_terminate(self, signal_number, stack_frame):
        self.cleanup()
        sys.exit()

    def get_signal_name_map(self):
        name_map = super(WorkerUnit, self).get_signal_name_map()
        name_map['SIGINT'] = self.handle_terminate
        return name_map

    # Форкнуться
    # получить логгер
    # Установить кастомные хенлдеры для сигналов
    # выполнить работу:
    ## вычитать таску
    ## обработать
    ## отписаться
    def run(self):
        self.init_logger()
        self.log_debug('Logger configure: complete.')
        self.log_debug('Set signal handlers: ...')
        self.set_signal_handlers()
        self.log_debug('Set signal handlers: complete')
        self.log_debug('Connect to income and outcome queues: ...')
        self.connect_to_queues()
        self.log_debug('Connect to income and outcome queues: complete')
        self.log_info('Begin processing jobs...')
        try:
            self.processing()
        except Exception as e:
            self.log_error('Error occurred during job processing: {err}, traceback: {trace}'.format(
                err=e,
                trace=traceback.format_exc(10)))
        finally:
            self.log_info('Terminate process')
            return

    # TODO code logic
    def processing(self):
        pass
