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
    var
      state, gapi;

    function showSubmissions(submissions) {
      var div = doc.getElementById("submissions"), img, i, l, cols;
      cols = div.querySelectorAll(".colour");
      l = cols.length;
      for (i = 0; i < l; i++) {
        cols[i].innerHTML = "";
      }
      l = submissions.length;
      for (i = 0; i < l; i++) {
        img = doc.createElement("img");
        img.src = submissions[i].url;
        doc.getElementById(submissions[i].colour).appendChild(img);
      }
      doc.getElementById("loading").style.visibility = "hidden";
    }
      
    function fetchSubmissions() {
      var xhr = new global.XMLHttpRequest();
      xhr.onreadystatechange = function () {
        var response;
        if (xhr.readyState === 4) {
          if (xhr.status === 200) {
            response = JSON.parse(xhr.responseText);
            showSubmissions(response.items);
          } else {
            console.log("Error " + xhr.status + ": " + xhr.statusText);
            if (xhr.responseText) {
              console.log(xhr.responseText);
            }
            doc.getElementById("loading").style.visibility = "hidden";
          }
        }
      };
      
      xhr.open("GET", global.location.pathname + "list", true);
      xhr.send();
    }
      
    function initialize() {
      gapi = global.gapi.client;
      fetchSubmissions();
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
            doc.getElementById("colours").style.display = "block";
            initialize();
          } else {
            console.log("Error " + xhr.status + ": " + xhr.statusText);
            if (xhr.responseText) {
              console.log(xhr.responseText);
            }
            doc.getElementById("signin").style.display = "block";
            doc.getElementById("signout").style.display = "none";
            doc.getElementById("colours").style.display = "none";
            doc.getElementById("loading").style.visibility = "hidden";
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
      if (!global.confirm("Are you sure? This will delete all your submissions, scores and achievements.")) { return; }
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
      doc.getElementById("colours").style.display = "none";
      doc.getElementById("loading").style.visibility = "hidden";
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
        doc.getElementById("loading").style.visibility = "visible";
        global.gapi.client.load("plus", "v1", function () {
          global.gapi.client.load("youtube", "v3", function () {
            global.gapi.client.plus.people.get({"userId": "me"}).execute(function (result) {
              if (result.error) {
                console.log(result.error);
                doc.getElementById("signin").style.display = "block";
                doc.getElementById("signout").style.display = "none";
                doc.getElementById("colours").style.display = "none";
                doc.getElementById("loading").style.visibility = "hidden";
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
        doc.getElementById("colours").style.display = "none";
        doc.getElementById("loading").style.visibility = "hidden";
      }
    };

    this.getPosts = function () {
      return sources;
    };
  }

  global.mirrorService = new Service();
  global.onSignInCallback = global.mirrorService.signInCallback;

  global.onload = function () {
    doc.getElementById("signout_button").onclick = global.mirrorService.disconnect;
  };
}(this));