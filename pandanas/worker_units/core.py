import multiprocessing as mp

from pandanas.exceptions import ImproperlyConfigured


class UnitBase(mp.Process):

    def __init__(self, target=None, name=None, args=(), kwargs={}):
        super(UnitBase, self).__init__(name=name)
        self.target = target
        self.args = args
        self.kwargs = kwargs.copy()

    def processing(self):
        if self.target is None:
            raise ImproperlyConfigured('Can not run process cause target property is not configured.')
        self.target(*self.args, **self.kwargs)

    def run(self):
        self.processing()
        self.cleanup()

    def cleanup(self):
        pass
