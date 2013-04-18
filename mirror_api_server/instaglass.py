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

"""RequestHandlers for Instaglass requests"""

__author__ = 'scarygami@gmail.com (Gerwin Sturm)'

import utils
from auth import get_auth_service

import json
import logging
import Image
import ImageOps
import cStringIO
import re

from google.appengine.ext import ndb


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


class InstaglassHandler(utils.BaseHandler):
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


INSTAGLASS_ROUTES = [
    ("/timeline_update", InstaglassHandler)
]
