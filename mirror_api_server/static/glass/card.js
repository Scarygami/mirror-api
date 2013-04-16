(function (global) {
  "use strict";

  var
    doc = global.document,
    cardDiv = doc.querySelector(".card"),
    FONT_SIZES = ["text-x-large", "text-large", "text-normal", "text-small", "text-x-small"];

  function autoResizeText(elem) {
    var prevClass, computedStyle, maxHeight, maxWidth, i, oldStyle, fontSize;
    computedStyle = doc.defaultView.getComputedStyle(elem, null);
    maxHeight = parseInt(computedStyle.height, 10);
    maxWidth = parseInt(computedStyle.width, 10);
    oldStyle = elem.style;

    prevClass = "text-auto-size";
    for (i = 0; i < FONT_SIZES.length; i++) {
      fontSize = FONT_SIZES[i];
      elem.style.height = "auto";
      elem.style.width = "auto";
      elem.classList.remove(prevClass);
      elem.classList.add(fontSize);
      elem.dataset.textClass = fontSize;
      prevClass = fontSize;

      if (elem.scrollHeight <= maxHeight &&
          elem.scrollWidth <= maxWidth) {
        break;
      }
    }
    elem.style.height = "";
    elem.style.width = "";

    if (oldStyle) {
      elem.style = oldStyle;
    }
  }

  global.setData = function (text, image, html, date) {
    var tmpDiv, timeDiv, resize, i;
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
    resize = cardDiv.querySelectorAll(".text-auto-size");
    for (i = 0; i < resize.length; i++) {
      autoResizeText(resize[i]);
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