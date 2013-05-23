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

Handles subscription post requests coming from the Mirror API

"""

__author__ = 'scarygami@gmail.com (Gerwin Sturm)'

import utils
from auth import get_auth_service

import json
import logging
from datetime import datetime
from google.appengine.api import taskqueue
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
        if user is None:
            logging.info("Wrong user")
            return
        if user.verifyToken != verifyToken:
            logging.info("verifyToken mismatch")
            return

        if data["collection"] != "timeline":
            logging.info("Wrong collection")
            return

        share = False
        if "userActions" in data:
            for action in data["userActions"]:
                if "type" in action and action["type"] == "SHARE":
                    share = True
                    break

        if share:
            # Evaluate submission
            taskqueue.add(url="/tasks/evaluate",
                          params={"user": gplus_id, "test": test, "item": data["itemId"]},
                          method="POST")

                          
NOTIFY_ROUTES = [
    (r"(/test)?/timeline_update", TimelineNotifyHandler)
]
