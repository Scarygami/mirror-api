(function (global) {
  "use strict";

  var
    doc = global.document,
    cardDiv = doc.querySelector(".card");

  global.setData = function (text, image, html, date) {
    var tmpDiv, timeDiv;
    if (!html) {
      // HTML Contents overwrite all other contents, otherwise create html from text and image
      if (!!image) {
        html = "<article class=\"photo\">";
        html += "<img src=\"" + image + "\" style=\"width: 100%; height: 100%;\">";
        html += "<div class=\"photo-overlay\"></div>";
      } else {
        html = "<article>";
      }
      html += "<section><p class=\"text-auto-size\">" + text + "</p></section>";
      html += "</article>";
    }
    cardDiv.innerHTML = html;
    tmpDiv = cardDiv.querySelector("article");
    if (tmpDiv) {
      timeDiv = doc.createElement("footer");
      timeDiv.id = "map-time-footer";
      timeDiv.innerHTML = "<time>" + date + "</time>";
      tmpDiv.appendChild(timeDiv);
    } else {
      global.console.log("Invalid HTML...");
    }
  };

  global.updateDate = function (date) {
    var timeDiv;
    timeDiv = cardDiv.querySelector("article #map-time-footer time");
    if (timeDiv) {
      timeDiv.innerHTML = date;
    }
  };

}(this));