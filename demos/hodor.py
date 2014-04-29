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

"""Methods for Hodor service"""

__author__ = 'scarygami@gmail.com (Gerwin Sturm)'

from utils import base_url

import logging
import random

__all__ = ["handle_item", "CONTACTS", "WELCOMES"]

"""Contacts that need to registered when the user connects to this service"""
CONTACTS = [
    {
        "id": "hodor",
        "displayName": "Hodor",
        "imageUrls": [base_url + "/images/hodor.jpg"],
        "acceptCommands": [{
            "type": "POST_AN_UPDATE"
        }]
    }
]

"""
Welcome message cards that are sent when the user first connects
to this service
"""
WELCOMES = [
    {
        "html": ("<article class=\"photo\">"
                 "  <img src=\"" + base_url + "/images/hodor.jpg\""
                 "       width=\"100%\" height=\"100%\">"
                 "  <div class=\"photo-overlay\"></div>"
                 "  <section>"
                 "    <p class=\"text-auto-size\">Hodor!</p>"
                 "  </section>"
                 "</article>"),
        "menuItems": [{
            "action": "REPLY"
        }],
        "creator": {
            "id": "hodor"
        }
    }
]

"""
Possible responses to messages
"""
RESPONSES = [
    {
        "text": "Hodor!",
        "image": "hodor1.jpg"
    },
    {
        "text": "Hodor?",
        "image": "hodor2.jpg"
    },
    {
        "text": "Hodor...",
        "image": "hodor3.jpg"
    },
    {
        "text": "Hodor.",
        "image": "hodor4.jpg"
    },
]


def handle_item(item, notification, service, test):
    """Callback for Timeline updates."""

    if "userActions" in notification:
        for action in notification["userActions"]:
            if ("type" in action and
               (action["type"] == "LAUNCH" or action["type"] == "REPLY")):
                break
        else:
            # No SHARE action
            return
    else:
        # No SHARE action
        return

    if "recipients" in item:
        for rec in item["recipients"]:
            if rec["id"] == "hodor":
                break
        else:
            # Item not meant for this service
            return
    else:
        # Item not meant for this service
        return

    hodor = random.randint(0, len(RESPONSES) - 1)

    response = {
        "html": ("<article class=\"photo\">"
                 "  <img src=\"" + base_url + "/images/" + RESPONSES[hodor]["image"] + "\""
                 "       width=\"100%\" height=\"100%\">"
                 "  <div class=\"photo-overlay\"></div>"
                 "  <section>"
                 "    <p class=\"text-auto-size\">" + RESPONSES[hodor]["text"] + "</p>"
                 "  </section>"
                 "</article>"),
        "menuItems": [{
            "action": "REPLY"
        }],
        "creator": {
            "id": "hodor"
        }
    }

    if "inReplyTo" in item:
        result = service.timeline().update(id=item["inReplyTo"], body=response).execute()
    else:
        result = service.timeline().insert(body=response).execute()
    logging.info(result)

    # Delete reply card
    result = service.timeline().delete(id=item["id"]).execute()
