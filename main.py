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

"""RequestHandlers for Glass emulator and Demo services"""

__author__ = 'scarygami@gmail.com (Gerwin Sturm)'

# Add the library location to the path
import sys
sys.path.insert(0, 'lib')

from utils import config
import webapp2

from service.auth import AUTH_ROUTES
from service.notify import NOTIFY_ROUTES
from service.service import SERVICE_ROUTES
from demos import DEMO_ROUTES

ROUTES = (AUTH_ROUTES + SERVICE_ROUTES + NOTIFY_ROUTES + DEMO_ROUTES)

# Remove the next two lines if you don't want to host a Glass emulator
from emulator.glass import GLASS_ROUTES
ROUTES = (ROUTES + GLASS_ROUTES)

app = webapp2.WSGIApplication(ROUTES, debug=True, config=config)
