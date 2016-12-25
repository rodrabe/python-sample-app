from jumpgate.common import config
import os


PROJECT = 'jumpgate'
import logging
logger = logging.getLogger(PROJECT)
logger.setLevel('INFO')
logger.addHandler(logging.StreamHandler())
logger.info("PATH CONFIG  AAA%s "% os.getcwd())
virtualenv = os.path.join(os.path.dirname(__file__), 'jumpgate.conf')

logger.info("PATH CONFIG AAAA %s "% virtualenv)

logger.info("PATH CONFIG %s "% os.path.isfile(virtualenv))
config.PARSER.read(virtualenv)
a = config.PARSER.options('softlayer')
logger.info("Options %s"% a)
