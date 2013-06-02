# mirror-api

### Description

This is an attempt to recreate the behaviour of the Mirror API
(based on the [official documentation](https://developers.google.com/glass/))
to allow developers like me who can't be  part of the Glass Explorer program,
to test potential applications that could be feasible using Glass.

And even if the real Mirror API turns out to be completely different from what
I envision it to be you can use this as a learning place for different Google
technologies:

- Google Cloud Endpoints, with JavaScript and Python clients

- Google+ Sign-in, client-side flow (Glass emulator)

- Google+ Sign-in, server-side flow (Web app)

- Google App Engine for Web applications in general

- Channel API for push notifications to the browser-based emulator

- And how they all can work together

See [this document](https://docs.google.com/document/d/1_qP2wxbYvfjbImdsk24ZPZkeERCUD4hIvBgBqvpHl9s/edit?usp=sharing)
for a detailed description of what this does and how it works.


### Parts

`mirror_api_server`
is meant to be hosted on Google App Engine and includes several parts.

`mirror_api`
is an implementation of the Mirror API using Google Cloud Endpoints.

`static/glass`
contains a browser based emulator for Glass.
(can be accessed at `yourapp.appspot.com/glass/`)

`service.py`
is a simple playground implementation for a Web Application that makes use of
the Mirror API.

`auth.py`
handles all authentication and storing of credentials when a user signs up
for the demo services. Sets up contacts and subscriptions when the user
first connects. Also handles disconnection by removing all contacts and
subscriptions and deleting credentials when the user wants to disconnect.

`notify.py`
handles subscription post requests coming from the Mirror API and forwards
the requests to the relevant demo services.

`demos/*.py`
are demo services that react to incoming notifications.

### Getting the code - The proper way

1.  Clone (or fork and clone) this repository

    ```
    git clone https://github.com/Scarygami/mirror-api.git
    cd mirror-api
    ```

2.  Fetch the endpoints_proto_datastore repository:

    ```
    git submodule init
    git submodule update
    ```

3.  Create symlink `mirror_api_server/endpoints_proto_datastore` to
    `endpoints-proto-datastore/endpoints_proto_datastore`

    Linux/Unix-based systems:
    ```
    cd mirror_api_server
    ln -s ../endpoints-proto-datastore/endpoints_proto_datastore/ endpoints_proto_datastore
    ```

    Windows systems: (run cmd as Administrator)
    ```
    cd mirror_api_server
    mklink /D endpoints_proto_datastore ..\endpoints-proto-datastore\endpoints_proto_datastore\
    ```

    In case you can't get the symlink to work correctly (meaning the API won't work correctly
    after deploying because of the missing endpoints_proto_datastore library) you can
    alternatively copy the folder `endpoints-proto-datastore/endpoints_proto_datastore/`
    over to `mirror_api_server` manually so that you get this folder structure:
    ```
    mirror_api_server/
    - endpoints_proto_datastore/
      - ndb/
    ```
    You will need to repeat this copy step whenever there are changes in the
    endpoints_proto_datastore library.

### Getting the code - The easy way

Download the latest zip file from https://www.googledrive.com/host/0B1pwzJXH7GP8Z3VRcnVudERPQ2M/ and extract it.
This includes all dependencies, but won't always be the newest available version.

### Setup

1.  Create a new App Engine application at https://appengine.google.com/
    The name of the application will be referred to as `yourapp` for the following steps.

2.  Create a new project in the [Google APIs Console](https://code.google.com/apis/console/)

3.  Activate the Google+ API in `Services`, and the Places API for one of the demo services.

4.  Create a new Client ID for web applications in `API Access`.

    1.  Click on `Create an OAuth 2.0 client ID...`.
    2.  Fill out a `Product name` and click `Next`.
    3.  Keep `Web application` and select `(more options)` next to `Your site or hostname`.
    4.  Make `Authorized Redirect URIs` empty.
    5.  Set `Authorized JavasSript Origins` to `https://yourapp.appspot.com` and `http://localhost:8080` for local testing.
    6.  Click on `Create client ID`.


5. Create a new `Simple API Access` server key.

    1. Click on `Create new Server key...`.
    2. Keep the IP field empty if you want to accept all IP adresses, or fill in the IP subnets that you got from your ISP.
    3. Click on `Create`.


6.  Edit `mirror_api_server/client_secrets.json` and change `YOUR_CLIENT_ID`,
    `YOUR_CLIENT_SECRET` and `YOUR_API_KEY` to the information from the
    APIs Console. Also enter a random long string as `RANDOM_SESSION_SECRET` (Click [here](http://www.random.org/strings/?num=1&len=20&digits=on&upperalpha=on&loweralpha=on&unique=on&rnd=new) to get a string with 20 random characters).

    If you have additional Client IDs you want to access the Mirror API with
    add them in `additional_client_ids`

    Important: Don't commit that file if you contribute to this project. One possible
    solution to prevent this: http://blog.bossylobster.com/2011/10/protecting.html

7.  Edit `mirror_api_server/app.yaml` to change the name of the application to `yourapp`.

8.  Follow the steps in the [Google App Engine Python 2.7 Getting Started](https://developers.google.com/appengine/docs/python/gettingstartedpython27/)
    to install the necessary dependencies and deploy the application. Specifically you will need the steps
    [The Development Environment](https://developers.google.com/appengine/docs/python/gettingstartedpython27/devenvironment) and
    [Uploading Your Application](https://developers.google.com/appengine/docs/python/gettingstartedpython27/uploading)


### Testing

To register contacts and subscriptions you will first have to sign in at the
web app hosted at `https://yourapp.appspot.com/test/`. The functionality of
this app is very limited so far but will be improved.

(Plan is to have your real web app hosted at `https://yourapp.appspot.com/` using
the same UI as the test UI, but with the difference that the real web app
will use calls directly to the Mirror API while the test web app uses the
self-hosted Mirror API clone.)

You can then use the API Explorer at `https://yourapp.appspot.com/_ah/api/explorer#p/mirror/v1/`
to directly send requests to the API.
You will have to turn on OAuth (in the upper right corner of the Explorer) with
the `https://www.googleapis.com/auth/userinfo.email` scope.

You can then see the result at the Glass emulator available at
`https://yourapp.appspot.com/glass/`. The Glass emulator will display actions
and shares correctly and send them to the Mirror API Server which forwards the
information to the relevant subscriptions.


### Deviations from the actual Mirror API

For simplification (and because it's easier to implement like this for Cloud endpoints)
this assumes that there is only one application (i.e. one Client ID) that uses the
Mirror API, so you will have access to all timeline cards of a user, whereas in the
real Mirror API you would only have access to cards created by or shared with your application.

The real Mirror API supports Multipart-bodies to attach images to cards.
Since this isn't possible using Google Cloud Endpoints
(they only support `application/json` as request/response bodies),
I went for a different solution with filling the contentUrl in attachments directly
with any URL, which also works with Data-URIs if the image isn't available online.

Not all features of the Mirror API are implemented yet. Location data is missing and not
all available fields for timeline cards are used yet.

### Disclaimer

I'm not part of the Glass Explorer program so there are no guarantees that
the final Mirror API will work anything like I suppose it will in this demo
implementation. The information is collected from the various public bits and
pieces that have been published. Also see
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
