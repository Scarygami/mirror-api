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

"""

RequestHandlers and helper functions for authentication

Handles all authentication and storing of credentials when a user signs up
for the demo services. Sets up Contacts and Subscriptions when the user
first connects. Also handles disconnection by removing all contacts and
subscriptions and deleting credentials when the user wants to disconnect.

"""

__author__ = 'scarygami@gmail.com (Gerwin Sturm)'

import utils

import random
import string
import httplib2
import json
import logging

from apiclient.discovery import build
from apiclient.errors import HttpError
from apiclient.errors import UnknownApiNameOrVersion
from google.appengine.ext import ndb
from oauth2client.client import AccessTokenRefreshError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from oauth2client.appengine import StorageByKeyName


def get_credentials(gplus_id):
    storage = StorageByKeyName(utils.User, gplus_id, "credentials")
    credentials = storage.get()
    return credentials


def store_credentials(gplus_id, credentials):
    storage = StorageByKeyName(utils.User, gplus_id, "credentials")
    storage.put(credentials)


def get_auth_service(gplus_id):
    credentials = get_credentials(gplus_id)
    if credentials is None:
        return None

    http = httplib2.Http()
    http = credentials.authorize(http)
    service = build(
        "mirror", "v1",
        discoveryServiceUrl=utils.discovery_url + "/discovery/v1/apis/{api}/{apiVersion}/rest",
        http=http
    )

    return service


class ConnectHandler(utils.BaseHandler):
    def post(self):
        """Exchange the one-time authorization code for a token and
        store the token in the session."""

        self.response.content_type = "application/json"

        state = self.request.get("state")
        gplus_id = self.request.get("gplus_id")
        code = self.request.body

        if state != self.session.get("state"):
            self.response.status = 401
            self.response.out.write(utils.createError(401, "Invalid state parameter"))
            return

        try:
            oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
            oauth_flow.redirect_uri = 'postmessage'
            credentials = oauth_flow.step2_exchange(code)
        except FlowExchangeError:
            self.response.status = 401
            self.response.out.write(utils.createError(401, "Failed to upgrade the authorization code."))
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
            self.response.out.write(utils.createError(401, "Token's user ID doesn't match given user ID."))
            return

        # Verify that the access token is valid for this app.
        if result['issued_to'] != utils.CLIENT_ID:
            self.response.status = 401
            self.response.out.write(utils.createError(401, "Token's client ID does not match the app's client ID"))
            return

        self.session["gplus_id"] = gplus_id
        stored_credentials = get_credentials(gplus_id)
        new_user = False
        if stored_credentials is None:
            new_user = True
            store_credentials(gplus_id, credentials)

        # TODO: handle cases where credentials don't have a refresh token

        # Create a new authorized API client
        try:
            service = get_auth_service(gplus_id)
        except AccessTokenRefreshError:
            self.response.status = 500
            self.response.out.write(utils.createError(500, "Failed to refresh access token."))
            return
        except UnknownApiNameOrVersion:
            self.response.status = 500
            self.response.out.write(utils.createError(500, "Failed to initialize client library. Discovery document not found."))
            return
        except HttpError as e:
            self.response.status = 500
            self.response.out.write(utils.createError(500, "Failed to initialize client library. %s" % e))
            return

        # Re-register contacts just in case new ones have been added
        # TODO: include description of contacts in demo services and read from there
        body = {}
        body["acceptTypes"] = ["image/*"]
        body["id"] = "instaglass_sepia"
        body["displayName"] = "Sepia"
        body["imageUrls"] = [utils.base_url + "/images/sepia.jpg"]
        try:
            result = service.contacts().insert(body=body).execute()
        except AccessTokenRefreshError:
            self.response.status = 500
            self.response.out.write(utils.createError(500, "Failed to refresh access token."))
            return
        except HttpError as e:
            self.response.status = 500
            self.response.out.write(utils.createError(500, "Failed to initialize client library. %s" % e))
            return

        body = {}
        body["acceptTypes"] = ["image/*"]
        body["id"] = "add_a_cat"
        body["displayName"] = "Add a Cat to that"
        body["imageUrls"] = [utils.base_url + "/images/cat.png"]
        try:
            result = service.contacts().insert(body=body).execute()
        except AccessTokenRefreshError:
            self.response.status = 500
            self.response.out.write(utils.createError(500, "Failed to refresh access token."))
            return
        except HttpError as e:
            self.response.status = 500
            self.response.out.write(utils.createError(500, "Failed to initialize client library. %s" % e))
            return

        """
        Re-register subscriptions to make sure all of them are available.
        Normally it would be best to use subscriptions.list first to check.
        For the purposes of this demo service all possible subscriptions are made.
        Normally you would only set-up subscriptions for the services you need.
        """

        # Delete all existing subscriptions
        try:
            result = service.subscriptions().list().execute()
            if "items" in result:
                for subscription in result["items"]:
                    del_result = service.subscriptions().delete(id=subscription["id"]).execute()
        except AccessTokenRefreshError:
            self.response.status = 500
            self.response.out.write(utils.createError(500, "Failed to refresh access token."))
            return
        except HttpError as e:
            self.response.status = 500
            self.response.out.write(utils.createError(500, "Failed to initialize client library. %s" % e))
            return

        # Generate random verifyToken and store it in User entity
        verifyToken = ''.join(random.choice(string.ascii_letters + string.digits) for x in range(32))
        user = ndb.Key("User", gplus_id).get()
        user.verifyToken = verifyToken
        user.put()

        # Subscribe to all timeline inserts/updates/deletes
        body = {}
        body["collection"] = "timeline"
        body["userToken"] = gplus_id
        body["verifyToken"] = verifyToken
        body["callbackUrl"] = utils.base_url + "/timeline_update"
        try:
            result = service.subscriptions().insert(body=body).execute()
        except AccessTokenRefreshError:
            self.response.status = 500
            self.response.out.write(utils.createError(500, "Failed to refresh access token."))
            return
        except HttpError as e:
            self.response.status = 500
            self.response.out.write(utils.createError(500, "Failed to initialize client library. %s" % e))
            return

        # Subscribe to all location updates
        body = {}
        body["collection"] = "locations"
        body["userToken"] = gplus_id
        body["verifyToken"] = verifyToken
        body["callbackUrl"] = utils.base_url + "/locations_update"
        try:
            result = service.subscriptions().insert(body=body).execute()
        except AccessTokenRefreshError:
            self.response.status = 500
            self.response.out.write(utils.createError(500, "Failed to refresh access token."))
            return
        except HttpError as e:
            self.response.status = 500
            self.response.out.write(utils.createError(500, "Failed to initialize client library. %s" % e))
            return

        if not new_user:
            self.response.status = 200
            self.response.out.write(utils.createMessage("Current user is already connected."))
            return

        # Send welcome messages for new users
        body = {}
        body["text"] = "Welcome to Instaglass!"
        body["attachments"] = [{"contentType": "image/jpeg", "contentUrl": utils.base_url + "/images/sepia.jpg"}]
        try:
            result = service.timeline().insert(body=body).execute()
        except AccessTokenRefreshError:
            self.response.status = 500
            self.response.out.write(utils.createError(500, "Failed to refresh access token."))
            return
        except HttpError as e:
            self.response.status = 500
            self.response.out.write(utils.createError(500, "Failed to initialize client library. %s" % e))
            return

        self.response.status = 200
        self.response.out.write(utils.createMessage("Successfully connected user."))


class DisconnectHandler(utils.BaseHandler):
    def post(self):
        """Revoke current user's token and reset their session."""

        self.response.content_type = "application/json"

        gplus_id = self.session.get("gplus_id")

        # Only disconnect a connected user.
        credentials = get_credentials(gplus_id)
        if credentials is None:
            self.response.status = 401
            self.response.out.write(utils.createError(401, "Current user not connected."))
            return

        # Create a new authorized API client
        try:
            service = get_auth_service(gplus_id)
        except AccessTokenRefreshError:
            self.response.status = 500
            self.response.out.write(utils.createError(500, "Failed to refresh access token."))
            return
        except UnknownApiNameOrVersion:
            self.response.status = 500
            self.response.out.write(utils.createError(500, "Failed to initialize client library. Discovery document not found."))
            return
        except HttpError as e:
            self.response.status = 500
            self.response.out.write(utils.createError(500, "Failed to initialize client library. %s" % e))
            return

        # De-register contacts
        try:
            result = service.contacts().list().execute()
            if "items" in result:
                for contact in result["items"]:
                    del_result = service.contacts().delete(id=contact["id"]).execute()
        except AccessTokenRefreshError:
            self.response.status = 500
            self.response.out.write(utils.createError(500, "Failed to refresh access token."))
            return
        except HttpError as e:
            self.response.status = 500
            self.response.out.write(utils.createError(500, "Failed to initialize client library. %s" % e))
            return

        # De-register subscriptions
        try:
            result = service.subscriptions().list().execute()
            if "items" in result:
                for subscription in result["items"]:
                    del_result = service.subscriptions().delete(id=subscription["id"]).execute()
        except AccessTokenRefreshError:
            self.response.status = 500
            self.response.out.write(utils.createError(500, "Failed to refresh access token."))
            return
        except HttpError as e:
            self.response.status = 500
            self.response.out.write(utils.createError(500, "Failed to initialize client library. %s" % e))
            return

        # Execute HTTP GET request to revoke current token.
        access_token = credentials.access_token
        url = "https://accounts.google.com/o/oauth2/revoke?token=%s" % access_token
        h = httplib2.Http()
        try:
            result = h.request(url, "GET")[0]
            if result["status"] == "200":
                # Reset the user's session.
                self.response.status = 200
                self.response.out.write(utils.createMessage("Successfully disconnected user."))
            else:
                # For whatever reason, the given token was invalid.
                self.response.status = 400
                self.response.out.write(utils.createError(400, "Failed to revoke token for given user."))
        except HttpError as e:
            self.response.status = 500
            self.response.out.write(utils.createError(500, "Failed to initialize client library. %s" % e))
            return

        ndb.Key("User", gplus_id).delete()


AUTH_ROUTES = [
    ("/connect", ConnectHandler),
    ("/disconnect", DisconnectHandler)
]
