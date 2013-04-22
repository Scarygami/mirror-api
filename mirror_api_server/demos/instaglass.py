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

import logging
import Image
import ImageOps
import cStringIO
import re

__all__ = ["handle_item"]


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


def handle_item(item):
    """Callback for Timeline updates."""

    if "recipients" in item:
        for rec in item["recipients"]:
            if rec["id"] == "instaglass_sepia":
                break
        else:
            # Item not meant for this service
            return None
    else:
        # Item not meant for this service
        return None

    image = None
    if "attachments" in item:
        for att in item["attachments"]:
            if att["contentType"].startswith("image/"):
                image = att["contentUrl"]
                break

    if image is None:
        logging.info("No suitable attachment")
        return None

    if not image.startswith("data:image"):
        logging.info("Can only work with data-uri")
        return None

    img_data = re.search(r'base64,(.*)', image).group(1)
    tempimg = cStringIO.StringIO(img_data.decode('base64'))
    im = Image.open(tempimg)
    new_im = _apply_sepia_filter(im)

    f = cStringIO.StringIO()
    new_im.save(f, "JPEG")
    content = f.getvalue()
    f.close()
    data_uri = "data:image/jpeg;base64," + content.encode("base64").replace("\n", "")

    new_item = {}
    new_item["attachments"] = [{"contentType": "image/jpeg", "contentUrl": data_uri}]
    new_item["menuItems"] = [{"action": "SHARE"}]

    return new_item
