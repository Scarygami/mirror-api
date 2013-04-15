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
import jinja2

from apiclient.discovery import build
from google.appengine.ext import ndb
from google.appengine.api.app_identity import get_application_id
from oauth2client.client import AccessTokenRefreshError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from oauth2client.appengine import CredentialsNDBProperty
from oauth2client.appengine import StorageByKeyName
from webapp2_extras import sessions
from webapp2_extras.appengine import sessions_memcache

import logging

JINJA = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

appname = get_application_id()
base_url = "https://" + appname + ".appspot.com"
discovery_url = base_url + "/_ah/api"

config = {}
config["webapp2_extras.sessions"] = {
    "secret_key": "ajksdlj1029jlksndajsaskd7298hkajsbdkaukjassnkjankj",
}

with open("client_secrets.json", "r") as fh:
    CLIENT_ID = json.load(fh)["web"]["client_id"]


def createError(code, message):
    return json.dumps({"error": {"code": code, "message": message}})


def createMessage(message):
    return json.dumps({"message": message})


class User(ndb.Model):
    verifyToken = ndb.StringProperty()
    credentials = CredentialsNDBProperty()


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
        template = JINJA.get_template("templates/service.html")
        state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
        self.session["state"] = state
        self.response.out.write(template.render({"client_id": CLIENT_ID, "state": state}))


class GlassHandler(BaseHandler):
    def get(self):
        template = JINJA.get_template("templates/glass.html")
        self.response.out.write(template.render({"client_id": CLIENT_ID, "discovery_url": discovery_url}))


class ConnectHandler(BaseHandler):
    def post(self):
        """Exchange the one-time authorization code for a token and
        store the token in the session."""

        self.response.content_type = "application/json"

        state = self.request.get("state")
        gplus_id = self.request.get("gplus_id")
        code = self.request.body

        if state != self.session.get("state"):
            self.response.status = 401
            self.response.out.write(createError(401, "Invalid state parameter"))
            return

        try:
            oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
            oauth_flow.redirect_uri = 'postmessage'
            credentials = oauth_flow.step2_exchange(code)
        except FlowExchangeError:
            self.response.status = 401
            self.response.out.write(createError(401, "Failed to upgrade the authorization code."))
            return

        # Check that the access token is valid.
        access_token = credentials.access_token
        url = ("https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s" % access_token)
        h = httplib2.Http()
        result = json.loads(h.request(url, 'GET')[1])

        # If there was an error in the access token info, abort.
        if result.get("error") is not None:
            self.response.status = 500
            self.response.out.write(json.dumps(result.get("error")))
            return

        # Verify that the access token is used for the intended user.
        if result["user_id"] != gplus_id:
            self.response.status = 401
            self.response.out.write(createError(401, "Token's user ID doesn't match given user ID."))
            return

        # Verify that the access token is valid for this app.
        if result['issued_to'] != CLIENT_ID:
            self.response.status = 401
            self.response.out.write(createError(401, "Token's client ID does not match the app's client ID"))
            return

        stored_credentials = self.session.get("credentials")
        stored_gplus_id = self.session.get("gplus_id")
        if stored_credentials is not None and gplus_id == stored_gplus_id:
            self.response.status = 200
            self.response.out.write(createMessage("Current user is already connected."))
            return

        # Store the access token in the session for later use.
        self.session["credentials"] = credentials
        self.session["gplus_id"] = gplus_id
        self.response.status = 200
        self.response.out.write(createMessage("Successfully connected user."))


class DisconnectHandler(BaseHandler):
    def post(self):
        """Revoke current user's token and reset their session."""

        self.response.content_type = "application/json"

        # Only disconnect a connected user.
        credentials = self.session.get("credentials")
        if credentials is None:
            self.response.status = 401
            self.response.out.write(createError(401, "Current user not connected."))
            return

        # Execute HTTP GET request to revoke current token.
        access_token = credentials.access_token
        url = "https://accounts.google.com/o/oauth2/revoke?token=%s" % access_token
        h = httplib2.Http()
        result = h.request(url, "GET")[0]

        del self.session["credentials"]

        if result["status"] == "200":
            # Reset the user's session.
            self.response.status = 200
            self.response.out.write(createMessage("Successfully disconnected user."))
        else:
            # For whatever reason, the given token was invalid.
            self.response.status = 400
            self.response.out.write(createError(400, "Failed to revoke token for given user."))


class ListHandler(BaseHandler):
    def get(self):
        """Retrieve timeline cards for the current user."""

        self.response.content_type = "application/json"

        credentials = self.session.get("credentials")
        if credentials is None:
            self.response.status = 401
            self.response.out.write(createError(401, "Current user not connected."))
            return
        try:
            # Create a new authorized API client.
            http = httplib2.Http()
            http = credentials.authorize(http)
            service = build("mirror", "v1", discoveryServiceUrl=discovery_url + "/discovery/v1/apis/{api}/{apiVersion}/rest", http=http)

            # Retrieve timeline cards and return as reponse
            result = service.timeline().list().execute()
            self.response.status = 200
            self.response.out.write(json.dumps(result))
        except AccessTokenRefreshError:
            self.response.status = 500
            self.response.out.write(createError(500, "Failed to refresh access token."))


class NewCardHandler(BaseHandler):
    def post(self):
        """Create a new timeline card for the current user."""

        self.response.content_type = "application/json"

        credentials = self.session.get("credentials")
        if credentials is None:
            self.response.status = 401
            self.response.out.write(createError(401, "Current user not connected."))
            return

        message = self.request.body

        logging.info(message)

        data = json.loads(message)

        logging.info(data["text"])

        body = {}
        body["text"] = data["text"]
        if "image" in data:
            body["image"] = data["image"]
            logging.info(data["image"])
        body["cardOptions"] = [{"action": "SHARE"}, {"action": "REPLY"}]

        try:
            # Create a new authorized API client.
            http = httplib2.Http()
            http = credentials.authorize(http)
            service = build("mirror", "v1", discoveryServiceUrl=discovery_url + "/discovery/v1/apis/{api}/{apiVersion}/rest", http=http)

            # Retrieve timeline cards and return as reponse
            result = service.timeline().insert(body=body).execute()
            self.response.status = 200
            self.response.out.write(json.dumps(result))
        except AccessTokenRefreshError:
            self.response.status = 500
            self.response.out.write(createError(500, "Failed to refresh access token."))


app = webapp2.WSGIApplication(
    [
        ('/', IndexHandler),
        ('/glass/', GlassHandler),
        ('/connect', ConnectHandler),
        ('/disconnect', DisconnectHandler),
        ('/list', ListHandler),
        ('/new', NewCardHandler)
    ],
    debug=True, config=config)
