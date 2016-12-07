# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


import json

import falcon


MESSAGE = 'something'


class _SimpleResource(object):
    def on_get(self, req, resp):
        resp.body = json.dumps({'message': MESSAGE})
        resp.set_header('Content-Type', 'application/json')

    def on_put(self, req, resp):
        global MESSAGE

        doc = json.load(req.stream)
        MESSAGE = doc['message']
        resp.body = json.dumps({'message': MESSAGE})


application = falcon.API()
application.add_route('/', _SimpleResource())
