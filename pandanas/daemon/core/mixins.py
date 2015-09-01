# -*- coding: utf-8 -*-
# system
import argparse
import os
import time
import logging
import signal
# my
from pandanas.exceptions import ImproperlyConfigured, DaemonException


# TODO code logic
class DaemonStartupConfigureMixin(object):

    DEFAULT_WORK_DIRECTORY = './'
    DEFAULT_PIDFILE = 'daemon.pid'
    DEFAULT_CONFIG_PATH = 'config.ini'
    DEFAULT_LOG_FILE = 'daemon.log'

    def __init__(self):
        super(DaemonStartupConfigureMixin, self).__init__()
        cli_options = self._get_cli_options()

        file_options = dict()
        if not cli_options['no_config']:
            self.config_path = cli_options['config_path']
            file_options = self._get_file_options(self.config_path)
        else:
            self.config_path = None

        del(cli_options['config_path'])

        self._config = self._combine_config_options(cli_options, file_options)

    @property
    def config(self):
        if not self._config:
            raise ImproperlyConfigured('{}: config property not configure.'.format(self.__class__))
        return self._config

    @config.setter
    def config(self, value):
        self._config = value

    def _get_cli_options(self):
        """
        Parse startup options and prepare dict with processed values

        :return: dict
        """
        argparser = self._get_argparser()
        args = argparser.parse_args()
        return self._parse_cli_options(args)

    #TODO code logic, add doc comment
    def _get_file_options(self, file_path):
        return dict()

    @staticmethod
    def _combine_config_options(cli_options, file_options):
        result = file_options.copy()
        result.update(cli_options)
        return result

    def _get_argparser(self):
        """
        Parse startup options and return ArgumentParser object.
        For define your own options simple override this method with calling parent method and build new
        ArgumentParser with parent object,
        like this: parser  = argparse.ArgumentParser(super(Daemon, self)._get_argparser)
        :return: ArgumentParser
        """
        parser = argparse.ArgumentParser(description='Worker daemon.')
        parser.add_argument('-d', action='store_true', default=False, dest='detach_process',
                            help='Detach and daemonize process')
        parser.add_argument('--work_directory', type=str,
                            help='Working directory for worker processes. [Default: {}]'.format(self.DEFAULT_WORK_DIRECTORY))
        parser.add_argument('--pidfile', type=str, help='Path for pid file. [Default: {}]'.format(self.DEFAULT_PIDFILE))
        parser.add_argument('--uid', type=int, help='User id for running processes after fork')
        parser.add_argument('--gid', type=int, help='Group id for running processes after fork')
        parser.add_argument('--config', type=str, dest='config_path',
                            help='Path to config file. [Default: {}]'.format(self.DEFAULT_CONFIG_PATH))
        parser.add_argument('--no-config', action='store_true', dest='no_config', default=False,
                            help='Do not use config file')
        parser.add_argument('--logfile', type=str, default=self.DEFAULT_LOG_FILE,
                            help='Logging file. [Default: {}]'.format(self.DEFAULT_LOG_FILE))
        parser.add_argument('--log-level', type=str, default='info', dest='log_level',
                            choices=['debug', 'info', 'warn', 'error', 'critical'],
                            help='Logging level. [Default: info]')
        parser.add_argument('-f', '--force', action='store_true', dest='force', help='Force mode for run under root')
        parser.add_argument('--debug', action='store_true', dest='debug', default=False, help='Use debug mode')
        return parser

    def _parse_cli_options(self, args):
        """
        Parsing startup options for define core daemon behavior and worker processes.
        For parsing additional params need override this method with calling parent and adding your own params to
        result dict.

        :param argparser: Fulfil instance of ArgumentParser
        :return: dict
        """
        options = dict()

        options['work_directory'] = args.work_directory if args.work_directory else self.DEFAULT_WORK_DIRECTORY
        options['pidfile'] = args.pidfile if args.pidfile else self.DEFAULT_PIDFILE
        options['uid'] = args.uid if args.uid else os.getuid()
        options['gid'] = args.gid if args.gid else os.getgid()
        options['config_path'] = args.config_path if args.config_path else self.DEFAULT_CONFIG_PATH
        options['detach_process'] = args.detach_process
        options['no_config'] = args.no_config
        options['log_level'] = args.log_level.upper()
        options['force'] = args.force
        options['debug'] = args.debug
        return options


class CliInteractionMixin(object):

    action_handlers = None

    def get_handlers(self):
        if not self.action_handlers:
            raise ImproperlyConfigured('{cls}: property action_handlers or get method not configured.'.format(
                cls=self.__class__))
        return self.action_handlers

    def handle_action(self, action):
        handler = self.get_handlers().get(action, None)
        if handler is None:
            raise DaemonException('{cls}: missing handler for action {action}'.format(self.__class__, action))

        handler()


class WorkerUnitManagerMixin(object):

    worker_num = 2
    worker_name_prefix = 'worker_unit'
    worker_spawn_count = 0
    worker_class = None
    worker_pool = []

    def get_worker_name_prefix(self):
        if self.worker_name_prefix:
            return self.worker_name_prefix

    def increment_worker_count(self):
        self.worker_spawn_count += 1
        return self.worker_spawn_count

    def get_worker_name(self):
        return '{prefix}_{id}'.format(prefix=self.get_worker_name_prefix(), id=self.increment_worker_count())

    def get_worker_base(self):
        if self.worker_class is None:
            raise ImproperlyConfigured('{cls}: Missing worker_class property'.format(cls=self.__class__))
        return self.worker_class

    def spawn_worker(self):
        worker_base = self.get_worker_base()
        worker = worker_base(name=self.get_worker_name())
        return worker

    def all_worker_alive(self):
        if not len(self.worker_pool):
            return False
        return all(map(lambda x: x.is_alive(), self.worker_pool))

    def clean_dead_workers(self):
        self.worker_pool = [w for w in self.worker_pool if w.is_alive()]

    def stop_workers(self):
        for worker in self.worker_pool:
            worker.terminate()

    def respawn_workers(self):
        while len(self.worker_pool) < self.worker_num:
            worker = self.spawn_worker()
            self.worker_pool.append(worker)
            worker.start()

    def handle_jobs(self):
        while True:
            if not self.all_worker_alive():
                self.clean_dead_workers()
                self.respawn_workers()
            time.sleep(2)


class LoggerMixin(object):

    logfile_name = 'daemon.log'
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


class SignalHandleableMixin(object):

    def get_signal_map(self):
        name_map = {
            'SIGHUP': self.handle_reload,
            'SIGTERM': self.handle_terminate,
            'SIGCHLD': self.handle_child
        }

        signal_map = {}
        for name, target in name_map.items():
            if hasattr(signal, name):
                signal_map[getattr(signal, name)] = target
        return signal_map

    def handle_terminate(self, signal_number, stack_frame):
        raise NotImplemented('This method must be implemented for usage.')

    def handle_reload(self, signal_number, stack_frame):
        raise NotImplemented('This method must be implemented for usage.')

    def handle_child(self, signal_number, stack_frame):
        pass
