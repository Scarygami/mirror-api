# hangout_companion

### Description

An example of a Hangout application that accesses the Mirror API. And for added fun it is written in Dart.

Hangouts API documentation: https://developers.google.com/+/hangouts/

Mirror API documentation: https://developers.google.com/glass/


### Setup

If you have access to the real Mirror API use the dependency as specified in `pubspec.yaml.real`
```
  google_mirror_v1_api: any
```


If you don't have access to the real Mirror API and want to test this with your own hosted
[Mirror API Emulator](https://github.com/Scarygami/mirror-api) you will have to do the following:

1.  Setup and deploy the [Mirror API Emulator](https://github.com/Scarygami/mirror-api) as described there.

2.  Get the [Dart Client Library Generator](https://github.com/dart-gde/discovery_api_dart_client_generator).

3.  Run the generator with this command:

```
dart generate.dart --url=https://<yourapp>.appspot.com/_ah/api/discovery/v1/apis/mirror/v1/rest
```

4.  Change the `google_mirror_v1_api` dependency in `pubspec.yaml` to point to the generated library
    (see `pubspec.yaml.test`)

```
  google_mirror_v1_api:
    path: /path/to/dart_mirror_v1_api_client
```

### Running

First make sure to change the css and dart paths in `hangout_companion.xml` to match where you plan to upload the files.

To test your application you will first have to upload it (including the packages) to `<YOUR_SERVER_PATH>`

Then go to the [Google APIs Console](https://code.google.com/apis/console/) and create a new Project.

Create a new `Client ID` for web applications in "API Access"

Activate the Google+ Hangouts API, Google+ API (and Mirror API if you have access) in "Services"

In "Hangouts" enter the URL to your XML file in Application URL.

Check "This application requires additional OAuth 2.0 scopes" and enter:
```
https://www.googleapis.com/auth/glass.timeline
https://www.googleapis.com/auth/userinfo.email
```

If you have access to the real Mirror API you can remove the `userinfo.email` scope.
Make sure to remove it from the `SCOPES` in `hangout_companion.dart` as well.

At the bottom of that page you can then "Save" and "Enter a hangout".

(Of course this will only work in Dartium without compiling to js...)


### Special note if you are running with the Mirror API emulator and not the real Mirror API

During the first run the authentication will fail, check the Javascript console and you will see a message `Client ID: <some client id here>`

Copy this client ID and add it as `additional_client_id` in the `client_secrets.json` of your Mirror API instance. Deploy the instance again and authentication should work.

Please note that you will have to repeat those steps whenever you save the Hangouts settings in the API console, because this will result in a new Client ID.


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
