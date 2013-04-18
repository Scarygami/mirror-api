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

"""Configuration options and helper functions for all services"""

__author__ = 'scarygami@gmail.com (Gerwin Sturm)'

import jinja2
import json
import os
import webapp2

from google.appengine.api.app_identity import get_application_id
from google.appengine.ext import ndb
from oauth2client.appengine import CredentialsNDBProperty
from webapp2_extras import sessions
from webapp2_extras.appengine import sessions_memcache

JINJA = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

appname = get_application_id()
base_url = "https://" + appname + ".appspot.com"
discovery_url = base_url + "/_ah/api"

with open("client_secrets.json", "r") as fh:
    CLIENT_ID = json.load(fh)["web"]["client_id"]

config = {}
# TODO: load sesseion secret from a file
config["webapp2_extras.sessions"] = {
    "secret_key": "ajksdlj1029jlksndajsaskd7298hkajsbdkaukjassnkjankj",
}


def createError(code, message):
    return json.dumps({"error": {"code": code, "message": message}})


def createMessage(message):
    return json.dumps({"message": message})


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


class User(ndb.Model):
    verifyToken = ndb.StringProperty()
    credentials = CredentialsNDBProperty()
