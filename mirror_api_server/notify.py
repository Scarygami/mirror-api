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

"""Methods for Instaglass service"""

__author__ = 'scarygami@gmail.com (Gerwin Sturm)'

import utils
from auth import get_auth_service
from instaglass import handle_image as instaglass_image

import json
import logging

from google.appengine.ext import ndb


class NotifyHandler(utils.BaseHandler):
    def post(self):
        """Callback for Timeline updates."""
        message = self.request.body
        data = json.loads(message)
        logging.info(data)

        self.response.status = 200

        gplus_id = data["userToken"]
        verifyToken = data["verifyToken"]
        user = ndb.Key("User", gplus_id).get()
        if user is None or user.verifyToken != verifyToken:
            logging.info("Wrong user")
            return

        if data["operation"] != "UPDATE" or data["userActions"][0]["type"] != "SHARE":
            logging.info("Wrong operation")
            return

        service = get_auth_service(gplus_id)

        if service is None:
            logging.info("No valid credentials")
            return

        result = service.timeline().get(id=data["itemId"]).execute()
        logging.info(result)

        shares = {}

        if "recipients" in result:
            for rec in result["recipients"]:
                if rec["id"] == "instaglass_sepia":
                    if not "instaglass" in shares:
                        shares["instaglass"] = []
                    if not "sepia" in shares["instaglass"]:
                        shares["instaglass"].append("sepia")
                    break

        for share in shares:
            if share == "instaglass":
                for method in shares[share]:
                    new_item = instaglass_image(result, method)
                    if new_item is not None:
                        result = service.timeline().insert(body=new_item).execute()
                        logging.info(result)


NOTIFY_ROUTES = [
    ("/timeline_update", NotifyHandler)
]
