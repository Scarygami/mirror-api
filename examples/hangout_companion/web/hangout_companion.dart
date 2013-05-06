import "dart:html";
import "dart:async";
import "dart:json" as JSON;
import "package:hangouts_api/hangouts_api.dart";
import "src/HangoutOAuth2.dart";
import "package:google_mirror_v1_api/mirror_v1_api_browser.dart" as mirrorlib;
import "package:google_plus_v1_api/plus_v1_api_browser.dart" as pluslib;

Hangout hapi;
HangoutOAuth2 auth;
mirrorlib.Mirror mirror;
pluslib.Plus plus;

// Note: The userinfo.email scope is only necessary for the emulated Mirror API
final SCOPES = [
  "https://www.googleapis.com/auth/glass.timeline",
  "https://www.googleapis.com/auth/userinfo.email"
];

final BUNDLE_ID = "hangout_companion";

mirrorlib.TimelineItem coverCard = null;
List<mirrorlib.TimelineItem> cards = [];

void updateCoverCard() {
  var participants = hapi.getParticipants().length - 1;
  var text = "";
  if (participants == 0) {
    text = "nobody";
  } else if (participants == 1) {
    text = "one person";
  } else {
    text = "$participants people";
  }
  var html = """
    <article>
      <figure>
        <img src="https://developers.google.com/+/images/hangouts-logo.png" style="width: 150px; margin-left: auto; margin-right: auto; display: block; margin-top: 100px">
      </figure>
      <section><p class="text-auto-size">Hanging out with $text</p></section>
    </article>""";
  if (coverCard == null) {
    coverCard = new mirrorlib.TimelineItem.fromJson({});
    coverCard.bundleId = BUNDLE_ID;
    coverCard.isBundleCover = true;
    coverCard.html = html;
    mirror.timeline.insert(coverCard)
      .then((result) => print("Cover card created: $result"))
      .catchError((e) => print("Error while inserting cover card: $e"));
  } else {
    coverCard.html = html;
    mirror.timeline.update(coverCard, coverCard.id)
      .then((result) => print("Cover card updated: $result"))
      .catchError((e) => print("Error while updating cover card: $e"));
  }
}

void onParticipantsChanged(ParticipantsChangedEvent e) {
  updateCoverCard();
  // TODO: update participant cards
}

Future<bool> fetchCurrentCards() {
  var completer = new Completer<bool>();
  mirror.timeline.list(bundleId: BUNDLE_ID).then((result) {
    result.items.forEach((item) {
      if (item.isBundleCover) {
        coverCard = item; 
      } else {
        cards.add(item);
      }
    });
    completer.complete(true);
  })
  .catchError((e) {
    print("Error while fetching cards: $e");
    completer.complete(false);
  });
  return completer.future;
}

void initialize() {
  auth = new HangoutOAuth2([]);
  auth.login().then((t) {
    plus = new pluslib.Plus(auth);
    mirror = new mirrorlib.Mirror(auth);
    mirror.makeAuthRequests = true;
    fetchCurrentCards.then((result) {
      hapi.onParticipantsChanged.add(onParticipantsChanged);
      onParticipantsChanged(null);
    });
  });
}

void main() {
  var hapi = new Hangout();
  hapi.onApiReady.add((ApiReadyEvent e) {
    if (e.isApiReady) initialize();
  });
}



