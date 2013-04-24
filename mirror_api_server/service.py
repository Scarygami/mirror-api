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

"""RequestHandlers for Web service"""

__author__ = 'scarygami@gmail.com (Gerwin Sturm)'

import utils
from auth import get_auth_service

import random
import string
import json

from oauth2client.client import AccessTokenRefreshError


class IndexHandler(utils.BaseHandler):
    """Renders the main page that is mainly used for authentication only so far"""

    def get(self):
        reconnect = (self.request.get("reconnect") == "true")
        template = utils.JINJA.get_template("templates/service.html")
        state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
        self.session["state"] = state
        self.response.out.write(template.render({"client_id": utils.CLIENT_ID, "state": state, "reconnect": reconnect}))


class ListHandler(utils.BaseHandler):

    def get(self):
        """Retrieve timeline cards for the current user."""

        self.response.content_type = "application/json"

        gplus_id = self.session.get("gplus_id")
        service = get_auth_service(gplus_id)

        if service is None:
            self.response.status = 401
            self.response.out.write(utils.createError(401, "Current user not connected."))
            return
        try:
            # Retrieve timeline cards and return as reponse
            result = service.timeline().list().execute()
            self.response.status = 200
            self.response.out.write(json.dumps(result))
        except AccessTokenRefreshError:
            self.response.status = 500
            self.response.out.write(utils.createError(500, "Failed to refresh access token."))


class NewCardHandler(utils.BaseHandler):

    def post(self):
        """Create a new timeline card for the current user."""

        self.response.content_type = "application/json"

        gplus_id = self.session.get("gplus_id")
        service = get_auth_service(gplus_id)

        if service is None:
            self.response.status = 401
            self.response.out.write(utils.createError(401, "Current user not connected."))
            return

        message = self.request.body

        data = json.loads(message)

        body = {}
        body["text"] = data["text"]
        if "image" in data:
            body["attachments"] = [{"contentType": "image/*", "contentUrl": data["image"]}]
        body["menuItems"] = [{"action": "SHARE"}, {"action": "REPLY"}]

        try:
            # Insert timeline card and return as reponse
            result = service.timeline().insert(body=body).execute()
            self.response.status = 200
            self.response.out.write(json.dumps(result))
        except AccessTokenRefreshError:
            self.response.status = 500
            self.response.out.write(utils.createError(500, "Failed to refresh access token."))


SERVICE_ROUTES = [
    ("/", IndexHandler),
    ("/list", ListHandler),
    ("/new", NewCardHandler)
]
