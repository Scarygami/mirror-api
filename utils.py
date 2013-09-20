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

from apiclient.discovery import build
from google.appengine.api.app_identity import get_application_id
from google.appengine.ext import ndb
from oauth2client.appengine import CredentialsNDBProperty
from webapp2_extras import sessions
from webapp2_extras.appengine import sessions_memcache

JINJA = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

appname = get_application_id()
base_url = "https://" + appname + ".appspot.com"
discovery_url = base_url + "/_ah/api"
discovery_service_url = discovery_url + "/discovery/v1/apis/{api}/{apiVersion}/rest"

with open("client_secrets.json", "r") as fh:
    secrets = json.load(fh)["web"]
    CLIENT_ID = secrets["client_id"]
    SESSION_KEY = str(secrets["session_secret"])
    API_KEY = secrets["api_key"]

config = {}
config["webapp2_extras.sessions"] = {"secret_key": SESSION_KEY}

# Add any additional scopes that you might need for your service to access other Google APIs
COMMON_SCOPES = ["https://www.googleapis.com/auth/plus.login"]

# userinfo.email scope is required to work with Google Cloud Endpoints
TEST_SCOPES = ["https://www.googleapis.com/auth/userinfo.email"]

# Remove the location scope from here if you don't need it
REAL_SCOPES = [
    "https://www.googleapis.com/auth/glass.timeline",
    "https://www.googleapis.com/auth/glass.location"
]

# Requests for app activities during the Auth flow
REQUEST_VISIBLE_ACTIONS = [
    "http://schemas.google.com/CheckInActivity"
]


def createError(code, message):
    """Create a JSON string to be returned as error response to requests"""
    return json.dumps({"error": {"code": code, "message": message}})


def createMessage(message):
    """Create a JSON string to be returned as response to requests"""
    return json.dumps({"message": message})


class BaseHandler(webapp2.RequestHandler):
    """Base request handler to enable session storage for all handlers"""

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


def build_service_from_service(service, api, version):
    """Build a Google API service using another pre-authed service"""
    
    new_service = build(api, version, http=service._http)
    
    return new_service


class User(ndb.Model):
    """Datastore model to keep all relevant information about a user

    Properties:
        displayName     Name of the user as returned by the Google+ API
        imageUrl        Avatar image of the user as returned by the Google+ API
        verifyToken     Random token generated for each user to check validity of incoming notifications
        credentials     OAuth2 Access and refresh token to be used for requests against the Mirror API
        latitude        Latest recorded latitude of the user
        longitude       Latest recorded longitude of the user
        locationUpdate  DateTime at which the location of the user was last update
        friends         List of Google+ friends id, as returned by the Google+ API
    """

    displayName = ndb.StringProperty()
    imageUrl = ndb.StringProperty()
    verifyToken = ndb.StringProperty()
    credentials = CredentialsNDBProperty()
    latitude = ndb.FloatProperty()
    longitude = ndb.FloatProperty()
    locationUpdate = ndb.DateTimeProperty()
    friends = ndb.StringProperty(repeated=True)


class TestUser(User):

    _testUser = True
