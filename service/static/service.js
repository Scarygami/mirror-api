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

  function Service() {
    var state;

    function displayCard(div, data) {
      var card, iframe, html, text, image, date, i, l, att, tmpDate;
      card = doc.createElement("div");
      card.classList.add("card");
      card.innerHTML =
        "<iframe frameborder=\"0\" allowtransparency=\"true\" scrolling=\"no\" src=\"/glass/inner.html\" class=\"card_iframe\"></iframe>" +
        "<pre class=\"card_metadata\"></pre>";
      div.appendChild(card);
      tmpDate = data.displayDate || data.updated || data.created;
      if (tmpDate) {
        date = new Date(tmpDate);
      }
      html = data.html;
      text = data.text;
      image = undefined;
      if (data.attachments && data.attachments.length > 0) {
        l = data.attachments.length;
        for (i = 0; i < l; i++) {
          att = data.attachments[i];
          if (att.contentType.indexOf("image/") === 0) {
            if (att.id) {
              image = global.location.pathname + "attachment/" + data.id + "/" + att.id;
            } else {
              image = att.contentUrl;
            }
            break;
          }
        }
      }
      if (html) {
        // HTML overrides text and image in card, can't be mixed
        text = "";
        image = undefined;
      }

      iframe = card.querySelector(".card_iframe");
      iframe.onload = function () {
        var tmpDate;
        if (date) {
          tmpDate = date.niceDate();
        } else {
          tmpDate = "";
        }
        iframe.contentWindow.setData(text, image, html, tmpDate);
      };

      card.querySelector(".card_metadata").appendChild(doc.createTextNode(JSON.stringify(data, null, 2)));
    }

    function listCards(items) {
      var i, l, div, card, iframe;
      if (items) {
        div = doc.getElementById("timeline");
        div.innerHTML = "";
        l = items.length;
        for (i = 0; i < l; i++) {
          displayCard(div, items[i]);
        }
      }
    }

    function requestCards() {
      var xhr;

      xhr = new global.XMLHttpRequest();
      xhr.onreadystatechange = function () {
        var response, json;
        if (xhr.readyState === 4) {
          if (xhr.status === 200) {
            console.log("Success: " + xhr.responseText);
            json = JSON.parse(xhr.responseText);
            listCards(json.items);
          } else {
            console.log("Error " + xhr.status + ": " + xhr.statusText);
            if (xhr.responseText) {
              console.log(xhr.responseText);
            }
          }
        }
      };

      xhr.open("GET", global.location.pathname + "list", true);
      xhr.send();
    }

    function connect(id, code) {
      var xhr;

      xhr = new global.XMLHttpRequest();
      xhr.onreadystatechange = function () {
        var response;
        if (xhr.readyState === 4) {
          if (xhr.status === 200) {
            console.log("Success: " + xhr.responseText);
            doc.getElementById("signin").style.display = "none";
            doc.getElementById("signout").style.display = "block";
            doc.getElementById("glass").style.display = "block";
            requestCards();
          } else {
            console.log("Error " + xhr.status + ": " + xhr.statusText);
            if (xhr.responseText) {
              console.log(xhr.responseText);
            }
            doc.getElementById("signin").style.display = "block";
            doc.getElementById("signout").style.display = "none";
            doc.getElementById("glass").style.display = "none";
            if (xhr.status === 401) {
              global.location.href = global.location.pathname + "?reconnect=true";
            }
          }
        }
      };

      xhr.open("POST", global.location.pathname + "connect?state=" + state + "&gplus_id=" + id, true);
      xhr.setRequestHeader("Content-Type", "application/octet-stream; charset=utf-8");
      xhr.send(code);
    }

    this.disconnect = function () {
      var xhr;

      xhr = new global.XMLHttpRequest();
      xhr.onreadystatechange = function () {
        var response;
        if (xhr.readyState === 4) {
          if (xhr.status === 200) {
            console.log("Success: " + xhr.responseText);
          } else {
            console.log("Error " + xhr.status + ": " + xhr.statusText);
            if (xhr.responseText) {
              console.log(xhr.responseText);
            }
          }
        }
      };

      xhr.open("POST", global.location.pathname + "disconnect", true);
      xhr.send();

      doc.getElementById("signin").style.display = "block";
      doc.getElementById("signout").style.display = "none";
      doc.getElementById("glass").style.display = "none";
    };

    this.setState = function (s) {
      if (!state) {
        state = s;
      } else {
        console.log("State variable already set!");
      }
    };

    this.signInCallback = function (authResult) {
      if (authResult.access_token) {
        doc.getElementById("signin").style.display = "none";
        global.gapi.client.load("plus", "v1", function () {
          global.gapi.client.plus.people.get({"userId": "me"}).execute(function (result) {
            if (result.error) {
              console.log(result.error);
              doc.getElementById("signin").style.display = "block";
              doc.getElementById("signout").style.display = "none";
              doc.getElementById("glass").style.display = "none";
              return;
            }
            connect(result.id, authResult.code);
          });
        });
      } else if (authResult.error) {
        console.log("There was an error: " + authResult.error);
        doc.getElementById("signin").style.display = "block";
        doc.getElementById("signout").style.display = "none";
        doc.getElementById("glass").style.display = "none";
      }
    };

    this.sendCard = function () {
      var input, xhr, text, message;
      input = doc.getElementById("new_card");
      text = input.value;

      message = {};

      if (text) {
        input.value = "";
        message.text = text;

        xhr = new global.XMLHttpRequest();
        xhr.onreadystatechange = function () {
          var response;
          if (xhr.readyState === 4) {
            if (xhr.status === 200) {
              console.log("Success: " + xhr.responseText);
              requestCards();
            } else {
              console.log("Error " + xhr.status + ": " + xhr.statusText);
              if (xhr.responseText) {
                console.log(xhr.responseText);
              }
            }
          }
        };

        xhr.open("POST", global.location.pathname + "new", true);
        xhr.setRequestHeader("Content-Type", "application/json; charset=utf-8");
        xhr.send(JSON.stringify(message));
      }

    };
  }

  global.mirrorService = new Service();
  global.onSignInCallback = global.mirrorService.signInCallback;

  global.onload = function () {
    doc.getElementById("signout_button").onclick = global.mirrorService.disconnect;
    doc.getElementById("send_card").onclick = global.mirrorService.sendCard;
  };
}(this));