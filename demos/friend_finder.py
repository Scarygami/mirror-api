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

"""Methods for Friend finder service"""

__author__ = 'scarygami@gmail.com (Gerwin Sturm)'

__all__ = ["handle_location", "WELCOMES"]


"""Welcome message cards that are sent when the user first connects to this service"""
WELCOMES = [
    {
        "html": ("<article class=\"photo\">"
                 "  <img src=\"glass://map?w=640&h=360&zoom=1\" width=\"100%\" height=\"100%\">"
                 "  <div class=\"photo-overlay\"></div>"
                 "  <section>"
                 "    <p class=\"text-auto-size\">Welcome to Friend Finder</p>"
                 "  </section>"
                 "</article>")
    }
]


def handle_location(item, notification, service, test):
    """Callback for Location updates."""

    """
    Card layout for cover:
        <article class="photo">
            <img src="glass://map?w=640&h=360&marker=0;48.20887,16.3708&marker=1;48.20949,16.37143&marker=2;48.20903,16.36924&marker=3;48.20772,16.37036&marker=4;48.20753,16.36954" width="100%" height="100%">
            <div class="photo-overlay"></div>
            <footer><div>4 friends nearby</div></footer>
        </article>

    Card layout for detailed card:
        <article>
            <figure>
                <img src="https://lh3.googleusercontent.com/-khaIYLifQik/AAAAAAAAAAI/AAAAAAAA3bA/CWAtORun9is/photo.jpg?sz=240" width="240">
                <div><p class="text-small align-center">Gerwin Sturm</p></div>
            </figure>
            <section>
                <img src="glass://map?w=330&h=240&marker=0;48.20887,16.3708&marker=1;48.20949,16.37143" width="330" height="240">
            </section>
        </article>
    """

    # TODO: implement

    return
