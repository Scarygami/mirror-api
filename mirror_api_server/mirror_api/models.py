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


from google.appengine.ext import ndb
from google.appengine.ext.ndb import msgprop
from protorpc import messages

from endpoints_proto_datastore.ndb import EndpointsDateTimeProperty
from endpoints_proto_datastore.ndb import EndpointsModel
from endpoints_proto_datastore.ndb import EndpointsUserProperty
from endpoints_proto_datastore.ndb import EndpointsAliasProperty


class CardAction(messages.Enum):
    SHARE = 1
    REPLY = 2
    READ_ALOUD = 3
    CUSTOM = 4


class CardOptionValue(EndpointsModel):
    displayName = ndb.StringProperty(required=True)
    iconUrl = ndb.StringProperty(required=True)


class CardOption(EndpointsModel):
    action = msgprop.EnumProperty(CardAction, required=True)
    id = ndb.StringProperty()
    values = ndb.LocalStructuredProperty(CardOptionValue, repeated=True)


class Card(EndpointsModel):
    """Model for timeline cards.

    Since the when property is auto_now_add=True, Cards will document when
    they were inserted immediately after being stored.
    """
    _message_fields_schema = ("id", "when", "text", "html", "image", "cardOptions")
    text = ndb.StringProperty()
    html = ndb.StringProperty()
    when = EndpointsDateTimeProperty(auto_now_add=True)
    user = EndpointsUserProperty(required=True, raise_unauthorized=True)
    image = ndb.TextProperty()
    cardOptions = ndb.LocalStructuredProperty(CardOption, repeated=True)


class ShareEntity(EndpointsModel):
    """Model for share entities"""

    _message_fields_schema = ("id", "displayName", "imageUrls")

    displayName = ndb.StringProperty(required=True)
    imageUrls = ndb.StringProperty(repeated=True)
    user = EndpointsUserProperty(required=True, raise_unauthorized=True)

    def IdSet(self, value):
        if not isinstance(value, basestring):
            raise TypeError("ID must be a string.")

        self.UpdateFromKey(ndb.Key(ShareEntity, value))

    @EndpointsAliasProperty(setter=IdSet, required=True)
    def id(self):
        if self.key is not None:
            return self.key.string_id()
