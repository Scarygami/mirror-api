# Copyright 2013 Gerwin Sturm, FoldedSoft e.U. / www.foldedsoft.at
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import httplib2
import os
import webapp2
import json
import difflib

from datetime import datetime
from lib.apiclient.discovery import build
from lib.apiclient.errors import HttpError
from google.appengine.api import memcache
from google.appengine.ext.webapp import template
from webapp2_extras import sessions
from webapp2_extras import sessions_memcache

http = httplib2.Http(memcache)
userIp = os.environ["REMOTE_ADDR"]
service = build("mirror", "v1", discoveryServiceUrl="https://mirror-api.appspot.com/_ah/api/discovery/v1/apis/{api}/{apiVersion}/rest", http=http)

config = {}
config["webapp2_extras.sessions"] = {
    "secret_key": "ajksdlj1029jlksndajsaskd7298hkajsbdkaukjassnkjankj",
}


class BaseHandler(webapp2.RequestHandler):
    def dispatch(self):
        # Get a session store for this request.
        self.session_store = sessions.get_store(request=self.request)

        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
        return self.session_store.get_session(name='mirror_session', factory=sessions_memcache.MemcacheSessionFactory)


class WelcomeHandler(BaseHandler):
    def get(self):
        path = os.path.join(os.path.dirname(__file__), 'templates/welcome.html')
        self.response.out.write(template.render(path, {}))


class ListHandler(webapp2.RequestHandler):
    def get(self):
        try:
            apis_list = service.apis().list(userIp=userIp).execute(http)
        except HttpError:
            self.response.out.write("Error accessing the API, please try again later")
            return

        apis = []
        if "items" in apis_list:
            apis += apis_list["items"]

        for a in apis:
            a["first_check"] = ""
            a["last_check"] = ""
            a["last_change"] = ""
            a["listed"] = True
            a["checked"] = False

        api_docs = ApiDoc.gql("ORDER BY last_check DESC")
        for api_doc in api_docs:
            chk_listed = False
            for a in apis:
                if api_doc.key().parent().parent() is not None:
                    if a["name"] == api_doc.key().parent().parent().name() and a["version"] == api_doc.key().parent().name():
                        chk_listed = True
                        a["first_check"] = api_doc.last_change
                        if not a["checked"]:
                            a["last_check"] = api_doc.last_check
                            a["last_change"] = api_doc.last_change
                            a["checked"] = True
                        break

            if not chk_listed:
                if api_doc.key().parent().parent() is not None:
                    a = {}
                    a["name"] = api_doc.key().parent().parent().name()
                    a["version"] = api_doc.key().parent().name()
                    a["first_check"] = api_doc.last_change
                    a["last_check"] = api_doc.last_check
                    a["last_change"] = api_doc.last_change
                    a["checked"] = True
                    a["listed"] = False
                    apis.append(a)

        path = os.path.join(os.path.dirname(__file__), 'list.html')
        self.response.out.write(template.render(path, {'apis': apis}))


class CheckHandler(webapp2.RequestHandler):
    def get(self, api, version):
        try:
            api_json1 = service.apis().getRest(api=api, version=version, userIp=userIp).execute(http)
            api_doc1 = json.dumps(api_json1, indent=2, sort_keys=True)
            chk_in_api = True
            if "etag" in api_json1:
                api_json1["etag"] = ""
            if "revision" in api_json1:
                api_json1["revision"] = ""
        except HttpError:
            chk_in_api = False

        api_id = 0
        chk_new = False
        chk_changes = False
        api_docs = ApiDoc.gql("WHERE ANCESTOR IS :1 ORDER BY last_check DESC LIMIT 1", api_version_dbkey(api, version))
        if api_docs.count() > 0:
            api_doc_old = api_docs.get()
            api_json2 = json.loads(api_doc_old.doc)
            api_doc2 = json.dumps(api_json2, indent=2, sort_keys=True)

            if "etag" in api_json2:
                api_json2["etag"] = ""
            if "revision" in api_json2:
                api_json2["revision"] = ""

            if not chk_in_api:
                api_doc1 = api_doc2
                api_json1 = api_json2

            if json.dumps(api_json1, indent=2, sort_keys=True) == json.dumps(api_json2, indent=2, sort_keys=True):
                time_now = datetime.utcnow()
                if (time_now - api_doc_old.last_check).total_seconds() > 3600:
                    api_doc_old.put()
                api_id = api_doc_old.key().id()
        else:
            if not chk_in_api:
                self.redirect("/")
                return
            chk_new = True
            api_doc2 = ""
            api_json2 = json.loads("{}")

        if json.dumps(api_json1, indent=2, sort_keys=True) != json.dumps(api_json2, indent=2, sort_keys=True):
            api_doc_new = ApiDoc(parent=api_version_dbkey(api, version))
            api_doc_new.doc = api_doc1
            api_doc_new.put()
            api_id = api_doc_new.key().id()
            chk_changes = True

        str_message = ""
        if chk_new:
            str_message = "This API-Doc has been loaded for the first time.<br>"
        else:
            if chk_changes:
                str_message = "Look at that, something changed!<br>"
            else:
                str_message = "Nothing new :(<br>"

        if chk_changes and not chk_new:
            differ = difflib.Differ()
            doc1 = create_doc(api_doc1)
            doc2 = create_doc(api_doc2)
            diff_output = list(differ.compare(api_doc2.split("\n"), api_doc1.split("\n")))
            diff_table = create_diff_table(diff_output, api, version, "old", doc2, api, version, "new", doc1)
        else:
            doc1 = create_doc(api_doc1)
            diff_table = create_code_table(api_doc1.split("\n"), doc1)
            api_docs = ApiDoc.gql("WHERE ANCESTOR IS :1 ORDER BY last_check DESC LIMIT 1, 10", api_version_dbkey(api, version))
            chk_first = True

            for api_doc in api_docs:
                if chk_first:
                    str_message += "<br>Compare current documentation to a previous one:<br>"
                    chk_first = False
                str_message += "<a href=\"/%s/%s/%d/%s/%s/%d\">%s</a><br>" % (api, version, api_doc.key().id(), api, version, api_id, api_doc.last_change.strftime("%Y-%m-%d %H:%M"))

            api_docs = ApiDoc.gql("WHERE ANCESTOR IS :1 ORDER BY last_check DESC LIMIT 0, 10", api_dbkey(api))
            chk_first = True
            for api_doc in api_docs:
                if api_doc.parent_key().name() != version:
                    if chk_first:
                        str_message += "<br>Compare this version to another one:<br>"
                        chk_first = False
                    str_message += "%s <a href=\"/%s/%s/%d/%s/%s/%d\">%s</a><br>" % (api_doc.parent_key().name(), api, api_doc.parent_key().name(), api_doc.key().id(), api, version, api_id, api_doc.last_change.strftime("%Y-%m-%d %H:%M"))

        path = os.path.join(os.path.dirname(__file__), "compare.html")
        self.response.out.write(template.render(path, {"message": str_message, "diff_table": diff_table, "api": api, "version": version, "api2": api, "version2": version}))


class CompareHandler(webapp2.RequestHandler):
    def get(self, api1, version1, id1, api2, version2, id2):
        if not id1.isdigit() or not id2.isdigit():
            self.redirect("/")
            return

        api_doc1 = ApiDoc.get_by_id(int(id1), parent=api_version_dbkey(api1, version1))
        api_doc2 = ApiDoc.get_by_id(int(id2), parent=api_version_dbkey(api2, version2))

        if not api_doc1 or not api_doc2:
            self.redirect("/")
            return

        api_doc1.doc = json.dumps(json.loads(api_doc1.doc), indent=2, sort_keys=True)
        api_doc2.doc = json.dumps(json.loads(api_doc2.doc), indent=2, sort_keys=True)
        differ = difflib.Differ()
        diff_output = list(differ.compare(api_doc1.doc.split("\n"), api_doc2.doc.split("\n")))

        doc1 = create_doc(api_doc1.doc)
        doc2 = create_doc(api_doc2.doc)

        path = os.path.join(os.path.dirname(__file__), "compare.html")
        self.response.out.write(template.render(path, {"diff_table": create_diff_table(diff_output, api1, version1, api_doc1.last_change.strftime("%Y-%m-%d %H:%M"), doc1, api2, version2, api_doc2.last_change.strftime("%Y-%m-%d %H:%M"), doc2), "api": api1, "version": version1, "api2": api2, "version2": version2}))


app = webapp2.WSGIApplication(
    [
        ('/', ListHandler),
        ('/(.+)/(.+)/(.+)/(.+)/(.+)/(.+)', CompareHandler),
        ('/(.+)/(.+)', CheckHandler)
    ],
    debug=True, config=config)
