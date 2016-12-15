

class ExtensionsV2(object):
    def on_get(self, req, resp):
        # client = req.sl_client
        resp.body = {'extensions': []}
