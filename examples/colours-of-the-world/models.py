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

"""Datastore models for comment tracker"""

__author__ = 'scarygami@gmail.com (Gerwin Sturm)'

from google.appengine.ext import ndb
from oauth2client.appengine import CredentialsNDBProperty

PLUS_POST = 1
YT_POST = 2
PLUS_SEARCH = 3


class Author(ndb.Model):
    """Datastore model for the author of a post or comment"""
    author = ndb.StringProperty()
    author_url = ndb.StringProperty()
    author_image = ndb.StringProperty()


class Comment(ndb.Model):
    """Datastore model for a single comment or search result"""

    id = ndb.StringProperty()
    author = ndb.LocalStructuredProperty(Author)
    posted = ndb.DateTimeProperty()
    link = ndb.StringProperty()
    content = ndb.TextProperty()


class Source(ndb.Model):
    """
    Datastore model to keep track of all sources currently being tracked
    This will contain the sources for all users to prevent duplicate
    requests in case serveral people are tracking the same source.

    When all users remove a source `active` will be set to False to prevent
    unnecessary tracking, but the Source will be kept with its comments
    so people can resume tracking at a later point
    """
    id = ndb.StringProperty()
    type = ndb.IntegerProperty()
    author = ndb.LocalStructuredProperty(Author)
    posted = ndb.DateTimeProperty()
    link = ndb.StringProperty()
    content = ndb.TextProperty()
    comments = ndb.LocalStructuredProperty(Comment, repeated=True)
    active = ndb.BooleanProperty()


class User(ndb.Model):
    """
    Datastore model to keep all relevant information about a user

    Properties:
        displayName     Name of the user as returned by the Google+ API
        imageUrl        Avatar image of the user as returned by the Google+ API
        verifyToken     Random token generated for each user to check validity of incoming notifications
        credentials     OAuth2 Access and refresh token to be used for requests against the Mirror API
        sources         List of tracked sources
    """

    displayName = ndb.StringProperty()
    imageUrl = ndb.StringProperty()
    verifyToken = ndb.StringProperty()
    credentials = CredentialsNDBProperty()
    sources = ndb.KeyProperty(kind=Source, repeated=True)


class TestUser(User):
    """Separate datastore model to keep credentials for test and real environment separate"""

    _testUser = True
