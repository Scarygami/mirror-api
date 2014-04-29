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


"""Model definition for the Mirror API."""

import sys
sys.path.insert(1, 'endpoints-proto-datastore')

import endpoints

from google.appengine.ext import ndb
from google.appengine.ext.ndb import msgprop
from protorpc import messages
from protorpc import message_types

from endpoints_proto_datastore.ndb import EndpointsDateTimeProperty
from endpoints_proto_datastore.ndb import EndpointsModel
from endpoints_proto_datastore.ndb import EndpointsUserProperty
from endpoints_proto_datastore.ndb import EndpointsAliasProperty


class MenuAction(messages.Enum):
    REPLY = 1
    REPLY_ALL = 2
    DELETE = 3
    SHARE = 4
    READ_ALOUD = 5
    VOICE_CALL = 6
    NAVIGATE = 7
    TOGGLE_PINNED = 8
    CUSTOM = 9
    VIEW_WEBSITE = 10
    PLAY_VIDEO = 11


class MenuValue(EndpointsModel):

    class MenuValueState(messages.Enum):
        DEFAULT = 1
        PENDING = 2
        CONFIRMED = 3

    displayName = ndb.StringProperty(required=True)
    iconUrl = ndb.StringProperty(required=True)
    state = msgprop.EnumProperty(MenuValueState)


class MenuItem(EndpointsModel):
    action = msgprop.EnumProperty(MenuAction, required=True)
    id = ndb.StringProperty()
    payload = ndb.StringProperty()
    removeWhenSelected = ndb.BooleanProperty(default=False)
    values = ndb.LocalStructuredProperty(MenuValue, repeated=True)


class Location(EndpointsModel):
    """Model for location"""

    _latest = False

    _message_fields_schema = (
        "id",
        "timestamp",
        "latitude",
        "longitude",
        "accuracy",
        "displayName",
        "address"
    )

    user = EndpointsUserProperty(required=True, raise_unauthorized=True)
    timestamp = EndpointsDateTimeProperty(auto_now_add=True)
    latitude = ndb.FloatProperty()
    longitude = ndb.FloatProperty()
    accuracy = ndb.FloatProperty()
    displayName = ndb.StringProperty()
    address = ndb.StringProperty()

    def IdSet(self, value):
        if not isinstance(value, basestring):
            raise TypeError("ID must be a string.")

        if value == "latest":
            self._latest = True
            loc_query = Location.query().order(-Location.timestamp)
            loc_query = loc_query.filter(Location.user == self.user)
            loc = loc_query.get()
            if loc is not None:
                self.UpdateFromKey(loc.key)
            return

        if value.isdigit():
            self.UpdateFromKey(ndb.Key(Location, int(value)))

    @EndpointsAliasProperty(setter=IdSet, required=False)
    def id(self):
        if self._latest:
            return "latest"
        if self.key is not None:
            return str(self.key.integer_id())


class TimelineItem(EndpointsModel):
    """Model for timeline cards.

    Since the created property is auto_now_add=True, Cards will document when
    they were inserted immediately after being stored.
    """

    class Attachment(EndpointsModel):
        """Represents media content, such as a photo, that can be attached to a timeline item."""
        id = ndb.StringProperty()
        contentType = ndb.StringProperty()
        contentUrl = ndb.StringProperty()
        isProcessingContent = ndb.BooleanProperty(default=False)

    class TimelineContact(EndpointsModel):
        """A person or group that can be used as a creator or a contact."""

        class ContactType(messages.Enum):
            INDIVIDUAL = 1
            GROUP = 2

        acceptTypes = ndb.StringProperty(repeated=True)
        displayName = ndb.StringProperty()
        id = ndb.StringProperty(required=True)
        imageUrls = ndb.StringProperty(repeated=True)
        phoneNumber = ndb.StringProperty()
        source = ndb.StringProperty()
        type = msgprop.EnumProperty(ContactType)

    class Notification(EndpointsModel):

        level = ndb.StringProperty(default="DEFAULT")
        deliveryTime = EndpointsDateTimeProperty()

    _message_fields_schema = (
        "id",
        "attachments",
        "bundleId",
        "canonicalUrl",
        "created",
        "creator",
        "displayTime",
        "html",
        "inReplyTo",
        "isBundleCover",
        "isDeleted",
        "isPinned",
        "location",
        "menuItems",
        "notification",
        "pinScore",
        "recipients",
        "sourceItemId",
        "speakableText",
        "speakableType",
        "text",
        "title",
        "updated"
    )

    user = EndpointsUserProperty(required=True, raise_unauthorized=True)

    attachments = ndb.LocalStructuredProperty(Attachment, repeated=True)
    bundleId = ndb.StringProperty()
    canonicalUrl = ndb.StringProperty()
    created = EndpointsDateTimeProperty(auto_now_add=True)
    creator = ndb.LocalStructuredProperty(TimelineContact)
    displayTime = EndpointsDateTimeProperty()
    html = ndb.TextProperty()
    inReplyTo = ndb.IntegerProperty()
    isBundleCover = ndb.BooleanProperty()
    isDeleted = ndb.BooleanProperty()
    isPinned = ndb.BooleanProperty()
    location = ndb.LocalStructuredProperty(Location)
    menuItems = ndb.LocalStructuredProperty(MenuItem, repeated=True)
    notification = ndb.LocalStructuredProperty(Notification)
    pinScore = ndb.IntegerProperty()
    recipients = ndb.LocalStructuredProperty(TimelineContact, repeated=True)
    sourceItemId = ndb.StringProperty()
    speakableText = ndb.TextProperty()
    speakableType = ndb.TextProperty()
    text = ndb.StringProperty()
    title = ndb.StringProperty()
    updated = EndpointsDateTimeProperty(auto_now=True)

    def IncludeDeletedSet(self, value):
        """
        If value is true all timelineItems will be returned.
        Otherwise a filter for non-deleted items is necessary for the query.
        """
        if value is None or value is False:
            self._endpoints_query_info._AddFilter(TimelineItem.isDeleted == False)

    @EndpointsAliasProperty(setter=IncludeDeletedSet, property_type=messages.BooleanField, default=False)
    def includeDeleted(self):
        """
        includedDeleted is only used as parameter in query_methods
        so there should never be a reason to actually retrieve the value
        """
        return None

    def PinnedOnlySet(self, value):
        """
        If value is true only pinned timelineItems will be returned.
        Otherwise all timelineItems are returned.
        """
        if value is True:
            self._endpoints_query_info._AddFilter(TimelineItem.isPinned == True)

    @EndpointsAliasProperty(setter=PinnedOnlySet, property_type=messages.BooleanField, default=False)
    def pinnedOnly(self):
        """
        pinnedOnly is only used as parameter in query_methods
        so there should never be a reason to actually retrieve the value
        """
        return None

    def MaxResultsSet(self, value):
        """Setter to be used for default limit EndpointsAliasProperty.

        Simply sets the limit on the entity's query info object, and the query
        info object handles validation.

        Args:
          value: The limit value to be set.
        """
        self._endpoints_query_info.limit = value

    @EndpointsAliasProperty(setter=MaxResultsSet, property_type=messages.IntegerField, default=20)
    def maxResults(self):
        """Getter to be used for default limit EndpointsAliasProperty.

        Uses the ProtoRPC property_type IntegerField since a limit.

        Returns:
          The integer (or null) limit from the query info on the entity.
        """
        return self._endpoints_query_info.limit


class Contact(EndpointsModel):
    """A person or group that can be used as a creator or a contact."""

    class Command(EndpointsModel):

        class CommandType(messages.Enum):
            TAKE_A_NOTE = 1
            POST_AN_UPDATE = 2

        """A single menu command that is part of a Contact."""
        type = msgprop.EnumProperty(CommandType, required=True)

    class ContactType(messages.Enum):
        INDIVIDUAL = 1
        GROUP = 2

    _message_fields_schema = (
        "id",
        "acceptCommands",
        "acceptTypes",
        "displayName",
        "imageUrls",
        "phoneNumber",
        "priority",
        "source",
        "type"
    )

    user = EndpointsUserProperty(required=True, raise_unauthorized=True)

    acceptCommands = ndb.LocalStructuredProperty(Command, repeated=True)
    acceptTypes = ndb.StringProperty(repeated=True)
    displayName = ndb.StringProperty(required=True)
    imageUrls = ndb.StringProperty(repeated=True)
    phoneNumber = ndb.StringProperty()
    priority = ndb.IntegerProperty()
    source = ndb.StringProperty()
    speakableName = ndb.StringProperty()
    type = msgprop.EnumProperty(ContactType)

    def IdSet(self, value):
        if not isinstance(value, basestring):
            raise TypeError("ID must be a string.")

        self.UpdateFromKey(ndb.Key("User", self.user.email(), Contact, value))

    @EndpointsAliasProperty(setter=IdSet, required=True)
    def id(self):
        if self.key is not None:
            return self.key.pairs()[1][1]


class Operation(messages.Enum):
    UPDATE = 1
    INSERT = 2
    DELETE = 3


class Subscription(EndpointsModel):
    """Model for subscriptions"""

    _message_fields_schema = ("id", "collection", "userToken", "verifyToken", "operation", "callbackUrl")

    user = EndpointsUserProperty(required=True, raise_unauthorized=True)
    collection = ndb.StringProperty(required=True)
    userToken = ndb.StringProperty(required=True)
    verifyToken = ndb.StringProperty(required=True)
    operation = msgprop.EnumProperty(Operation, repeated=True)
    callbackUrl = ndb.StringProperty(required=True)


class UserAction(messages.Enum):
    """Represents an action taken by the user that triggers a notification."""
    REPLY = 1
    REPLY_ALL = 2
    DELETE = 3
    SHARE = 4
    PIN = 5
    UNPIN = 6
    LAUNCH = 7
    CUSTOM = 10


class Action(messages.Message):
    """ProtoRPC Message Class for actions performed on timeline cards

    Since those actions are directly forwarded to subscriptions they
    don't need to be saved to the data store, hence no EndpointsModel class
    """

    collection = messages.StringField(1, default="timeline")
    itemId = messages.IntegerField(2, required=True)
    action = messages.EnumField(UserAction, 3, required=True)
    value = messages.StringField(4)


class ActionResponse(messages.Message):
    """Simple response to actions send to the Mirror API"""
    success = messages.BooleanField(1, default=True)


AttachmentListRequest = endpoints.ResourceContainer(
    message_types.VoidMessage,
    itemId=messages.IntegerField(2, required=True))


AttachmentRequest = endpoints.ResourceContainer(
    message_types.VoidMessage,
    itemId=messages.IntegerField(2, required=True),
    attachmentId=messages.StringField(3, required=True))


class AttachmentResponse(messages.Message):
    id = messages.StringField(1)
    contentType = messages.StringField(2)
    contentUrl = messages.StringField(3)
    isProcessingContent = messages.BooleanField(4, default=False)


class AttachmentList(messages.Message):
    items = messages.MessageField(AttachmentResponse, 1, repeated=True)
