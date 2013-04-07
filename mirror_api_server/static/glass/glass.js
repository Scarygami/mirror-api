(function (global) {
  "use strict";
  var doc = global.document, console = global.console, demoCards, templates, actions;

  demoCards = {
    "items": [
      {
        "text": "Also works with Data-URIs!",
        "image": "https://lh5.googleusercontent.com/-L7PvYS3WeJQ/TvqB-VcRklI/AAAAAAAAP9U/eEBCbBNS9bY/s1012/IMG_0135-2.jpg",
        "cardOptions": [{"action": "SHARE"}, {"action": "REPLY"}],
        "when": "2013-04-05T12:36:52.755260",
        "id": 1
      },
      {
        "text": "Hello World!",
        "cardOptions": [{"action": "READ_ALOUD"}],
        "when": "2013-04-05T12:26:55.837450",
        "id": 2
      },
      {
        "text": "What a nice photo!",
        "image": "http://farm5.staticflickr.com/4122/4784220578_2ce8d9fac3_b.jpg",
        "cardOptions": [{"action": "SHARE"}, {"action": "REPLY"}],
        "when": "2013-04-05T11:32:19.603850",
        "id": 3
      },
      {
       "text": "Awesome!",
       "cardOptions": [
        {
         "action": "CUSTOM",
         "values": [
          {
           "iconUrl": "http://cdn4.iconfinder.com/data/icons/gnome-desktop-icons-png/PNG/48/Gnome-Face-Smile-48.png",
           "displayName": "Smile"
          }
         ],
         "id": "smile"
        }
       ],
       "when": "2013-04-07T12:45:41.841880",
       "id": 4,
      }
    ]
  };

  // Predefined actions
  actions = {
    "SHARE": {
      "action": "SHARE",
      "id": "SHARE",
      "values": [{
        "displayName": "Share",
        "iconUrl": "https://mirror-api.appspot.com/images/share.png"
      }]
    },
    "REPLY": {
      "action": "REPLY",
      "id": "REPLY",
      "values": [{
        "displayName": "Reply",
        "iconUrl": "https://mirror-api.appspot.com/images/reply.png"
      }]
    },
    "READ_ALOUD": {
      "action": "READ_ALOUD",
      "id": "READ_ALOUD",
      "values": [{
        "displayName": "Read aloud",
        "iconUrl": "https://mirror-api.appspot.com/images/read_aloud.png"
      }]
    }
  };

  templates = {
    "start": "<div class=\"card_interface\"></div>",
    "normal": "<div class=\"card_text\"></div><div class=\"card_date\"></div><div class=\"card_interface\"></div>",
    "action": "<div class=\"card_action\"><img class=\"card_icon\"> <div class=\"card_text\"></div></div><div class=\"card_interface\"></div>"
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
      startCard,
      mirror,
      mainDiv = doc.getElementById("glass"),
      timer, running = false,
      START_CARD = 1, CLOCK_CARD = 2, CONTENT_CARD = 3, ACTION_CARD = 4,
      UP = 1, DOWN = 2, LEFT = 3, RIGHT = 4;

    if (!global.glassDemoMode) {
      mirror = global.gapi.client.mirror;
    }

    function cardSort(a, b) {
      if (a.type === CLOCK_CARD) { return -1; }
      if (b.type === CLOCK_CARD) { return 1; }
      return b.date.getTime() - a.date.getTime();
    }

    function getClickDirection(x, y) {
      if (x < 30) { return RIGHT; }
      if (x > 610) { return LEFT; }
      if (y < 30) { return DOWN; }
      if (y > 330) { return UP; }
      return UP;
    }

    function getDirection(x1, y1, x2, y2) {
      var tmp, dx, dy;
      dx = x2 - x1;
      dy = y2 - y1;
      if (dx * dx + dy * dy < 3000) {
        // move too short
        return getClickDirection(x2, y2);
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
        return getClickDirection(x2, y2);
      }

      if (tmp > 1.5) {
        // mainly horizontal movement
        return (dx > 0) ? RIGHT : LEFT;
      }

      // mainly vertical movement
      return (dy > 0) ? DOWN : UP;
    }

    function Card(type, id, parent, data) {
      var cardDiv, textDiv, dateDiv, interfaceDiv, mouseX, mouseY, ignoreClick = false, that = this, cards = [];
      data = data || {};
      this.id = id;
      this.text = data.text || "";
      this.action = data.action || "";
      this.type = type;
      if (data.when) {
        this.date = new Date(data.when);
      } else {
        this.date = new Date();
      }
      this.image = data.image;
      type = type || CONTENT_CARD;

      this.cardCount = function () {
        return cards.length;
      };

      this.showCard = function (pos) {
        cards[pos].show();
      };

      function loadImage() {
        cardDiv.style.backgroundImage = "url(" + that.image + ")";
      }

      function up() {
        if (cards && cards.length > 0) {
          cards[0].show();
          that.hide(type === CONTENT_CARD);
        }
      }

      function down() {
        if (!!parent) {
          that.hide();
          parent.show();
        }
      }

      function left() {
        var pos;
        if (!!parent) {
          pos = parent.findPosition(that.id);
          if (pos < parent.cardCount() - 1) {
            that.hide();
            parent.showCard(pos + 1);
          }
        }
      }

      function right() {
        var pos;
        if (!!parent) {
          pos = parent.findPosition(that.id);
          if (pos > 0) {
            that.hide();
            parent.showCard(pos - 1);
          }
        }
      }

      function onMouseDown(e) {
        mouseX = e.pageX - cardDiv.offsetLeft;
        mouseY = e.pageY - cardDiv.offsetTop;
      }

      function onTouchStart(e) {
        if (e.changedTouches && e.changedTouches.length > 0) {
          e.preventDefault();
          mouseX = e.changedTouches[0].pageX - cardDiv.offsetLeft;
          mouseY = e.changedTouches[0].pageY - cardDiv.offsetTop;
        }
      }

      function makeMove(x1, y1, x2, y2) {
        var dir;
        dir = getDirection(x1, y1, x2, y2);

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

      function onTouchEnd(e) {
        var x, y;
        if (e.changedTouches && e.changedTouches.length > 0) {
          e.preventDefault();
          x = e.changedTouches[0].pageX - cardDiv.offsetLeft;
          y = e.changedTouches[0].pageY - cardDiv.offsetTop;
          makeMove(mouseX, mouseY, x, y);
        }
      }

      function onMouseUp(e) {
        var x, y;
        if (e.which !== 2 && e.button !== 2) {
          x = e.pageX - cardDiv.offsetLeft;
          y = e.pageY - cardDiv.offsetTop;

          makeMove(mouseX, mouseY, x, y);
        }
      }

      this.show = function () {
        // Update timestamp
        this.updateDisplayDate();
        cardDiv.style.display = "block";
        this.updateCardStyle();
      };

      this.hide = function (shadowOnly) {
        if (shadowOnly) {
          this.updateCardStyle(true);
        } else {
          cardDiv.style.display = "none";
        }
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
          }
          this.updateCardStyle();
        }
      };

      this.updateDisplayDate = function () {
        var i, l;
        switch (type) {
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

      this.updateCardStyle = function (noShadow) {
        var shadow = "", pos, last;
        cardDiv.className = "card";

        if (!noShadow) {
          if (cards && cards.length > 0) {
            shadow += "_down";
          }

          if (!!parent) {
            pos = parent.findPosition(this.id);
            last = parent.cardCount() - 1;
            if (pos > 0) {
              shadow += "_left";
            }
            if (pos < last) {
              shadow += "_right";
            }
            shadow += "_up";
          }

          if (shadow !== "") {
            cardDiv.classList.add("shadow" + shadow);
          }
        }

        switch (type) {
        case START_CARD:
          break;
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
        case ACTION_CARD:
          cardDiv.classList.add("card_type_action");
          break;
        }
      };

      this.getDiv = function () { return cardDiv; };

      this.findCard = function (id) {
        var i, l;
        l = cards.length;
        for (i = 0; i < l; i++) {
          if (cards[i].id === id) {
            return cards[i];
          }
        }
        return undefined;
      };

      this.findPosition = function (id) {
        var i, l;
        cards.sort(cardSort);
        l = cards.length;
        for (i = 0; i < l; i++) {
          if (cards[i].id === id) {
            return i;
          }
        }
      };

      this.addCard = function (card) {
        cards.push(card);
      };

      function setupEvents() {
        if (global.ontouchstart !== undefined) {
          interfaceDiv.addEventListener("touchstart", onTouchStart, false);
          interfaceDiv.addEventListener("touchend", onTouchEnd, false);
        } else {
          interfaceDiv.onmousedown = onMouseDown;
          interfaceDiv.onmouseup = onMouseUp;
        }
        cardDiv.onselectstart = function () { return false; };
      }

      function createDiv() {
        cardDiv = doc.createElement("div");
        cardDiv.id = "c" + id;

        switch (type) {
        case START_CARD:
          cardDiv.innerHTML = templates.start;
          mainDiv.appendChild(cardDiv);
          break;
        case CLOCK_CARD:
          cardDiv.innerHTML = templates.normal;
          mainDiv.appendChild(cardDiv);
          textDiv = cardDiv.querySelector(".card_text");
          textDiv.appendChild(doc.createTextNode("\"ok glass\""));
          dateDiv = cardDiv.querySelector(".card_date");
          dateDiv.appendChild(doc.createTextNode((new Date()).formatTime()));
          break;
        case CONTENT_CARD:
          cardDiv.innerHTML = templates.normal;
          mainDiv.appendChild(cardDiv);
          textDiv = cardDiv.querySelector(".card_text");
          textDiv.appendChild(doc.createTextNode(that.text));
          dateDiv = cardDiv.querySelector(".card_date");
          dateDiv.appendChild(doc.createTextNode(that.date.niceDate()));
          if (that.image) {
            loadImage();
          }
          break;
        case ACTION_CARD:
          cardDiv.innerHTML = templates.action;
          mainDiv.appendChild(cardDiv);
          textDiv = cardDiv.querySelector(".card_text");
          if (!!actions[that.action]) {
            textDiv.appendChild(doc.createTextNode(actions[that.action].values[0].displayName));
            cardDiv.querySelector(".card_icon").src = actions[that.action].values[0].iconUrl;
          } else {
            textDiv.appendChild(doc.createTextNode(data.values[0].displayName));
            cardDiv.querySelector(".card_icon").src = data.values[0].iconUrl;
          }
          break;
        }

        interfaceDiv = cardDiv.querySelector(".card_interface");
        that.updateCardStyle();
        that.hide();
      }

      function createActionCards() {
        var i, l;
        l = data.cardOptions.length;
        for (i = 0; i < l; i++) {
          if (data.cardOptions[i].action) {
            cards.push(new Card(ACTION_CARD, that.id + "_" + data.cardOptions[i].action, that, data.cardOptions[i]));
          }
        }
      }

      createDiv();
      setupEvents();
      if (data.cardOptions && data.cardOptions.length > 0) {
        createActionCards();
      }
    }

    function handleCards(result) {
      var i, l, card, cardDiv;
      if (result && result.items) {
        l = result.items.length;
        for (i = 0; i < l; i++) {
          card = startCard.findCard(result.items[i].id);
          if (card) {
            card.updateText(result.items[i].text);
            card.updateDate(result.items[i].when);
            card.updateImage(result.items[i].image);
            card.updateCardStyle();
          } else {
            card = new Card(CONTENT_CARD, result.items[i].id, startCard, result.items[i]);
            startCard.addCard(card);
          }
        }
      }
    }


    function fetchCards() {
      timer = undefined;
      mirror.timeline.list().execute(function (result) {
        console.log(result);
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
      var card;

      mainDiv.innerHTML = "";

      startCard = new Card(START_CARD, "start");

      card = new Card(CLOCK_CARD, "clock", startCard);
      startCard.addCard(card);

      if (global.glassDemoMode) {
        handleCards(demoCards);
      }

      startCard.show();
    }

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