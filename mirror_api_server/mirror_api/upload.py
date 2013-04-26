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
import logging
import json
import webapp2


class UploadHandler(webapp2.RequestHandler):

    _metainfo = None
    _content_type = None
    _content = None

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
                if payload.get_content_type().startswith("image/"):
                    if self._content is None:
                        self._content_type = payload.get_content_type()
                        self._content = payload.get_payload(decode=True)
                elif payload.get_content_type() == "application/json":
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
        self._decode()

        logging.info(self.request.headers)

        if self._metainfo is None and self._content is None:
            self.response.out.write("Invalid request")

        if self._metainfo is not None:
            self.response.out.write("<pre>" + json.dumps(self._metainfo, indent=2, separators=(",", ": ")) + "</pre><br><br>")

        if self._content is not None:
            self.response.out.write("<img src=\"data:%s;base64,%s\"><br><br>" % (self._content_type, self._content))


class UpdateHandler(UploadHandler):

    def put(self, id):
        self._decode()

        if self._metainfo is None and self._content is None:
            self.response.out.write("Invalid request")

        if self._metainfo is not None:
            self.response.out.write("<pre>" + json.dumps(self._metainfo, indent=2, separators=(",", ": ")) + "</pre><br><br>")

        if self._content is not None:
            self.response.out.write("<img src=\"data:%s;base64,%s\"><br><br>" % (self._content_type, self._content))


class AttachmentInsertHandler(UploadHandler):

    def post(self, id):
        self._decode()

        if self._metainfo is None and self._content is None:
            self.response.out.write("Invalid request")

        if self._metainfo is not None:
            self.response.out.write("<pre>" + json.dumps(self._metainfo, indent=2, separators=(",", ": ")) + "</pre><br><br>")

        if self._content is not None:
            self.response.out.write("<img src=\"data:%s;base64,%s\"><br><br>" % (self._content_type, self._content))


class DownloadHandler(webapp2.RequestHandler):

    def get(self, id, attachment):

        self.response.out.write("Not implemented yet")


app = webapp2.WSGIApplication(
    [
        (r"/upload/mirror/v1/timeline/(.*)/attachments/(.*)", DownloadHandler),
        (r"/upload/mirror/v1/timeline/(.*)/attachments", AttachmentInsertHandler),
        (r"/upload/mirror/v1/timeline/(.*)", UpdateHandler),
        ("/upload/mirror/v1/timeline", InsertHandler)
    ],
    debug=True
)
