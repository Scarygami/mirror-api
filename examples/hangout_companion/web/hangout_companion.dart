import "dart:html";
import "dart:async";
import "dart:json" as JSON;
import "package:hangouts_api/hangouts_api.dart";

var hapi;

void main() {
  hapi = new Hangout();
  
  hapi.onApiReady.add((ApiReadyEvent event) {
    if (event.isApiReady) {
      // DO someting
    }
  });
}



