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

  function renderMap(image) {
    var src, parts, part, i, l, width = 640, height = 360, elements = [], marker, coords, polyline, polystyle, tmp;

    src = image.src;
    if (src.indexOf("glass://map?") !== 0) { return; }
    src = src.substring(12);
    parts = src.split("&");

    l = parts.length;
    for (i = 0; i < l; i++) {
      part = parts[i].split("=");
      if (part.length !== 2) { continue; }
      switch (part[0]) {
      case "w":
        width = part[1];
        break;
      case "h":
        height = part[1];
        break;
      case "marker":
        marker = part[1].split(";");
        if (marker.length === 2) {
          coords = marker[1].split(",");
          if (coords.length === 2) {
            tmp = "markers=";
            if (marker[0] === "0") {
              tmp += "color:0xF7594A";
            } else {
              tmp += "icon:http://" + global.location.host + "/glass/images/map_dot.png|shadow:false";
            }
            tmp += "|" + coords[0] + "," + coords[1];
            elements.push(tmp);
          }
        }
        break;
      case "polyline":
        polyline = part[1].split(";");
        if (polyline.length === 2) {
          polystyle = polyline[0].split(",");
          if (polystyle.length === 2) {
            /**
             * According to documentation ffff0000 results in a red line,
             * meaning that FF is the opacity followed by the RGB Values FF0000
             * representation in Google Static maps is the other way round (RGBA)
             * Unless of course the documentation is wrong, but I'll go by that for now
             */
            if (polystyle[1].length !== 8) {
              polystyle[1] = "0x1871ADFF";
            } else {
              polystyle[1] = "0x" + polystyle[1].substring(2) + polystyle[1].substring(0, 2);
            }
          } else {
            polystyle = ["8", "0x1871ADFF"];
          }
          coords = polyline[1].split(",");
          if (coords.length > 0) {
            tmp = "path=color:" + polystyle[1] + "|weight:" + polystyle[0];
            l = coords.length;
            for (i = 0; i < l; i += 2) {
              // skipping last coord in case odd number given
              if (i !== l - 1) {
                tmp += "|" + coords[i] + "," + coords[i + 1];
              }
            }
            elements.push(tmp);
          }
        }
        break;
      case "center":
        elements.push("center=" + part[1]);
        break;
      case "zoom":
        elements.push("zoom=" + part[1]);
        break;
      }
    }

    src =
      "https://maps.googleapis.com/maps/api/staticmap?sensor=false&size=" + width + "x" + height +
      "&style=feature:all|element:all|saturation:-100|lightness:-25|gamma:0.5|visibility:simplified" +
      "&style=feature:roads|element:geometry&style=feature:landscape|element:geometry|lightness:-25";

    if (elements.length > 0) {
      src += "&" + elements.join("&");
    }

    image.src = src;
  }

  global.setData = function (text, image, html, date) {
    var tmpDiv, timeDiv, resize, i, images;
    if (!html) {
      // HTML Contents overwrite all other contents, otherwise create html from text and image
      if (!!image) {
        html = "<article class=\"photo\">";
        html += "<img src=\"" + image + "\" style=\"width: 100%; height: 100%;\">";
        if (!!text || !!date) {
          html += "<div class=\"photo-overlay\"></div>";
        }
      } else {
        html = "<article>";
      }
      html += "<section><p class=\"text-auto-size\">" + (text || "") + "</p></section>";
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

    images = cardDiv.querySelectorAll("img");
    for (i = 0; i < images.length; i++) {
      if (images[i].src.indexOf("glass://map?") === 0) {
        renderMap(images[i]);
      }
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