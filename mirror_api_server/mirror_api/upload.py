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

import email
import json
import webapp2


class UploadHandler(webapp2.RequestHandler):

    _metainfo = None
    _content_type = None
    _content = None

    def _decode(self):
        # Check if we are receiving a valid content_type
        content_type = self.request.content_type
        if content_type != "multipart/related" and content_type != "multipart/mixed":
            return

        # Attach content-type header to body so that email library can decode it correctly
        message = "Content-Type: " + self.request.headers["Content-Type"] + "\r\n"
        message += self.request.body

        msg = email.message_from_string(message)

        if not msg.is_multipart():
            return

        for payload in msg.get_payload():
            if payload.get_content_type().startswith("image/"):
                if self._content is None:
                    self._content_type = payload.get_content_type()
                    self._content = payload.get_payload()  # TODO: decode base64 data
            elif payload.get_content_type() == "application/json":
                self._metainfo = json.loads(payload.get_payload())


class InsertHandler(UploadHandler):

    def post(self):
        # Check if we are receiving a valid content_type
        self._decode()

        if self._metainfo is None and self._content is None:
            self.response.out.write("Invalid request")

        if self._metainfo is not None:
            self.response.out.write("<pre>" + self._metainfo + "</pre><br><br>")

        if self._content is not None:
            self.response.out.write("<img src=\"data:%s;base64,%s\"><br><br>" % (self._content_type, self._content))


class UpdateHandler(UploadHandler):

    def put(self, id):
        self._decode()

        if self._metainfo is None and self._content is None:
            self.response.out.write("Invalid request")

        if self._metainfo is not None:
            self.response.out.write("<pre>" + self._metainfo + "</pre><br><br>")

        if self._content is not None:
            self.response.out.write("<img src=\"data:%s;base64,%s\"><br><br>" % (self._content_type, self._content))


class AttachmentInsertHandler(UploadHandler):

    def post(self, id):
        self._decode()

        if self._metainfo is None and self._content is None:
            self.response.out.write("Invalid request")

        if self._metainfo is not None:
            self.response.out.write("<pre>" + self._metainfo + "</pre><br><br>")

        if self._content is not None:
            self.response.out.write("<img src=\"data:%s;base64,%s\"><br><br>" % (self._content_type, self._content))


app = webapp2.WSGIApplication(
    [
        (r"/upload/mirror/v1/timeline/(.*)/attachments", AttachmentInsertHandler),
        (r"/upload/mirror/v1/timeline/(.*)", UpdateHandler),
        ("/upload/mirror/v1/timeline", InsertHandler)
    ],
    debug=True
)
