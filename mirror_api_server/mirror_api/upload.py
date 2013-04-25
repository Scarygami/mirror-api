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

    def post(self):
        # Check if we are receiving a valid content_type
        content_type = self.request.content_type
        if content_type != "multipart/related" and content_type != "multipart/mixed":
            self.response.out.write("Invalid Content-Type")

        # Attach content-type header to body so that email library can decode it correctly
        message = "Content-Type: " + self.request.headers["Content-Type"] + "\r\n"
        message += self.request.body

        msg = email.message_from_string(message)

        if not msg.is_multipart():
            self.response.out.write("Couldn't decode multipart body")
            return

        for payload in msg.get_payload():
            if payload.get_content_type().startswith("image/"):
                # Display attached image
                self.response.out.write("<img src=\"data:%s;base64,%s\"><br><br>" % (payload.get_content_type(), payload.get_payload()))
            elif payload.get_content_type() == "application/json":
                # Parse and display JSON metadata
                j = json.loads(payload.get_payload())
                self.response.out.write("<pre>" + json.dumps(j, indent=2, separators=(",", ": ")) + "</pre><br><br>")
            else:
                self.response.out.write("Invalid content-type: %s<br><br>" % payload.get_content_type())


app = webapp2.WSGIApplication(
    [("/upload/", UploadHandler)],
    debug=True
)
