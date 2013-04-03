# mirror-api

### Description

This is an attempt to recreate the behaviour of the Mirror API (based on public information available) to allow developers like me who aren't part of the Glass Explorer program, to test potential applications that could be feasible using Glass.


### Parts

`mirror_api_server` is meant to be hosted on Google App Engine and includes several parts.

`mirror_api` is an implementation of the Mirror API using Google Cloud Endpoints.

`static/glass` contains a browser based emulator for Glass (can be accessed at `yourapp.appspot.com/glass/`).

`service.py` is a dummy implementation for a Web Application that makes use of the Mirror API.


### Setup

Create a new project in the [Google APIs Console](https://code.google.com/apis/console/)

Activate the Google+ API in `Services`

Create a new Client ID for web applications in `API Access`

Leave Redirect URIs empty but set Javascript origin to `https://yourapp.appspot.com` and `http://localhost:8080` for local testing.

`Download JSON` to get the `client_secrets.json` file.

Include that file in `mirror_api_server` where the `app.yaml` is located.

Change the name of the application in `app.yaml` to match your App Engine application.


### Limitations

For simplification (and because it's easier to implement like this for Cloud endpoints) this assumes
that there is only one application that uses the Mirror API, so you will have access to all timeline cards of a user,
whereas in the real Mirror API you would only have access to cards created by or shared with your application.


### Disclaimer

I'm not part of the Glass Explorer program so there are not guarantees that the final Mirror API
will work anything like I suppose it will in this demo implementation. The information is collected
from the various public bits and pieces that have been published. Also see
[my document about the topic](https://docs.google.com/document/d/1XgYDbWNKEDLfm-F44sZy0uSOQKton5ksg5pWdv9XCo0/edit).


### Licenses

```
Copyright (c) 2013 Gerwin Sturm, FoldedSoft e.U. / www.foldedsoft.at

Licensed under the Apache License, Version 2.0 (the "License"); you may not
use this file except in compliance with the License. You may obtain a copy of
the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
License for the specific language governing permissions and limitations under
the License

```