(function (global) {
  "use strict";
  var doc = global.document, console = global.console, Tween;

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

  /**
   * Basic tween object
   * @constructor
   */
  Tween = function (element, attribute, type, from, to, duration) {
    var raf, started, update, me;
    type = type || "";
    this.then = function (cb) {
      this._cb = cb;
      if (this._done) { cb(); }
    };

    raf =
      global.requestAnimationFrame || global.mozRequestAnimationFrame
      || global.webkitRequestAnimationFrame || global.msRequestAnimationFrame;

    if (raf) {
      started = new Date();
      me = this;
      update = function () {
        var t = ((new Date()) - started) / 1000;
        if (t <= duration) {
          element.style[attribute] = (from + ((to - from) * t / duration)) + type;
          raf(update);
        } else {
          element.style[attribute] = to + type;
          me._done = true;
          if (me._cb !== undefined) { me._cb(); }
        }
      };
      raf(update);
    } else {
      this._done = true;
    }
  };

  /**
   * Main Glass object
   * @constructor
   */
  function Glass() {
    var
      startCard, shareCards = [], replyCard,
      demoCards, demoShareEntities, templates, actions,
      mirror,
      emulator = this,
      mainDiv = doc.getElementById("glass"),
      activeCard,
      timer, running = false,
      START_CARD = 1, CLOCK_CARD = 2, CONTENT_CARD = 3, ACTION_CARD = 4, SHARE_CARD = 5, REPLY_CARD = 6, HTML_BUNDLE_CARD = 7, CARD_BUNDLE_CARD = 8,
      recognition, mouseX, mouseY, glassevent, Card, ActionCard, ClockCard, ReplyCard, lastCardSync, timestep;

    /*@type{enum}*/
    glassevent = {UP: 1, DOWN: 2, LEFT: 3, RIGHT: 4, TAP: 5};

    demoCards = {
      "items": [
        {
          "text": "Just some text... easiest Card ever",
          "cardOptions": [{"action": "SHARE"}, {"action": "REPLY"}],
          "when": "2013-04-12T16:21:41.000000",
          "id": 7
        },
        {
          "html": "<b>Html Bundle Cards</b><br><p style=\"font-size: 40px\">have a cover page...</p>",
          "htmlPages": [
            "<p style=\"color: blue; text-align: left; font-weight: 300;\">...and...</p>",
            "<p style=\"color: red; text-align: center; font-weight: 300;\">...several...</p>",
            "<p style=\"color: green; text-align: right; font-weight: 300;\">...pages.</p>"
          ],
          "cardOptions": [{"action": "SHARE"}],
          "when": "2013-04-12T15:36:41.000000",
          "id": 6
        },
        {
          "html": "<ul style=\"font-size: 40px; margin-left: 30px;\"><li>Just</li><li>some</li><li>simple</li><li>html</li></ul><img src=\"http://cdn4.iconfinder.com/data/icons/gnome-desktop-icons-png/PNG/48/Gnome-Face-Smile-48.png\">",
          "when": "2013-04-12T15:35:41.000000",
          "id": 5
        },
        {
          "text": "Card Bundles can have mixed content, like an image...",
          "image": "https://lh6.googleusercontent.com/-wS9sJ-3oHao/TRnf4MmmlvI/AAAAAAAABX4/BebMZPistPo/s967/2010_09_20+-+Moon.jpg",
          "cardOptions": [{"action": "SHARE"}, {"action": "REPLY"}],
          "when": "2013-04-12T15:34:41.000000",
          "bundleId": 123,
          "id": 3
        },
        {
          "text": "...or just text...",
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
          "when": "2013-04-12T15:33:41.000000",
          "id": 4,
          "bundleId": 123
        },
        {
          "html": "<p style=\"font-size: 40px\">...or maybe some <b style=\"color: blue\">HTML</b></p>",
          "cardOptions": [{"action": "READ_ALOUD"}],
          "when": "2013-04-12T15:32:41.000000",
          "id": 2,
          "bundleId": 123
        },
        {
          "text": "Sample Image Card",
          "image": "https://lh5.googleusercontent.com/-L7PvYS3WeJQ/TvqB-VcRklI/AAAAAAAAP9U/eEBCbBNS9bY/s1012/IMG_0135-2.jpg",
          "cardOptions": [{"action": "SHARE"}, {"action": "REPLY"}],
          "when": "2013-04-12T15:31:41.000000",
          "id": 1
        }
      ]
    };

    demoShareEntities = {
      "items": [
        {
          "imageUrls": ["https://lh3.googleusercontent.com/-ZO4sujjRC-A/UOIniBoro3I/AAAAAAAAx8s/HQ5EhSH8YuA/s1013/IMG_1720.jpg"],
          "displayName": "Fireworks",
          "id": "fireworks"
        },
        {
          "imageUrls": ["https://lh4.googleusercontent.com/-qmJ8gxQYMkc/T0v4Ker0nRI/AAAAAAAATME/CzdYK65ZSuc/s1013/IMG_7706.JPG"],
          "displayName": "Android",
          "id": "android"
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
          "iconUrl": "../images/share.png"
        }]
      },
      "REPLY": {
        "action": "REPLY",
        "id": "REPLY",
        "values": [{
          "displayName": "Reply",
          "iconUrl": "../images/reply.png"
        }]
      },
      "READ_ALOUD": {
        "action": "READ_ALOUD",
        "id": "READ_ALOUD",
        "values": [{
          "displayName": "Read aloud",
          "iconUrl": "../images/read_aloud.png"
        }]
      }
    };

    templates = [];
    templates[START_CARD] =
      "<div class=\"card_interface\"></div>";
    templates[CLOCK_CARD] =
      "<div class=\"card_date\"></div>" +
      "<div class=\"card_text\"></div>" +
      "<div class=\"card_interface\"></div>";
    templates[CONTENT_CARD] =
      "<iframe frameborder=\"0\" allowtransparency=\"true\" scrolling=\"no\" src=\"inner.html\" class=\"card_iframe\"></iframe>" +
      "<div class=\"card_text\"></div>" +
      "<div class=\"card_date\"></div>" +
      "<div class=\"card_interface\"></div>";
    templates[ACTION_CARD] =
      "<div class=\"card_action\"><img class=\"card_icon\"> <div class=\"card_text\"></div></div>" +
      "<div class=\"card_interface\"></div>";
    templates[SHARE_CARD] =
      "<div class=\"card_text\"></div>" +
      "<div class=\"card_interface\"></div>" +
      "<div class=\"card card_type_progress\" style=\"display: none\">" +
      "  <div class=\"card_progress\"><img class=\"card_progress_icon\" src=\"../images/share.png\"> <div class=\"card_progress_text\">Sharing</div></div>" +
      "</div>";
    templates[REPLY_CARD] =
      "<div class=\"card_text\"></div>" +
      "<img class=\"card_icon\" src=\"../images/talk.png\">" +
      "<div class=\"card card_type_progress\" style=\"display: none\">" +
      "  <div class=\"card_progress\"><img class=\"card_progress_icon\" src=\"../images/share.png\"> <div class=\"card_progress_text\">Sharing</div></div>" +
      "</div>";
    templates[HTML_BUNDLE_CARD] =
      "<iframe frameborder=\"0\" allowtransparency=\"true\" scrolling=\"no\" src=\"inner.html\" class=\"card_iframe\"></iframe>" +
      "<div class=\"card_text\"></div>" +
      "<div class=\"card_date\"></div>" +
      "<img class=\"card_icon\" src=\"../images/corner.png\"></div>" +
      "<div class=\"card_interface\"></div>";
    templates[CARD_BUNDLE_CARD] = templates[HTML_BUNDLE_CARD];

    if (!global.glassDemoMode) {
      mirror = global.gapi.client.mirror;
    }

    if (global.webkitSpeechRecognition) {
      recognition = new global.webkitSpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = "en-US";
      recognition.grammars.addFromUri("grammar.grxml", 10);
    }

    function cardSort(a, b) {
      if (a.type === CLOCK_CARD) { return -1; }
      if (b.type === CLOCK_CARD) { return 1; }
      if (!(b.date && a.date)) { return 1; }
      return b.date.getTime() - a.date.getTime();
    }

    /**
     * @returns glassevent
     */
    function getClickDirection(x, y) {
      if (x < 30) { return glassevent.RIGHT; }
      if (x > 610) { return glassevent.LEFT; }
      if (y < 30) { return glassevent.DOWN; }
      if (y > 330) { return glassevent.UP; }
      return glassevent.TAP;
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
        return (dy > 0) ? glassevent.DOWN : glassevent.UP;
      }
      if (dy === 0) {
        return (dx > 0) ? glassevent.RIGHT : glassevent.LEFT;
      }
      tmp = Math.abs(dx / dy);
      if (tmp >= 0.5 && tmp <= 1.5) {
        // direction too diagonal, not distinct enough
        return getClickDirection(x2, y2);
      }

      if (tmp > 1.5) {
        // mainly horizontal movement
        return (dx > 0) ? glassevent.RIGHT : glassevent.LEFT;
      }

      // mainly vertical movement
      return (dy > 0) ? glassevent.DOWN : glassevent.UP;
    }

    /**
     * @constructor
     * @param {Object=} data data for instantiating card
     */
    Card = function (type, id, parent, data) {
      this.init(type, id, parent, data);
    };

    Card.prototype.init = function (type, id, parent, data) {
      data = data || {};
      this.cards = [];
      this.data = data;
      this.id = id;
      this.text = data.text || data.displayName || "";
      this.html = data.html || "";
      this.htmlPages = data.htmlPages || [];
      if (this.htmlPages && this.htmlPages.length > 0) {
        type = HTML_BUNDLE_CARD;
      }
      this.action = data.action || "";
      this.actionId = data.id || "";
      this.type = type;
      this.active = false;
      this.parent = parent;
      if (data.when) {
        this.date = new Date(data.when);
      } else {
        this.date = undefined;
      }
      this.image = data.image;
      if (data.imageUrls && data.imageUrls.length > 0) {
        this.image = data.imageUrls[0];
      }

      if (this.html) {
        // HTML overrides text and image, can't be mixed
        this.text = "";
        this.image = undefined;
      }

      this.createCardElements();
      if (this.type !== CARD_BUNDLE_CARD && data.cardOptions && data.cardOptions.length > 0) {
        this.createActionCards();
      }
      if (this.htmlPages && this.htmlPages.length > 0) {
        this.createHtmlBundle();
      }
    };

    Card.prototype.shareCard = function () {
      var data, me = this;

      if (this.type !== SHARE_CARD) { return; }

      function closeShare() {
        me.progressDiv.style.display = "none";
        me.hide();
        me.parent.hide();
        me.parent.parent.show();
      }

      function onSuccess() {
        me.progressIconDiv.src = "../images/success.png";
        me.progressTextDiv.innerHTML = "Shared";
        global.setTimeout(closeShare, 2000);
      }

      function onError() {
        me.progressIconDiv.src = "../images/error.png";
        me.progressTextDiv.innerHTML = "Failed";
        global.setTimeout(closeShare, 2000);
      }

      /**
       * TODO: Sharing Progress should be separate overlay which can be
       * animated in
       */
      this.progressIconDiv.src = "../images/share.png";
      this.progressTextDiv.innerHTML = "Sharing";
      this.progressDiv.style.display = "block";
      if (global.glassDemoMode) {
        global.setTimeout(onSuccess, 2000);
      } else {
        data = {};
        data.collection = "timeline";
        data.itemId = this.parent.parent.id;
        data.operation = "SHARE";
        data.value = this.id;
        mirror.actions.insert({"resource": data}).execute(function (resp) {
          console.log(resp);
          if (resp.success) {
            onSuccess();
          } else {
            onError();
          }
        });
      }
    };

    /**
     * User up event
     */
    Card.prototype.up = function () {
      this.tap();
    };

    /**
     * User down event
     */
    Card.prototype.down = function () {
      if (!!this.parent) {
        if (this.parent.type == ACTION_CARD) {

          this.parent.show();
          this.parent.animateIn();
          this.hide();
        } else {
          emulator.switchToCard(this.parent);
        }
      }
    };

    /**
     * User left event
     */
    Card.prototype.left = function () {
      var pos;
      if (!!this.parent) {
        pos = this.parent.findPosition(this.id, this.type === ACTION_CARD);
        if (pos < this.parent.cardCount(this.type === ACTION_CARD) - 1) {
          this.hide();
          this.parent.showCard(pos + 1, this.type === ACTION_CARD);
        }
      }
    };

    /**
     * User right event
     */
    Card.prototype.right = function () {
      var pos;
      if (!!this.parent) {
        pos = this.parent.findPosition(this.id, this.type === ACTION_CARD);
        if (pos > 0) {
          this.hide();
          this.parent.showCard(pos - 1, this.type === ACTION_CARD);
        }
      }
    };

    /**
     * User tap event
     * @param {boolean=} action
     */
    Card.prototype.tap = function (action) {
      if (this.type === SHARE_CARD) {
        this.shareCard();
        return;
      }

      if (this.type === CONTENT_CARD && this.parent.type === HTML_BUNDLE_CARD && this.parent.hasActions()) {
        this.parent.showActions();
        this.hide();
      }

      if (this.type === CONTENT_CARD || action) {
        if (this.actionCards && this.actionCards.length > 0) {
          emulator.introduceActionCard(this.actionCards[0]);
          return;
        }
      }

      // "power on"
      if (this.cards && this.cards.length > 0) {
        if (this.type !== HTML_BUNDLE_CARD) { this.cards.sort(cardSort); }
        emulator.switchToCard(this.cards[0]);
        return;
      }
    };


    Card.prototype.updateDisplayDate = function () {
      switch (this.type) {
      case CONTENT_CARD:
      case HTML_BUNDLE_CARD:
      case CARD_BUNDLE_CARD:
        this.dateDiv.innerHTML = "";
        if (this.date) { this.dateDiv.appendChild(doc.createTextNode(this.date.niceDate())); }
        break;
      }
    };


    Card.prototype.updateCardStyle = function (noHide) {
      var shadow = "", pos, last;
      this.cardDiv.className = "card";

      if (this.active) {
        if (
          (this.cards && this.cards.length > 0)
            || this.action === "SHARE"
            || (this.actionCards && this.actionCards.length > 0)
            || (this.parent && this.parent.hasActions())
        ) {
          shadow += "_down";
        }

        if (!!this.parent) {
          pos = this.parent.findPosition(this.id, this.type === ACTION_CARD);
          last = this.parent.cardCount(this.type === ACTION_CARD) - 1;
          if (pos > 0) {
            shadow += "_left";
          }
          if (pos < last) {
            shadow += "_right";
          }
          shadow += "_up";
        }

        if (shadow !== "") {
          this.cardDiv.classList.add("shadow" + shadow);
        }
      } else {
        if (!noHide) {
          this.cardDiv.style.display = "none";
        }
      }

      if (this.type === HTML_BUNDLE_CARD || this.type === CARD_BUNDLE_CARD) {
        this.cardDiv.classList.add("card_type_bundle");
      }

      switch (this.type) {
      case START_CARD:
        break;
      case REPLY_CARD:
        this.cardDiv.classList.add("card_type_reply");
        break;
      case CLOCK_CARD:
        this.cardDiv.classList.add("card_type_clock");
        break;
      case CONTENT_CARD:
      case HTML_BUNDLE_CARD:
      case CARD_BUNDLE_CARD:
        if (!!this.html) {
          this.cardDiv.classList.add("card_type_html");
        } else {
          if (!!this.image) {
            this.cardDiv.classList.add("card_type_image");
          } else {
            this.cardDiv.classList.add("card_type_text");
          }
        }
        break;
      case ACTION_CARD:
        this.cardDiv.classList.add("card_type_action");
        break;
      case SHARE_CARD:
        this.cardDiv.classList.add("card_type_share");
        break;
      }
    };

    Card.prototype.show = function () {
      this.active = true;
      this.updateDisplayDate();
      this.updateCardStyle();
      this.cardDiv.style.display = "block";

      activeCard = this;

      if (this.type === CLOCK_CARD && recognition) {
        recognition.onstart = function (e) {
          console.log(e);
        };
        recognition.onresult = function (e) {
          var i, interim = "";
          for (i = e.resultIndex; i < e.results.length; i++) {
            if (e.results[i].isFinal) {
              this.speech_result += e.results[i][0].transcript;
            } else {
              interim += e.results[i][0].transcript;
            }
          }
          console.log("Final: " + this.speech_result);
          console.log("Interim: " + interim);
        };
        recognition.onerror = function (e) {
          console.log(e);
        };
        recognition.onend = function (e) {
          console.log(e);
        };
        this.speech_result = "";
        // recognition.start();
        // TODO: actually make recognition do something
      }

      if (this.type === REPLY_CARD && this.parent) {
        this.sendReply();
      }

      if (this.type === ACTION_CARD) {
        this.textDiv.innerHTML = "";
        if (!!actions[this.action]) {
          this.textDiv.appendChild(doc.createTextNode(actions[this.action].values[0].displayName));
          this.iconDiv.src = actions[this.action].values[0].iconUrl;
        } else {
          this.textDiv.appendChild(doc.createTextNode(this.data.values[0].displayName));
          this.iconDiv.src = this.data.values[0].iconUrl;
        }
      }
    };

    /**
     * @param {boolean=} shadowOnly optional
     */
    Card.prototype.hide = function () {
      this.active = false;
      this.cardDiv.style.display = "none";

      if (this.type === CLOCK_CARD && recognition) {
        recognition.stop();
      }
    };

    Card.prototype.update = function (data) {
      var tmpDate;
      if (data.when) {
        tmpDate = new Date(data.when);
        if (this.date.getTime() !== tmpDate.getTime()) {
          this.date = tmpDate;
          this.updateDisplayDate();
        }
      }
      if (this.html !== data.html) {
        this.html = data.html || "";
        this.htmlDiv.innerHTML = this.html;
      }
      if (this.html) {
        // HTML overrides text and image in card, can't be mixed
        this.text = "";
        this.image = undefined;
        this.cardDiv.style.backgroundImage = "none";
        this.textDiv.innerHTML = "";
      } else {
        if (this.text !== data.text) {
          this.text = data.text || "";
          this.textDiv.innerHTML = "";
          this.textDiv.appendChild(doc.createTextNode(this.text));
        }
        if (this.image !== data.image) {
          if (data.image && !this.html) {
            this.image = data.image;
            this.cardDiv.style.backgroundImage = "url(" + this.image + ")";
          } else {
            this.image = undefined;
            this.cardDiv.style.backgroundImage = "none";
          }
        }
      }
      this.updateCardStyle();
    };

    /** Traverse the card tree looking for a card */
    Card.prototype.findCard = function (id) {
      var i, l, card;
      l = this.cards.length;
      for (i = 0; i < l; i++) {
        if (this.cards[i].id === id) {
          return this.cards[i];
        }
        if (this.cards[i].type === CARD_BUNDLE_CARD) {
          card = this.cards[i].findCard(id);
          if (card) {
            return card;
          }
        }
      }
      return undefined;
    };

    Card.prototype.cardCount = function (action) {
      var array;
      if (this.type === ACTION_CARD && this.action === "SHARE") {
        array = shareCards;
      } else {
        array = action ? this.actionCards : this.cards;
      }
      return array.length;
    };

    Card.prototype.findPosition = function (id, action) {
      var i, l, array;
      if (this.type === ACTION_CARD && this.action === "SHARE") {
        array = shareCards;
      } else {
        if (action) {
          array = this.actionCards;
        } else {
          array = this.cards;
          if (this.type !== HTML_BUNDLE_CARD) {
            array.sort(cardSort);
          }
        }
      }
      l = array.length;
      for (i = 0; i < l; i++) {
        if (array[i].id === id) {
          return i;
        }
      }
    };

    Card.prototype.showCard = function (pos, action) {
      if (this.type === ACTION_CARD && this.action === "SHARE") {
        emulator.slideToCard(shareCards[pos]);
      } else {
        if (action) {
          emulator.slideToCard(this.actionCards[pos]);
        } else {
          emulator.slideToCard(this.cards[pos]);
        }
      }
    };

    Card.prototype.addCard = function (card) {
      this.cards.push(card);
    };

    Card.prototype.hasActions = function () {
      if (this.type !== HTML_BUNDLE_CARD) { return false; }
      return (this.actionCards && this.actionCards.length > 0);
    };

    Card.prototype.showActions = function () {
      if (this.type !== HTML_BUNDLE_CARD) { return; }
      this.tap(true);
    };

    /**
     * Overload this for subclasses
     */
    Card.prototype.createCardElements = function () {
      this.createDiv();
    };


    Card.prototype.createDiv = function () {
      var me = this;
      this.cardDiv = doc.createElement("div");
      this.cardDiv.id = "c" + this.id;
      this.cardDiv.innerHTML = templates[this.type];
      mainDiv.appendChild(this.cardDiv);
      this.textDiv = this.cardDiv.querySelector(".card_text");
      this.dateDiv = this.cardDiv.querySelector(".card_date");
      this.interfaceDiv = this.cardDiv.querySelector(".card_interface");
      this.iconDiv = this.cardDiv.querySelector(".card_icon");
      this.progressDiv = this.cardDiv.querySelector(".card_type_progress");
      this.progressIconDiv = this.cardDiv.querySelector(".card_progress_icon");
      this.progressTextDiv = this.cardDiv.querySelector(".card_progress_text");
      switch (this.type) {
      case CONTENT_CARD:
      case HTML_BUNDLE_CARD:
      case CARD_BUNDLE_CARD:
        this.htmlFrame = this.cardDiv.querySelector(".card_iframe");
        this.htmlFrame.onload = function () {
          me.htmlDiv = me.htmlFrame.contentWindow.document.getElementById("html");
          if (!!me.html) {
            me.htmlDiv.innerHTML = me.html;
          }
        };
        if (!!this.text) {
          this.textDiv.appendChild(doc.createTextNode(this.text));
        }
        if (this.date) { this.dateDiv.appendChild(doc.createTextNode(this.date.niceDate())); }
        if (this.image) {
          this.cardDiv.style.backgroundImage = "url(" + this.image + ")";
        }
        break;

      case SHARE_CARD:
        this.textDiv.appendChild(doc.createTextNode(this.text));
        this.cardDiv.style.backgroundImage = "url(" + this.image + ")";
        break;
      }
      this.updateCardStyle();
    };

    Card.prototype.createActionCards = function () {
      var i, l;
      this.actionCards = this.actionCards || [];
      l = this.data.cardOptions.length;
      for (i = 0; i < l; i++) {
        if (this.data.cardOptions[i].action) {
          this.actionCards.push(new ActionCard(this.id + "_" + this.data.cardOptions[i].action, this, this.data.cardOptions[i]));
        }
      }
    };

    /** @constructor */
    ActionCard = function (id, parent, data) {
      this.init(ACTION_CARD, id, parent, data);
    };

    ActionCard.prototype = new Card();

    ActionCard.prototype.createCardElements = function () {
      this.createDiv();
      if (!!actions[this.action]) {
        this.textDiv.appendChild(doc.createTextNode(actions[this.action].values[0].displayName));
        this.iconDiv.src = actions[this.action].values[0].iconUrl;
      } else {
        this.textDiv.appendChild(doc.createTextNode(this.data.values[0].displayName));
        this.iconDiv.src = this.data.values[0].iconUrl;
      }
    };

    ActionCard.prototype.animateIn = function () {
      var wrapDiv;
      this.active = true;
      activeCard = this;
      wrapDiv = this.cardDiv.getElementsByClassName('card_action')[0];
      new Tween(wrapDiv, 'paddingTop', '%', 50, 1, 0.25);
      new Tween(this.cardDiv, 'opacity', null, 0, 1, 0.25);
    };

    ActionCard.prototype.animateOut = function () {
      var cd, h, wrapDiv;
      this.active = false;
      cd = this.cardDiv;
      h = function () {
        cd.style.display = "none";
      };

      if (this.type === ACTION_CARD) {
        wrapDiv = this.cardDiv.getElementsByClassName('card_action')[0];
        new Tween(wrapDiv, 'paddingTop', '%', 1, 50, 0.25);
        (new Tween(this.cardDiv, 'opacity', null, 1, 0, 0.25)).then(h);
      } else {
        h();
      }
    };

    /**
     * Overload handler to animate out
     */
    ActionCard.prototype.down = function () {
      var cd, h, wrapDiv;
      cd = this.cardDiv;
      h = function () {
        cd.style.display = "none";
      };

      if (this.type === ACTION_CARD) {
        wrapDiv = this.cardDiv.getElementsByClassName('card_action')[0];
        new Tween(wrapDiv, 'paddingTop', '%', 1, 50, 0.25);
        (new Tween(this.cardDiv, 'opacity', null, 1, 0, 0.25)).then(h);
      } else {
        h();
      }

      activeCard = this.parent;
      activeCard.show();
    };


    ActionCard.prototype.tap = function () {
      this.startAction();
    };

    ActionCard.prototype.sendCustomAction = function () {
      var data, me = this;

      if (this.type !== ACTION_CARD || this.action !== "CUSTOM") { return; }

      function closeAction() {
        me.hide();
        me.parent.show();
      }

      function onSuccess() {
        me.iconDiv.src = "../images/success.png";
        me.textDiv.innerHTML = "Sent";
        global.setTimeout(closeAction, 2000);
      }

      function onError() {
        me.iconDiv.src = "../images/error.png";
        me.textDiv.innerHTML = "Failed";
        global.setTimeout(closeAction, 2000);
      }

      this.active = false;
      this.updateCardStyle(true);
      this.iconDiv.src = "../images/share.png";
      this.textDiv.innerHTML = "Sending";
      if (global.glassDemoMode) {
        global.setTimeout(onSuccess, 2000);
      } else {
        data = {};
        data.collection = "timeline";
        data.itemId = this.parent.id;
        data.operation = "CUSTOM";
        data.value = this.actionId;
        mirror.actions.insert({"resource": data}).execute(function (resp) {
          console.log(resp);
          if (resp.success) {
            onSuccess();
          } else {
            onError();
          }
        });
      }
    };

    ActionCard.prototype.startAction = function () {
      var i, l;
      switch (this.action) {
      case "SHARE":
        l = shareCards.length;
        if (l === 0) { return; }
        for (i = 0; i < l; i++) {
          shareCards[i].parent = this;
        }
        shareCards[0].show();
        this.animateOut();
        break;
      case "REPLY":
        this.hide();
        replyCard.parent = this;
        replyCard.show();
        break;
      case "CUSTOM":
        this.sendCustomAction();
        break;
      }
    };


    Card.prototype.createHtmlBundle = function () {
      var i, l;
      l = this.htmlPages.length;
      for (i = 0; i < l; i++) {
        this.cards.push(new Card(CONTENT_CARD, this.id + "_" + i, this, {"html": this.htmlPages[i]}));
      }
    };


    /** @constructor */
    ClockCard = function (id, parent) {
      this.init(CLOCK_CARD, id, parent);
    };

    ClockCard.prototype = new Card();

    ClockCard.prototype.createCardElements = function () {
      this.createDiv();
      this.dateDiv.appendChild(doc.createTextNode((new Date()).formatTime()));
      this.textDiv.appendChild(doc.createTextNode("\"ok glass\""));
    };

    ClockCard.prototype.updateDisplayDate = function () {
      this.dateDiv.innerHTML = "";
      this.dateDiv.appendChild(doc.createTextNode((new Date()).formatTime()));
    };


    ClockCard.prototype.tap = function () {
      this.parent.show();
      this.hide();
    };


    /** @constructor */
    ReplyCard = function (id, parent) {
      this.init(REPLY_CARD, id, parent);
    };

    ReplyCard.prototype = new Card();

    ReplyCard.prototype.createCardElements = function () {
      this.createDiv();
      this.textDiv.innerHTML = "Speak your message";
    };

    ReplyCard.prototype.sendReply = function () {
      var result = "", me = this;
      if (this.type !== REPLY_CARD) { return; }
      this.textDiv.classList.remove("real_input");
      this.textDiv.innerHTML = "Speak your message";
      this.progressDiv.style.display = "none";

      function closeReply() {
        me.progressDiv.style.display = "none";
        me.hide();
        me.parent.hide();
        me.parent.parent.show();
      }

      function onSuccess() {
        me.progressIconDiv.src = "../images/success.png";
        me.progressTextDiv.innerHTML = "Sent";
        me.progressDiv.style.display = "block";
        global.setTimeout(closeReply, 2000);
      }

      function onError() {
        me.progressIconDiv.src = "../images/error.png";
        me.progressTextDiv.innerHTML = "Failed";
        me.progressDiv.style.display = "block";
        global.setTimeout(closeReply, 2000);
      }

      if (recognition) {
        recognition.interimResults = true;
        recognition.continuous = false;
        recognition.onstart = function () {
          result = "";
        };
        recognition.onresult = function (e) {
          var i;
          console.log(e);
          for (i = e.resultIndex; i < e.results.length; i++) {
            if (e.results[i].isFinal) {
              result += e.results[i][0].transcript;
            }
          }
          me.textDiv.innerHTML = result;
          me.textDiv.classList.add("real_input");
        };
        recognition.onerror = onError;
        recognition.onend = function () {
          var data;
          if (result !== "") {
            me.progressIconDiv.src = "../images/reply.png";
            me.progressTextDiv.innerHTML = "Sending";
            me.progressDiv.style.display = "block";
            if (global.glassDemoMode) {
              global.setTimeout(onSuccess, 2000);
            } else {
              // create Timeline Card with reply text
              data = {};
              data.text = result;
              mirror.timeline.insert({"resource": data}).execute(function (resp) {
                var action;
                console.log(resp);
                if (resp.id) {
                  // Send action with reply card id and ID of original card
                  action = {};
                  action.collection = "timeline";
                  action.itemId = resp.id;
                  action.operation = "REPLY";
                  action.value = me.parent.parent.id.toString();
                  mirror.actions.insert({"resource": action}).execute(function (actionResp) {
                    console.log(actionResp);
                    if (actionResp.success) {
                      onSuccess();
                    } else {
                      onError();
                    }
                  });
                } else {
                  onError();
                }
              });
            }
          } else {
            onError();
          }
        };
        recognition.start();
      }
    };



    /** Event Listeners */

    function onMouseDown(e) {
      mouseX = e.pageX - activeCard.cardDiv.offsetLeft;
      mouseY = e.pageY - activeCard.cardDiv.offsetTop;
    }

    function onTouchStart(e) {
      if (e.changedTouches && e.changedTouches.length > 0) {
        e.preventDefault();
        mouseX = e.changedTouches[0].pageX - activeCard.cardDiv.offsetLeft;
        mouseY = e.changedTouches[0].pageY - activeCard.cardDiv.offsetTop;
      }
    }

    /**
     * Convert a movement to a UI Event
     */
    function makeMove(x1, y1, x2, y2) {
      /** @type {glassevent} */
      var dir;
      dir = getDirection(x1, y1, x2, y2);

      switch (dir) {
      case glassevent.RIGHT:
        activeCard.right();
        break;
      case glassevent.LEFT:
        activeCard.left();
        break;
      case glassevent.UP:
        activeCard.up();
        break;
      case glassevent.DOWN:
        activeCard.down();
        break;
      case glassevent.TAP:
        activeCard.tap();
        break;
      }
    }

    function onTouchEnd(e) {
      var x, y;
      if (e.changedTouches && e.changedTouches.length > 0) {
        e.preventDefault();
        x = e.changedTouches[0].pageX - activeCard.cardDiv.cardDiv.offsetLeft;
        y = e.changedTouches[0].pageY - activeCard.cardDiv.cardDiv.offsetTop;
        makeMove(mouseX, mouseY, x, y);
      }
    }

    function onMouseUp(e) {
      var x, y;
      if (e.which !== 2 && e.button !== 2) {
        x = e.pageX - activeCard.cardDiv.offsetLeft;
        y = e.pageY - activeCard.cardDiv.offsetTop;

        makeMove(mouseX, mouseY, x, y);
      }
    }

    function handleCards(result) {
      var i, l, card, bundles = {}, bundleId, bundleCard;
      if (result && result.items) {
        l = result.items.length;
        for (i = 0; i < l; i++) {
          card = startCard.findCard(result.items[i].id);
          if (card) {
            card.update(result.items[i]);
          } else {
            if (result.items[i].bundleId) {
              bundleId = "b" + result.items[i].bundleId;
              // handle card bundels separately
              if (!bundles[bundleId]) {
                bundles[bundleId] = [];
              }
              bundles[bundleId].push(result.items[i]);
            } else {
              card = new Card(CONTENT_CARD, result.items[i].id, startCard, result.items[i]);
              startCard.addCard(card);
            }
          }
        }
      }
      for (bundleId in bundles) {
        if (bundles.hasOwnProperty(bundleId)) {
          bundleCard = startCard.findCard(bundleId);
          if (!bundleCard) {
            bundleCard = new Card(CARD_BUNDLE_CARD, bundleId, startCard, bundles[bundleId][0]);
            startCard.addCard(bundleCard);
          }
          l = bundles[bundleId].length;
          for (i = 0; i < l; i++) {
            bundleCard.addCard(new Card(CONTENT_CARD, bundles[bundleId][i].id, bundleCard, bundles[bundleId][i]));
          }
        }
      }
    }

    function fetchCards() {
      timer = undefined;
      mirror.timeline.list().execute(function (result) {
        console.log(result);
        handleCards(result);
      });
    }

    lastCardSync = 0;
    /** Called every 1s - use to schedule updates etc **/
    timestep = function () {
      var now = (new Date());

      // Keep clock up to date
      activeCard.updateDisplayDate();

      if (!global.glassDemoMode && ((now - lastCardSync) > 30000)) {
        lastCardSync = new Date();
        fetchCards();
      }

      timer = global.setTimeout(timestep, 1000);
    };

    function handleShareEntities(result) {
      var i, l;
      if (result && result.items) {
        l = result.items.length;
        for (i = 0; i < l; i++) {
          shareCards.push(new Card(SHARE_CARD, result.items[i].id, undefined, result.items[i]));
        }
      }
    }

    function fetchShareEntities() {
      mirror.shareEntities.list().execute(function (result) {
        console.log(result);
        handleShareEntities(result);
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
      timer = global.setTimeout(timestep, 1);
      running = true;
    };


    /** TODO: Add nice slide effect here */
    this.slideToCard = function (newcard) {
      var oldcard = activeCard;
      activeCard = newcard;
      newcard.show();
      oldcard.hide();
    };

    /** Go straight to a card without fancy effects */
    this.switchToCard = function (newcard) {
      var oldcard = activeCard;
      activeCard = newcard;
      newcard.show();
      oldcard.hide();
    };

    /** Only hide style of parent card */
    this.introduceActionCard = function (newcard) {
      var oldcard = activeCard;
      activeCard = newcard;
      oldcard.active = false;
      oldcard.updateCardStyle(true);
      newcard.show();
      newcard.animateIn();
    };

    /**
     * Set up main UI event handlers
     */
    this.setupEvents = function () {
      if (global.ontouchstart !== undefined) {
        mainDiv.addEventListener("touchstart", onTouchStart, false);
        mainDiv.addEventListener("touchend", onTouchEnd, false);
      } else {
        mainDiv.onmousedown = onMouseDown;
        mainDiv.onmouseup = onMouseUp;
      }

      //TODO
      mainDiv.onselectstart = function () { return false; };
    };

    this.initialize = function () {
      var card;

      mainDiv.innerHTML = "";

      startCard = new Card(START_CARD, "start");

      replyCard = new ReplyCard("reply");

      card = new ClockCard("clock", startCard);
      startCard.addCard(card);

      if (global.glassDemoMode) {
        handleShareEntities(demoShareEntities);
        handleCards(demoCards);
      } else {
        fetchShareEntities();
      }

      activeCard = startCard;
      activeCard.show();

      this.setupEvents();
    };

    this.initialize();
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
      global.glassapp.start();
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
