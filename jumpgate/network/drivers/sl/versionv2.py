class VersionV2(object):
    def __init__(self, app):
        self.app = app

    def on_get(self, req, resp):
        resources = [{
            "links": [
                {
                    "rel": "self",
                    "href":
                        self.app.get_endpoint_url('network', req,
                                                  'v2_subnets')

                }
            ],
            "name": "subnet",
            "collection": "subnets"
        }, {
            "links": [
                {
                    "rel": "self",
                    "href":
                        self.app.get_endpoint_url('network', req,
                                                  'v2_networks')

                }
            ],
            "name": "network",
            "collection": "networks"
        }]

        resp.body = {'resources': resources}
