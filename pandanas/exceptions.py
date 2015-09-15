# -*- coding: utf-8 -*-
class ImproperlyConfigured(Exception):
    """
    The ImproperlyConfigured exception is raised when application
    components is somehow improperly configured
    """

    def __init__(self, *args, **kwargs):
        super(ImproperlyConfigured, self).__init__(*args, **kwargs)


class DaemonException(Exception):
    """
    Base daemon exception
    """

    def __init__(self, *args, **kwargs):
        super(DaemonException, self).__init__(*args, **kwargs)


class JobProcessException(Exception):
    """
    Base exception for worker unit job processing
    """
    def __init__(self, *args, **kwargs):
        super(JobProcessException, self).__init__(*args, **kwargs)
