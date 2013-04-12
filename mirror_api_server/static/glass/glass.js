(function (global) {
  "use strict";
  var doc = global.document, console = global.console;

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
      startCard, shareCards = [], replyCard,
      demoCards, demoShareEntities, templates, actions,
      mirror,
      mainDiv = doc.getElementById("glass"),
      timer, running = false,
      START_CARD = 1, CLOCK_CARD = 2, CONTENT_CARD = 3, ACTION_CARD = 4, SHARE_CARD = 5, REPLY_CARD = 6, HTML_BUNDLE_CARD = 7, CARD_BUNDLE_CARD = 8,
      UP = 1, DOWN = 2, LEFT = 3, RIGHT = 4,
      recognition;

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
      var
        cardDiv, textDiv, htmlFrame, htmlDiv, dateDiv, interfaceDiv, iconDiv, progressDiv, progressIconDiv, progressTextDiv, mouseX, mouseY,
        that = this, cards = [], actionCards = [];
      data = data || {};
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

      function shareCard() {
        var data;

        if (type !== SHARE_CARD) { return; }

        function closeShare() {
          progressDiv.style.display = "none";
          that.hide();
          that.parent.hide();
          that.parent.parent.show();
        }

        function onSuccess() {
          progressIconDiv.src = "../images/success.png";
          progressTextDiv.innerHTML = "Shared";
          global.setTimeout(closeShare, 2000);
        }

        function onError() {
          progressIconDiv.src = "../images/error.png";
          progressTextDiv.innerHTML = "Failed";
          global.setTimeout(closeShare, 2000);
        }

        that.hide(true);
        progressIconDiv.src = "../images/share.png";
        progressTextDiv.innerHTML = "Sharing";
        progressDiv.style.display = "block";
        if (global.glassDemoMode) {
          global.setTimeout(onSuccess, 2000);
        } else {
          data = {};
          data.collection = "timeline";
          data.itemId = that.parent.parent.id;
          data.operation = "SHARE";
          data.value = that.id;
          mirror.actions.insert({"resource": data}).execute(function (resp) {
            console.log(resp);
            if (resp.success) {
              onSuccess();
            } else {
              onError();
            }
          });
        }
      }

      function sendCustomAction() {
        var data;

        if (type !== ACTION_CARD || that.action !== "CUSTOM") { return; }

        function closeAction() {
          that.hide();
          that.parent.show();
        }

        function onSuccess() {
          iconDiv.src = "../images/success.png";
          textDiv.innerHTML = "Sent";
          global.setTimeout(closeAction, 2000);
        }

        function onError() {
          iconDiv.src = "../images/error.png";
          textDiv.innerHTML = "Failed";
          global.setTimeout(closeAction, 2000);
        }

        that.hide(true);
        iconDiv.src = "../images/share.png";
        textDiv.innerHTML = "Sending";
        if (global.glassDemoMode) {
          global.setTimeout(onSuccess, 2000);
        } else {
          data = {};
          data.collection = "timeline";
          data.itemId = that.parent.id;
          data.operation = "CUSTOM";
          data.value = that.actionId;
          mirror.actions.insert({"resource": data}).execute(function (resp) {
            console.log(resp);
            if (resp.success) {
              onSuccess();
            } else {
              onError();
            }
          });
        }
      }

      function sendReply() {
        var result = "";
        if (type !== REPLY_CARD) { return; }
        textDiv.classList.remove("real_input");
        textDiv.innerHTML = "Speak your message";
        progressDiv.style.display = "none";

        function closeReply() {
          progressDiv.style.display = "none";
          that.hide();
          that.parent.hide();
          that.parent.parent.show();
        }

        function onSuccess() {
          progressIconDiv.src = "../images/success.png";
          progressTextDiv.innerHTML = "Sent";
          progressDiv.style.display = "block";
          global.setTimeout(closeReply, 2000);
        }

        function onError() {
          progressIconDiv.src = "../images/error.png";
          progressTextDiv.innerHTML = "Failed";
          progressDiv.style.display = "block";
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
            textDiv.innerHTML = result;
            textDiv.classList.add("real_input");
          };
          recognition.onerror = onError;
          recognition.onend = function () {
            var data;
            if (result !== "") {
              progressIconDiv.src = "../images/reply.png";
              progressTextDiv.innerHTML = "Sending";
              progressDiv.style.display = "block";
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
                    action.value = that.parent.parent.id.toString();
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
      }

      function startReply() {
        if (type !== ACTION_CARD || that.action !== "REPLY") { return; }

        that.hide();
        replyCard.parent = that;
        replyCard.show();
      }

      function up(action) {
        var i, l;
        if (type === ACTION_CARD && that.action === "SHARE") {
          l = shareCards.length;
          if (l === 0) { return; }
          for (i = 0; i < l; i++) {
            shareCards[i].parent = that;
          }
          shareCards[0].show();
          that.hide();
          return;
        }
        if (type === SHARE_CARD) {
          shareCard();
          return;
        }

        if (type === ACTION_CARD) {
          if (that.action === "REPLY") {
            startReply();
            return;
          }
          if (that.action === "CUSTOM") {
            sendCustomAction();
            return;
          }
        }

        if (type === CONTENT_CARD && that.parent.type === HTML_BUNDLE_CARD && that.parent.hasActions()) {
          that.parent.showActions();
          that.hide();
        }

        if (type === CONTENT_CARD || action) {
          if (actionCards && actionCards.length > 0) {
            actionCards[0].show();
            that.hide(true);
            return;
          }
        }

        if (cards && cards.length > 0) {
          if (type !== HTML_BUNDLE_CARD) { cards.sort(cardSort); }
          cards[0].show();
          that.hide();
          return;
        }
      }

      function down() {
        if (!!that.parent) {
          that.hide();
          that.parent.show();
        }
      }

      function left() {
        var pos;
        if (!!that.parent) {
          pos = that.parent.findPosition(that.id, type === ACTION_CARD);
          if (pos < that.parent.cardCount(type === ACTION_CARD) - 1) {
            that.hide();
            that.parent.showCard(pos + 1, type === ACTION_CARD);
          }
        }
      }

      function right() {
        var pos;
        if (!!that.parent) {
          pos = that.parent.findPosition(that.id, type === ACTION_CARD);
          if (pos > 0) {
            that.hide();
            that.parent.showCard(pos - 1, type === ACTION_CARD);
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

      function updateDisplayDate() {
        switch (type) {
        case CLOCK_CARD:
          dateDiv.innerHTML = "";
          dateDiv.appendChild(doc.createTextNode((new Date()).formatTime()));
          break;
        case CONTENT_CARD:
        case HTML_BUNDLE_CARD:
        case CARD_BUNDLE_CARD:
          dateDiv.innerHTML = "";
          if (that.date) { dateDiv.appendChild(doc.createTextNode(that.date.niceDate())); }
          break;
        }
      }

      function updateCardStyle() {
        var shadow = "", pos, last;
        cardDiv.className = "card";

        if (that.active) {
          if (
            (cards && cards.length > 0)
              || that.action === "SHARE"
              || (actionCards && actionCards.length > 0)
              || (that.parent && that.parent.hasActions())
          ) {
            shadow += "_down";
          }

          if (!!that.parent) {
            pos = that.parent.findPosition(that.id, type === ACTION_CARD);
            last = that.parent.cardCount(type === ACTION_CARD) - 1;
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

        if (type === HTML_BUNDLE_CARD || type === CARD_BUNDLE_CARD) {
          cardDiv.classList.add("card_type_bundle");
        }

        switch (type) {
        case START_CARD:
          break;
        case REPLY_CARD:
          cardDiv.classList.add("card_type_reply");
          break;
        case CLOCK_CARD:
          cardDiv.classList.add("card_type_clock");
          break;
        case CONTENT_CARD:
        case HTML_BUNDLE_CARD:
        case CARD_BUNDLE_CARD:
          if (!!that.html) {
            cardDiv.classList.add("card_type_html");
          } else {
            if (!!that.image) {
              cardDiv.classList.add("card_type_image");
            } else {
              cardDiv.classList.add("card_type_text");
            }
          }
          break;
        case ACTION_CARD:
          cardDiv.classList.add("card_type_action");
          break;
        case SHARE_CARD:
          cardDiv.classList.add("card_type_share");
          break;
        }
      }

      this.show = function () {
        this.active = true;
        updateDisplayDate();
        updateCardStyle();
        cardDiv.style.display = "block";

        if (that.type === CLOCK_CARD && recognition) {
          recognition.onstart = function (e) {
            console.log(e);
          };
          recognition.onresult = function (e) {
            var i, interim = "";
            for (i = e.resultIndex; i < e.results.length; i++) {
              if (e.results[i].isFinal) {
                that.speech_result += e.results[i][0].transcript;
              } else {
                interim += e.results[i][0].transcript;
              }
            }
            console.log("Final: " + that.speech_result);
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

        if (that.type === REPLY_CARD && that.parent) {
          sendReply();
        }

        if (that.type === ACTION_CARD) {
          textDiv.innerHTML = "";
          if (!!actions[that.action]) {
            textDiv.appendChild(doc.createTextNode(actions[that.action].values[0].displayName));
            iconDiv.src = actions[that.action].values[0].iconUrl;
          } else {
            textDiv.appendChild(doc.createTextNode(data.values[0].displayName));
            iconDiv.src = data.values[0].iconUrl;
          }
        }
      };

      this.hide = function (shadowOnly) {
        this.active = false;
        if (shadowOnly) {
          updateCardStyle();
        } else {
          cardDiv.style.display = "none";
        }
        if (that.type === CLOCK_CARD && recognition) {
          recognition.stop();
        }
      };

      this.update = function (data) {
        var tmpDate;
        if (data.when) {
          tmpDate = new Date(data.when);
          if (this.date.getTime() !== tmpDate.getTime()) {
            this.date = tmpDate;
            updateDisplayDate();
          }
        }
        if (this.html !== data.html) {
          this.html = data.html || "";
          htmlDiv.innerHTML = this.html;
        }
        if (this.html) {
          // HTML overrides text and image in card, can't be mixed
          this.text = "";
          this.image = undefined;
          cardDiv.style.backgroundImage = "none";
          textDiv.innerHTML = "";
        } else {
          if (this.text !== data.text) {
            this.text = data.text || "";
            textDiv.innerHTML = "";
            textDiv.appendChild(doc.createTextNode(this.text));
          }
          if (this.image !== data.image) {
            if (data.image && !this.html) {
              this.image = data.image;
              cardDiv.style.backgroundImage = "url(" + that.image + ")";
            } else {
              this.image = undefined;
              cardDiv.style.backgroundImage = "none";
            }
          }
        }
        updateCardStyle();
      };

      this.findCard = function (id) {
        var i, l, card;
        l = cards.length;
        for (i = 0; i < l; i++) {
          if (cards[i].id === id) {
            return cards[i];
          }
          if (cards[i].type === CARD_BUNDLE_CARD) {
            card = cards[i].findCard(id);
            if (card) {
              return card;
            }
          }
        }
        return undefined;
      };

      this.cardCount = function (action) {
        var array;
        if (this.type === ACTION_CARD && this.action === "SHARE") {
          array = shareCards;
        } else {
          array = action ? actionCards : cards;
        }
        return array.length;
      };

      this.findPosition = function (id, action) {
        var i, l, array;
        if (this.type === ACTION_CARD && this.action === "SHARE") {
          array = shareCards;
        } else {
          if (action) {
            array = actionCards;
          } else {
            array = cards;
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

      this.showCard = function (pos, action) {
        if (type === ACTION_CARD && that.action === "SHARE") {
          shareCards[pos].show();
        } else {
          if (action) {
            actionCards[pos].show();
          } else {
            cards[pos].show();
          }
        }
      };

      this.addCard = function (card) {
        cards.push(card);
      };

      this.hasActions = function () {
        if (this.type !== HTML_BUNDLE_CARD) { return false; }
        return (actionCards && actionCards.length > 0);
      };

      this.showActions = function () {
        if (this.type !== HTML_BUNDLE_CARD) { return; }
        up(true);
      };

      function createDiv() {
        cardDiv = doc.createElement("div");
        cardDiv.id = "c" + id;
        cardDiv.innerHTML = templates[type];
        mainDiv.appendChild(cardDiv);
        textDiv = cardDiv.querySelector(".card_text");
        dateDiv = cardDiv.querySelector(".card_date");
        interfaceDiv = cardDiv.querySelector(".card_interface");
        iconDiv = cardDiv.querySelector(".card_icon");
        progressDiv = cardDiv.querySelector(".card_type_progress");
        progressIconDiv = cardDiv.querySelector(".card_progress_icon");
        progressTextDiv = cardDiv.querySelector(".card_progress_text");
        switch (type) {
        case CLOCK_CARD:
          dateDiv.appendChild(doc.createTextNode((new Date()).formatTime()));
          textDiv.appendChild(doc.createTextNode("\"ok glass\""));
          break;

        case CONTENT_CARD:
        case HTML_BUNDLE_CARD:
        case CARD_BUNDLE_CARD:
          htmlFrame = cardDiv.querySelector(".card_iframe");
          htmlFrame.onload = function () {
            htmlDiv = htmlFrame.contentWindow.document.getElementById("html");
            if (!!that.html) {
              htmlDiv.innerHTML = that.html;
            }
          };
          if (!!that.text) {
            textDiv.appendChild(doc.createTextNode(that.text));
          }
          if (that.date) { dateDiv.appendChild(doc.createTextNode(that.date.niceDate())); }
          if (that.image) {
            cardDiv.style.backgroundImage = "url(" + that.image + ")";
          }
          break;

        case ACTION_CARD:
          if (!!actions[that.action]) {
            textDiv.appendChild(doc.createTextNode(actions[that.action].values[0].displayName));
            iconDiv.src = actions[that.action].values[0].iconUrl;
          } else {
            textDiv.appendChild(doc.createTextNode(data.values[0].displayName));
            iconDiv.src = data.values[0].iconUrl;
          }
          break;

        case SHARE_CARD:
          textDiv.appendChild(doc.createTextNode(that.text));
          cardDiv.style.backgroundImage = "url(" + that.image + ")";
          break;

        case REPLY_CARD:
          textDiv.innerHTML = "Speak your message";
          break;
        }
        updateCardStyle();
        that.hide();
      }

      function createActionCards() {
        var i, l;
        l = data.cardOptions.length;
        for (i = 0; i < l; i++) {
          if (data.cardOptions[i].action) {
            actionCards.push(new Card(ACTION_CARD, that.id + "_" + data.cardOptions[i].action, that, data.cardOptions[i]));
          }
        }
      }

      function setupEvents() {
        if (!interfaceDiv) { return; }
        if (global.ontouchstart !== undefined) {
          interfaceDiv.addEventListener("touchstart", onTouchStart, false);
          interfaceDiv.addEventListener("touchend", onTouchEnd, false);
        } else {
          interfaceDiv.onmousedown = onMouseDown;
          interfaceDiv.onmouseup = onMouseUp;
        }
        cardDiv.onselectstart = function () { return false; };
      }

      function createHtmlBundle() {
        var i, l;
        l = that.htmlPages.length;
        for (i = 0; i < l; i++) {
          cards.push(new Card(CONTENT_CARD, that.id + "_" + i, that, {"html": that.htmlPages[i]}));
        }
      }

      function initialize() {
        createDiv();
        setupEvents();
        if (that.type !== CARD_BUNDLE_CARD && data.cardOptions && data.cardOptions.length > 0) {
          createActionCards();
        }
        if (that.htmlPages && that.htmlPages.length > 0) {
          createHtmlBundle();
        }
      }

      initialize();
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
        timer = global.setTimeout(fetchCards, 30000);
      });
    }

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
      if (running || global.glassDemoMode) { return; }
      timer = global.setTimeout(fetchCards, 1);
      running = true;
    };

    function initialize() {
      var card;

      mainDiv.innerHTML = "";

      startCard = new Card(START_CARD, "start");

      replyCard = new Card(REPLY_CARD, "reply");

      card = new Card(CLOCK_CARD, "clock", startCard);
      startCard.addCard(card);

      if (global.glassDemoMode) {
        handleShareEntities(demoShareEntities);
        handleCards(demoCards);
      } else {
        fetchShareEntities();
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