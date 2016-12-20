from jumpgate.common import config
import os



import logging
LOG = logging.getLogger(__name__)
LOG.info("PATH CONFIG %s "% os.path.isfile("jumpgate.conf"))

config.configure('jumpgate.conf')
