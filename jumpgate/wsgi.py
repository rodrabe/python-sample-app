import logging
import os
import os.path
from jumpgate.common import config



from jumpgate import api







def make_api(config_path=None):

    app = api.Jumpgate()
    app.load_endpoints()
    app.load_drivers()

    return app.make_api()
