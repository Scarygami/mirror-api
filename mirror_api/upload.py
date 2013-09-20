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

"""Handle multipart and simple uploads to the API"""

__author__ = 'scarygami@gmail.com (Gerwin Sturm)'

# Add the library location to the path
import sys
sys.path.insert(0, 'lib')

import email
import httplib2
import logging
import json
import utils
import webapp2

from google.appengine.api import files
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers

from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.client import AccessTokenCredentials


class UploadHandler(webapp2.RequestHandler):

    _metainfo = None
    _content_type = None
    _content = None
    _token = None
    _service = None

    def dispatch(self):
        self._checkauth()
        self._decode()
        if self._token is None:
            self.abort(401)
        else:
            credentials = AccessTokenCredentials(self._token, "mirror-api-upload-handler/1.0")
            http = httplib2.Http()
            http = credentials.authorize(http)
            http.timeout = 60
            self._service = build("mirror", "v1", http=http, discoveryServiceUrl=utils.discovery_service_url)
            super(UploadHandler, self).dispatch()

    def _checkauth(self):
        if "Authorization" in self.request.headers:
            self._token = self.request.headers["Authorization"].split(" ")[1]

    def _decode(self):
        """Check for valid content types and decode data accordingly"""

        content_type = self.request.content_type
        if content_type == "multipart/related" or content_type == "multipart/mixed":
            # Attach content-type header to body so that email library can decode it correctly
            message = "Content-Type: " + self.request.headers["Content-Type"] + "\r\n"
            message += self.request.body

            msg = email.message_from_string(message)

            if not msg.is_multipart():
                return

            for payload in msg.get_payload():
                content_type = payload.get_content_type()
                if content_type.startswith("image/") or content_type.startswith("audio/") or content_type.startswith("video/"):
                    if self._content is None:
                        self._content_type = content_type
                        self._content = payload.get_payload(decode=True)
                elif content_type == "application/json":
                    if self._metainfo is None:
                        self._metainfo = json.loads(payload.get_payload())

            return

        if content_type.startswith("image/") or content_type.startswith("audio/") or content_type.startswith("video/"):
            self._content_type = content_type
            if "Content-Transfer-Encoding" in self.request.headers and self.request.headers["Content-Transfer-Encoding"].lower() == "base64":
                self._content = self.request.body.decode("base64")
            else:
                self._content = self.request.body


class InsertHandler(UploadHandler):

    def post(self):

        self.response.content_type = "application/json"

        if self._content is None:
            self.response.status = 400
            self.response.out.write(utils.createError(400, "Couldn't decode content or invalid content-type"))

        # 1) Insert new card using
        if self._metainfo is None:
            request = self._service.internal().timeline().insert(body={})
        else:
            request = self._service.internal().timeline().insert(body=self._metainfo)

        try:
            card = request.execute()
        except HttpError as e:
            self.response.status = e.resp.status
            self.response.out.write(e.content)
            return

        # 2) Insert data into blob store
        file_name = files.blobstore.create(mime_type=self._content_type)
        with files.open(file_name, 'a') as f:
            f.write(self._content)
        files.finalize(file_name)
        blob_key = files.blobstore.get_blob_key(file_name)

        # 3) Update card with attachment info
        if not "attachments" in card:
            card["attachments"] = []

        attachment = {
            "id": str(blob_key),
            "contentType": self._content_type,
            "contentUrl": "%s/upload/mirror/v1/timeline/%s/attachments/%s" % (utils.base_url, card["id"], str(blob_key)),
            "isProcessing": False
        }

        card["attachments"].append(attachment)

        request = self._service.internal().timeline().update(id=card["id"], body=card)

        try:
            result = request.execute()
        except HttpError as e:
            self.response.status = e.resp.status
            self.response.out.write(e.content)
            return

        self.response.status = 200
        self.response.out.write(json.dumps(result))


class UpdateHandler(UploadHandler):

    def put(self, id):

        self.response.content_type = "application/json"

        if self._content is None:
            self.response.status = 400
            self.response.out.write(utils.createError(400, "Couldn't decode content or invalid content-type"))

        # Trying to access card to see if user is allowed to
        request = self._service.timeline().get(id=id)
        try:
            card = request.execute()
        except HttpError as e:
            self.response.status = e.resp.status
            self.response.out.write(e.content)
            return

        # 2) Insert data into blob store
        file_name = files.blobstore.create(mime_type=self._content_type)
        with files.open(file_name, 'a') as f:
            f.write(self._content)
        files.finalize(file_name)
        blob_key = files.blobstore.get_blob_key(file_name)

        # 3) Update card with attachment info and new metainfo
        if self._metainfo is None:
            new_card = {}
        else:
            new_card = self._metainfo

        if "attachments" in card:
            new_card["attachments"] = card["attachments"]
        else:
            new_card["attachments"] = []

        attachment = {
            "id": str(blob_key),
            "contentType": self._content_type,
            "contentUrl": "%s/upload/mirror/v1/timeline/%s/attachments/%s" % (utils.base_url, card["id"], str(blob_key)),
            "isProcessing": False
        }

        new_card["attachments"].append(attachment)

        request = self._service.internal().timeline().update(id=card["id"], body=new_card)

        try:
            result = request.execute()
        except HttpError as e:
            self.response.status = e.resp.status
            self.response.out.write(e.content)
            return

        self.response.status = 200
        self.response.out.write(json.dumps(result))


class AttachmentInsertHandler(UploadHandler):

    def post(self, id):

        self.response.content_type = "application/json"

        if self._content is None:
            self.response.status = 400
            self.response.out.write(utils.createError(400, "Couldn't decode content or invalid content-type"))

        # Trying to access card to see if user is allowed to
        request = self._service.timeline().get(id=id)
        try:
            card = request.execute()
        except HttpError as e:
            self.response.status = e.resp.status
            self.response.out.write(e.content)
            return

        # 2) Insert data into blob store
        file_name = files.blobstore.create(mime_type=self._content_type)
        with files.open(file_name, 'a') as f:
            f.write(self._content)
        files.finalize(file_name)
        blob_key = files.blobstore.get_blob_key(file_name)

        # 3) Update card with attachment info
        if not "attachments" in card:
            card["attachments"] = []

        attachment = {
            "id": str(blob_key),
            "contentType": self._content_type,
            "contentUrl": "%s/upload/mirror/v1/timeline/%s/attachments/%s" % (utils.base_url, card["id"], str(blob_key)),
            "isProcessing": False
        }

        card["attachments"].append(attachment)

        request = self._service.internal().timeline().update(id=card["id"], body=card)

        try:
            result = request.execute()
        except HttpError as e:
            self.response.status = e.resp.status
            self.response.out.write(e.content)
            return

        self.response.status = 200
        self.response.out.write(json.dumps(result))


class DownloadHandler(UploadHandler, blobstore_handlers.BlobstoreDownloadHandler):

    def get(self, id, attachment):

        # Trying to access card to see if user is allowed to
        request = self._service.timeline().get(id=id)
        try:
            request.execute()
        except HttpError as e:
            self.response.status = e.resp.status
            self.response.out.write(e.content)
            return

        if not blobstore.get(attachment):
            self.response.content_type = "application/json"
            self.response.status = 404
            self.response.out.write(utils.createError(404, "Attachment not found"))
            return

        self.send_blob(attachment)


app = webapp2.WSGIApplication(
    [
        (r"/upload/mirror/v1/timeline/(.*)/attachments/(.*)", DownloadHandler),
        (r"/upload/mirror/v1/timeline/(.*)/attachments", AttachmentInsertHandler),
        (r"/upload/mirror/v1/timeline/(.*)", UpdateHandler),
        ("/upload/mirror/v1/timeline", InsertHandler)
    ],
    debug=True
)
