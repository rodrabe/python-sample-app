class VersionV2(object):
    def __init__(self, app):
        self.app = app

    def on_get(self, req, resp, tenant_id=None):
        version = {
            "id": "v2.0",
            "links": [
                {
                    "rel": "self",
                    "href":
                        self.app.get_endpoint_url('compute', req, 'v2_detail')

                }
            ],
            "updated": "2011-01-21T11:33:21Z",
            "status": "CURRENT",
            "version": "",
            "min_version": ""
        }

        resp.body = {'version': version}
