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

from service import upload
from utils import base_url

import logging
import Image
import ImageOps
import cStringIO

__all__ = ["handle_item", "CONTACTS", "WELCOMES"]

"""Contacts that need to registered when the user connects to this service"""
CONTACTS = [
    {
        "acceptTypes": "image/*",
        "id": "instaglass_sepia",
        "displayName": "Sepia",
        "imageUrls": [base_url + "/images/sepia.jpg"]
    }
]

"""Welcome message cards that are sent when the user first connects to this service"""
WELCOMES = [
    {
        "html": ("<article class=\"photo\">"
                 "  <img src=\"" + base_url + "/images/sepia.jpg\" width=\"100%\" height=\"100%\">"
                 "  <div class=\"photo-overlay\"></div>"
                 "  <section>"
                 "    <p class=\"text-auto-size\">Welcome to Instaglass!</p>"
                 "  </section>"
                 "</article>")
    }
]


def _make_linear_ramp(white):
    """ generate a palette in a format acceptable for `putpalette`, which
        expects [r,g,b,r,g,b,...]
    """
    ramp = []
    r, g, b = white
    for i in range(255):
        ramp.extend((r*i/255, g*i/255, b*i/255))
    return ramp


def _apply_sepia_filter(image):
    """ Apply a sepia-tone filter to the given PIL Image
        Based on code at: http://effbot.org/zone/pil-sepia.htm
    """
    # make sepia ramp (tweak color as necessary)
    sepia = _make_linear_ramp((255, 240, 192))

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
            if rec["id"] == "instaglass_sepia":
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
    new_im = _apply_sepia_filter(im)

    f = cStringIO.StringIO()
    new_im.save(f, "JPEG")
    content = f.getvalue()
    f.close()

    new_item = {}
    new_item["menuItems"] = [{"action": "SHARE"}]

    result = upload.multipart_insert(new_item, content, "image/jpeg", service, test)
    logging.info(result)
