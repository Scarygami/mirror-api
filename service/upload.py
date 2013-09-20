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

"""Helper functions to upload mediacontent to cards"""

__author__ = 'scarygami@gmail.com (Gerwin Sturm)'

from utils import base_url

import io
import json
import logging

from apiclient import errors
from apiclient.http import MediaIoBaseUpload

_BOUNDARY = "-----1234567890abc"


def _create_multipart_body(metadata, content, contentType):
    base64_data = content.encode("base64").replace("\n", "")
    multipart_body = "\r\n--" + _BOUNDARY + "\r\n"
    multipart_body += "Content-Type: application/json\r\n\r\n"
    multipart_body += json.dumps(metadata)
    multipart_body += "\r\n--" + _BOUNDARY + "\r\n"
    multipart_body += "Content-Type: " + contentType + "\r\n"
    multipart_body += "Content-Transfer-Encoding: base64\r\n\r\n"
    multipart_body += base64_data
    multipart_body += "\r\n\r\n--" + _BOUNDARY + "--"

    return multipart_body


def multipart_insert(metadata, content, contentType, service, test):

    if metadata is None:
        metadata = {}

    """Insert a new card with metainfo card and media."""
    if test is None:
        # Using the functionality of the API Client library to directly send multipart request
        media = MediaIoBaseUpload(io.BytesIO(content), contentType, resumable=True)
        try:
            return service.timeline().insert(body=metadata, media_body=media).execute()
        except errors.HttpError, error:
            logging.error("Multipart update error: %s" % error)
            return error

    # Constructing the multipart upload for test environement
    multipart_body = _create_multipart_body(metadata, content, contentType)

    headers = {}
    headers["Content-Type"] = "multipart/related; boundary=\"" + _BOUNDARY + "\""

    return service._http.request(base_url + "/upload/mirror/v1/timeline", method="POST", body=multipart_body, headers=headers)


def multipart_update(cardId, metadata, content, contentType, service, test):

    if metadata is None:
        metadata = {}

    """Update a card with metainfo and media."""
    if test is None:
        # Using the functionality of the API Client library to directly send multipart request
        media = MediaIoBaseUpload(io.BytesIO(content), contentType, resumable=True)
        try:
            return service.timeline().update(id=cardId, body=metadata, media_body=media).execute()
        except errors.HttpError, error:
            logging.error("Multipart update error: %s" % error)
            return error

    # Constructing the multipart upload for test environement
    multipart_body = _create_multipart_body(metadata, content, contentType)

    headers = {}
    headers["Content-Type"] = "multipart/related; boundary=\"" + _BOUNDARY + "\""

    return service._http.request("%s/upload/mirror/v1/timeline/%s" % (base_url, cardId), method="POST", body=multipart_body, headers=headers)


def media_insert(cardId, content, contentType, service, test):

    """Insert attachment to an existing card."""
    if test is None:
        # Using the functionality of the API Client library to directly send request
        media = MediaIoBaseUpload(io.BytesIO(content), contentType, resumable=True)
        try:
            return service.timeline().attachments().insert(id=cardId, media_body=media).execute()
        except errors.HttpError, error:
            logging.error("Attachment insert error: %s" % error)
            return error

    # Constructing the multipart upload for test environement
    multipart_body = _create_multipart_body({}, content, contentType)

    headers = {}
    headers["Content-Type"] = "multipart/related; boundary=\"" + _BOUNDARY + "\""

    return service._http.request("%s/upload/mirror/v1/timeline/%s/attachments" % (base_url, cardId), method="POST", body=multipart_body, headers=headers)
