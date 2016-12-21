import importlib
import logging
import os

from jumpgate.common import config

LOG = logging.getLogger(__name__)


class APIHooks(object):
    # singleton pattern: http://goo.gl/1MtF3B

    class __APIHooks(object):

        def __init__(self):
            self.reset()

        def reset(self):
            self._req_hooks = {'optional': [], 'required': []}
            self._res_hooks = {'optional': [], 'required': []}
            self._loaded = False

        def load_hooks(self):
            LOG.info("GOT HERE %s "% config.PARSER.defaults().__len__())

            if not self._loaded:
                for hook in (['core'] +
                             config.PARSER.get('DEFAULT','request_hooks').split(',') +
                             config.PARSER.get('DEFAULT','response_hooks').split(',')):
                    LOG.info("Importing hook module '%s'" % (hook))
                    self._load_module(hook)
            self._loaded = True

        def _load_module(self, module):
            #try:
            importlib.import_module(os.path.join(os.path.dirname(__file__), module))
            #except ImportError:
             #   raise ImportError("Failed to import hook module '%s'. "
             #                     "Verify it exists in PYTHONPATH" % (module))

        def add_request_hook(self, hook, optional=True):
            LOG.debug("Adding request hook '%s'" % (str(hook)))
            cache = (self._req_hooks['optional'] if optional
                     else self._req_hooks['required'])
            cache.append(hook)
            return hook

        def add_response_hook(self, hook, optional=True):
            LOG.debug("Adding response hook '%s'" % (str(hook)))
            cache = (self._res_hooks['optional'] if optional
                     else self._res_hooks['required'])
            cache.append(hook)
            return hook

        def required_request_hooks(self):
            self.load_hooks()
            return list(self._req_hooks['required'])

        def optional_request_hooks(self):
            self.load_hooks()
            return list(self._req_hooks['optional'])

        def required_response_hooks(self):
            self.load_hooks()
            return list(self._res_hooks['required'])

        def optional_response_hooks(self):
            self.load_hooks()
            return list(self._res_hooks['optional'])

    instance = None

    def __new__(cls):
        if not APIHooks.instance:
            APIHooks.instance = APIHooks.__APIHooks()
        return APIHooks.instance

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def __setattr__(self, name):
        return setattr(self.instance, name)


def request_hook(optional=True):
    """Decorator for request hook functions.

    Request hook functions should take 3 arguments:
    req - The incoming request object.
    resp - The response object.
    kwargs - Request arg params.
    """
    def _hook(hook):
        return APIHooks().add_request_hook(hook, optional)
    return _hook


def response_hook(optional=True):
    """Decorator for response hook functions.

    Response hook functions should take 2 arguments:
    req - The incoming request object.
    resp - The response object.
    """
    def _hook(hook):
        return APIHooks().add_response_hook(hook, optional)
    return _hook
