import logging
import os
import os.path


from jumpgate import api
from jumpgate import config as jumpgate_config

import ConfigParser
import json

PROJECT = 'jumpgate'




def make_api(config_path=None):
    # Find configuration files
    conf = ConfigParser.RawConfigParser()
    config_files = conf.read()

    # Check for environmental variable config file
    env_config_loc = os.environ.get('JUMPGATE_CONFIG')
    if env_config_loc and os.path.exists(env_config_loc):
        config_files.insert(0, env_config_loc)




    logger = logging.getLogger(PROJECT)
    logger.setLevel('INFO')
    logger.addHandler(logging.StreamHandler())
    app = api.Jumpgate()
    app.load_endpoints()
    app.load_drivers()

    return app.make_api()
