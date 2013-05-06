library hangoutoauth2;

import "dart:async";
import "dart:html";
import "dart:json" as JSON;
import "package:google_oauth2_client/google_oauth2_browser.dart";
import "package:js/js.dart" as js;

/*
 * OAuth2 authentication using the Google JS API client inside of a Hangout.
 * 
 * This doesn't require additional User interaction since the User already gave
 * permissions when they started the Hangout application
 */
class HangoutOAuth2 extends SimpleOAuth2 {
  
  bool _clientLoaded = false;
  Future<bool> _clientLoader;
  
  DateTime _expiry;
  
  Set<String> _scopes = new Set();
  
  /*
   * [scopes] has to match the additional OAuth Scopes you defined for the
   * Hangout application in the API Console 
   */
  HangoutOAuth2(List<String> scopes) : super(null) {
    _scopes.addAll(scopes);
    _scopes.add("https://www.googleapis.com/auth/plus.me");
    _scopes.add("https://www.googleapis.com/auth/hangout.av");
    _scopes.add("https://www.googleapis.com/auth/hangout.participants");
  }

  /*
   * Loads the Google JS API client if it hasn't been loaded before 
   */
  Future<bool> _loadClient() {
    if (_clientLoaded) return new Future.value(true);
    if (_clientLoader != null) return _clientLoader;
    
    var completer = new Completer<bool>();
    js.scoped(() {
      js.context.onClientReady =  new js.Callback.once(() {
        _clientLoaded = true;
        _clientLoader = null;
        completer.complete(true);
      });
    });
    
    ScriptElement script = new ScriptElement();
    script.src = "https://apis.google.com/js/client.js?onload=onClientReady";
    script.type = "text/javascript";
    document.body.children.add(script);

    _clientLoader = completer.future;
    return _clientLoader;
  }
  
  /*
   * Takes a normal HttpRequest and sets the authentication headers
   * if a valid token is available or can be retrieved
   */
  Future<HttpRequest> authenticate(HttpRequest request) {
    var completer = new Completer();
    login().then((t) {
      if (token != null) {
        super.authenticate(request).then(
          (authenticatedRequest) => completer.complete(authenticatedRequest)
        );
      } else {
        completer.complete(request);
      }
    });
    return completer.future;
  }
  
  /*
   * Uses the JS API Client to retrieve a valid OAuth2 token
   * or returns the current token if it is still valid
   */
  Future<String> login() {
    if (token != null && _expiry != null && _expiry.isAfter(new DateTime.now())) {
      return new Future.value(token);
    }
    var completer = new Completer<String>();
    _loadClient().then((success) {
      if (success) {
        js.scoped(() {
          js.context.gapi.auth.authorize(
            js.map({"client_id": null, "scope": new List.from(_scopes), "immediate": true}),
            new js.Callback.once((js.Proxy authResult) {
              Map result = JSON.parse(js.context.JSON.stringify(authResult));
              print("Client ID: ${result["client_id"]}");
              if (result.containsKey("access_token")) {
                token = result["access_token"];
                tokenType = result["token_type"];
                _expiry = new DateTime.now().add(new Duration(seconds: int.parse(result["expires_in"])));
                completer.complete(result["access_token"]);
              } else {
                token = null;
                _expiry = null;
                completer.complete(null);
              }
            })
          );
        });
      }
    });
    return completer.future;
  }
}