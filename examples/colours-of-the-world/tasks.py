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

"""Create tasks and evaluate submissions, implemented as taskqueues to work in the background"""

import upload
from auth import get_auth_service
from models import Submission
from utils import base_url

import cStringIO
import Image
import numpy
import logging
import random
import webapp2
from apiclient.errors import HttpError
from google.appengine.ext import ndb
from oauth2client.client import AccessTokenRefreshError

COLORS = {
    "red": {"name": "Red", "hue": 0, "range": 15},
    "orange": {"name": "Orange", "hue": 30, "range": 15},
    "yellow": {"name": "Yellow", "hue": 60, "range": 15},
    "green": {"name": "Green", "hue": 120, "range": 15},
    "blue": {"name": "Blue", "hue": 240, "range": 15},
    "indigo": {"name": "Indigo", "hue": 280, "range": 15},
    "violet": {"name": "Violet", "hue": 320, "range": 15}
}


class CreateTaskWorker(webapp2.RequestHandler):
  """
  Creates a new task for a user
  """
 
  def post(self):
      
    gplus_id = self.request.get("user")
    test = self.request.get("test")
    if test == "":
        test = None

    service = get_auth_service(gplus_id, test)
    if service is None:
        logging.error("User not authenticated")
        return
    
    if test is not None:
        user = ndb.Key("TestUser", gplus_id).get()
    else:
        user = ndb.Key("User", gplus_id).get()
    
    if user is None:
        logging.error("User not found")
        return
        
    col = random.choice(COLORS.keys())
    
    user.currentTask = col
    user.put()
    
    card = {
        "html": ("<article class=\"photo\">"
                 "  <img src=\"" + base_url + "/images/" + col + ".png\" width=\"100%\" height=\"100%\">"
                 "  <div class=\"photo-overlay\"></div>"
                 "  <section>"
                 "    <p class=\"text-auto-size\">Current Task: " + COLORS[col]["name"] + "</p>"
                 "  </section>"
                 "</article>"),
        "menuItems": [
            {
                "action": "CUSTOM",
                "id": "giveup",
                "values": [{
                  "displayName": "Give Up",
                  "iconUrl": "https://mirror-api.appspot.com/glass/images/error.png"
                }]
            },
            {
                "action": "TOGGLE_PINNED"
            }
        ]
    }

    try:
        service.timeline().insert(body=card).execute()
    except AccessTokenRefreshError:
        logging.error("Failed to refresh access token.")
        return
    except HttpError as e:
        logging.error("Failed to execute request. %s" % e)
        return    


class EvaluateWorker(webapp2.RequestHandler):
  """
  Creates a new task for a user
  """
 
  def post(self):
      
    gplus_id = self.request.get("user")
    test = self.request.get("test")
    if test == "":
        test = None

    item_id = self.request.get("item")
    
    service = get_auth_service(gplus_id, test)

    if service is None:
        logging.error("No valid credentials")
        return

    item = service.timeline().get(id=item_id).execute()
    
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
    i = Image.open(tempimg).convert("RGB")
    a = numpy.asarray(i, int)

    R, G, B = a.T

    m = numpy.min(a,2).T
    M = numpy.max(a,2).T

    C = M-m #chroma
    Cmsk = C!=0

    # Hue
    H = numpy.zeros(R.shape, int)
    mask = (M==R)&Cmsk
    H[mask] = numpy.mod(60*(G-B)/C, 360)[mask]
    mask = (M==G)&Cmsk
    H[mask] = (60*(B-R)/C + 120)[mask]
    mask = (M==B)&Cmsk
    H[mask] = (60*(R-G)/C + 240)[mask]

    # Value
    V = M

    # Saturation
    S = numpy.zeros(R.shape, int)
    S[Cmsk] = ((255*C)/V)[Cmsk]
    
    j = Image.fromarray(H)
    f = cStringIO.StringIO()
    j.save(f, "PNG")
    content = f.getvalue()
    f.close()

    new_item = {}
    new_item["menuItems"] = [{"action": "SHARE"}]

    result = upload.multipart_insert(new_item, content, "image/png", service, test)
    logging.info(result)


TASK_ROUTES = [
    ("/tasks/createtask", CreateTaskWorker),
    ("/tasks/evaluate", EvaluateWorker)
]
