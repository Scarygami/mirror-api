(function (global) {
  "use strict";
  var glass, doc = global.document, console = global.console;

  Date.prototype.niceDate = function () {
    var y, m, d, h, min, dif, now;
    now = new Date();
    dif = (now.getTime() - this.getTime()) / 1000 / 60;

    if (dif <= 1) { return "Just now"; }
    if (Math.round(dif) === 1) { return "a minute ago"; }
    if (dif < 60) { return Math.round(dif) + " minutes ago"; }

    dif = Math.round(dif / 60);
    if (dif === 1) { return "an hour ago"; }
    if (dif <= 4) { return dif + " hours ago"; }

    y = this.getFullYear().toString();
    m = (this.getMonth() + 1).toString();
    d = this.getDate().toString();
    h = this.getHours().toString();
    min = this.getMinutes().toString();

    if (this.getFullYear() === now.getFullYear() && this.getMonth() === now.getMonth() && this.getDate() === now.getDate()) {
      return (h[1] ? h : "0" + h[0]) + ":" + (min[1] ? min : "0" + min[0]);
    }
    return y + "-" + (m[1] ? m : "0" + m[0]) + "-" + (d[1] ? d : "0" + d[0]) + " " + (h[1] ? h : "0" + h[0]) + ":" + (min[1] ? min : "0" + min[0]);
  };

  function cardSort(a, b) {
    return a.date.getTime() - b.date.getTime();
  }

  function Glass() {
    var
      cards = [],
      mirror = global.gapi.client.mirror,
      mainDiv = doc.getElementById("glass"),
      timer, running = false;

    function Card(id, text, date, image) {
      var cardDiv, textDiv, dateDiv;
      this.id = id;
      this.text = text || "";
      this.date = new Date(date);
      this.image = image;

      function loadImage() {
        cardDiv.style.backgroundImage = "url(" + image + ")";
        cardDiv.style.backgroundSize = "640px";
        textDiv.style.fontSize = "3em";
        textDiv.style.backgroundColor = "rgba(0,0,0,0.3)";
        dateDiv.style.backgroundColor = "rgba(0,0,0,0.3)";
      }
      
      this.createDiv = function () {
        var tmpDiv;
        tmpDiv = doc.createElement("div");
        tmpDiv.classList.add("card");
        tmpDiv.id = "c" + id;

        cardDiv = tmpDiv;

        tmpDiv = doc.createElement("div");
        tmpDiv.classList.add("card_text");
        tmpDiv.appendChild(doc.createTextNode(this.text));
        textDiv = tmpDiv;
        cardDiv.appendChild(textDiv);
        tmpDiv = doc.createElement("div");
        tmpDiv.classList.add("card_date");
        tmpDiv.appendChild(doc.createTextNode(this.date.niceDate()));
        dateDiv = tmpDiv;
        cardDiv.appendChild(dateDiv);

        if (this.image) {
          loadImage();
        }
        
        return cardDiv;
      };

      this.updateText = function (text) {
        if (this.text !== text) {
          this.text = text || "";
          textDiv.innerHTML = "";
          textDiv.appendChild(doc.createTextNode(this.text));
          return true;
        }
        return false;
      };

      this.updateDate = function (date) {
        var tmpDate = new Date(date);
        if (this.date.getTime() !== tmpDate.getTime()) {
          this.date = tmpDate;
          this.updateDisplayDate();
          return true;
        }
        return false;
      };
      
      this.updateImage = function (image) {
        if (this.image !== image) {
          if (image) {
            this.image = image;
            loadImage();
          } else {
            this.image = undefined;
            cardDiv.style.backgroundImage = "none";
            cardDiv.style.backgroundColor = "#CCC";
            textDiv.style.fontSize = "5em";
            textDiv.style.backgroundColor = "transparent";
            dateDiv.style.backgroundColor = "transparent";
          }
        }
      };

      this.updateDisplayDate = function () {
        dateDiv.innerHTML = "";
        dateDiv.appendChild(doc.createTextNode(this.date.niceDate()));
      };

      this.getDiv = function () { return cardDiv; };
    }

    function findCard(id) {
      var i, l;
      l = cards.length;
      for (i = 0; i < l; i++) {
        if (cards[i].id === id) {
          return cards[i];
        }
      }
      return undefined;
    }

    function findPosition(id) {
      var i, l;
      cards.sort(cardSort);
      l = cards.length;
      for (i = 0; i < l; i++) {
        if (cards[i].id === id) {
          if (i === 0) { return undefined; }
          return cards[i - 1];
        }
      }
    }

    function fetchCards() {
      timer = undefined;
      mirror.timeline.list().execute(function (result) {
        var i, l, card, cardDiv, pos;
        console.log(result);
        if (result && result.items) {
          l = result.items.length;
          for (i = 0; i < l; i++) {
            card = findCard(result.items[i].id);
            if (card) {
              card.updateText(result.items[i].text);
              if (card.updateDate(result.items[i].when)) {
                pos = findPosition(card.id);
                if (pos) {
                  mainDiv.insertBefore(card.getDiv(), pos.getDiv());
                } else {
                  mainDiv.appendChild(card.getDiv());
                }
              }
              card.updateImage(result.items[i].image);
            } else {
              card = new Card(result.items[i].id, result.items[i].text, result.items[i].when, result.items[i].image);
              cards.push(card);
              cardDiv = card.createDiv();
              pos = findPosition(card.id);
              if (pos) {
                mainDiv.insertBefore(cardDiv, pos.getDiv());
              } else {
                mainDiv.appendChild(cardDiv);
              }
            }
          }
        }
        l = cards.length;
        for (i = 0; i < l; i++) {
          cards[i].updateDisplayDate();
        }
        timer = global.setTimeout(fetchCards, 30000);
      });
    }

    this.stop = function () {
      if (timer) {
        global.clearTimeout(timer);
        timer = undefined;
      }
      running = false;
    };

    this.start = function () {
      if (running) { return; }
      timer = global.setTimeout(fetchCards, 1);
      running = true;
    };

    mainDiv.innerHTML = "";
  }

  global.onSignInCallback = function (authResult) {
    if (authResult.access_token) {
      global.gapi.client.load("mirror", "v1", function () {
        doc.getElementById("signin").style.display = "none";
        doc.getElementById("signout").style.display = "block";
        doc.getElementById("glass").style.display = "block";
        glass = glass || new Glass();
        glass.start();
      }, global.discoveryUrl);
    } else if (authResult.error) {
      console.log("There was an error: " + authResult.error);
      doc.getElementById("signin").style.display = "block";
      doc.getElementById("signout").style.display = "none";
      doc.getElementById("glass").style.display = "none";
    }
  };

  global.disconnectCallback = function (data) {
    console.log(data);
  };

  global.onload = function () {
    doc.getElementById("signout_button").onclick = function () {
      var script, token;
      if (glass) { glass.stop(); }
      doc.getElementById("signin").style.display = "block";
      doc.getElementById("signout").style.display = "none";
      doc.getElementById("glass").style.display = "none";

      token = global.gapi.auth.getToken();
      if (token && token.access_token) {
        script = doc.createElement("script");
        script.src = "https://accounts.google.com/o/oauth2/revoke?token=" + token.access_token + "&callback=disconnectCallback";
        doc.head.appendChild(script);
      }
    };
  };
}(this));