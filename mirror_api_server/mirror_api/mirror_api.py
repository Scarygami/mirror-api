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

import monkey_patch

import json
import os
import logging
import urllib2

from google.appengine.api import channel
from google.appengine.ext import endpoints
from protorpc import remote

from models import TimelineItem
from models import MenuAction
from models import Operation
from models import Contact
from models import Subscription
from models import Action
from models import ActionResponse
from models import Location


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
    """Class which defines the Mirror API v1."""

    @TimelineItem.query_method(query_fields=("limit", "pageToken", "bundleId", "includeDeleted", "pinnedOnly", "sourceItemId"),
                               user_required=True,
                               path="timeline", name="timeline.list")
    def timeline_list(self, query):
        """List timeline cards for the current user."""

        query = query.order(-TimelineItem.updated)
        query = query.filter(TimelineItem.user == endpoints.get_current_user())
        return query

    @TimelineItem.method(request_fields=("id",),
                         user_required=True,
                         path="timeline/{id}", http_method="GET",
                         name="timeline.get")
    def timeline_get(self, card):
        """Get card with ID for the current user"""

        if not card.from_datastore or card.user != endpoints.get_current_user():
            raise endpoints.NotFoundException("Card not found.")

        return card

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

        if card.htmlPages is not None and len(card.htmlPages) > 0 and card.bundleId is not None:
            raise endpoints.BadRequestException("Can't mix HTML and Card bundle.")

        # TODO: Temporary fix until default values are fixed
        card.isDeleted = False

        card.put()

        channel.send_message(card.user.email(), json.dumps({"id": card.id}))

        return card

    @TimelineItem.method(user_required=True,
                         path="timeline/{id}", http_method="PUT",
                         name="timeline.update")
    def timeline_update(self, card):
        """Update card with ID for the current user"""

        if not card.from_datastore or card.user != endpoints.get_current_user():
            raise endpoints.NotFoundException("Card not found.")

        if card.isDeleted:
            raise endpoints.NotFoundException("Card has been deleted")

        if card.htmlPages is not None and len(card.htmlPages) > 0 and card.bundleId is not None:
            raise endpoints.BadRequestException("Can't mix HTML and Card bundle.")

        card.put()

        channel.send_message(card.user.email(), json.dumps({"id": card.id}))

        return card

    @TimelineItem.method(request_fields=("id",),
                         response_fields=("id",),
                         user_required=True,
                         path="timeline/{id}", http_method="DELETE",
                         name="timeline.delete")
    def timeline_delete(self, card):
        """Remove an existing card for the current user.

        This will set all properties except the ID to None and set isDeleted to true
        """

        if not card.from_datastore or card.user != endpoints.get_current_user():
            raise endpoints.NotFoundException("Contact not found.")

        if card.isDeleted:
            raise endpoints.NotFoundException("Card has been deleted")

        card.attachments = []
        card.bundleId = None
        card.canonicalUrl = None
        card.created = None
        card.displayTime = None
        card.html = None
        card.htmlPages = []
        card.inReplyTo = None
        card.isBundleCover = None
        card.isPinned = None
        card.menuItems = []
        card.recipients = []
        card.sourceItemId = None
        card.speakableText = None
        card.text = None
        card.title = None
        card.updated = None
        card.isDeleted = True
        card.put()

        # Notify Glass emulator
        channel.send_message(card.user.email(), json.dumps({"id": card.id}))

        # TODO: Notify subscriptions

        return card

    @Contact.query_method(query_fields=("limit", "pageToken"),
                          user_required=True,
                          path="contacts", name="contacts.list")
    def contacts_list(self, query):
        """List all Contacts registered for the current user."""

        return query.filter(Contact.user == endpoints.get_current_user())

    @Contact.method(user_required=True,
                    path="contacts", name="contacts.insert")
    def contacts_insert(self, contact):
        """Insert a new Contact for the current user."""

        if contact.id is None:
            raise endpoints.BadRequestException("ID needs to be provided.")
        if contact.displayName is None:
            raise endpoints.BadRequestException("displayName needs to be provided.")
        if contact.imageUrls is None or len(contact.imageUrls) == 0:
            raise endpoints.BadRequestException("At least one imageUrl needs to be provided.")

        if contact.from_datastore:
            return contact

        contact.put()
        return contact

    @Contact.method(request_fields=("id",),
                    response_fields=("id",),
                    user_required=True,
                    path="contacts/{id}", http_method="DELETE",
                    name="contacts.delete")
    def contacts_delete(self, contact):
        """Remove an existing Contact for the current user."""

        if not contact.from_datastore or contact.user != endpoints.get_current_user():
            raise endpoints.NotFoundException("Contact not found.")

        contact.key.delete()

        # TODO: Check if a success HTTP code can be returned with an empty body
        return contact

    @Contact.method(user_required=True,
                    path="contacts/{id}", http_method="PUT",
                    name="contacts.update")
    def contacts_update(self, contact):
        """Update Contact with ID for the current user"""

        if not contact.from_datastore or contact.user != endpoints.get_current_user():
            raise endpoints.NotFoundException("Card not found.")

        contact.put()
        return contact

    @Subscription.query_method(query_fields=("limit", "pageToken"),
                               user_required=True,
                               path="subscriptions", name="subscriptions.list")
    def subscriptions_list(self, query):
        """List all Subscriptions registered for the current user."""

        return query.filter(Contact.user == endpoints.get_current_user())

    @Subscription.method(user_required=True, http_method="POST",
                         path="subscriptions", name="subscriptions.insert")
    def subscription_insert(self, subscription):
        """Insert a new subscription for the current user."""

        if subscription.id is not None:
            raise endpoints.BadRequestException("ID is not allowed in request body.")

        if subscription.operation is None or len(subscription.operation) == 0:
            subscription.operation = [Operation.UPDATE, Operation.INSERT, Operation.DELETE]

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

    @Location.query_method(query_fields=("limit", "pageToken"),
                           user_required=True,
                           path="locations", name="locations.list")
    def locations_list(self, query):
        """List locations for the current user."""

        query = query.order(-Location.timestamp)
        return query.filter(TimelineItem.user == endpoints.get_current_user())

    @Location.method(request_fields=("id",),
                     user_required=True,
                     path="locations/{id}", http_method="GET",
                     name="locations.get")
    def locations_get(self, location):
        """Retrieve a single location for the current user.

        ID can be a specific location ID or "latest" to retrieve the
        latest known position of the user.
        """

        if not location.from_datastore or location.user != endpoints.get_current_user():
            raise endpoints.NotFoundException("Location not found.")

        return location

    @Location.method(user_required=True, http_method="POST",
                     path="locations", name="locations.insert")
    def locations_insert(self, location):
        """Insert a new location for the current user.

        Not part of the actual mirror API but used by the emulator.
        """

        if location.id is not None:
            raise endpoints.BadRequestException("ID is not allowed in request body.")

        location.put()

        # Notify location subscriptions

        data = {}
        data["collection"] = "locations"
        data["itemId"] = "latest"
        operation = Operation.UPDATE
        data["operation"] = operation.name

        header = {"Content-type": "application/json"}

        query = Subscription.query().filter(Subscription.user == endpoints.get_current_user())
        query = query.filter(Subscription.collection == "locations")
        query = query.filter(Subscription.operation == operation)
        for subscription in query.fetch():
            data["userToken"] = subscription.userToken
            data["verifyToken"] = subscription.verifyToken

            req = urllib2.Request(subscription.callbackUrl, json.dumps(data), header)
            try:
                urllib2.urlopen(req)
            except urllib2.URLError as e:
                logging.error(e)

        return location

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

        data = None
        operation = None

        if action.action == MenuAction.SHARE:
            operation = Operation.UPDATE
            data = {}
            data["collection"] = "timeline"
            data["itemId"] = action.itemId
            data["operation"] = operation.name
            data["userActions"] = ({"type": MenuAction.SHARE.name},)

        if action.action == MenuAction.REPLY or action.action == MenuAction.REPLY_ALL:
            operation = Operation.INSERT
            data = {}
            data["collection"] = "timeline"
            data["itemId"] = action.itemId
            data["operation"] = operation.name
            data["userActions"] = ({"type": MenuAction.REPLY.name},)

        if action.action == MenuAction.DELETE:
            operation = Operation.DELETE
            data = {}
            data["collection"] = "timeline"
            data["itemId"] = action.itemId
            data["operation"] = operation.name
            data["userActions"] = ({"type": MenuAction.DELETE.name},)

        if action.action == MenuAction.CUSTOM:
            operation = Operation.UPDATE
            data = {}
            data["collection"] = "timeline"
            data["itemId"] = action.itemId
            data["operation"] = operation.name
            data["userActions"] = ({"type": MenuAction.DELETE.name, "payload": action.value},)

        if data is not None and operation is not None:
            header = {"Content-type": "application/json"}

            query = Subscription.query().filter(Subscription.user == current_user)
            query = query.filter(Subscription.collection == "timeline")
            query = query.filter(Subscription.operation == operation)
            for subscription in query.fetch():
                data["userToken"] = subscription.userToken
                data["verifyToken"] = subscription.verifyToken

                req = urllib2.Request(subscription.callbackUrl, json.dumps(data), header)
                try:
                    urllib2.urlopen(req)
                except urllib2.URLError as e:
                    logging.error(e)

        return ActionResponse(success=True)
