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

"""Methods for Check in service"""

from utils import JINJA
from utils import API_KEY
from utils import base_url
from utils import build_service_from_service

import json
import logging
import urllib2
import webapp2

from apiclient.errors import HttpError

__author__ = 'scarygami@gmail.com (Gerwin Sturm)'

__all__ = ["handle_item", "handle_location", "WELCOMES", "ROUTES"]


"""Welcome message cards that are sent when the user first connects to this service"""
WELCOMES = [
    {
        "html": ("<article class=\"photo\">"
                 "  <img src=\"glass://map?w=640&h=360&zoom=1\" width=\"100%\" height=\"100%\">"
                 "  <div class=\"photo-overlay\"></div>"
                 "  <section>"
                 "    <p class=\"text-auto-size\">Welcome to Check-in</p>"
                 "  </section>"
                 "</article>")
    }
]

_BUNDLE_ID = "checkin_service_123"
_ACTION_ID = "CHECKIN"


def handle_location(location, notification, service, test):
    """Callback for Location updates."""

    if not "longitude" in location or not "latitude" in location:
        # Incomplete location information
        return
    
    request_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    request_url += "?sensor=false&key=%s" % API_KEY
    request_url += "&location=%s,%s" % (location["latitude"], location["longitude"])
    request_url += "&radius=1000"
    request_url += "&types=food"

    try:
        places = json.load(urllib2.urlopen(request_url))
    except urllib2.URLError as e:
        # Couldn't retrieve results
        logging.info(e)
        return
        
    if not "results" in places or len(places["results"]) == 0:
        # No data retrieved
        if "status" in places:
            logging.info(places["status"])
        return

    # 1. retrieve current bundle cards and delete non-cover cards
    current_cards = service.timeline().list(bundleId=_BUNDLE_ID).execute()

    bundleCoverId = None
    if "items" in current_cards:
        for card in current_cards["items"]:
            if "isBundleCover" in card and card["isBundleCover"] == True:
                bundleCoverId = card["id"]
                break
               
        for card in current_cards["items"]:
            if bundleCoverId is None or card["id"] != bundleCoverId:
                # delete old cards
                service.timeline().delete(id=card["id"]).execute()
                
    # 2. create or update cover card
    map = "glass://map?w=640&h=360&"
    map += "marker=0;%s,%s" % (location["latitude"], location["longitude"])
    i = 1
    for place in places["results"]:
        map += "&marker=%s;%s,%s" % (i, place["geometry"]["location"]["lat"], place["geometry"]["location"]["lng"])
        i = i + 1
        if i > 10:
            break

    count = i - 1
    html = "<article class=\"photo\">"
    html += "<img src=\"%s\" width=\"100%%\" height=\"100%%\">" % map
    html += "<div class=\"photo-overlay\"></div>"
    html += "<footer><div>%s place%s nearby</div></footer>" % (count, "" if count == 1 else "s")
    html += "</article>"

    if bundleCoverId is None:
        body = {}
        body["html"] = html
        body["bundleId"] = _BUNDLE_ID
        body["isBundleCover"] = True
        result = service.timeline().insert(body=body).execute()
        logging.info(result)
    else:
        result = service.timeline().update(id=bundleCoverId, body={"html": html}).execute()
        logging.info(result)
    
    # 3. create up to 10 detailed cards
    i = 1
    
    checkinAction = {}
    checkinAction["action"] = "CUSTOM"
    checkinAction["id"] = _ACTION_ID
    actionValue = {}
    actionValue["state"] = "DEFAULT"
    actionValue["displayName"] = "Check-in"
    actionValue["iconUrl"] = base_url + "/glass/images/success.png"
    checkinAction["values"] = [actionValue]

    for place in places["results"]:
        body = {}
        map = "glass://map?w=330&h=240&"
        map += "marker=0;%s,%s" % (location["latitude"], location["longitude"])
        map += "&marker=1;%s,%s" % (place["geometry"]["location"]["lat"], place["geometry"]["location"]["lng"])
        html = "<article><figure>"
        
        if "name" in place:
            html += "<div style=\"margin-top: 40px;\"><p class=\"text-small align-center\">%s</p></div>" % place["name"]

        html += "</figure>"
        html += "<section><img src=\"%s\" width=\"330\" height=\"240\"></section></article>" % map
        
        body["html"] = html
        body["bundleId"] = _BUNDLE_ID
        body["isBundleCover"] = False
        body["location"] = {}
        body["location"]["latitude"] = place["geometry"]["location"]["lat"]
        body["location"]["longitude"] = place["geometry"]["location"]["lng"]
        body["sourceItemId"] = place["reference"]
        body["canonicalUrl"] = "%s/checkin/place/%s" % (base_url, place["reference"])
        
        body["menuItems"] = []
        body["menuItems"].append({"action": "NAVIGATE"})
        body["menuItems"].append(checkinAction)
        
        result = service.timeline().insert(body=body).execute()

        i = i + 1
        if i > 10:
            break    

    return

    
def handle_item(item, notification, service, test):
    """Callback for Timeline updates."""

    if "userActions" in notification:
        for action in notification["userActions"]:
            if "type" in action and "payload" in action and action["type"] == "CUSTOM" and action["payload"] == _ACTION_ID:
                break
        else:
            # No appropriate CUSTOM action
            return
    else:
        # No CUSTOM action
        return

    if not "canonicalUrl" in item:
        # No appropriate item
        return
            
    plus = build_service_from_service(service, "plus", "v1")

    body = {}
    body["type"] = "http://schemas.google.com/CheckInActivity"
    body["target"] = {}
    body["target"]["url"] = item["canonicalUrl"]
    
    try:
        result = plus.moments().insert(userId="me", collection="vault", body=body).execute()
        logging.info(result)
    except HttpError as e:
        logging.info(e)


class PlaceHandler(webapp2.RequestHandler):
    """Handler to create dummy pages from Google Places API result,
    so those pages can be added as App Activities"""

    def get(self, place_id):
    
        template = JINJA.get_template("demos/templates/place.html")
        request_url = "https://maps.googleapis.com/maps/api/place/details/json?reference=" + place_id + "&sensor=false&key=" + API_KEY

        try:
            result = json.load(urllib2.urlopen(request_url))
        except urllib2.URLError as e:
            logging.info(e)
            self.response.out.write(template.render({"chk_place": False, "chk_error": True, "error": "Couldn't access Places API"}))
            return

        if "result" in result:
            self.response.out.write(template.render({"chk_place": True, "place": result["result"]}))
        else:
            self.response.out.write(template.render({"chk_place": False, "chk_error": True, "error": result["status"]}))


ROUTES = [(r"/checkin/place/(.+)", PlaceHandler)]
