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


class CardAction(messages.Enum):
    SHARE = 1
    REPLY = 2


class CardOption(EndpointsModel):
    action = msgprop.EnumProperty(CardAction)


class Card(EndpointsModel):
    """Model to timeline cards.

    Since the when property is auto_now_add=True, Cards will document when
    they were inserted immediately after being stored.
    """
    _message_fields_schema = ("id", "when", "text", "html", "image", "cardOptions")
    text = ndb.StringProperty()
    html = ndb.StringProperty()
    when = EndpointsDateTimeProperty(auto_now_add=True)
    user = EndpointsUserProperty(required=True, raise_unauthorized=True)
    image = ndb.BlobProperty()
    cardOptions = ndb.StructuredProperty(CardOption, repeated=True)
