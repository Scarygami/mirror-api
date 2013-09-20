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
RequestHandlers for Glass emulator

Renders the glass emulator and handles authentication and setting up
push notifications via the Channel API

"""

__author__ = 'scarygami@gmail.com (Gerwin Sturm)'

import utils

import httplib2
import json
import logging
import random
import string

from google.appengine.api import channel
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError


class GlassHandler(utils.BaseHandler):
    """Renders the Glass emulator"""

    def get(self):
        template = utils.JINJA.get_template("emulator/templates/glass.html")
        state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
        self.session["state"] = state
        self.session["credentials"] = None
        self.response.out.write(template.render(
            {
                "state": state,
                "client_id": utils.CLIENT_ID,
                "discovery_url": utils.discovery_url
            }
        ))


class GlassConnectHandler(utils.BaseHandler):
    """Handles connection requests coming from the emulator"""

    def post(self):
        """
        Exchange the one-time authorization code for a token and verify user.
        Return a channel token for push notifications on success
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

        token = channel.create_channel(result["email"])

        self.session["credentials"] = credentials

        self.response.status = 200
        self.response.out.write(utils.createMessage({"token": token}))


class AttachmentHandler(utils.BaseHandler):
    """Retrieves an attachment using the current user's credentials"""

    def get(self, timelineId, attachmentId):
        credentials = self.session.get("credentials")
        if credentials is None:
            self.response.content_type = "application/json"
            self.response.status = 401
            self.response.out.write(utils.createError(401, "Invalid credentials."))
            return

        http = httplib2.Http()
        http = credentials.authorize(http)
        http.timeout = 60

        resp, content = http.request("%s/upload/mirror/v1/timeline/%s/attachments/%s" % (utils.base_url, timelineId, attachmentId))
        if resp.status == 200:
            self.response.content_type = resp["content-type"]
            self.response.out.write(content)
        else:
            self.response.content_type = "application/json"
            self.response.status = resp.status
            self.response.out.write(utils.createError(resp.status, "Unable to retrieve attachment."))


GLASS_ROUTES = [
    (r"/glass/attachment/(.*)/(.*)", AttachmentHandler),
    ("/glass/connect", GlassConnectHandler),
    ("/glass/", GlassHandler)
]
