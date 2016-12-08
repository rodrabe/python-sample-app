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

import fixtures
import testtools
import webtest

import sample_app


class TestCase(testtools.TestCase):
    def setUp(self):
        super(TestCase, self).setUp()
        fake_config_opts = self.useFixture(fixtures.MockPatchObject(
            sample_app.cfg, 'ConfigOpts')).mock
        fake_config_opts().message = 'something'

    def test_get(self):
        app = webtest.TestApp(sample_app.make_application())
        resp = app.get('/')
        self.assertEqual(200, resp.status_int)
        self.assertEqual('application/json', resp.content_type)
        self.assertEqual({'message': 'something'}, resp.json)

    def test_put(self):
        app = webtest.TestApp(sample_app.make_application())
        resp = app.put_json('/', {'message': 'a new thing'})
        self.assertEqual(200, resp.status_int)
        self.assertEqual('application/json', resp.content_type)
        self.assertEqual({'message': 'a new thing'}, resp.json)

    def test_put_get(self):
        app = webtest.TestApp(sample_app.make_application())
        resp = app.put_json('/', {'message': 'a new thing'})
        self.assertEqual(200, resp.status_int)
        self.assertEqual('application/json', resp.content_type)
        self.assertEqual({'message': 'a new thing'}, resp.json)

        resp = app.get('/')
        self.assertEqual(200, resp.status_int)
        self.assertEqual('application/json', resp.content_type)
        self.assertEqual({'message': 'a new thing'}, resp.json)
