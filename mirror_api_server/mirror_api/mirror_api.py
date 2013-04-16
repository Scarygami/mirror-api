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
import logging
import urllib2

from google.appengine.ext import endpoints
from protorpc import remote
from models import TimelineItem
from models import MenuAction
from models import ShareEntity
from models import Subscription
from models import Action
from models import ActionResponse


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

    @TimelineItem.query_method(query_fields=("limit", "pageToken"),
                               user_required=True,
                               path="timeline", name="timeline.list")
    def timeline_list(self, query):
        """List timeline cards for the current user."""

        query = query.order(-TimelineItem.updated)
        return query.filter(TimelineItem.user == endpoints.get_current_user())

    @TimelineItem.method(user_required=True, http_method="POST",
                         path="timeline", name="timeline.insert")
    def timeline_insert(self, card):
        """Insert a card for the current user."""

        if card.id is not None:
            raise endpoints.BadRequestException("ID is not allowed in request body.")

        if card.menuItems is not None:
            for menuItem in card.menuItems:
                if menuItem.action == MenuAction.CUSTOM:
                    if menuItem.id is None:
                        raise endpoints.BadRequestException("For custom actions id needs to be provided.")
                    if menuItem.values is None or len(menuItem.values) == 0:
                        raise endpoints.BadRequestException("For custom actions at least one value needs to be provided.")
                    for value in menuItem.values:
                        if value.displayName is None or value.iconUrl is None:
                            raise endpoints.BadRequestException("Each value needs to contain displayName and iconUrl.")

        card.put()
        return card

    @TimelineItem.method(request_fields=("id",),
                         user_required=True,
                         path="timeline/{id}", http_method="GET",
                         name="timeline.get")
    def timeline_get(self, card):
        """Get card with ID for the current user"""

        if not card.from_datastore or card.user != endpoints.get_current_user():
            raise endpoints.NotFoundException("Card not found.")
        return card

    @TimelineItem.method(user_required=True,
                         path="timeline/{id}", http_method="PUT",
                         name="timeline.update")
    def timeline_update(self, card):
        """Update card with ID for the current user"""

        if not card.from_datastore or card.user != endpoints.get_current_user():
            raise endpoints.NotFoundException("Card not found.")

        card.put()
        return card

    @ShareEntity.query_method(query_fields=("limit", "pageToken"),
                              user_required=True,
                              path="shareEntities", name="shareEntities.list")
    def shareEntities_list(self, query):
        """List all Share entities registered for the current user.

        This isn't part of the actual Mirror API but necessary for the emulator part
        to be able to display relevant Share options.
        """

        return query.filter(ShareEntity.user == endpoints.get_current_user())

    @ShareEntity.method(user_required=True,
                        path="shareEntities", name="shareEntities.insert")
    def shareEntities_insert(self, shareEntity):
        """Insert a new ShareEntity for the current user."""

        if shareEntity.id is None:
            raise endpoints.BadRequestException("ID needs to be provided.")
        if shareEntity.displayName is None:
            raise endpoints.BadRequestException("displayName needs to be provided.")
        if shareEntity.imageUrls is None or len(shareEntity.imageUrls) == 0:
            raise endpoints.BadRequestException("At least one imageUrl needs to be provided.")

        if shareEntity.from_datastore:
            name = shareEntity.key.string_id()
            raise endpoints.BadRequestException("ShareEntity with name %s already exists." % name)

        shareEntity.put()
        return shareEntity

    @ShareEntity.method(request_fields=("id",),
                        response_fields=("id",),
                        user_required=True,
                        path="shareEntities/{id}", http_method="DELETE",
                        name="shareEntities.delete")
    def shareEntities_delete(self, shareEntity):
        """Remove an existing ShareEntity for the current user."""

        if not shareEntity.from_datastore or shareEntity.user != endpoints.get_current_user():
            raise endpoints.NotFoundException("shareEntity not found.")

        shareEntity.key.delete()

        # TODO: Check if a success HTTP code can be returned with an empty body
        return shareEntity

    @Subscription.method(user_required=True, http_method="POST",
                         path="subscriptions", name="subscriptions.insert")
    def subscription_insert(self, subscription):
        """Insert a new subscription for the current user."""

        if subscription.id is not None:
            raise endpoints.BadRequestException("ID is not allowed in request body.")

        if subscription.operation is None or len(subscription.operation) == 0:
            raise endpoints.BadRequestException("At least one operation needs to be provided.")

        subscription.put()
        return subscription

    @Subscription.method(request_fields=("id",),
                         response_fields=("id",),
                         user_required=True,
                         path="subscriptions/{id}", http_method="DELETE",
                         name="subscriptions.delete")
    def subscription_delete(self, subscription):
        """Remove an existing subscription for the current user."""

        if not subscription.from_datastore or subscription.user != endpoints.get_current_user():
            raise endpoints.NotFoundException("Card not found.")

        subscription.key.delete()

        # TODO: Check if a success HTTP code can be returned with an empty body
        return subscription

    @endpoints.method(Action, ActionResponse,
                      path='actions', http_method='POST',
                      name='actions.insert')
    def action_insert(self, action):
        """Perform an action on a timeline card for the current user.

        This isn't part of the actual Mirror API but necessary for the emulator
        to send actions to the subscribed services.

        Returns just a simple success message
        """

        current_user = endpoints.get_current_user()
        if current_user is None:
            raise endpoints.UnauthorizedException('Authentication required.')

        # TODO: check if card exists and belongs to the user

        data = {}
        data["collection"] = action.collection
        data["operation"] = action.operation.name
        data["itemId"] = action.itemId
        data["value"] = action.value

        header = {"Content-type": "application/json"}

        query = Subscription.query().filter(Subscription.user == current_user).filter(Subscription.operation == action.operation)
        for subscription in query.fetch():
            data["userToken"] = subscription.userToken
            data["verifyToken"] = subscription.verifyToken

            req = urllib2.Request(subscription.callbackUrl, json.dumps(data), header)
            try:
                urllib2.urlopen(req)
            except urllib2.URLError as e:
                logging.error(e)

        return ActionResponse(success=True)
