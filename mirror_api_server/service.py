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

"""RequestHandlers for Demo services"""

__author__ = 'scarygami@gmail.com (Gerwin Sturm)'

import utils

import random
import string
import httplib2
import json
import logging
import Image
import ImageOps
import cStringIO
import re

from apiclient.discovery import build
from google.appengine.ext import ndb
from oauth2client.client import AccessTokenRefreshError
from oauth2client.appengine import StorageByKeyName


class IndexHandler(utils.BaseHandler):
    def get(self):
        template = utils.JINJA.get_template("templates/service.html")
        state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
        self.session["state"] = state
        self.response.out.write(template.render({"client_id": utils.CLIENT_ID, "state": state}))


class ListHandler(utils.BaseHandler):
    def get(self):
        """Retrieve timeline cards for the current user."""

        self.response.content_type = "application/json"

        gplus_id = self.session.get("gplus_id")
        storage = StorageByKeyName(utils.User, gplus_id, "credentials")
        credentials = storage.get()

        if credentials is None:
            self.response.status = 401
            self.response.out.write(utils.createError(401, "Current user not connected."))
            return
        try:
            # Create a new authorized API client.
            http = httplib2.Http()
            http = credentials.authorize(http)
            service = build(
                "mirror", "v1",
                discoveryServiceUrl=utils.discovery_url + "/discovery/v1/apis/{api}/{apiVersion}/rest",
                http=http
            )

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
        storage = StorageByKeyName(utils.User, gplus_id, "credentials")
        credentials = storage.get()

        if credentials is None:
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
            # Create a new authorized API client.
            http = httplib2.Http()
            http = credentials.authorize(http)
            service = build(
                "mirror", "v1",
                discoveryServiceUrl=utils.discovery_url + "/discovery/v1/apis/{api}/{apiVersion}/rest",
                http=http
            )

            # Retrieve timeline cards and return as reponse
            result = service.timeline().insert(body=body).execute()
            self.response.status = 200
            self.response.out.write(json.dumps(result))
        except AccessTokenRefreshError:
            self.response.status = 500
            self.response.out.write(utils.createError(500, "Failed to refresh access token."))


def make_linear_ramp(white):
    """ generate a palette in a format acceptable for `putpalette`, which
        expects [r,g,b,r,g,b,...]
    """
    ramp = []
    r, g, b = white
    for i in range(255):
        ramp.extend((r*i/255, g*i/255, b*i/255))
    return ramp


def apply_sepia_filter(image):
    """ Apply a sepia-tone filter to the given PIL Image
        Based on code at: http://effbot.org/zone/pil-sepia.htm
    """
    # make sepia ramp (tweak color as necessary)
    sepia = make_linear_ramp((255, 240, 192))

    # convert to grayscale
    orig_mode = image.mode
    if orig_mode != "L":
        image = image.convert("L")

    # apply contrast enhancement here, e.g.
    image = ImageOps.autocontrast(image)

    # apply sepia palette
    image.putpalette(sepia)

    # convert back to its original mode
    if orig_mode != "L":
        image = image.convert(orig_mode)

    return image


class UpdateHandler(utils.BaseHandler):
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

        storage = StorageByKeyName(utils.User, gplus_id, "credentials")
        credentials = storage.get()

        if credentials is None:
            logging.info("No credentials")
            return

        http = httplib2.Http()
        http = credentials.authorize(http)
        service = build(
            "mirror", "v1",
            discoveryServiceUrl=utils.discovery_url + "/discovery/v1/apis/{api}/{apiVersion}/rest",
            http=http
        )

        result = service.timeline().get(id=data["itemId"]).execute()
        logging.info(result)

        shareType = None
        if "recipients" in result:
            for rec in result["recipients"]:
                if rec["id"] == "instaglass_sepia":
                    shareType = "sepia"
                    break

        if shareType is None:
            logging.info("Wrong share ID")
            return

        image = None
        if "attachments" in result:
            for att in result["attachments"]:
                if att["contentType"].startswith("image/"):
                    image = att["contentUrl"]
                    break

        if image is None:
            logging.info("No suitable attachment")
            return

        if not image.startswith("data:image"):
            logging.info("Can only work with data-uri")
            return

        img_data = re.search(r'base64,(.*)', image).group(1)
        tempimg = cStringIO.StringIO(img_data.decode('base64'))
        im = Image.open(tempimg)
        new_im = apply_sepia_filter(im)

        f = cStringIO.StringIO()
        new_im.save(f, "JPEG")
        content = f.getvalue()
        f.close()
        data_uri = "data:image/jpeg;base64," + content.encode("base64").replace("\n", "")

        body = {}
        body["attachments"] = [{"contentType": "image/jpeg", "contentUrl": data_uri}]
        body["menuItems"] = [{"action": "SHARE"}]
        result = service.timeline().insert(body=body).execute()
        logging.info(result)


SERVICE_ROUTES = [
    ("/", IndexHandler),
    ("/list", ListHandler),
    ("/new", NewCardHandler),
    ("/timeline_update", UpdateHandler)
]
