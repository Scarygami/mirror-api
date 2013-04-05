# mirror-api

### Description

This is an attempt to recreate the behaviour of the Mirror API (based on public information available) to allow developers like me who aren't part of the Glass Explorer program, to test potential applications that could be feasible using Glass.

And even if the real Mirror API turns out to be completely different from what I envision it to be you can use this as a learning place for different Google technologies:

- Google Cloud Endpoints, with JavaScript and Python clients

- Google+ Sign-in, client-side flow (Glass emulator)

- Google+ Sign-in, server-side flow (Web app)

- Google App Engine for Web applications in general

- And how they all can work together


### Parts

`mirror_api_server` is meant to be hosted on Google App Engine and includes several parts.

`mirror_api` is an implementation of the Mirror API using Google Cloud Endpoints.

`static/glass` contains a browser based emulator for Glass (can be accessed at `yourapp.appspot.com/glass/`).

`service.py` is a simple playground implementation for a Web Application that makes use of the Mirror API.


### Setup

Create a new project in the [Google APIs Console](https://code.google.com/apis/console/)

Activate the Google+ API in `Services`

Create a new Client ID for web applications in `API Access`

Leave Redirect URIs empty but set Javascript origin to `https://yourapp.appspot.com` and `http://localhost:8080` for local testing.

Edit `mirror_api_server/client_secrets.json` to replace `YOUR_CLIENT_ID` and `YOUR_CLIENT_SECRET` with the information from the APIs Console.

Important: Don't commit that file if you contribute to this project. One possible solution to prevent this: http://blog.bossylobster.com/2011/10/protecting.html

Edit `mirror_api_server/app.yaml` to change the name of the application to match your App Engine application.


### Limitations

For simplification (and because it's easier to implement like this for Cloud endpoints) this assumes
that there is only one application that uses the Mirror API, so you will have access to all timeline cards of a user,
whereas in the real Mirror API you would only have access to cards created by or shared with your application.

The real Mirror API supports Multipart-bodies to attach images to cards. Since I couldn't figure out
(not sure if it is even possible) how to use multipart-bodies in Google Cloud Endpoints, I went for a different solution
with an `image` field inside of a card which takes any image URL. Also works with Data-URIs if the image isn't available online,
which will be the case mostly when uploading images from Glass itself.

At the moment the only functionality is to use the web app hosted at `https://yourapp.appspot.com/` to send text and image cards
to the Glass emulator available at `https://yourapp.appspot.com/glass/` but I'm planning to add more functionality
that will be available in the Mirror API as far as we know.


### Disclaimer

I'm not part of the Glass Explorer program so there are no guarantees that the final Mirror API
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