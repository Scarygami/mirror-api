(function (global) {
  "use strict";

  var doc = global.document, console = global.console;

  Date.prototype.niceDate = function () {
    var y, m, d, h, min;

    y = this.getFullYear().toString();
    m = (this.getMonth() + 1).toString();
    d = this.getDate().toString();
    h = this.getHours().toString();
    min = this.getMinutes().toString();

    return y + "-" + (m[1] ? m : "0" + m[0]) + "-" + (d[1] ? d : "0" + d[0]) + " " + (h[1] ? h : "0" + h[0]) + ":" + (min[1] ? min : "0" + min[0]);
  };

  function Service() {
    var state;

    function listCards(items) {
      var i, l, ul, li;
      if (items) {
        ul = doc.getElementById("cards");
        ul.innerHTML = "";
        l = items.length;
        for (i = l - 1; i >= 0; i--) {
          li = doc.createElement("li");
          li.innerHTML = (new Date(items[i].displayDate || items[i].udpated || items[i].created )).niceDate() + " - " + (items[i].text || "");
          ul.appendChild(li);
        }
      }
    }

    function requestCards() {
      var xhr;

      xhr = new global.XMLHttpRequest();
      xhr.onreadystatechange = function () {
        var response, json;
        if (xhr.readyState == 4) {
          if (xhr.status == 200) {
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

      xhr.open("GET", "/list", true);
      xhr.send();
    }

    function connect(id, code) {
      var xhr;

      xhr = new global.XMLHttpRequest();
      xhr.onreadystatechange = function () {
        var response;
        if (xhr.readyState == 4) {
          if (xhr.status == 200) {
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
          }
        }
      };

      xhr.open("POST", "/connect?state=" + state + "&gplus_id=" + id, true);
      xhr.setRequestHeader("Content-Type", "application/octet-stream; charset=utf-8");
      xhr.send(code);
    }

    this.disconnect = function () {
      var xhr;

      xhr = new global.XMLHttpRequest();
      xhr.onreadystatechange = function () {
        var response;
        if (xhr.readyState == 4) {
          if (xhr.status == 200) {
            console.log("Success: " + xhr.responseText);
          } else {
            console.log("Error " + xhr.status + ": " + xhr.statusText);
            if (xhr.responseText) {
              console.log(xhr.responseText);
            }
          }
        }
      };

      xhr.open("POST", "/disconnect", true);
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
        
        input = doc.getElementById("new_image");
        text = input.value;
        input.value = "";
        
        if (text) {
          message.image = text;
        }

        xhr = new global.XMLHttpRequest();
        xhr.onreadystatechange = function () {
          var response;
          if (xhr.readyState == 4) {
            if (xhr.status == 200) {
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

        xhr.open("POST", "/new", true);
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