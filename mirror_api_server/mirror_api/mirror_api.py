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
from google.appengine.ext import endpoints
from protorpc import remote

from models import DBCard
from timeline import Card
from timeline import CardRequest
from timeline import CardListRequest
from timeline import CardList


CLIENT_ID = json.loads(open("client_secrets.json", "r").read())["web"]["client_id"]


@endpoints.api(name="mirror", version="v1",
               description="Mirror API implemented using Google Cloud Endpoints for testing",
               allowed_client_ids=[CLIENT_ID, endpoints.API_EXPLORER_CLIENT_ID])
class MirrorApi(remote.Service):
    """Class which defines Mirror API v1."""

    @endpoints.method(CardListRequest, CardList,
                      path="timeline", http_method="GET",
                      name="timeline.list")
    def timeline_list(self, request):
        """List timeline cards for the current user.

        Args:
            request: An instance of CardListRequest parsed from the API request.

        Returns:
            An instance of CardList containing the cards for the
            current user returned in the query.
        """
        query = DBCard.query_current_user()
        query = query.order(-DBCard.when)
        items = [entity.to_message() for entity in query.fetch(request.limit)]
        return CardList(items=items)

    @endpoints.method(Card, Card,
                      path="timeline", http_method="POST",
                      name="timeline.insert")
    def timeline_insert(self, request):
        """Insert a card for the current user.

        Args:
            request: An instance of Card parsed from the API request.

        Returns:
            An instance of Card containing the information inserted,
            the time the card was inserted and the ID of the card.
        """
        entity = DBCard.put_from_message(request)
        return entity.to_message()

    @endpoints.method(CardRequest, Card,
                      path="timeline/{id}", http_method="GET",
                      name="timeline.get")
    def timeline_get(self, request):
        """Get card with ID for the current user

        Args:
            request: An instance of CardRequest parsed from the API request.

        Returns:
            An instance of Card requested.
        """
        entity = DBCard.get_by_id(request.id)
        return entity.to_message()
