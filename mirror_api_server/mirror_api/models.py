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


"""Helper model class for the Mirror API.

Defines models for persisting and querying score data on a per user basis and
provides a method for returning a 401 Unauthorized when no current user can be
determined.
"""


from google.appengine.ext import endpoints
from google.appengine.ext import ndb

from timeline import Card


TIME_FORMAT_STRING = '%Y-%m-%d %H:%M'


def get_endpoints_current_user(raise_unauthorized=True):
    """Returns a current user and (optionally) causes an HTTP 401 if no user.

    Args:
        raise_unauthorized: Boolean; defaults to True. If True, this method
            raises an exception which causes an HTTP 401 Unauthorized to be
            returned with the request.

    Returns:
        The signed in user if there is one, else None if there is no signed in
        user and raise_unauthorized is False.
    """
    current_user = endpoints.get_current_user()
    if raise_unauthorized and current_user is None:
        raise endpoints.UnauthorizedException('Invalid token.')
    return current_user


class DBCard(ndb.Model):
    """Model to timeline cards.

    Since the when property is auto_now_add=True, Scores will document when
    they were inserted immediately after being stored.
    """
    text = ndb.StringProperty()
    html = ndb.StringProperty()
    when = ndb.DateTimeProperty(auto_now_add=True)
    user = ndb.UserProperty(required=True)

    @property
    def timestamp(self):
        """Property to format a datetime object to string."""
        return self.when.strftime(TIME_FORMAT_STRING)

    def to_message(self):
        """Turns the CardDB entity into a ProtoRPC object.

        This is necessary so the entity can be returned in an API request.

        Returns:
            An instance of Card with the ID set to the datastore ID of the current entity.
        """
        return Card(id=self.key.id(),
                    when=self.timestamp,
                    text=self.text,
                    html=self.html)

    @classmethod
    def put_from_message(cls, message):
        """Gets the current user and inserts a new card.

        Args:
            message: A Card instance to be inserted.

        Returns:
            The DBCard entity that was inserted.
        """
        current_user = get_endpoints_current_user()
        entity = cls(text=message.text, html=message.html, user=current_user)
        entity.put()
        return entity

    @classmethod
    def query_current_user(cls):
        """Creates a query for the cards of the current user.

        Returns:
            An ndb.Query object bound to the current user. This can be used
            to filter for other properties or order by them.
        """
        current_user = get_endpoints_current_user()
        return cls.query(cls.user == current_user)
