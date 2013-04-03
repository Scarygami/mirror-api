# Copyright 2013 Gerwin Sturm, FoldedSoft e.U. / www.foldedsoft.at
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import httplib2
import os
import webapp2
import json
import difflib

from datetime import datetime
from apiclient.discovery import build
from apiclient.errors import HttpError
from google.appengine.api import memcache
from google.appengine.ext.webapp import template
from webapp2_extras import sessions
from webapp2_extras import sessions_memcache

http = httplib2.Http(memcache)
userIp = os.environ["REMOTE_ADDR"]
service = build("mirror", "v1", discoveryServiceUrl="https://mirror-api.appspot.com/_ah/api/discovery/v1/apis/{api}/{apiVersion}/rest", http=http)

config = {}
config["webapp2_extras.sessions"] = {
    "secret_key": "ajksdlj1029jlksndajsaskd7298hkajsbdkaukjassnkjankj",
}


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


class WelcomeHandler(BaseHandler):
    def get(self):
        path = os.path.join(os.path.dirname(__file__), 'templates/welcome.html')
        self.response.out.write(template.render(path, {}))


app = webapp2.WSGIApplication(
    [
        ('/', WelcomeHandler)
    ],
    debug=True, config=config)
