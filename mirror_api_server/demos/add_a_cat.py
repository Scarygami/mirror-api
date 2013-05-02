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

"""Methods for Add a Cat to that service"""

__author__ = 'scarygami@gmail.com (Gerwin Sturm)'

from service import upload
from utils import base_url

import logging
import Image
import cStringIO
import random

__all__ = ["handle_item", "CONTACTS", "WELCOMES"]

"""Contacts that need to registered when the user connects to this service"""
CONTACTS = [
    {
        "acceptTypes": "image/*",
        "id": "add_a_cat",
        "displayName": "Add a Cat to that",
        "imageUrls": [base_url + "/images/cat.png"]
    }
]

"""Welcome message cards that are sent when the user first connects to this service"""
WELCOMES = [
    {
        "html": ("<article class=\"photo\">"
                 "  <img src=\"" + base_url + "/images/cat.png\" width=\"100%\" height=\"100%\">"
                 "  <div class=\"photo-overlay\"></div>"
                 "  <section>"
                 "    <p class=\"text-auto-size\">Welcome to Add a Cat!</p>"
                 "  </section>"
                 "</article>")
    }
]

_NUM_CATS = 6


def handle_item(item, notification, service, test):
    """Callback for Timeline updates."""

    if "userActions" in notification:
        for action in notification["userActions"]:
            if "type" in action and action["type"] == "SHARE":
                break
        else:
            # No SHARE action
            return
    else:
        # No SHARE action
        return

    if "recipients" in item:
        for rec in item["recipients"]:
            if rec["id"] == "add_a_cat":
                break
        else:
            # Item not meant for this service
            return
    else:
        # Item not meant for this service
        return

    imageId = None
    if "attachments" in item:
        for att in item["attachments"]:
            if att["contentType"].startswith("image/"):
                imageId = att["id"]
                break

    if imageId is None:
        logging.info("No suitable attachment")
        return

    attachment_metadata = service.timeline().attachments().get(
        itemId=item["id"], attachmentId=imageId).execute()
    content_url = attachment_metadata.get("contentUrl")
    resp, content = service._http.request(content_url)

    if resp.status != 200:
        logging.info("Couldn't fetch attachment")

    tempimg = cStringIO.StringIO(content)
    im = Image.open(tempimg)

    cat = random.randint(1, _NUM_CATS)
    cat_image = Image.open("res/cat%s.png" % cat)

    zoom = im.size[0] / 640

    cat_image.resize((cat_image.size[0] * zoom, cat_image.size[1] * zoom), Image.ANTIALIAS)

    x = random.randint(0, im.size[0] - cat_image.size[0])
    y = random.randint(0, im.size[1] - cat_image.size[1])

    im.paste(cat_image, (x, y), cat_image)

    f = cStringIO.StringIO()
    im.save(f, "JPEG")
    content = f.getvalue()
    f.close()

    new_item = {}
    new_item["menuItems"] = [{"action": "SHARE"}]

    result = upload.multipart_insert(new_item, content, "image/jpeg", service, test)
    logging.info(result)
