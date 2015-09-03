# pandanas

Micro framework for fast building daemon app writen over [pep3143daemon](https://github.com/schlitzered/pep3143daemon) in python.

# Author:
Shestakov Dmitriy [<6reduk@gmail.com>](mailto:6reduk@gmail.com)

# License:

MIT

# Installing:

pandanas can be installed via pip like this:

```
pip install pandanas
```

# Usage:

Concrete daemon realisation located at pandanas.daemon.generic module. All concrete daemon class implements interfaces 
that provides features for startup daemon and app configure, logging, handle process signals and run app logic.

## Attention:
All daemon child processes must set own signal handler for interact with parent or avoid signal propagation from parent
process.

## Simple example:
Build concrete multiprocess daemon. App logic make via multiprocessing.Process:

```python
import multiprocessing as mp
import logging

# app logic wrapped at decorator for inject to Process object
def app():

    def f():
        logger = configure_logging()
        # worker can be killed only by parent or SIGKILL|SIGSTOP
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        counter = 60
        while counter > 0:
            time.sleep(1)
            logger.info('Now: {}'.format(time.time()))
            counter -= 1

    return f

# fabric for create multiprocessing.Process instances
def unit(*args, **kwargs):
    return mp.Process(target=app(), **kwargs)

from pandanas.daemon.generic import MultiprocessDaemon

# define
class Worker(MultiprocessDaemon):
    
    # Here define worker that will doing all business logic
    worker_class = unit
    # Path to pid file
    default_pidfile = 'test.pid'

    def __init__(self, *args, **kwargs):
        super(Worker, self).__init__(*args, **kwargs)

if __name__ == '__main__':
    daemon = Worker()
    daemon.run()
```

For run daemon:

```bash
python daemon.py -d start
```

Stop daemon:
```bash
python daemon.py stop
```

## Predefined daemon options:
For get all predefined cli startup options:

```bash
python daemon.py -h
```

Most usable options:

* Run as daemon use -d option
* Set config path --config, if not set will be used 
pandanas.daemon.core.mixins.DaemonStartupConfigureMixin.default_config_path value

## Configure cli/config options:

Now all configure logic located at pandanas.pandanas.daemon.core.mixins.DaemonStartupConfigureMixin class 
For change configurable behavior need override class attributes or appropriate class method 

Attributes:
* default_work_directory - set work directory for daemon after fork. Try code logic with relative paths that lets do
chrooting
* default_pidfile - set path for daemon pidfile
* default_config_path - set path for config file
* default_log_file - set path for daemon config file. Keep attention - this file uses only for internal daemon events,
for logging app logic use separate logger.

For getting config options uses two steps workflow - get cli options, get config options and merge them together.
Cli options have higher priority.

### Add your own cli options:
For getting cli options uses [argparse](https://docs.python.org/3/library/argparse.html) module.

DaemonStartupConfigureMixin.get_argparser() return ArgumentParser object. You can add your own options to parser, see
[argparse](https://docs.python.org/3/library/argparse.html) module documentation.

Example:

```python
class Worker(MultiprocessDaemon):
    def get_argparser(self):
        argparser = super(Worker, self).get_argparser()
        argparser.add_argument('-o', '--some-option', dest='my', help='My own argument')
        return argparser
```

For fix option collision use conflict_handler argument at ArgumentParser.add_argument() method

After configure argument parser we will processing daemon startup arguments and got Namespace object.

DaemonStartupConfigureMixin.parse_cli_options() return cli config dict.
Next step we extract values from Namespace and put to result config dict.
Before we can add our own options we must populate config dict by parent.

Example:
```python
class Worker(MultiprocessDaemon):
    def parse_cli_options(self, args):
        options = super(Worker, self).parse_cli_options(args)
        # Here custom logic for define cli result config
        options['my'] = args.my 
        return options
```

### Add your own config options:

Config use windows like ini files notation.
For parse ini files taken [configparser](https://docs.python.org/3/library/configparser.html).
Definition user config options seems as setting options for cli.
First step is setting options at ini file in your own called section.
Second step, read and parse file. This step no need any action cause configparser parse all section by default.
Third step, your need override DaemonStartupConfigureMixin.parse_config_options() for adding needed values

Example:

```python
class Worker(MultiprocessDaemon):
    def parse_config_options(self, conf_parser):
        options = super(Worker, self).parse_config_options(conf_parser)
        if not conf_parser.has_section('my_own_section'):
            return options
        
        if conf_parser.has_option('my_own_section', 'some_options'):
            options['some_option'] = conf_parser.get('my_own_section', 'some_option')
```
