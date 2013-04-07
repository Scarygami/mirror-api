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


"""Mirror API implemented using Google Cloud Endpoints."""


import json
import os

from google.appengine.ext import endpoints
from protorpc import remote
from models import Card
from models import CardAction


_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SECRETS_PATH = os.path.join(_ROOT_DIR, "client_secrets.json")
with open(_SECRETS_PATH, "r") as fh:
    CLIENT_ID = json.load(fh)["web"]["client_id"]
API_DESCRIPTION = ("Mirror API implemented using Google Cloud "
                   "Endpoints for testing")


@endpoints.api(name="mirror", version="v1",
               description=API_DESCRIPTION,
               allowed_client_ids=[CLIENT_ID, endpoints.API_EXPLORER_CLIENT_ID])
class MirrorApi(remote.Service):
    """Class which defines Mirror API v1."""

    @Card.query_method(query_fields=("limit", "pageToken"),
                       user_required=True,
                       path="timeline", name="timeline.list")
    def timeline_list(self, query):
        """List timeline cards for the current user.

        Args:
            query: An ndb Query object for Cards.

        Returns:
            An update ndb Query object for the current user.
        """
        query = query.order(-Card.when)
        return query.filter(Card.user == endpoints.get_current_user())

    @Card.method(user_required=True,
                 path="timeline", name="timeline.insert")
    def timeline_insert(self, card):
        """Insert a card for the current user.

        Args:
            card: An instance of Card parsed from the API request.

        Returns:
            An instance of Card containing the information inserted,
            the time the card was inserted and the ID of the card.
        """

        if card.cardOptions is not None:
            for cardOption in card.cardOptions:
                if cardOption.action == CardAction.CUSTOM:
                    if cardOption.id is None:
                        raise endpoints.BadRequestException('For custom actions id needs to be provided.')
                    if cardOption.values is None or len(cardOption.values) == 0:
                        raise endpoints.BadRequestException('For custom actions at least one value needs to be provided.')
                    for value in cardOption.values:
                        if value.displayName is None or value.iconUrl is None:
                            raise endpoints.BadRequestException('Each value needs to contain displayName and iconUrl.')

        card.put()
        return card

    @Card.method(request_fields=('id',),
                 user_required=True,
                 path="timeline/{id}", http_method="GET",
                 name="timeline.get")
    def timeline_get(self, card):
        """Get card with ID for the current user

        Args:
            card: An instance of Card parsed from the API request.

        Returns:
            An instance of Card requested.
        """
        if not card.from_datastore or card.user != endpoints.get_current_user():
            raise endpoints.NotFoundException('Card not found.')
        return card
