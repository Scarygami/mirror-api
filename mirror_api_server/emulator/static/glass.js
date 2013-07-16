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

  /**
   * Main Glass object
   * @constructor
   */
  function Glass() {
    var
      startCard, shareCards = [], replyCard, mapCard,
      demoCards, demoContacts, templates, actions,
      mirror,
      emulator = this,
      mainDiv = doc.getElementById("glass"),
      activeCard,
      timer, running = false,
      recognition, mouseX, mouseY, glassevent, cardType, Card, ActionCard, ClockCard, ReplyCard, CameraCard, timestep,
      photoCount = 0, lastLocationUpdate = 0, Tween;

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

    /*@type{enum}*/
    glassevent = {UP: 1, DOWN: 2, LEFT: 3, RIGHT: 4, TAP: 5};

    /*@type{enum}*/
    cardType = {
      START_CARD: 1,
      CLOCK_CARD: 2,
      CONTENT_CARD: 3,
      ACTION_CARD: 4,
      SHARE_CARD: 5,
      REPLY_CARD: 6,
      HTML_BUNDLE_CARD: 7,
      CARD_BUNDLE_CARD: 8,
      CAMERA_CARD: 9
    };

    demoCards = {
      "items": [
        {
          "text": "Just some text... easiest Card ever",
          "menuItems": [{"action": "SHARE"}, {"action": "REPLY"}],
          "created": "2013-04-12T16:21:41.000000",
          "updated": "2013-04-12T16:21:41.000000",
          "id": 7
        },
        {
          "html": "<article><section><p class=\"text-x-large\">Html Bundle Cards</p><p class=\"text-normal\">have a cover page...</p></section></article>",
          "htmlPages": [
            "<article><section><p class=\"text-normal align-left blue\">...and...</p></section></article>",
            "<article><section><p class=\"text-normal align-center red\">...several...</p></section></article>",
            "<article><section><p class=\"text-normal align-right green\">...pages.</p></section></article>"
          ],
          "menuItems": [{"action": "SHARE"}],
          "created": "2013-04-12T16:21:41.000000",
          "updated": "2013-04-12T16:21:41.000000",
          "displayDate": new Date(),
          "id": 6
        },
        {
          "html": "<article><figure><img src=\"https://lh6.googleusercontent.com/-wS9sJ-3oHao/TRnf4MmmlvI/AAAAAAAABX4/BebMZPistPo/s967/2010_09_20+-+Moon.jpg\" style=\"width: 100%\"></figure><section><ul><li>Just</li><li>some</li><li>simple</li><li>html</li></ul></section></article>",
          "created": "2013-04-12T15:35:41.000000",
          "updated": "2013-04-16T15:35:41.000000",
          "id": 5
        },
        {
          "text": "Card Bundles can have mixed content, like an image...",
          "attachments": [
            {
              "contentType": "image/jpeg",
              "contentUrl": "https://lh6.googleusercontent.com/-wS9sJ-3oHao/TRnf4MmmlvI/AAAAAAAABX4/BebMZPistPo/s967/2010_09_20+-+Moon.jpg"
            }
          ],
          "menuItems": [{"action": "SHARE"}, {"action": "REPLY"}],
          "created": "2013-04-12T15:34:41.000000",
          "updated": "2013-04-12T15:34:41.000000",
          "bundleId": 123,
          "id": 3
        },
        {
          "text": "...or just text...",
          "menuItems": [
            {
              "action": "CUSTOM",
              "values": [
                {
                  "state": "DEFAULT",
                  "iconUrl": "http://cdn4.iconfinder.com/data/icons/gnome-desktop-icons-png/PNG/48/Gnome-Face-Smile-48.png",
                  "displayName": "Smile"
                }
              ],
              "id": "smile"
            }
          ],
          "created": "2013-04-12T15:33:41.000000",
          "updated": "2013-04-12T15:33:41.000000",
          "id": 4,
          "bundleId": 123
        },
        {
          "html": "<article><section><p class=\"text-normal align-center\">...or maybe some <b class=\"blue\">HTML</b></p></section></article>",
          "menuItems": [{"action": "READ_ALOUD"}],
          "created": "2013-04-12T15:32:41.000000",
          "updated": "2013-04-12T15:32:41.000000",
          "id": 2,
          "bundleId": 123
        },
        {
          "text": "Sample Image Card",
          "attachments": [
            {
              "contentType": "image/jpeg",
              "contentUrl": "https://lh5.googleusercontent.com/-L7PvYS3WeJQ/TvqB-VcRklI/AAAAAAAAP9U/eEBCbBNS9bY/s1012/IMG_0135-2.jpg"
            }
          ],
          "menuItems": [{"action": "SHARE"}, {"action": "REPLY"}, {"action": "TOGGLE_PINNED"}],
          "created": "2013-04-12T15:31:41.000000",
          "updated": "2013-04-12T15:31:41.000000",
          "id": 1
        },
        {
          "id": 8,
          "created": "2013-04-22T16:00:00.000000",
          "updated": "2013-04-22T16:00:00.000000",
          "html": "<article><figure><img src=\"glass://map?w=240&h=360&marker=0;42.369590,-71.107132&marker=1;42.36254,-71.08726&polyline=;42.36254,-71.08726,42.36297,-71.09364,42.36579,-71.09208,42.3697,-71.102,42.37105,-71.10104,42.37067,-71.1001,42.36561,-71.10406,42.36838,-71.10878,42.36968,-71.10703\" height=\"360\" width=\"240\"></figure><section><div class=\"text-auto-size\"><p class=\"yellow\">12 minutes to home</p><p>Medium traffic on Broadway</p></div></section></article>"
        }
      ]
    };

    demoContacts = {
      "items": [
        {
          "acceptTypes": ["image/*"],
          "displayName": "Fireworks",
          "id": "fireworks",
          "imageUrls": ["https://lh3.googleusercontent.com/-ZO4sujjRC-A/UOIniBoro3I/AAAAAAAAx8s/HQ5EhSH8YuA/s1013/IMG_1720.jpg"]
        },
        {
          "acceptTypes": ["image/*"],
          "displayName": "Android",
          "id": "android",
          "imageUrls": ["https://lh4.googleusercontent.com/-qmJ8gxQYMkc/T0v4Ker0nRI/AAAAAAAATME/CzdYK65ZSuc/s1013/IMG_7706.JPG"]
        }
      ]
    };

    // Predefined actions
    actions = {
      "SHARE": {
        "action": "SHARE",
        "id": "SHARE",
        "values": [{
          "state": "DEFAULT",
          "displayName": "Share",
          "iconUrl": "images/share.png"
        }]
      },
      "NAVIGATE": {
        "action": "NAVIGATE",
        "id": "NAVIGATE",
        "values": [{
          "state": "DEFAULT",
          "displayName": "Navigate",
          "iconUrl": "images/navigate.png"
        }]
      },
      "REPLY": {
        "action": "REPLY",
        "id": "REPLY",
        "values": [{
          "state": "DEFAULT",
          "displayName": "Reply",
          "iconUrl": "images/reply.png"
        }]
      },
      "READ_ALOUD": {
        "action": "READ_ALOUD",
        "id": "READ_ALOUD",
        "values": [{
          "state": "DEFAULT",
          "displayName": "Read aloud",
          "iconUrl": "images/read_aloud.png"
        }]
      },
      "TOGGLE_PINNED": {
        "action": "TOGGLE_PINNED",
        "id": "TOGGLE_PINNED",
        "values": [{
          "state": "DEFAULT",
          "displayName": "Pin/Unpin card",
          "iconUrl": "images/pin.png"
        }]
      }
    };

    templates = [];
    templates[cardType.START_CARD] = "";
    templates[cardType.CLOCK_CARD] =
      "<div class=\"card_date\"></div>" +
      "<div class=\"card_text\"></div>";
    templates[cardType.CONTENT_CARD] =
      "<iframe frameborder=\"0\" allowtransparency=\"true\" scrolling=\"no\" src=\"inner.html\" class=\"card_iframe\"></iframe>" +
      "<img class=\"card_icon\" src=\"images/corner.png\"></div>" +
      "<div class=\"card_interface\"></div>";
    templates[cardType.ACTION_CARD] =
      "<div class=\"card_action\"><img class=\"card_icon\"> <div class=\"card_text\"></div></div>";
    templates[cardType.SHARE_CARD] =
      "<div class=\"card_text\"></div>" +
      "<div class=\"card card_type_progress\" style=\"display: none\">" +
      "  <div class=\"card_progress\"><img class=\"card_progress_icon\" src=\"images/share.png\"> <div class=\"card_progress_text\">Sharing</div></div>" +
      "</div>";
    templates[cardType.REPLY_CARD] =
      "<div class=\"card_text\"></div>" +
      "<img class=\"card_icon\" src=\"images/talk.png\">" +
      "<div class=\"card card_type_progress\" style=\"display: none\">" +
      "  <div class=\"card_progress\"><img class=\"card_progress_icon\" src=\"images/share.png\"> <div class=\"card_progress_text\">Sharing</div></div>" +
      "</div>";
    templates[cardType.CAMERA_CARD] =
      "<video class=\"card_video\"></video>" +
      "<canvas style=\"display: none\" class=\"card_canvas\"></canvas>" +
      "<div class=\"card_text\"></div>";
    templates[cardType.HTML_BUNDLE_CARD] = templates[cardType.CONTENT_CARD];
    templates[cardType.CARD_BUNDLE_CARD] = templates[cardType.CONTENT_CARD];

    if (!global.glassDemoMode) {
      mirror = global.gapi.client.mirror;
    }

    if (global.webkitSpeechRecognition) {
      recognition = new global.webkitSpeechRecognition();
      recognition.lang = "en-US";
      recognition.grammars.addFromUri("grammar.grxml", 10);
    }

    global.navigator.getUserMedia =
      global.navigator.getUserMedia || global.navigator.webkitGetUserMedia
      || global.navigator.mozGetUserMedia || global.navigator.msGetUserMedia;

    function cardSort(a, b) {
      if (a.isPinned || b.isPinned) {
        if (!b.isPinned) { return -1; }
        if (!a.isPinned) { return 1; }
        if (!(b.date && a.date)) { return 1; }
        return a.date.getTime() - b.date.getTime();
      }
      if (a.type === cardType.CLOCK_CARD) { return -1; }
      if (b.type === cardType.CLOCK_CARD) { return 1; }
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
      var tmpDate, i, l, att;
      data = data || {};
      this.cards = [];
      this.data = data;
      this.id = id;
      this.text = data.text || data.displayName || "";
      this.html = data.html || "";
      this.htmlPages = data.htmlPages || [];
      if (this.htmlPages && this.htmlPages.length > 0) {
        type = cardType.HTML_BUNDLE_CARD;
      }
      this.action = data.action || "";
      this.actionId = data.id || "";
      this.type = type;
      this.active = false;
      this.parent = parent;
      this.bundleId = data.bundleId;
      this.isPinned = !!data.isPinned;
      this.isBundleCover = !!data.isBundleCover;
      tmpDate = data.displayDate || data.updated || data.created;
      if (tmpDate) {
        this.date = new Date(tmpDate);
      } else {
        this.date = undefined;
      }
      if (data.attachments && data.attachments.length > 0) {
        l = data.attachments.length;
        for (i = 0; i < l; i++) {
          att = data.attachments[i];
          if (att.contentType.indexOf("image/") === 0) {
            this.imageType = att.contentType;
            if (att.id) {
              this.image = "/glass/attachment/" + this.id + "/" + att.id;
            } else {
              this.image = att.contentUrl;
            }
            break;
          }
        }
      }
      if (data.imageUrls && data.imageUrls.length > 0) {
        this.image = data.imageUrls[0];
      }

      if (this.html) {
        // HTML overrides text and image, can't be mixed
        this.text = "";
        this.image = undefined;
      }

      this.createCardElements();
      if (this.type !== cardType.CARD_BUNDLE_CARD && data.menuItems && data.menuItems.length > 0) {
        this.createActionCards();
      }
      if (this.htmlPages && this.htmlPages.length > 0) {
        this.createHtmlBundle();
      }
    };

    Card.prototype.shareCard = function () {
      var data, me = this, sharedCard = this.parent.parent;

      if (this.type !== cardType.SHARE_CARD) { return; }

      function closeShare() {
        me.progressDiv.style.display = "none";
        me.hide();
        me.parent.hide();
        me.parent.parent.show();
      }

      function onSuccess() {
        me.progressIconDiv.src = "images/success.png";
        me.progressTextDiv.innerHTML = "Shared";
        global.setTimeout(closeShare, 2000);
      }

      function onError() {
        me.progressIconDiv.src = "images/error.png";
        me.progressTextDiv.innerHTML = "Failed";
        global.setTimeout(closeShare, 2000);
      }

      function sendAction() {
        var data = {};
        data.collection = "timeline";
        data.itemId = sharedCard.id;
        data.action = "SHARE";
        mirror.internal.actions.insert({"resource": data}).execute(function (resp) {
          console.log(resp);
          if (resp.success) {
            onSuccess();
          } else {
            onError();
          }
        });
      }

      function shareMedia() {
        var data, boundary, delimiter, close_delim, imageData, multipartRequestBody, xhr;

        if (sharedCard.image.indexOf("data:image/") !== 0) {
          // can't share non data-uri's
          onError();
          return;
        }

        imageData = sharedCard.image.substring(("data:" + sharedCard.imageType + ";base64,").length);

        data = {};
        if (sharedCard.text) {
          data.text = sharedCard.text;
        }
        if (sharedCard.data.menuItems) {
          data.menuItems = sharedCard.data.menuItems;
        }
        data.recipients = [me.data];

        boundary = "-------314159265358979323846";
        delimiter = "\r\n--" + boundary + "\r\n";
        close_delim = "\r\n--" + boundary + "--";

        multipartRequestBody =
          delimiter +
          "Content-Type: application/json\r\n\r\n" +
          JSON.stringify(data) +
          delimiter +
          "Content-Type: " + sharedCard.imageType + "\r\n" +
          "Content-Transfer-Encoding: base64\r\n" +
          "\r\n" +
          imageData +
          close_delim;

        xhr = new global.XMLHttpRequest();
        xhr.onreadystatechange = function () {
          var resp;
          if (xhr.readyState === 4) {
            console.log(xhr.response);
            if (xhr.status === 200) {
              resp = JSON.parse(xhr.response);
              if (resp.id) {
                sharedCard.localOnly = false;
                sharedCard.id = resp.id;
                sharedCard.cardDiv.id = "c" + me.id;
                sendAction();
              } else {
                onError();
              }
            } else {
              console.log("Error sharing media", xhr.status, xhr.statusText);
              onError();
            }
          }
        };

        xhr.open("POST", "/upload/mirror/v1/timeline", true);
        xhr.setRequestHeader("Authorization", "Bearer " + global.gapi.auth.getToken().access_token);
        xhr.setRequestHeader("Content-Type", 'multipart/mixed; boundary="' + boundary + '"');
        xhr.send(multipartRequestBody);
      }

      function shareSimple() {
        var data;
        data = {};
        if (sharedCard.text) {
          data.text = sharedCard.text;
        }
        if (sharedCard.data.menuItems) {
          data.menuItems = sharedCard.data.menuItems;
        }
        data.recipients = [me.data];

        if (data.text) {
          mirror.internal.timeline.insert({"resource": data}).execute(function (resp) {
            console.log(resp);
            if (resp.id) {
              sharedCard.localOnly = false;
              sharedCard.id = resp.id;
              sharedCard.cardDiv.id = "c" + me.id;
              sendAction();
            } else {
              onError();
            }
          });
        } else {
          onError();
        }
      }

      /**
       * TODO: Sharing Progress should be separate overlay which can be
       * animated in
       */
      this.progressIconDiv.src = "images/share.png";
      this.progressTextDiv.innerHTML = "Sharing";
      this.progressDiv.style.display = "block";
      if (global.glassDemoMode) {
        global.setTimeout(onSuccess, 2000);
      } else {
        if (sharedCard.localOnly) {
          if (sharedCard.image) {
            shareMedia();
          } else {
            shareSimple();
          }
        } else {
          sharedCard.data.recipients = sharedCard.data.recipients || [];
          sharedCard.data.recipients.push(this.data);
          data = {"recipients": sharedCard.data.recipients};
          mirror.timeline.patch({"id": sharedCard.id, "resource": data}).execute(function (resp) {
            console.log(resp);
            if (resp.id) {
              sendAction();
            } else {
              onError();
            }
          });
        }
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
        if (this.parent.type === cardType.ACTION_CARD) {
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
        pos = this.parent.findPosition(this.id, this.type === cardType.ACTION_CARD);
        if (pos < this.parent.cardCount(this.type === cardType.ACTION_CARD) - 1) {
          this.hide();
          this.parent.showCard(pos + 1, this.type === cardType.ACTION_CARD);
        }
      }
    };

    /**
     * User right event
     */
    Card.prototype.right = function () {
      var pos;
      if (!!this.parent) {
        pos = this.parent.findPosition(this.id, this.type === cardType.ACTION_CARD);
        if (pos > 0) {
          this.hide();
          this.parent.showCard(pos - 1, this.type === cardType.ACTION_CARD);
        }
      }
    };

    /**
     * User tap event
     * @param {boolean=} action
     */
    Card.prototype.tap = function (action) {
      var i;
      if (this.type === cardType.SHARE_CARD) {
        this.shareCard();
        return;
      }

      if (this.type === cardType.CONTENT_CARD && this.parent.type === cardType.HTML_BUNDLE_CARD && this.parent.hasActions()) {
        this.parent.showActions();
        this.hide();
      }

      if (this.type === cardType.CONTENT_CARD || action) {
        if (this.actionCards && this.actionCards.length > 0) {
          emulator.introduceActionCard(this.actionCards[0]);
          return;
        }
      }

      // "power on"
      if (this.cards && this.cards.length > 0) {
        if (this.type !== cardType.HTML_BUNDLE_CARD) { this.cards.sort(cardSort); }
        i = 0;
        if (this.type === cardType.START_CARD) {
          for (i = 0; i < this.cards.length; i++) {
            if (this.cards[i].type === cardType.CLOCK_CARD) {
              break;
            }
          }
          if (i >= this.cards.length) { i = 0; }
        }
        emulator.switchToCard(this.cards[i]);
        return;
      }
    };


    Card.prototype.updateDisplayDate = function () {
      switch (this.type) {
      case cardType.CONTENT_CARD:
      case cardType.HTML_BUNDLE_CARD:
      case cardType.CARD_BUNDLE_CARD:
        if (this.htmlFrame && this.htmlFrame.contentWindow && this.htmlFrame.contentWindow.updateDate) {
          if (this.date) {
            this.htmlFrame.contentWindow.updateDate(this.date.niceDate());
          } else {
            this.htmlFrame.contentWindow.updateDate("");
          }
        }
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
          pos = this.parent.findPosition(this.id, this.type === cardType.ACTION_CARD);
          last = this.parent.cardCount(this.type === cardType.ACTION_CARD) - 1;
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

      if (this.type === cardType.HTML_BUNDLE_CARD || this.type === cardType.CARD_BUNDLE_CARD) {
        this.cardDiv.classList.add("card_type_bundle");
      }

      switch (this.type) {
      case cardType.REPLY_CARD:
        this.cardDiv.classList.add("card_type_reply");
        break;
      case cardType.CLOCK_CARD:
        this.cardDiv.classList.add("card_type_clock");
        break;
      case cardType.ACTION_CARD:
        this.cardDiv.classList.add("card_type_action");
        break;
      case cardType.SHARE_CARD:
        this.cardDiv.classList.add("card_type_share");
        break;
      case cardType.CAMERA_CARD:
        this.cardDiv.classList.add("card_type_camera");
        break;
      }
    };

    Card.prototype.show = function () {
      this.active = true;
      this.updateDisplayDate();
      this.updateCardStyle();
      this.cardDiv.style.display = "block";
      activeCard = this;
    };

    /**
     * @param {boolean=} shadowOnly optional
     */
    Card.prototype.hide = function () {
      this.active = false;
      this.cardDiv.style.display = "none";

      if (this.type === cardType.CLOCK_CARD && recognition) {
        recognition.stop();
      }
    };

    Card.prototype.update = function (data) {
      var i, l, att, tmpDate = data.displayDate || data.updated || data.created;
      this.data = data;
      if (tmpDate) {
        this.date = new Date(tmpDate);
        this.updateDisplayDate();
      }
      this.html = data.html;
      this.text = data.text;
      this.image = undefined;
      if (data.attachments && data.attachments.length > 0) {
        l = data.attachments.length;
        for (i = 0; i < l; i++) {
          att = data.attachments[i];
          if (att.contentType.indexOf("image/") === 0) {
            this.imageType = att.contentType;
            if (att.id) {
              this.image = "/glass/attachment/" + this.id + "/" + att.id;
            } else {
              this.image = att.contentUrl;
            }
            break;
          }
        }
      }
      if (this.html) {
        // HTML overrides text and image in card, can't be mixed
        this.text = "";
        this.image = undefined;
      }

      if (!data.bundleId) {
        data.isBundleCover = false;
      }
      if (this.bundleId !== data.bundleId) {
        this.bundleId = data.bundleId;
        if (!this.bundleId) {
          if (this.parent) {
            this.parent.removeCard(this.id);
          }
          startCard.addCard(this);
          this.parent = startCard;
        }
      }
      this.isBundleCover = !!data.isBundleCover;

      if (this.type === cardType.CONTENT_CARD && this.isBundleCover) {
        this.type = cardType.CARD_BUNDLE_CARD;
      }
      if (this.type === cardType.CARD_BUNDLE_CARD && !this.isBundleCover) {
        this.type = cardType.CONTENT_CARD;
      }

      if (this.htmlFrame) {
        if (this.date) {
          tmpDate = this.date.niceDate();
        } else {
          tmpDate = "";
        }
        this.htmlFrame.contentWindow.setData(this.text, this.image, this.html, tmpDate);
      }
      this.updateCardStyle();
    };

    /**
     * Traverse the card tree looking for a card
     */
    Card.prototype.findCard = function (id, local) {
      var i, l, card;
      l = this.cards.length;
      for (i = 0; i < l; i++) {
        if (this.cards[i].id === id) {
          return this.cards[i];
        }
        if (!local) {
          card = this.cards[i].findCard(id);
          if (card) {
            return card;
          }
        }
      }
      return undefined;
    };

    /**
     * Traverse the card tree looking for cards with bundleId
     */
    Card.prototype.findBundleCards = function (bundleId) {
      var i, l, cards = [];
      l = this.cards.length;
      for (i = 0; i < l; i++) {
        if (this.cards[i].bundleId === bundleId) {
          cards.push(this.cards[i]);
        }
        cards = cards.concat(this.cards[i].findBundleCards(bundleId));
      }
      return cards;
    };

    Card.prototype.cardCount = function (action) {
      var array;
      if (this.type === cardType.ACTION_CARD && this.action === "SHARE") {
        array = shareCards;
      } else {
        array = action ? this.actionCards : this.cards;
      }
      return array.length;
    };

    Card.prototype.findPosition = function (id, action) {
      var i, l, array;
      if (this.type === cardType.ACTION_CARD && this.action === "SHARE") {
        array = shareCards;
      } else {
        if (action) {
          array = this.actionCards;
        } else {
          array = this.cards;
          if (this.type !== cardType.HTML_BUNDLE_CARD) {
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
      if (this.type === cardType.ACTION_CARD && this.action === "SHARE") {
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
      if (!this.findCard(card.id, true)) {
        this.cards.push(card);
      }
    };

    Card.prototype.removeCard = function (id) {
      var i, l;
      l = this.cards.length;
      for (i = 0; i < l; i++) {
        if (this.cards[i].id === id) {
          this.cards.splice(i, 1);
          break;
        }
      }
    };

    Card.prototype.hasActions = function () {
      if (this.type !== cardType.HTML_BUNDLE_CARD) { return false; }
      return (this.actionCards && this.actionCards.length > 0);
    };

    Card.prototype.showActions = function () {
      if (this.type !== cardType.HTML_BUNDLE_CARD) { return; }
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
      this.iconDiv = this.cardDiv.querySelector(".card_icon");
      this.progressDiv = this.cardDiv.querySelector(".card_type_progress");
      this.progressIconDiv = this.cardDiv.querySelector(".card_progress_icon");
      this.progressTextDiv = this.cardDiv.querySelector(".card_progress_text");
      switch (this.type) {
      case cardType.CONTENT_CARD:
      case cardType.HTML_BUNDLE_CARD:
      case cardType.CARD_BUNDLE_CARD:
        this.htmlFrame = this.cardDiv.querySelector(".card_iframe");
        this.htmlFrame.onload = function () {
          var tmpDate;
          if (me.date) {
            tmpDate = me.date.niceDate();
          } else {
            tmpDate = "";
          }
          me.htmlFrame.contentWindow.setData(me.text, me.image, me.html, tmpDate);
        };
        break;

      case cardType.SHARE_CARD:
        this.textDiv.appendChild(doc.createTextNode(this.text));
        this.cardDiv.style.backgroundImage = "url(" + this.image + ")";
        break;
      }
      this.updateCardStyle();
    };

    /*
     * Remove card from the timeline.
     * Removes the full bundle for HTML Bundles.
     * Removes all action cards associated with the card.
     */
    Card.prototype.remove = function () {
      var i, l;
      if (this.type === cardType.HTML_BUNDLE_CARD) {
        l = this.cards.length;
        for (i = 0; i < l; i++) {
          this.cards[i].remove();
        }
      }
      if (this.actionCards) {
        l = this.actionCards.length;
        for (i = 0; i < l; i++) {
          this.actionCards[i].remove();
        }
      }
      this.cards = [];
      this.actionCards = [];
      this.cardDiv.parentNode.removeChild(this.cardDiv);
      if (this.type === cardType.CONTENT_CARD ||
          this.type === cardType.HTML_BUNDLE_CARD ||
          this.type === cardType.CONTENT_CARD) {
        if (!!this.parent) {
          // wrap in try/catch just in case the parent has been removed before the child card
          try {
            this.parent.removeCard(this.id);
          } catch (e) {
            console.log(e);
          }
        }
      }
    };

    Card.prototype.createActionCards = function () {
      var i, l;
      this.actionCards = this.actionCards || [];
      l = this.data.menuItems.length;
      for (i = 0; i < l; i++) {
        if (this.data.menuItems[i].action) {
          // For menuItem NAVIGATE a location has to be attached to the card
          if (this.data.menuItems[i].action == "NAVIGATE" &&
              (!this.data.location || !this.data.location.latitude || !this.data.location.longitude)) {
            continue;
          }
          // For menuItem READ_ALOUD speakableText or text have to be set
          if (this.data.menuItems[i].action == "READ_ALOUD" &&
              !this.data.text &&
              !this.data.speakableText) {
            continue;
          }
          this.actionCards.push(new ActionCard(this.id + "_" + this.data.menuItems[i].action, this, this.data.menuItems[i]));
        }
      }
    };

    Card.prototype.createHtmlBundle = function () {
      var i, l;
      l = this.htmlPages.length;
      for (i = 0; i < l; i++) {
        this.cards.push(new Card(cardType.CONTENT_CARD, this.id + "_" + i, this, {"html": this.htmlPages[i]}));
      }
    };


    /** @constructor */
    ActionCard = function (id, parent, data) {
      this.init(cardType.ACTION_CARD, id, parent, data);
    };

    ActionCard.prototype = new Card();

    ActionCard.prototype.show = function () {
      Card.prototype.show.call(this);
      this.textDiv.innerHTML = "";
      this.cardDiv.style.opacity = 1;
      this.actionDiv.style.paddingTop = "0%";
      if (!!actions[this.action]) {
        if (this.action == "TOGGLE_PINNED") {
          this.textDiv.appendChild(doc.createTextNode((this.parent.isPinned ? "Unpin" : "Pin")));
        } else {
          this.textDiv.appendChild(doc.createTextNode(actions[this.action].values[0].displayName));
        }
        this.iconDiv.src = actions[this.action].values[0].iconUrl;
      } else {
        this.textDiv.appendChild(doc.createTextNode(this.data.values[0].displayName));
        this.iconDiv.src = this.data.values[0].iconUrl;
      }
    };

    ActionCard.prototype.createCardElements = function () {
      this.createDiv();
      this.actionDiv = this.cardDiv.getElementsByClassName("card_action")[0];
      if (!!actions[this.action]) {
        this.textDiv.appendChild(doc.createTextNode(actions[this.action].values[0].displayName));
        this.iconDiv.src = actions[this.action].values[0].iconUrl;
      } else {
        this.textDiv.appendChild(doc.createTextNode(this.data.values[0].displayName));
        this.iconDiv.src = this.data.values[0].iconUrl;
      }
    };

    ActionCard.prototype.animateIn = function () {
      var tween;
      this.active = true;
      activeCard = this;
      tween = new Tween(this.actionDiv, "paddingTop", "%", 50, 0, 0.25);
      tween = new Tween(this.cardDiv, "opacity", null, 0, 1, 0.25);
    };

    ActionCard.prototype.animateOut = function () {
      var cd, h, tween;
      this.active = false;
      cd = this.cardDiv;
      h = function () {
        cd.style.display = "none";
      };

      tween = new Tween(this.actionDiv, "paddingTop", "%", 0, 50, 0.25);
      (new Tween(this.cardDiv, "opacity", null, 1, 0, 0.25)).then(h);
    };

    /**
     * Overload handler to animate out
     */
    ActionCard.prototype.down = function () {
      this.animateOut();

      activeCard = this.parent;
      activeCard.show();
    };

    ActionCard.prototype.tap = function () {
      this.startAction();
    };

    ActionCard.prototype.sendCustomAction = function () {
      var data, me = this;

      if (this.action !== "CUSTOM") { return; }

      function closeAction() {
        me.hide();
        me.parent.show();
      }

      function onSuccess() {
        me.iconDiv.src = "images/success.png";
        me.textDiv.innerHTML = "Sent";
        global.setTimeout(closeAction, 2000);
      }

      function onError() {
        me.iconDiv.src = "images/error.png";
        me.textDiv.innerHTML = "Failed";
        global.setTimeout(closeAction, 2000);
      }

      this.active = false;
      this.updateCardStyle(true);
      this.iconDiv.src = "images/share.png";
      this.textDiv.innerHTML = "Sending";
      if (global.glassDemoMode) {
        global.setTimeout(onSuccess, 2000);
      } else {
        data = {};
        data.collection = "timeline";
        data.itemId = this.parent.id;
        data.action = "CUSTOM";
        data.value = this.actionId;
        mirror.internal.actions.insert({"resource": data}).execute(function (resp) {
          console.log(resp);
          if (resp.success) {
            onSuccess();
          } else {
            onError();
          }
        });
      }
    };


    ActionCard.prototype.startNavigation = function () {
      var me = this;

      function showMap(lat1, long1, lat2, long2) {
        var url;
        url = "https://maps.googleapis.com/maps/api/staticmap?sensor=false&size=640x360&style=feature:all|element:all|saturation:-100|lightness:-25|gamma:0.5|visibility:simplified&style=feature:roads|element:geometry&style=feature:landscape|element:geometry|lightness:-25";
        if (!!lat2 && !!long2) {
          url += "&markers=color:0xF7594A%7C" + lat2 + "," + long2;
          if (!!lat1 && !!long1) {
            url += "&path=color:0x1871ADFF%7Cweight:8%7C" + lat1 + "," + long1 + "%7C" + lat2 + "," + long2;
          }
        }

        mapCard.update({id: "map", attachments: [{contentType: "image/png", contentUrl: url}]});
        mapCard.parent = me.parent;
        mapCard.show();
        me.parent.hide();
        me.animateOut();
      }

      if (global.navigator.geolocation) {
        global.navigator.geolocation.getCurrentPosition(function (loc) {
          if (!global.glassDemoMode) {
            if (loc.coords && loc.coords.longitude && loc.coords.latitude) {
              showMap(loc.coords.latitude, loc.coords.longitude, me.parent.data.location.latitude, me.parent.data.location.longitude);
            } else {
              showMap(null, null, me.parent.location.latitude, me.parent.data.location.longitude);
            }
          }
        }, function () {
          showMap(null, null, me.parent.location.latitude, me.parent.data.location.longitude);
        });
      } else {
        showMap(null, null, this.parent.location.latitude, this.parent.data.location.longitude);
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
      case "NAVIGATE":
        this.startNavigation();
        break;
      case "TOGGLE_PINNED":
        this.parent.isPinned = !this.parent.isPinned;
        if (!global.glassDemoMode) {
          mirror.timeline.patch({"id": this.parent.id, "resource": {"isPinned": true}}).execute(function (resp) {
            console.log(resp);
          });
        }
        this.down();
        break;
      }
    };


    /** @constructor */
    ClockCard = function (id, parent) {
      this.init(cardType.CLOCK_CARD, id, parent);
    };

    ClockCard.prototype = new Card();

    ClockCard.prototype.show = function () {
      var speech_result = "", me = this, photo = false;
      Card.prototype.show.call(this);

      if (recognition) {

        recognition.onresult = function (e) {
          var i, interim = "";
          for (i = e.resultIndex; i < e.results.length; i++) {
            if (e.results[i].isFinal) {
              speech_result += e.results[i][0].transcript;
            } else {
              interim += e.results[i][0].transcript;
            }
          }
          interim = speech_result + interim;
          if (interim.indexOf("take a picture") >= 0 || interim.indexOf("take a photo") >= 0) {
            photo = true;
            recognition.stop();
          }
        };
        recognition.onerror = function (e) {
          console.log(e);
        };
        recognition.onend = function () {
          if (photo) {
            emulator.switchToCard(me.cards[0]);
          }
        };
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.start();
      }
    };

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
      emulator.switchToCard(this.cards[0]);
    };


    /** @constructor */
    ReplyCard = function (id, parent) {
      this.init(cardType.REPLY_CARD, id, parent);
    };

    ReplyCard.prototype = new Card();

    ReplyCard.prototype.show = function () {
      Card.prototype.show.call(this);
      this.sendReply();
    };

    ReplyCard.prototype.createCardElements = function () {
      this.createDiv();
      this.textDiv.innerHTML = "Speak your message";
    };

    ReplyCard.prototype.sendReply = function () {
      var result = "", me = this;
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
        me.progressIconDiv.src = "images/success.png";
        me.progressTextDiv.innerHTML = "Sent";
        me.progressDiv.style.display = "block";
        global.setTimeout(closeReply, 2000);
      }

      function onError() {
        me.progressIconDiv.src = "images/error.png";
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
          var i, interim = "";
          console.log(e);
          for (i = e.resultIndex; i < e.results.length; i++) {
            if (e.results[i].isFinal) {
              result += e.results[i][0].transcript;
            } else {
              interim += e.results[i][0].transcript;
            }
          }
          me.textDiv.innerHTML = result + "<br>" + interim;
          me.textDiv.classList.add("real_input");
        };
        recognition.onerror = onError;
        recognition.onend = function () {
          var data;
          if (result !== "") {
            me.progressIconDiv.src = "images/reply.png";
            me.progressTextDiv.innerHTML = "Sending";
            me.progressDiv.style.display = "block";
            if (global.glassDemoMode) {
              global.setTimeout(onSuccess, 2000);
            } else {
              // create Timeline Card with reply text
              data = {};
              data.text = result;
              data.inReplyTo = me.parent.parent.id;
              mirror.internal.timeline.insert({"resource": data}).execute(function (resp) {
                var action;
                console.log(resp);
                if (resp.id) {
                  // Send action with reply card id and ID of original card
                  action = {};
                  action.collection = "timeline";
                  action.itemId = resp.id;
                  action.action = "REPLY";
                  mirror.internal.actions.insert({"resource": action}).execute(function (actionResp) {
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

    /** @constructor */
    CameraCard = function (id, parent) {
      this.init(cardType.CAMERA_CARD, id, parent);
    };

    CameraCard.prototype = new Card();

    CameraCard.prototype.show = function () {
      Card.prototype.show.call(this);
      this.startRecording();
    };

    CameraCard.prototype.hide = function () {
      this.video.pause();
      if (this.stream) {
        this.stream.stop();
        this.stream = undefined;
      }
      Card.prototype.hide.call(this);
    };

    CameraCard.prototype.takePicture = function () {
      var me = this;
      me.textDiv.innerHTML = "3";
      global.setTimeout(function () {
        me.textDiv.innerHTML = "2";
        global.setTimeout(function () {
          me.textDiv.innerHTML = "1";
          global.setTimeout(function () {
            var card;
            me.textDiv.innerHTML = "";
            me.canvas.width = me.video.offsetWidth;
            me.canvas.height = Math.floor(me.canvas.width / 16 * 9);
            me.ctx.drawImage(me.video, 0, 0);
            me.image = me.canvas.toDataURL("image/jpeg");
            me.cardDiv.style.backgroundImage = "url(" + me.image + ")";
            me.video.style.display = "none";
            me.video.pause();
            photoCount++;
            card = new Card(
              cardType.CONTENT_CARD,
              "new_" + photoCount,
              startCard,
              {attachments: [{contentType: "image/jpeg", contentUrl: me.image}], created: new Date(), menuItems: [{action: "SHARE"}]}
            );
            card.localOnly = true;
            startCard.addCard(card);
            emulator.switchToCard(card);
          }, 1000);
        }, 1000);
      }, 1000);
    };

    CameraCard.prototype.startRecording = function () {
      var me = this;
      me.cardDiv.style.backgroundImage = "none";
      global.navigator.getUserMedia({video: true}, function (stream) {
        me.stream = stream;
        me.video.style.display = "block";
        me.video.src = global.URL.createObjectURL(stream);
        me.video.play();
      }, function (e) {
        me.stream = undefined;
        console.log(e);
      });
    };

    CameraCard.prototype.createCardElements = function () {
      this.createDiv();
      this.video = this.cardDiv.querySelector(".card_video");
      this.canvas = this.cardDiv.querySelector(".card_canvas");
      this.ctx = this.canvas.getContext("2d");
      this.video.addEventListener("play", this.takePicture.bind(this));
    };

    /** Event Listeners */

    function onTouchStart(e) {
      if (e.changedTouches && e.changedTouches.length > 0) {
        e.preventDefault();
        mouseX = e.changedTouches[0].pageX - activeCard.cardDiv.offsetLeft;
        mouseY = e.changedTouches[0].pageY - activeCard.cardDiv.offsetTop;
      }
    }

    function onMouseDown(e) {
      e.changedTouches = [{pageX: e.pageX, pageY: e.pageY}];
      onTouchStart(e);
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
        x = e.changedTouches[0].pageX - activeCard.cardDiv.offsetLeft;
        y = e.changedTouches[0].pageY - activeCard.cardDiv.offsetTop;
        makeMove(mouseX, mouseY, x, y);
      }
    }

    function onMouseUp(e) {
      if (e.which !== 2 && e.button !== 2) {
        e.changedTouches = [{pageX: e.pageX, pageY: e.pageY}];
        onTouchEnd(e);
      }
    }

    function handleBundle(bundleId) {
      var i, l, bundleCards, bundleCover;

      bundleCards = startCard.findBundleCards(bundleId);

      if (bundleCards.length === 0) { return; }

      bundleCards.sort(cardSort);

      l = bundleCards.length;
      for (i = 0; i < l; i++) {
        if (bundleCards[i].data.isBundleCover) {
          bundleCover = bundleCards[i];
          break;
        }
      }

      if (!bundleCover) {
        bundleCover = bundleCards[0];
      }

      if (!!bundleCover.parent) {
        bundleCover.parent.removeCard(bundleCover.id);
      }
      bundleCover.cards = [];
      bundleCover.isBundleCover = true;
      bundleCover.type = cardType.CARD_BUNDLE_CARD;
      bundleCover.parent = startCard;
      startCard.addCard(bundleCover);
      for (i = 0; i < l; i++) {
        if (bundleCards[i].id !== bundleCover.id) {
          if (!!bundleCards[i].parent) {
            bundleCards[i].parent.removeCard(bundleCards[i].id);
          }
          bundleCards[i].cards = [];
          bundleCards[i].isBundleCover = false;
          bundleCards[i].type = cardType.CONTENT_CARD;
          bundleCards[i].parent = bundleCover;
          bundleCover.addCard(bundleCards[i]);
        }
        bundleCards[i].updateCardStyle();
      }
    }

    function handleCards(result) {
      var i, l, card, updatedBundles = [], bundleId;
      if (result && result.items) {
        l = result.items.length;
        for (i = 0; i < l; i++) {
          card = startCard.findCard(result.items[i].id);
          if (card) {
            if (card.bundleId || result.items[i].bundleId) {
              if (!!card.bundleId) {
                bundleId = card.bundleId;
                if (updatedBundles.indexOf(bundleId) === -1) {
                  updatedBundles.push(bundleId);
                }
              }
              if (!!result.items[i].bundleId) {
                bundleId = result.items[i].bundleId;
                if (updatedBundles.indexOf(bundleId) === -1) {
                  updatedBundles.push(bundleId);
                }
              }
            }
            if (result.items[i].isDeleted) {
              card.remove();
            } else {
              card.update(result.items[i]);
            }
          } else {
            if (!result.items[i].isDeleted) {
              card = new Card(cardType.CONTENT_CARD, result.items[i].id, startCard, result.items[i]);
              startCard.addCard(card);
              if (result.items[i].bundleId) {
                bundleId = result.items[i].bundleId;
                if (updatedBundles.indexOf(bundleId) === -1) {
                  updatedBundles.push(bundleId);
                }
              }
            }
          }
        }
      }

      l = updatedBundles.length;
      for (i = 0; i < l; i++) {
        handleBundle(updatedBundles[i]);
      }
    }

    function fetchCards() {
      mirror.timeline.list().execute(function (result) {
        console.log(result);
        handleCards(result);
      });
    }

    function fetchCard(id) {
      mirror.timeline.get({"id": id}).execute(function (result) {
        console.log(result);
        if (!result.error) {
          handleCards({"items": [result]});
        }
      });
    }

    /** Called every 1s - use to update timestamps etc **/
    timestep = function () {
      // Keep clock up to date
      var now = new Date().getTime();
      activeCard.updateDisplayDate();

      if (now - lastLocationUpdate > 600000) {
        lastLocationUpdate = now;
        if (global.navigator.geolocation) {
          global.navigator.geolocation.getCurrentPosition(function (loc) {
            var data = {};
            if (!global.glassDemoMode) {
              if (loc.coords) {
                if (loc.coords.accuracy) { data.accuracy = loc.coords.accuracy; }
                if (loc.coords.longitude) { data.longitude = loc.coords.longitude; }
                if (loc.coords.latitude) { data.latitude = loc.coords.latitude; }
                mirror.internal.locations.insert({"resource": data}).execute(function (resp) {
                  console.log(resp);
                });
              }
            }
          });
        }
      }

      timer = global.setTimeout(timestep, 1000);
    };

    function handleContacts(result) {
      var i, l;
      if (result && result.items) {
        l = result.items.length;
        for (i = 0; i < l; i++) {
          shareCards.push(new Card(cardType.SHARE_CARD, result.items[i].id, undefined, result.items[i]));
        }
      }
    }

    function fetchContacts() {
      mirror.contacts.list().execute(function (result) {
        console.log(result);
        handleContacts(result);
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

    function onKeyDown(e) {
      if (activeCard) {
        switch (e.keyCode) {
        case 37:
          activeCard.right();
          break;
        case 38:
          activeCard.up();
          break;
        case 39:
          activeCard.left();
          break;
        case 40:
          activeCard.down();
          break;
        case 13:
        case 32:
          activeCard.tap();
          break;
        }
      }
    }

    /**
     * Set up main UI event handlers
     */
    this.setupEvents = function () {
      if (global.ontouchstart !== undefined) {
        mainDiv.addEventListener("touchstart", onTouchStart, false);
        mainDiv.addEventListener("touchend", onTouchEnd, false);
      }
      mainDiv.onmousedown = onMouseDown;
      mainDiv.onmouseup = onMouseUp;
      doc.onkeydown = onKeyDown;
      mainDiv.onselectstart = function () { return false; };
    };

    this.initialize = function () {
      var card;

      mainDiv.innerHTML = "";

      startCard = new Card(cardType.START_CARD, "start");

      replyCard = new ReplyCard("reply");

      card = new ClockCard("clock", startCard);
      startCard.addCard(card);

      if (!!global.navigator.getUserMedia) {
        card.addCard(new CameraCard("camera", card));
      }

      mapCard = new Card(cardType.CONTENT_CARD, "map", undefined, {"id": "map"});

      if (global.glassDemoMode) {
        handleContacts(demoContacts);
        handleCards(demoCards);
      } else {
        fetchContacts();
      }

      activeCard = startCard;
      activeCard.show();

      this.setupEvents();
    };

    this.openChannel = function (token) {
      var channel, socket;
      channel = new global.goog.appengine.Channel(token);
      socket = channel.open();
      socket.onopen = function () {
        console.log("Channel connected");
        fetchCards();
      };
      socket.onmessage = function (message) {
        var data;
        if (message && message.data) {
          data = JSON.parse(message.data);
          if (data.id) {
            fetchCard(data.id);
          }
        }
      };
      socket.onerror = function (e) {
        console.log("Channel error", e);
      };
      socket.onclose = function () {
        console.log("Channel closed");
      };
    };

    this.initialize();
  }

  function ConnectService() {

    var state;

    function connect(id, code) {
      var xhr;

      xhr = new global.XMLHttpRequest();
      xhr.onreadystatechange = function () {
        var response;
        if (xhr.readyState === 4) {
          if (xhr.status === 200) {
            console.log("Success: " + xhr.responseText);
            response = JSON.parse(xhr.responseText);
            if (response.message && response.message.token) {
              doc.getElementById("signin").style.display = "none";
              doc.getElementById("signout").style.display = "block";
              doc.getElementById("glass").style.display = "block";
              global.glassapp = global.glassapp || new Glass();
              global.glassapp.start();
              global.glassapp.openChannel(response.message.token);
            }
          } else {
            console.log("Error setting up Channel: " + xhr.responseText);
          }
        }
      };

      xhr.open("POST", "/glass/connect?state=" + state + "&gplus_id=" + id, true);
      xhr.setRequestHeader("Content-Type", "application/octet-stream; charset=utf-8");
      xhr.send(code);
    }

    this.connectCallback = function (authResult) {
      if (authResult.access_token) {
        global.gapi.client.load("mirror", "v1", function () {
          global.gapi.client.load("plus", "v1", function () {
            global.gapi.client.plus.people.get({"userId": "me"}).execute(function (result) {
              if (result.error) {
                console.log("There was an error: " + result.error);
                doc.getElementById("signin").style.display = "block";
                doc.getElementById("signout").style.display = "none";
                doc.getElementById("glass").style.display = "none";
              } else {
                connect(result.id, authResult.code);
              }
            });
          });
        }, global.discoveryUrl);
      } else if (authResult.error) {
        console.log("There was an error: " + authResult.error);
        doc.getElementById("signin").style.display = "block";
        doc.getElementById("signout").style.display = "none";
        doc.getElementById("glass").style.display = "none";
      }
    };

    this.disconnectCallback = function (data) {
      console.log(data);
    };

    this.setState = function (s) {
      if (!state) {
        state = s;
      } else {
        console.log("State variable already set!");
      }
    };
  }

  global.connectService = new ConnectService();
  global.onSignInCallback = global.connectService.connectCallback;
  global.disconnectCallback = global.connectService.disconnectCallback;

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
