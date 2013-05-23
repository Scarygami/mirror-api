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
from models import User, TestUser

import random
import string
import httplib2
import json

from apiclient.discovery import build
from apiclient.errors import HttpError
from apiclient.errors import UnknownApiNameOrVersion
from google.appengine.ext import ndb
from oauth2client.client import AccessTokenRefreshError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from oauth2client.appengine import StorageByKeyName
from google.appengine.api import taskqueue


def get_credentials(gplus_id, test):
    """Retrieves credentials for the provided Google+ User ID from the Datastore"""
    if test is not None:
        storage = StorageByKeyName(TestUser, gplus_id, "credentials")
    else:
        storage = StorageByKeyName(User, gplus_id, "credentials")
    credentials = storage.get()
    return credentials


def store_credentials(gplus_id, test, credentials):
    """Stores credentials for the provide Google+ User ID to Datastore"""
    if test is not None:
        storage = StorageByKeyName(TestUser, gplus_id, "credentials")
    else:
        storage = StorageByKeyName(User, gplus_id, "credentials")
    storage.put(credentials)


def get_auth_service(gplus_id, test, api="mirror", version="v1"):
    """Creates a new authenticated API client using the stored credentials"""

    if test is not None and api == "mirror" and version == "v1":
        # Use internal API for mirror API in test mode
        discovery_service_url = utils.discovery_service_url
    else:
        # Use Google APIs in all other cases
        discovery_service_url = None

    credentials = get_credentials(gplus_id, test)
    if credentials is None:
        return None

    http = httplib2.Http()
    http = credentials.authorize(http)
    http.timeout = 60

    if discovery_service_url is None:
        service = build(api, version, http=http)
    else:
        service = build(api, version, http=http, discoveryServiceUrl=discovery_service_url)

    return service


def _disconnect(gplus_id, test):
    """Delete credentials in case of errors"""

    store_credentials(gplus_id, test, None)


class ConnectHandler(utils.BaseHandler):
    def post(self, test):
        """
        Exchange the one-time authorization code for a token and
        store the credentials for later access.

        Setup all contacts and subscriptions necessary for the hosted services.
        """

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

        # Store credentials associated with the User ID for later use
        self.session["gplus_id"] = gplus_id
        stored_credentials = get_credentials(gplus_id, test)
        new_user = False
        if stored_credentials is None:
            new_user = True
            store_credentials(gplus_id, test, credentials)

        # handle cases where credentials don't have a refresh token
        credentials = get_credentials(gplus_id, test)

        if credentials.refresh_token is None:
            _disconnect(gplus_id, test)
            self.response.status = 401
            self.response.out.write(utils.createError(401, "No Refresh token available, need to reauthenticate"))
            return

        # Create new authorized API clients for the Mirror API and Google+ API
        try:
            service = get_auth_service(gplus_id, test)
            plus_service = get_auth_service(gplus_id, test, "plus", "v1")
        except AccessTokenRefreshError:
            _disconnect(gplus_id, test)
            self.response.status = 401
            self.response.out.write(utils.createError(401, "Failed to refresh access token."))
            return
        except UnknownApiNameOrVersion:
            self.response.status = 500
            self.response.out.write(utils.createError(500, "Failed to initialize client library. Discovery document not found."))
            return
        except HttpError as e:
            self.response.status = 500
            self.response.out.write(utils.createError(500, "Failed to initialize client library. %s" % e))
            return

        # Fetch user information
        try:
            result = plus_service.people().get(userId="me", fields="displayName,image").execute()
        except AccessTokenRefreshError:
            _disconnect(gplus_id, test)
            self.response.status = 401
            self.response.out.write(utils.createError(401, "Failed to refresh access token."))
            return
        except HttpError as e:
            self.response.status = 500
            self.response.out.write(utils.createError(500, "Failed to execute request. %s" % e))
            return

        # Store some public user information for later user
        if test is not None:
            user = ndb.Key("TestUser", gplus_id).get()
        else:
            user = ndb.Key("User", gplus_id).get()
        user.displayName = result["displayName"]
        user.imageUrl = result["image"]["url"]
        user.put()

        """
        Re-register subscriptions and contacts to make sure all of them are available.
        """

        # Delete all existing subscriptions
        try:
            result = service.subscriptions().list().execute()
            if "items" in result:
                for subscription in result["items"]:
                    service.subscriptions().delete(id=subscription["id"]).execute()
        except AccessTokenRefreshError:
            _disconnect(gplus_id, test)
            self.response.status = 401
            self.response.out.write(utils.createError(401, "Failed to refresh access token."))
            return
        except HttpError as e:
            self.response.status = 500
            self.response.out.write(utils.createError(500, "Failed to execute request. %s" % e))
            return

        # Generate random verifyToken and store it in User entity
        if user.verifyToken is None:
            verifyToken = ''.join(random.choice(string.ascii_letters + string.digits) for x in range(32))
            user.verifyToken = verifyToken
            user.put()
        else:
            verifyToken = user.verifyToken

        # Contact for receiving submissions
        contact_id = "colours_of_the_world"
        existing = True
        try:
            result = service.contacts().get(id=contact_id).execute()
        except AccessTokenRefreshError:
            _disconnect(gplus_id, test)
            self.response.status = 401
            self.response.out.write(utils.createError(401, "Failed to refresh access token."))
            return
        except HttpError as e:
            if e.resp.status == 404:
                existing = False
            else:
                self.response.status = 500
                self.response.out.write(utils.createError(500, "Failed to execute request. %s" % e))
                return
        
        body =  {}
        body["acceptTypes"] = "image/*"
        body["id"] = contact_id
        body["displayName"] = "Colours of the World"
        body["imageUrls"] = [utils.base_url + "/images/card.png"]
        
        try:
            if existing:
                result = service.contacts().update(id=contact_id, body=body).execute()
            else:
                result = service.contacts().insert(body=body).execute()
        except AccessTokenRefreshError:
            _disconnect(gplus_id, test)
            self.response.status = 401
            self.response.out.write(utils.createError(401, "Failed to refresh access token."))
            return
        except HttpError as e:
            self.response.status = 500
            self.response.out.write(utils.createError(500, "Failed to execute request. %s" % e))
            return

        # Subscribe to all timeline inserts/updates/deletes
        body = {}
        body["collection"] = "timeline"
        body["userToken"] = gplus_id
        body["verifyToken"] = verifyToken
        body["callbackUrl"] = utils.base_url + ("" if test is None else "/test") + "/timeline_update"
        try:
            result = service.subscriptions().insert(body=body).execute()
        except AccessTokenRefreshError:
            _disconnect(gplus_id, test)
            self.response.status = 401
            self.response.out.write(utils.createError(401, "Failed to refresh access token."))
            return
        except HttpError as e:
            self.response.status = 500
            self.response.out.write(utils.createError(500, "Failed to execute request. %s" % e))
            return

        if not new_user:
            self.response.status = 200
            self.response.out.write(utils.createMessage("Current user is already connected."))
            return


        # Send welcome messages for new users
        welcome = {
            "html": ("<article>"
                     "  <img src=\"" + utils.base_url + "/images/card.png\" width=\"100%\" height=\"100%\">"
                     "  <div class=\"photo-overlay\"></div>"
                     "  <section>"
                     "    <p class=\"text-large\">Welcome to Colours of the World!</p>"
                     "    <p class=\"text-small\">Your first task will be sent to you soon</p>"
                     "  </section>"
                     "</article>")
        }

        try:
            result = service.timeline().insert(body=welcome).execute()
        except AccessTokenRefreshError:
            _disconnect(gplus_id, test)
            self.response.status = 401
            self.response.out.write(utils.createError(401, "Failed to refresh access token."))
            return
        except HttpError as e:
            self.response.status = 500
            self.response.out.write(utils.createError(500, "Failed to execute request. %s" % e))
            return

        # Create a new task for the user
        taskqueue.add(url="/tasks/createtask", countdown=10,
                      params={"user": gplus_id, "test": test},
                      method="POST")

        self.response.status = 200
        self.response.out.write(utils.createMessage("Successfully connected user."))


class DisconnectHandler(utils.BaseHandler):
    def post(self, test):
        """
        Remove subscriptions registered for the user.
        Revoke current user's token and reset their session.
        Delete User entity from Data store.
        """

        self.response.content_type = "application/json"

        gplus_id = self.session.get("gplus_id")

        # Only disconnect a connected user.
        credentials = get_credentials(gplus_id, test)
        if credentials is None:
            self.response.status = 401
            self.response.out.write(utils.createError(401, "Current user not connected."))
            return

        # Create a new authorized API client
        try:
            service = get_auth_service(gplus_id, test)
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
                    service.contacts().delete(id=contact["id"]).execute()
        except AccessTokenRefreshError:
            self.response.status = 500
            self.response.out.write(utils.createError(500, "Failed to refresh access token."))
            return
        except HttpError as e:
            self.response.status = 500
            self.response.out.write(utils.createError(500, "Failed to execute request. %s" % e))
            return

        # De-register subscriptions
        try:
            result = service.subscriptions().list().execute()
            if "items" in result:
                for subscription in result["items"]:
                    service.subscriptions().delete(id=subscription["id"]).execute()
        except AccessTokenRefreshError:
            self.response.status = 500
            self.response.out.write(utils.createError(500, "Failed to refresh access token."))
            return
        except HttpError as e:
            self.response.status = 500
            self.response.out.write(utils.createError(500, "Failed to execute request. %s" % e))
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
            self.response.out.write(utils.createError(500, "Failed to execute request. %s" % e))
            return

        # Delete User entity from datastore
        if test is not None:
            ndb.Key("TestUser", gplus_id).delete()
        else:
            ndb.Key("User", gplus_id).delete()


AUTH_ROUTES = [
    (r"(/test)?/connect", ConnectHandler),
    (r"(/test)?/disconnect", DisconnectHandler)
]
