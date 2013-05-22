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


class User(ndb.Model):
    """
    Datastore model to keep all relevant information about a user

    Properties:
        displayName     Name of the user as returned by the Google+ API
        imageUrl        Avatar image of the user as returned by the Google+ API
        verifyToken     Random token generated for each user to check validity of incoming notifications
        credentials     OAuth2 Access and refresh token to be used for requests against the Mirror API
        sources         List of tracked sources
        currentTask     Colour
    """

    displayName = ndb.StringProperty()
    imageUrl = ndb.StringProperty()
    verifyToken = ndb.StringProperty()
    credentials = CredentialsNDBProperty()
    currentTask = ndb.StringProperty()


class TestUser(User):
    """Separate datastore model to keep credentials for test and real environment separate"""

    _testUser = True

    
class Submission(ndb.Model):
    """
    Datastore model for a submission for one of the tasks
    
    Properties:
        colour   Colour for which the submission was meant
        hue      Hue value of the colour for sorting
        blobkey  Reference to the image in blobstore
        url      Public serving url for the image in blobstore
        date     Submission date
    """
    
    colour = ndb.StringProperty()
    hue = ndb.IntegerProperty()
    blobkey = ndb.BlobKeyProperty()
    url = ndb.StringProperty()
    date = ndb.DateTimeProperty(auto_now_add=True)
