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

onParticipantsChanged(ParticipantsChangedEvent e) {
  updateCoverCard();
  var participants = hapi.getParticipants();
  cards.forEach((mirrorlib.TimelineItem c) {
    c.isDeleted = true;
  });
  participants.forEach((Participant part) {
    mirrorlib.TimelineItem card = null;
    cards.forEach((mirrorlib.TimelineItem c) {
      if (c.sourceItemId == part.person.id) {
        c.isDeleted = false;
        card = c;
      }
    });
    if (card == null) {
      plus.people.get(part.person.id)
        .then((pluslib.Person p) {
          var image = p.image.url.replaceFirst("?sz=50", "?sz=240");
          var name = p.displayName;
          var placeName = "";
          if (p.placesLived != null) {
            p.placesLived.forEach((pluslib.PersonPlacesLived place) {
              if (place.primary != null && place.primary == true) {
                placeName = place.value;
              } else {
                if (placeName == "") {
                  placeName = place.value;
                }
              }
            });
          }
          var workName = "";
          var eduName = "";
          if (p.organizations != null) {
            p.organizations.forEach((pluslib.PersonOrganizations org) {
              if (org.primary != null && org.primary == true) {
                if (org.type == "work") {
                  workName = org.name;
                } else {
                  eduName = org.name;
                }
              } else {
                if (org.type == "work") {
                  if (workName == "") {
                    workName = org.name;
                  }
                } else {
                  if (eduName == "") {
                    eduName = org.name;
                  }
                }
              }
            });
          }
          var tagline = "";
          if (p.tagline != null) {
            tagline = p.tagline;
          }

          var html = """
            <article>
              <figure>
                <img src="$image">
            <div class="align-center"><p class="text-small">$name</p></div>
              </figure>
              <section>
                <table class="text-small align-right"> 
                  <tbody>""";
          if (placeName != "") {
            html += "<tr><td>$placeName</td></tr>";
          }
          if (workName != "") {
            html += "<tr><td>$workName</td></tr>";
          } else if (eduName != "") {
            html += "<tr><td>$eduName</td></tr>";
          }
          if (tagline !="") {
            html += "<tr><td>$tagline</td></tr>";            
          }
          html += "</tbody></table></section></article>";
          card = new mirrorlib.TimelineItem.fromJson({});
          card.bundleId = BUNDLE_ID;
          card.isBundleCover = false;
          card.html = html;
          card.sourceItemId = part.person.id;
          mirror.timeline.insert(card)
            .then((mirrorlib.TimelineItem c) {
              cards.add(c);
              print("Participant card created: $c");
            })
            .catchError((e) => print("Error inserting participant card: $e"));
        })
        .catchError((e) => print("Error fetching profile information: $e"));
    }
  });
  cards.forEach((mirrorlib.TimelineItem c) {
    if (c.isDeleted) {
      mirror.timeline.delete(c.id)
        .then((result) => print("Card deleted: $result"))
        .catchError((e) => print("Error deleting card: $e"));
      cards.remove(c);
    }
  });
}

Future<bool> fetchCurrentCards() {
  var completer = new Completer<bool>();
  mirror.timeline.list(bundleId: BUNDLE_ID).then((result) {
    if (result.items != null) {
      result.items.forEach((item) {
        if (item.isBundleCover) {
          coverCard = item; 
        } else {
          cards.add(item);
        }
      });
    }
    completer.complete(true);
  })
  .catchError((e) => completer.completeError(e));
  return completer.future;
}

void initialize() {
  auth = new HangoutOAuth2(SCOPES);
  auth.login()
    .then((t) {
      plus = new pluslib.Plus(auth);
      plus.makeAuthRequests = true;
      mirror = new mirrorlib.Mirror(auth);
      mirror.makeAuthRequests = true;
      fetchCurrentCards()
        .then((result) {
          hapi.onParticipantsChanged.add(onParticipantsChanged);
          onParticipantsChanged(null);
        })
        .catchError((e) => print("Error while fetching cards: $e"));
    })
    .catchError((e) => print("Error during authentication: $e"));
}

void main() {
  hapi = new Hangout();
  hapi.onApiReady.add((ApiReadyEvent e) {
    if (e.isApiReady) {
      new Timer(const Duration(milliseconds: 1), initialize);
    }
  });
}



