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
Notification/subscription handler

Handles subscription post requests coming from the Mirror API and forwards
the requests to the relevant demo services.

"""

__author__ = 'scarygami@gmail.com (Gerwin Sturm)'

import utils
from auth import get_auth_service

import json
import logging
from datetime import datetime
from google.appengine.ext import ndb


class TimelineNotifyHandler(utils.BaseHandler):
    """
    Handles all timeline notifications (updates, deletes, inserts)
    Forwards the information to implemented demo services
    """

    def post(self, test):
        """Callback for Timeline updates."""

        message = self.request.body
        data = json.loads(message)
        logging.info(data)

        self.response.status = 200

        gplus_id = data["userToken"]
        verifyToken = data["verifyToken"]
        if test is not None:
            user = ndb.Key("TestUser", gplus_id).get()
        else:
            user = ndb.Key("User", gplus_id).get()
        if user is None or user.verifyToken != verifyToken:
            logging.info("Wrong user")
            return

        if data["collection"] != "timeline":
            logging.info("Wrong collection")
            return

        service = get_auth_service(gplus_id, test)

        if service is None:
            logging.info("No valid credentials")
            return

        result = service.timeline().get(id=data["itemId"]).execute()
        logging.info(result)

        #for demo_service in demo_services:
        #    if hasattr(demo_service, "handle_item"):
        #        demo_service.handle_item(result, data, service, test)


NOTIFY_ROUTES = [
    (r"(/test)?/timeline_update", TimelineNotifyHandler)
]
