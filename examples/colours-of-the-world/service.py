#!/usr/bin/python

# Copyright (C) 2013 Gerwin Sturm, FoldedSoft e.U.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""RequestHandlers for HCT Web service"""

__author__ = 'scarygami@gmail.com (Gerwin Sturm)'

import utils
from auth import get_auth_service
from models import Submission

import json
import logging
import random
import string

from google.appengine.ext import ndb
from google.appengine.datastore.datastore_query import Cursor
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
        """Retrieve recent submissions"""

        self.response.content_type = "application/json"

        qry = Submission.query()
        qry = qry.order(-Submission.date)

        items = []
        users = set()
        curs = Cursor(urlsafe=self.request.get('cursor'))
        submissions, next_curs, more = qry.fetch_page(10, start_cursor=curs)
        for submission in submissions:
            items.append({
              "id": submission.key.id(),
              "user": submission.key.parent().id(),
              "colour": submission.colour,
              "url": submission.url,
              "date": submission.date.strftime("%Y-%m-%dT%H:%M:%S.%f")
            })
            users.add(submission.key.parent().id())

        user_data = dict()
        for user_id in users:
          user = ndb.Key("User", user_id).get()
          if user is None:
              user = ndb.Key("TestUser", user_id).get()

          if user is not None:
            user_data[user_id] = {
              "displayName": user.displayName,
              "imageUrl": user.imageUrl
            }

        response = {}
        response["items"] = items
        response["users"] = user_data
        if more and next_curs:
          response["next"] = next_curs.urlsafe()

        self.response.out.write(json.dumps(response))

            
class RemoveHandler(utils.BaseHandler):

    def get(self, test, submission_id):
        """Remove a Submission for the user."""

        self.response.content_type = "application/json"

        gplus_id = self.session.get("gplus_id")
        if test is not None:
            user = ndb.Key("TestUser", gplus_id).get()
        else:
            user = ndb.Key("User", gplus_id).get()

        if user.get() is None:
            self.response.status = 401
            self.response.out.write(utils.createError(401, "Current user not connected."))
            return

        # TODO


SERVICE_ROUTES = [
    (r"(/test)?/", IndexHandler),
    (r"(/test)?/list", ListHandler),
    (r"(/test)?/remove/(.+)", RemoveHandler)
]
