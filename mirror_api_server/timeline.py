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


"""ProtoRPC message class definitions for the Mirror API."""


from protorpc import messages


class Card(messages.Message):
    """ProtoRPC message definition to represent a timeline card."""
    id = messages.IntegerField(1)
    when = messages.StringField(2)
    text = messages.StringField(3)
    html = messages.StringField(4)


class CardRequest(messages.Message):
    id = messages.IntegerField(1, required=True)


class CardListRequest(messages.Message):
    limit = messages.IntegerField(1, default=10)


class CardList(messages.Message):
    items = messages.MessageField(Card, 1, repeated=True)
