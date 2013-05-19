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

"""RequestHandlers for HCT Web service"""

__author__ = 'scarygami@gmail.com (Gerwin Sturm)'

import utils
from auth import get_auth_service

import json
import logging
import random
import string

from google.appengine.ext import ndb
from oauth2client.client import AccessTokenRefreshError


class IndexHandler(utils.BaseHandler):
    """Renders the main page that is mainly used for authentication only so far"""

    def get(self, test):

        if test is None:
            scopes = ' '.join(utils.COMMON_SCOPES + utils.REAL_SCOPES)
        else:
            scopes = ' '.join(utils.COMMON_SCOPES + utils.TEST_SCOPES)

        reconnect = (self.request.get("reconnect") == "true")
        template = utils.JINJA.get_template("templates/service.html")
        state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
        self.session["state"] = state
        self.response.out.write(template.render({"client_id": utils.CLIENT_ID, "state": state, "scopes": scopes, "reconnect": reconnect}))


class ListHandler(utils.BaseHandler):

    def get(self, test):
        """Retrieve currently tracked sources for the current user."""

        self.response.content_type = "application/json"

        gplus_id = self.session.get("gplus_id")
        if test is not None:
            user = ndb.Key("TestUser", gplus_id).get()
        else:
            user = ndb.Key("User", gplus_id).get()

        if user is None:
            self.response.status = 401
            self.response.out.write(utils.createError(401, "Current user not connected."))
            return

        items = []
        if user.sources is not None:
            for source in user.sources:
                data = source.get()
                items.append(data.id)

        self.response.out.write(json.dumps({"items": items}))

        # TODO


class AddHandler(utils.BaseHandler):

    def post(self, test):
        """Add a new source to be tracker."""

        self.response.content_type = "application/json"

        gplus_id = self.session.get("gplus_id")
        service = get_auth_service(gplus_id, test)

        if service is None:
            self.response.status = 401
            self.response.out.write(utils.createError(401, "Current user not connected."))
            return

        data = json.loads(self.request.body)

        # TODO
        logging.info(data)


class RemoveHandler(utils.BaseHandler):

    def get(self, test, source_id):
        """
        Remove a Source for the user.
        Set Source.active = False if no users are tracking it anymore.
        """

        self.response.content_type = "application/json"

        gplus_id = self.session.get("gplus_id")
        service = get_auth_service(gplus_id, test)

        if service is None:
            self.response.status = 401
            self.response.out.write(utils.createError(401, "Current user not connected."))
            return

        # TODO


SERVICE_ROUTES = [
    (r"(/test)?/", IndexHandler),
    (r"(/test)?/list", ListHandler),
    (r"(/test)?/add", AddHandler),
    (r"(/test)?/remove/(.+)", RemoveHandler)
]
