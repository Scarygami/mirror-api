import "dart:html";
import "dart:async";
import "dart:json" as JSON;
import "package:hangouts_api/hangouts_api.dart";
import "src/HangoutOAuth2.dart";

Hangout hapi;
HangoutOAuth2 auth;

void initialize() {
  auth = new HangoutOAuth2([]);
  auth.login().then((t) {
    print(t);
  });
}

void main() {
  var hapi = new Hangout();
  hapi.onApiReady.add((e) {
    if (e.isApiReady) initialize();
  });
}



