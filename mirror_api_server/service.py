#!/usr/bin/python

# Copyright (C) 2013 Gerwin Sturm, FoldedSoft e.U.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import random
import string
import httplib2
import os
import webapp2
import json

from datetime import datetime
from apiclient.discovery import build
from apiclient.errors import HttpError
from google.appengine.api import memcache
from google.appengine.ext.webapp import template
from webapp2_extras import sessions
from webapp2_extras import sessions_memcache
from google.appengine.api.app_identity import get_application_id

appname = get_application_id()
# For local testing set base_url to http://localhost:8080
base_url = "https://" + appname + ".appspot.com"
discovery_url = base_url + "/_ah/api"

http = httplib2.Http(memcache)
userIp = os.environ["REMOTE_ADDR"]
service = build("mirror", "v1", discoveryServiceUrl=discovery_url + "/discovery/v1/apis/{api}/{apiVersion}/rest", http=http)

config = {}
config["webapp2_extras.sessions"] = {
    "secret_key": "ajksdlj1029jlksndajsaskd7298hkajsbdkaukjassnkjankj",
}

CLIENT_ID = json.loads(open("client_secrets.json", "r").read())["web"]["client_id"]


class BaseHandler(webapp2.RequestHandler):
    def dispatch(self):
        # Get a session store for this request.
        self.session_store = sessions.get_store(request=self.request)

        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
        return self.session_store.get_session(name='mirror_session', factory=sessions_memcache.MemcacheSessionFactory)


class IndexHandler(BaseHandler):
    def get(self):
        path = os.path.join(os.path.dirname(__file__), "templates/service.html")
        state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
        self.session["state"] = state
        self.response.out.write(template.render(path, {"client_id": CLIENT_ID, "state": state}))


class GlassHandler(BaseHandler):
    def get(self):
        path = os.path.join(os.path.dirname(__file__), "templates/glass.html")
        self.response.out.write(template.render(path, {"client_id": CLIENT_ID, "discovery_url": discovery_url}))


app = webapp2.WSGIApplication(
    [
        ('/', IndexHandler),
        ('/glass/', GlassHandler)
    ],
    debug=True, config=config)
