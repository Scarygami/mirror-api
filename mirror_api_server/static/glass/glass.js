(function (global) {
  "use strict";
  var doc = global.document, console = global.console, demoCards;

  demoCards = {
    "items": [
      {
        "text": "Also works with Data-URIs!",
        "image": "http://farm5.staticflickr.com/4122/4784220578_2ce8d9fac3_b.jpg",
        "cardOptions": [{"action": "SHARE"}, {"action": "REPLY"}],
        "when": "2013-04-05T12:36:52.755260",
        "id": 19001
      },
      {
        "text": "Hello World!",
        "cardOptions": [{"action": "SHARE"}, {"action": "REPLY"}],
        "when": "2013-04-05T12:26:55.837450",
        "id": 18001
      },
      {
        "text": "What a nice photo!",
        "image": "http://farm5.staticflickr.com/4122/4784220578_2ce8d9fac3_b.jpg",
        "cardOptions": [{"action": "SHARE"}, {"action": "REPLY"}],
        "when": "2013-04-05T11:32:19.603850",
        "id": 10002
      }
    ]
  };

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

  Date.prototype.formatTime = function () {
    var h, min;

    h = this.getHours().toString();
    min = this.getMinutes().toString();

    return h + ":" + (min[1] ? min : "0" + min[0]);
  };

  function Glass() {
    var
      cards = [],
      mirror,
      mainDiv = doc.getElementById("glass"),
      timer, running = false,
      CONTENT_CARD = 1,
      START_CARD = 2,
      CLOCK_CARD = 3,
      UP = 1, DOWN = 2, LEFT = 3, RIGHT = 4;

    if (!global.glassDemoMode) {
      mirror = global.gapi.client.mirror;
    }

    function cardSort(a, b) {
      if (a.type === START_CARD) { return -1; }
      if (b.type === START_CARD) { return 1; }
      if (a.type === CLOCK_CARD) { return -1; }
      if (b.type === CLOCK_CARD) { return 1; }
      return b.date.getTime() - a.date.getTime();
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
          return i;
        }
      }
    }

    function getDirection(dx, dy) {
      var tmp;
      if (dx * dx + dy * dy < 3000) {
        // move too short
        return 0;
      }

      if (dx === 0) {
        return (dy > 0) ? DOWN : UP;
      }
      if (dy === 0) {
        return (dx > 0) ? RIGHT : LEFT;
      }
      tmp = Math.abs(dx / dy);
      if (tmp >= 0.5 && tmp <= 1.5) {
        // direction too diagonal, not distinct enough
        return 0;
      }

      if (tmp > 1.5) {
        // mainly horizontal movement
        return (dx > 0) ? RIGHT : LEFT;
      }

      // mainly vertical movement
      return (dy > 0) ? DOWN : UP;
    }

    function Card(type, id, text, date, image) {
      var cardDiv, textDiv, dateDiv, interfaceDiv, mouseX, mouseY, ignoreClick, that = this;
      this.id = id;
      this.text = text || "";
      this.type = type;
      if (date) {
        this.date = new Date(date);
      } else {
        this.date = new Date();
      }
      this.image = image;
      type = type || CONTENT_CARD;

      this.loadImage = function () {
        cardDiv.style.backgroundImage = "url(" + image + ")";
      };

      this.createDiv = function () {
        var tmpDiv;
        switch (type) {
        case CONTENT_CARD:
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
            this.loadImage();
          }

          cardDiv.style.display = "none";
          break;
        case START_CARD:
          this.id = "start";
          tmpDiv = doc.createElement("div");
          tmpDiv.classList.add("card");
          tmpDiv.id = "c" + id;
          tmpDiv.style.zIndex = 1;
          cardDiv = tmpDiv;
          break;
        case CLOCK_CARD:
          this.id = "clock";
          tmpDiv = doc.createElement("div");
          tmpDiv.classList.add("card");
          tmpDiv.id = "c" + id;
          cardDiv = tmpDiv;

          tmpDiv = doc.createElement("div");
          tmpDiv.classList.add("card_text");
          tmpDiv.appendChild(doc.createTextNode("\"ok glass\""));
          textDiv = tmpDiv;
          cardDiv.appendChild(textDiv);

          tmpDiv = doc.createElement("div");
          tmpDiv.classList.add("card_date");
          tmpDiv.appendChild(doc.createTextNode((new Date()).formatTime()));
          dateDiv = tmpDiv;
          cardDiv.appendChild(dateDiv);

          cardDiv.style.display = "none";
          break;
        }

        this.updateCardType();

        tmpDiv = doc.createElement("div");
        tmpDiv.classList.add("card_interface");
        interfaceDiv = tmpDiv;
        cardDiv.appendChild(interfaceDiv);
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
            this.loadImage();
          } else {
            this.image = undefined;
            cardDiv.style.backgroundImage = "none";
            textDiv.style.fontSize = "5em";
            textDiv.style.backgroundColor = "transparent";
            dateDiv.style.backgroundColor = "transparent";
          }
        }
      };

      this.updateDisplayDate = function () {
        switch (type) {
        case START_CARD:
          return;
        case CLOCK_CARD:
          dateDiv.innerHTML = "";
          dateDiv.appendChild(doc.createTextNode((new Date()).formatTime()));
          break;
        case CONTENT_CARD:
          dateDiv.innerHTML = "";
          dateDiv.appendChild(doc.createTextNode(this.date.niceDate()));
          break;
        }
      };

      this.updateCardType = function () {
        // Reset type
        cardDiv.className = "card";

        switch (type) {
        case CLOCK_CARD:
          cardDiv.classList.add("card_type_clock");
          break;
        case CONTENT_CARD:
          if (!!this.image) {
            cardDiv.classList.add("card_type_image");
          } else {
            cardDiv.classList.add("card_type_text");
            // And in the future possibly also card_type_html
          }
          break;
        }
      };

      this.getDiv = function () { return cardDiv; };

      function up() {
        switch (type) {
        case START_CARD:
          findCard("clock").show();
          break;
        }
      }

      function down() {
        switch (type) {
        case CONTENT_CARD:
        case CLOCK_CARD:
          that.hide();
          break;
        }
      }

      function left() {
        var pos;
        switch (type) {
        case CONTENT_CARD:
        case CLOCK_CARD:
          pos = findPosition(that.id);
          if (pos < cards.length - 1) {
            that.hide();
            cards[pos + 1].show();
          }
          break;
        }
      }

      function right() {
        var pos;
        switch (type) {
        case CONTENT_CARD:
          pos = findPosition(that.id);
          that.hide();
          cards[pos - 1].show();
          break;
        }
      }

      function onClick(e) {
        var x, y;
        if (ignoreClick) {
          ignoreClick = false;
          return;
        }
        x = e.offsetX || e.layerX || 0;
        y = e.offsetY || e.layerY || 0;
        if (x < 30) {
          right();
          return;
        }
        if (x > 610) {
          left();
          return;
        }
        if (y < 30) {
          up();
          return;
        }
        if (y > 330) {
          down();
          return;
        }
        switch (type) {
        case CONTENT_CARD:
          // TODO: check and display possible actions
          break;
        case START_CARD:
          findCard("clock").show();
          break;
        case CLOCK_CARD:
          // Nothing to do here so far
          break;
        }
      }

      function onMouseDown(e) {
        mouseX = e.offsetX || e.layerX || 0;
        mouseY = e.offsetY || e.layerY || 0;
      }

      function onMouseUp(e) {
        var x, y, dir;

        x = e.offsetX || e.layerX || 0;
        y = e.offsetY || e.layerY || 0;

        dir = getDirection(x - mouseX, y - mouseY);

        if (dir !== 0) {
          ignoreClick = true;
        }
        switch (dir) {
        case RIGHT:
          right();
          break;
        case LEFT:
          left();
          break;
        case UP:
          up();
          break;
        case DOWN:
          down();
          break;
        }
      }

      this.show = function () {
        cardDiv.style.display = "block";
      };

      this.hide = function () {
        cardDiv.style.display = "none";
      };

      this.setupEvents = function () {
        interfaceDiv.onclick = onClick;
        interfaceDiv.onmousedown = onMouseDown;
        interfaceDiv.onmouseup = onMouseUp;
        /*
          cardDiv.addEventListener("touchstart", card.touchstart, false);
          cardDiv.addEventListener("touchend", card.touchend, false);
        */
        cardDiv.onselectstart = function () { return false; };
      };
    }

    function handleCards(result) {
      var i, l, card, cardDiv;
      if (result && result.items) {
        l = result.items.length;
        for (i = 0; i < l; i++) {
          card = findCard(result.items[i].id);
          if (card) {
            card.updateText(result.items[i].text);
            card.updateDate(result.items[i].when);
            card.updateImage(result.items[i].image);
            card.updateCardType();
          } else {
            card = new Card(CONTENT_CARD, result.items[i].id, result.items[i].text, result.items[i].when, result.items[i].image);
            cards.push(card);
            cardDiv = card.createDiv();
            mainDiv.appendChild(cardDiv);
            card.setupEvents();
          }
        }
      }
      l = cards.length;
      for (i = 0; i < l; i++) {
        cards[i].updateDisplayDate();
      }
    }


    function fetchCards() {
      timer = undefined;
      mirror.timeline.list().execute(function (result) {
        handleCards(result);
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
      if (running || global.glassDemoMode) { return; }
      timer = global.setTimeout(fetchCards, 1);
      running = true;
    };

    function initialize() {
      var card, cardDiv;

      mainDiv.innerHTML = "";

      card = new Card(START_CARD, "start");
      cards.push(card);
      cardDiv = card.createDiv();
      mainDiv.appendChild(cardDiv);
      card.setupEvents();

      card = new Card(CLOCK_CARD, "clock");
      cards.push(card);
      cardDiv = card.createDiv();
      mainDiv.appendChild(cardDiv);
      card.setupEvents();

      if (glassDemoMode) {
        handleCards(demoCards);
      }
    }

    // Some debug functions, should be removed for real use
    this.getCards = function () { return cards; };

    initialize();
  }

  global.onSignInCallback = function (authResult) {
    if (authResult.access_token) {
      global.gapi.client.load("mirror", "v1", function () {
        doc.getElementById("signin").style.display = "none";
        doc.getElementById("signout").style.display = "block";
        doc.getElementById("glass").style.display = "block";
        global.glassapp = global.glassapp || new Glass();
        global.glassapp.start();
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
    if (global.glassDemoMode) {
      global.glassapp = global.glassapp || new Glass();
      return;
    }
    doc.getElementById("signout_button").onclick = function () {
      var script, token;
      if (global.glassapp) { global.glassapp.stop(); }
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