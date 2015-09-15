import logging
import signal
from pandanas.exceptions import ImproperlyConfigured


class LoggerMixin(object):

    logfile_name = 'output.log'
    log_level = logging.DEBUG
    logger_name = None

    def get_logger_name(self):
        if not self.logger_name:
            raise ImproperlyConfigured('{}: logger_name not configured.'.format(cls=self.__class__))
        return self.logger_name

    def get_logfile_name(self):
        return self.logfile_name

    def get_log_level(self):
        return self.log_level

    @staticmethod
    def get_handler_formatter():
        return logging.Formatter('[%(asctime)s]:[%(name)s]:[#%(process)s]:[%(levelname)s]:[%(processName)s] - %(message)s')

    def get_logger_handlers(self):
        handlers = []

        fh = logging.FileHandler(self.get_logfile_name())
        fh.setLevel(self.get_log_level())
        fh.setFormatter(self.get_handler_formatter())

        handlers.append(fh)

        return handlers

    def init_logger(self):
        logger = logging.getLogger(self.get_logger_name())
        logger.setLevel(self.get_log_level())

        for handler in self.get_logger_handlers():
            logger.addHandler(handler)

        self.logger = logger

    def clear_logger_handlers(self):
        for handler in self.logger.handlers:
            handler.close()

        self.logger.handlers = []

    @property
    def logger(self):
        if not hasattr(self, '_logger'):
            raise ImproperlyConfigured('{cls}: Logger not configured'.format(cls=self.__class__))
        return self._logger

    @logger.setter
    def logger(self, value):
        self._logger = value

    def log_debug(self, message, *args, **kwargs):
        self.logger.debug(message, *args, **kwargs)

    def log_info(self, message, *args, **kwargs):
        self.logger.info(message, *args, **kwargs)

    def log_warn(self, message, *args, **kwargs):
        self.logger.warn(message, *args, **kwargs)

    def log_error(self, message, *args, **kwargs):
        self.logger.error(message, *args, **kwargs)

    def log_critical(self, message, *args, **kwargs):
        self.logger.critical(message, *args, **kwargs)


class SignalHandleMixin(object):

    def get_signal_name_map(self):
        name_map = {
            'SIGHUP': self.handle_reload,
            'SIGTERM': self.handle_terminate,
            'SIGCHLD': self.handle_child
        }
        return name_map

    def get_signal_map(self):
        signal_map = {}
        for name, target in self.get_signal_name_map().items():
            if hasattr(signal, name):
                signal_map[getattr(signal, name)] = target
        return signal_map

    def set_signal_handlers(self):
        for (signal_number, handler) in self.get_signal_map().items():
            signal.signal(signal_number, handler)

    def handle_terminate(self, signal_number, stack_frame):
        raise NotImplemented('This method must be implemented for usage.')

    def handle_reload(self, signal_number, stack_frame):
        raise NotImplemented('This method must be implemented for usage.')

    def handle_child(self, signal_number, stack_frame):
        pass


class QueueJobHandleMixin(object):
    def __init__(self):
        super(QueueJobHandleMixin, self).__init__()

    # TODO code logic
    def connect_to_income_queue(self):
        pass

    # TODO code logic
    def connect_to_outcome_queue(self):
        pass

    # TODO code logic
    def connect_to_queues(self):
        self.connect_to_income_queue()
        self.connect_to_outcome_queue()

    # TODO code logic
    def get_job(self):
        pass

    # TODO code logic
    def put_job_result(self, message):
        pass

    # TODO code logic
    def close_income_queue(self):
        pass

    # TODO code logic
    def close_outcoume_queue(self):
        pass

    # TODO code logic
    def close_queues(self):
        pass
