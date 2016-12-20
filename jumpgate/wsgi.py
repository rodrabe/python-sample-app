import logging
import os
import os.path


from jumpgate import api
from jumpgate import config as jumpgate_config

import ConfigParser
import json

PROJECT = 'jumpgate'




def make_api(config_path=None):






    logger = logging.getLogger(PROJECT)
    logger.setLevel('INFO')
    logger.addHandler(logging.StreamHandler())
    logger.info("PATH CONFIG  AAA%s "% os.getcwd())
    virtenv = os.environ['OPENSHIFT_PYTHON_DIR'] + '/virtenv/'
    virtualenv = os.path.join(virtenv, 'jumpgate.conf')

    logger.info("PATH CONFIG AAAA %s "% virtualenv)

    logger.info("PATH CONFIG %s "% os.path.isfile(virtualenv))
    app = api.Jumpgate()
    app.load_endpoints()
    app.load_drivers()

    return app.make_api()
