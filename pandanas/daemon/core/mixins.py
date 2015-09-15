# -*- coding: utf-8 -*-
# system
import time
import argparse
import configparser
import os

# my
from pandanas.exceptions import ImproperlyConfigured, DaemonException


class DaemonStartupConfigureMixin(object):

    default_work_directory = './'
    default_pidfile = 'daemon.pid'
    default_config_path = 'config.ini'
    default_log_file = 'daemon.log'
    config_file_path = None

    def __init__(self):
        super(DaemonStartupConfigureMixin, self).__init__()

        cli_options = self.get_cli_options()

        self.config_file = cli_options['config_path']
        del(cli_options['config_path'])
        file_options = self.get_file_options(self.config_file)

        self._config = self.combine_config_options(cli_options, file_options)

    @property
    def config_file(self):
        if self.config_file_path is None:
            raise ImproperlyConfigured('Config file options not configured')
        return self.config_file_path

    @config_file.setter
    def config_file(self, value):
        self.config_file_path = value

    @property
    def config(self):
        if not self._config:
            raise ImproperlyConfigured('{}: config property not configure.'.format(self.__class__))
        return self._config

    @config.setter
    def config(self, value):
        self._config = value

    def get_cli_options(self):
        """
        Parse startup options and prepare dict with processed values

        :return: dict
        """
        argparser = self.get_argparser()
        args = argparser.parse_args()
        return self.parse_cli_options(args)

    def get_configparser(self, config_file):
        try:
            conf_parser = configparser.ConfigParser()
            conf_parser.read(config_file)
        except Exception as e:
            raise DaemonException('Can not read or parse config file: {err}'.format(e))

        return conf_parser

    def parse_config_options(self, conf_parser):
        options = dict()
        if not conf_parser.has_section('daemon'):
            return options

        if conf_parser.has_option('daemon', 'work_directory'):
            options['work_directory'] = conf_parser.get('daemon', 'work_directory')
        if conf_parser.has_option('daemon', 'pidfile'):
            options['pidfile'] = conf_parser.get('daemon', 'pidfile')
        if conf_parser.has_option('daemon', 'uid'):
            options['uid'] = conf_parser.get('daemon', 'uid')
        if conf_parser.has_option('daemon', 'gid'):
            options['gid'] = conf_parser.get('daemon', 'gid')
        if conf_parser.has_option('daemon', 'log_level'):
            options['log_level'] = conf_parser.get('daemon', 'log_level')
        if conf_parser.has_option('daemon', 'debug'):
            options['debug'] = conf_parser.get('daemon', 'debug')
        return options

    def get_file_options(self, config_file):
        conf_parser = self.get_configparser(config_file)
        options = self.parse_config_options(conf_parser)
        return options

    @staticmethod
    def combine_config_options(cli_options, file_options):
        result = file_options.copy()
        result.update(cli_options)
        return result

    def get_argparser(self):
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
                            help='Working directory for worker processes. [Default: {}]'.format(self.default_work_directory))
        parser.add_argument('--pidfile', type=str, help='Path for pid file. [Default: {}]'.format(self.default_pidfile))
        parser.add_argument('--uid', type=int, help='User id for running processes after fork')
        parser.add_argument('--gid', type=int, help='Group id for running processes after fork')
        parser.add_argument('--config', type=str, dest='config_path',
                            help='Path to config file. [Default: {}]'.format(self.default_config_path))
        parser.add_argument('--no-config', action='store_true', dest='no_config', default=False,
                            help='Do not use config file')
        parser.add_argument('--logfile', type=str, default=self.default_log_file,
                            help='Logging file. [Default: {}]'.format(self.default_log_file))
        parser.add_argument('--log-level', type=str, default='info', dest='log_level',
                            choices=['debug', 'info', 'warn', 'error', 'critical'],
                            help='Logging level. [Default: info]')
        parser.add_argument('-f', '--force', action='store_true', dest='force', help='Force mode for run under root')
        parser.add_argument('--debug', action='store_true', dest='debug', default=False, help='Use debug mode')
        return parser

    def parse_cli_options(self, args):
        """
        Parsing startup options for define core daemon behavior and worker processes.
        For parsing additional params need override this method with calling parent and adding your own params to
        result dict.

        :param argparser: Fulfil instance of ArgumentParser
        :return: dict
        """
        options = dict()

        options['work_directory'] = args.work_directory if args.work_directory else self.default_work_directory
        options['pidfile'] = args.pidfile if args.pidfile else self.default_pidfile
        options['uid'] = args.uid if args.uid else os.getuid()
        options['gid'] = args.gid if args.gid else os.getgid()
        options['config_path'] = args.config_path if args.config_path else self.default_config_path
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
        worker = worker_base(config=self.config, name=self.get_worker_name())
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


