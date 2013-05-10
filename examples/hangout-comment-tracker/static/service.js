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
          global.gapi.client.load("youtube", "v3", function () {
            global.gapi.client.plus.people.get({"userId": "me"}).execute(function (result) {
              console.log(result);
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
        });
      } else if (authResult.error) {
        console.log("There was an error: " + authResult.error);
        doc.getElementById("signin").style.display = "block";
        doc.getElementById("signout").style.display = "none";
        doc.getElementById("glass").style.display = "none";
      }
    };

    this.addSource = function () {
      var search = doc.getElementById("ct-source-input").value;
      global.gapi.client.youtube.videos.list({"part": "snippet", "id": search}).execute(function (result) {
        console.log(result);
      })
    }
  }

  global.mirrorService = new Service();
  global.onSignInCallback = global.mirrorService.signInCallback;

  global.onload = function () {
    doc.getElementById("signout_button").onclick = global.mirrorService.disconnect;
    doc.getElementById("ct-add").onclick = global.mirrorService.addSource;
  };
}(this));