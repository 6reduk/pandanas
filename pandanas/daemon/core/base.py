# -*- coding: utf-8 -*-
# system
import sys
import logging
import traceback
import os
import time
# 3rd party
from pep3143daemon import DaemonContext, DaemonError, PidFile
# my
from pandanas.daemon.core.mixins import DaemonStartupConfigureMixin, LoggerMixin, SignalHandleableMixin, \
    CliInteractionMixin
from pandanas.daemon.tools import stop_process
from pandanas.exceptions import ImproperlyConfigured


class DaemonBase(DaemonStartupConfigureMixin, LoggerMixin, SignalHandleableMixin, CliInteractionMixin):

    STATUS_EXIT_OK = 0
    STATUS_EXIT_ERROR = 1

    def __init__(self, app=None, pid_path=None, work_directory=None, uid=None, gid=None):
        super(DaemonBase, self).__init__()

        self.app = app
        self.pid_path = pid_path if pid_path else self.config['pidfile']
        self.pidfile = PidFile(pid_path) if pid_path else PidFile(self.config['pidfile'])
        self.work_directory = work_directory if work_directory else self.config['work_directory']
        self.stdout = sys.stdout if not self.config['detach_process'] else None
        self.stderr = sys.stderr if not self.config['detach_process'] else None
        self.detach_process = self.config['detach_process']
        self.uid = uid if uid else self.config['uid']
        self.gid = gid if gid else self.config['gid']

        self.daemon = DaemonContext(working_directory=self.work_directory,
                                    pidfile=self.pidfile,
                                    detach_process=self.detach_process,
                                    stdout=self.stdout,
                                    stderr=self.stderr,
                                    uid=self.uid,
                                    gid=self.gid,
                                    signal_map=self.get_signal_map())
        self.init_logger()

    def get_logger_name(self):
        return 'daemon.log'

    def get_log_level(self):
        return logging.DEBUG

    def get_logger_handlers(self):
        handlers = super(DaemonBase, self).get_logger_handlers()
        if not self.config['detach_process']:
            sh = logging.StreamHandler(self.stdout)
            sh.setLevel(self.get_log_level())
            sh.setFormatter(self.get_handler_formatter())
            handlers.append(sh)

        return handlers

    def get_argparser(self):
        parser = super(DaemonBase, self).get_argparser()
        parser.add_argument('action', choices=['start', 'stop', 'reload'], help='Action')
        return parser

    def parse_cli_options(self, args):
        options = super(DaemonBase, self).parse_cli_options(args)
        options['action'] = args.action
        return options

    def daemon_stop(self):
        self.log_info('Stopping daemon...')
        pid = None
        if os.path.exists(self.pid_path):
            with open(self.pid_path, 'r') as pidfile:
                pidfile.seek(0)
                pid = int(pidfile.readline())
                self.log_info('Attempt shutdown process #{pid}'.format(pid=pid))
                try:
                    stop_process(pid)
                except ProcessLookupError as e:
                    self.log_info('Can not shutdown process with pid {}. Pid file exists but process missing'.format(pid))
                    sys.exit(self.STATUS_EXIT_OK)

            attempts = 30
            while attempts:
                if not os.path.exists(self.pid_path):
                    sys.exit(self.STATUS_EXIT_OK)
                attempts -= 1
                time.sleep(1)

        if os.path.exists(self.pid_path):
            self.log_error('Can not shutdown daemon. Pid: {}'.format(pid))
        else:
            self.log_info('Daemon stopped.')
        sys.exit(self.STATUS_EXIT_OK)

    def daemon_start(self):
        """
        Dummy action for keep follow start daemon logic
        :return:
        """
        self.log_info('Start daemon')
        pass

    def daemon_reload(self):
        self.log_info('Action reload daemon not implemented')
        sys.exit(self.STATUS_EXIT_OK)

    def get_handlers(self):
        return {
            'start': self.daemon_start,
            'stop': self.daemon_stop,
            'reload': self.daemon_reload
        }

    def get_app(self):
        if self.app is None:
            raise ImproperlyConfigured('{cls}: Missing app property.'.format(cls=self.__class__))
        return self.app

    def handle_jobs(self):
        app = self.get_app()
        app()

    def _is_force_mode(self):
        return self.config.get('force', False)

    def _check_uid(self):
        if self.uid == 0 and not self._is_force_mode():
            return False
        return True

    def daemonize(self):
        # stop logging for parent process
        self.clear_logger_handlers()
        self.log_info('test')
        try:
            self.daemon.open()
            try:
                # reinit logger after fork
                self.init_logger()
            except Exception as e:
                sys.__stdout__.write(
                    'Can not reinitializate logger for destination {dest}. Error: {err}, backtrace: {traceback}'.format(
                        dest=self.get_logfile_name(), err=e, traceback=traceback.format_exc()
                    ))
                self.daemon.close()
                sys.exit(self.STATUS_EXIT_ERROR)
        except DaemonError as e:
            msg = "Error occurred during fork, error: {message}, stacktrace: {traceback}".format(
                message=e, traceback=traceback.format_exc()
            )
            print(msg)
            self.log_error(msg)
            sys.exit(self.STATUS_EXIT_ERROR)

    def terminate(self):
        self.log_info('Release resources...')
        self.daemon.close()
        self.log_info('Exit from process.')
        sys.exit(self.STATUS_EXIT_OK)

    def run(self):
        self.handle_action(self.config['action'])

        if not self._check_uid():
            msg = 'Detected attempt run process from root. For run daemon under root use -f or --force option.'
            print(msg)
            self.log_warn(msg)
            sys.exit(0)

        self.daemonize()
        self.log_info('Running...')
        self.log_info('Try handling jobs')

        try:
            self.handle_jobs()
        except Exception as e:
            self.log_error('Error occurred: {err}, traceback: {traceback}'.format(
                err=e, traceback=traceback.format_exc()
            ))
        finally:
            self.log_info('Shutdown master process: {pid}'.format(pid=os.getpid()))
            self.terminate()
