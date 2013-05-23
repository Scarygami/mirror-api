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
from google.appengine.api import files
from google.appengine.api import taskqueue
from google.appengine.api.images import get_serving_url
from google.appengine.ext import blobstore
from google.appengine.ext import ndb
from oauth2client.client import AccessTokenRefreshError

COLORS = {
    "red": {"name": "Red", "hue": 0, "min": -15, "max": 15},
    "orange": {"name": "Orange", "hue": 30, "min": 15, "max": 45},
    "yellow": {"name": "Yellow", "hue": 60, "min": 40, "max": 90},
    "green": {"name": "Green", "hue": 120, "min": 90, "max": 180},
    "blue": {"name": "Blue", "hue": 240, "min": 180, "max": 260},
    "indigo": {"name": "Indigo", "hue": 280, "min": 250, "max": 310},
    "violet": {"name": "Violet", "hue": 320, "min": 300, "max": 345}
}

SOURCE_ITEM_ID = "colours_of_the_world_task"

class CreateTaskWorker(webapp2.RequestHandler):
    """
    Creates a new task for a user
    """

    def post(self):

        gplus_id = self.request.get("user")
        test = self.request.get("test")
        if test == "" or test == "None":
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
            ],
            "sourceItemId": SOURCE_ITEM_ID
        }

        result = service.timeline().list(sourceItemId=SOURCE_ITEM_ID).execute()
        if "items" in result and len(result["items"]) > 0:
            request = service.timeline().update(id=result["items"][0]["id"], body=card)
        else:
            request = service.timeline().insert(body=card)

        try:
            request.execute()
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
        if test == "" or test == "None":
            test = None

        item_id = self.request.get("item")

        service = get_auth_service(gplus_id, test)

        if service is None:
            logging.error("No valid credentials")
            return

        if test is not None:
            user = ndb.Key("TestUser", gplus_id).get()
        else:
            user = ndb.Key("User", gplus_id).get()            

        if user.currentTask is None:
            logging.info("User has no current task")
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
        content_type = attachment_metadata.get("contentType")
        resp, content = service._http.request(content_url)

        if resp.status != 200:
            logging.info("Couldn't fetch attachment")

        tempimg = cStringIO.StringIO(content)
        i = Image.open(tempimg).convert("RGB").resize((200, 200), Image.ANTIALIAS)
        a = numpy.asarray(i, int)

        R, G, B = a.T

        m = numpy.min(a, 2).T
        M = numpy.max(a, 2).T

        #Chroma
        C = M - m
        Cmsk = C != 0

        # Hue
        H = numpy.zeros(R.shape, int)
        mask = (M == R) & Cmsk
        H[mask] = numpy.mod(60*(G-B)/C, 360)[mask]
        mask = (M == G) & Cmsk
        H[mask] = (60*(B-R)/C + 120)[mask]
        mask = (M == B) & Cmsk
        H[mask] = (60*(R-G)/C + 240)[mask]

        # Value
        V = M

        # Saturation
        S = numpy.zeros(R.shape, int)
        S[Cmsk] = ((255*C)/V)[Cmsk]

        mask = (V > 100) & (S > 100)

        count = {}
        for col in COLORS:
            count[col] = 0
            v1 = COLORS[col]["min"]
            v2 = COLORS[col]["max"]
            if (v1 < 0):
                col_mask = ((H < v2) | (H > 360 + v1)) & mask
            else:
                col_mask = ((H > v1) & (H < v2)) & mask
            Col = numpy.zeros(R.shape, int)
            Col[col_mask] = numpy.ones(R.shape, int)[col_mask]
            count[col] = numpy.count_nonzero(Col)

        sum = 0
        for col in count:
            if count[col] < 1000:
                count[col] = 0
            else:
                sum = sum + count[col]
        
        if sum == 0:
            item["text"] = "No colours recognized."
            service.timeline().update(id=item_id, body=item).execute()
            return

        recognized = []
        correct = False
        task = user.currentTask
        for col in count:
            count[col] = count[col] * 100 / sum
            if count[col] > 40:
                if col == task:
                    correct = True
                    break
                recognized.append(col)

        if correct:
            item["text"] = "Congratulations!"
            service.timeline().update(id=item_id, body=item).execute()
            user.currentTask = None
            user.put()
            
            # Insert submission
            file_name = files.blobstore.create(mime_type=content_type)
            with files.open(file_name, 'a') as f:
                f.write(content)
            files.finalize(file_name)
            blob_key = files.blobstore.get_blob_key(file_name)
            url = get_serving_url(blob_key, secure_url=True, size=640)

            submission = Submission(colour=task,
                                    hue=COLORS[task]["hue"],
                                    blobkey=blob_key,
                                    url=url,
                                    parent=user.key)
            submission.put()
            
            # TODO: Update scores/achievements
            
            # Create next task
            taskqueue.add(url="/tasks/createtask",
                          params={"user": gplus_id, "test": test},
                          method="POST")
        
        else:
            if len(recognized) == 0:
                item["text"] = "No colours recognized."
            else:
                item["text"] = "Recognized " + ", ".join(recognized) + " but your current task is " + user.currentTask

            service.timeline().update(id=item_id, body=item).execute()


TASK_ROUTES = [
    ("/tasks/createtask", CreateTaskWorker),
    ("/tasks/evaluate", EvaluateWorker)
]
