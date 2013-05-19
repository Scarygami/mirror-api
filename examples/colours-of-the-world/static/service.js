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
      state,
      PLUS_POST = 1,
      YT_POST = 2,
      PLUS_SEARCH = 3,
      sources = [],
      tracked = [],
      addPost, gapi,
      sources_div, tracked_div, search_input, searching_div, search_id = 1;

    function post_ready() {
      var i, l, chk_all_done, div;
      l = sources.length;
      chk_all_done = true;
      for (i = 0; i < l; i++) {
        if (!sources[i].ready) {
          chk_all_done = false;
        }
      }
      if (chk_all_done) {
        searching_div.style.display = "none";
      }
    }

    function Post(post_type, post_user, post_id, cb, chk_reshare) {
      var org_author, contents, author_name, author_pic, author_link, published, request, this_post, comments, max_results;
      this.post_type = post_type;
      this.ready = false;
      this.valid = false;
      this.checking = false;
      this.url = "";
      this.activity_id = "";
      this.org_id = "";
      this.post_user = post_user;
      this.post_id = post_id;
      contents = "";
      author_name = "";
      author_pic = "/images/noimage.png";
      author_link = "";
      published = null;
      this_post = this;

      switch (this.post_type) {
      case PLUS_POST:
        this.service_pic = "/images/comment.png";
        max_results = 100;
        break;
      case YT_POST:
        this.service_pic = "/images/youtube.png";
        max_results = 50;
        break;
      case PLUS_SEARCH:
        this.service_pic = "/images/gplus.png";
        max_results = 20;
        author_pic = "/images/search.png";
        break;
      }

      if (this.post_type === PLUS_SEARCH) {
        this.activity_id = post_id;
        this.post_id = search_id;
        search_id++;
      }
      this.div_id = this.post_user + "_" + this.post_id;

      function display_post() {
        var str_tmp = "", div;
        div = doc.getElementById(this_post.div_id);
        if (!div) {
          div = doc.createElement("div");
          div.id = this_post.div_id;
          div.className = "ct-post";
          sources_div.appendChild(div);
        }
        str_tmp = "<img class=\"ct-post_pic\" src=\"" + author_pic + "\">\n";
        str_tmp += "<img class=\"ct-service_pic\" src=\"" + this_post.service_pic + "\">\n";
        if (this_post.activity_id !== "") {
          if (this_post.post_type !== PLUS_SEARCH) {
            str_tmp += "<div class=\"ct-post_time\"><a href=\"" + this_post.url + "\" target=\"_blank\">" + published.niceDate() + "</a></div>";
            str_tmp += "<b>" + author_name + "</b><br>";
          } else {
            str_tmp += "<div class=\"ct-post_time\"><a href=\"" + this_post.url + "\" target=\"_blank\">Search</a></div>";
          }
        }
        str_tmp += "<div class=\"ct-post_text\">" + contents + "</div>";
        div.innerHTML = str_tmp;

        // TODO: create buttons and events
      }

      if (this.post_type === PLUS_SEARCH) {
        contents = "Google+ search for<br><b>" + this.activity_id + "</b>";
        this.url = "https://plus.google.com/s/" + encodeURIComponent(this.activity_id);
        this.ready = true;
        this.valid = true;
        display_post();
        global.setTimeout(cb, 10);
      }
      if (this.post_type === PLUS_POST) {
        if (!this.post_user) {
          this.activity_id = post_id;
          gapi.plus.activities.get({"activityId": this.activity_id}).execute(function (result) {
            console.log(result);
            if (!!result.actor) {
              this_post.post_user = result.actor.id;
              this_post.div_id = this_post.post_user + "_" + this_post.post_id;
              if (result.url.indexOf("plus.google.com") >= 0) {
                this_post.url = result.url;
              } else {
                this_post.url = "https://plus.google.com/" + result.url;
              }
              contents = result.title.trim();
              if (contents === "") {
                contents = "(No post text...)";
              }
              author_name = result.actor.displayName;
              author_pic = result.actor.image.url;
              author_link = result.actor.url;
              published = new Date(result.published);
              this_post.valid = true;
              this_post.org_id = result.object.id || result.id;
              if (result.object.actor) {
                org_author = result.object.actor.id;
              } else {
                org_author = result.actor.id;
              }
            } else {
              contents = "Post " + this_post.post_id + " not found.";
            }
            display_post();
            this_post.ready = true;
            global.setTimeout(cb, 10);
          });
        } else {
          gapi.plus.activities.list({"userId": post_user, "maxResults": max_results}).execute(function (result) {
            var i, l, api_url, api_url_parts, item_id, item;
            if (!!result.items) {
              l = result.items.length;
              for (i = 0; i < l; i++) {
                if (chk_reshare) {
                  if ((result.items[i].object.id === this_post.post_id) || (!result.items[i].object.id && (result.items[i].id === this_post.post_id))) {
                    this_post.activity_id = result.items[i].id;
                    item_id = i;
                    break;
                  }
                } else {
                  api_url = result.items[i].url;
                  api_url_parts = api_url.split("/");
                  if (api_url_parts.length > 0) {
                    if (this_post.post_type === PLUS_POST) {
                      if (api_url_parts[api_url_parts.length - 1] === this_post.post_id) {
                        this_post.activity_id = result.items[i].id;
                        item_id = i;
                        break;
                      }
                    }
                  }
                }
              }
              if (this_post.activity_id === "") {
                if (chk_reshare) {
                  contents = "Reshare by user " + this_post.post_user + " not found.";
                  this_post.chk_delete = true;
                } else {
                  contents = "Post " + this_post.post_id + " for user " + this_post.post_user + " not found. Please check your Post URL and make sure it's a public post.";
                }
              } else {
                item = result.items[item_id];
                if (item.url.indexOf("plus.google.com") >= 0) {
                  this_post.url = item.url;
                } else {
                  this_post.url = "https://plus.google.com/" + item.url;
                }
                contents = item.title.trim();
                if (contents === "") {
                  contents = "(No post text...)";
                }
                author_name = item.actor.displayName;
                author_pic = item.actor.image.url;
                author_link = item.actor.url;
                published = new Date(item.published);
                this_post.valid = true;
                this_post.org_id = item.object.id || item.id;
                if (item.object.actor) {
                  org_author = item.object.actor.id;
                } else {
                  org_author = item.actor.id;
                }
              }
              this_post.ready = true;
              display_post();
              global.setTimeout(cb, 10);
            } else {
              contents = "No posts found for User ID " + this_post.post_user + "<br>\nPlease check your Post URL and make sure it's a public post.";
              if (!!result.error) {
                contents += "<br>API Error: " + result.error.message;
              }
              this_post.ready = true;
              if (chk_reshare) {
                this_post.chk_delete = true;
              }
              display_post();
              global.setTimeout(cb, 10);
            }
          });
        }
      }
      if (this.post_type === YT_POST) {
        gapi.youtube.videos.list({"part": "snippet", "id": this.post_id}).execute(function (result) {
          var video;
          console.log(result);
          if (!!result.items && result.items.length === 1) {
            video = result.items[0].snippet;
            gapi.youtube.channels.list({"part": "snippet", "id": video.channelId}).execute(function (result) {
              console.log(result);
              var channel;
              if (!!result.items && result.items.length === 1) {
                channel = result.items[0].snippet;
                this_post.activity_id = this_post.post_id;
                this_post.url = "https://www.youtube.com/watch?v=" + this_post.post_id;
                contents = "";
                if (!!video.title) {
                  contents += video.title.trim();
                }
                if (!!video.description) {
                  if (contents !== "") {
                    contents += " - ";
                  }
                  contents += video.description.trim();
                }
                contents = contents.substring(0, 250) + "<br>";
                author_name = channel.title;
                if (!!channel.thumbnails && !!channel.thumbnails["default"]) {
                  author_pic = channel.thumbnails["default"].url;
                } else {
                  author_pic = "/images/youtube_author.png";
                }
                author_link = "https://www.youtube.com/channel/" + video.channelId;
                published = new Date(video.publishedAt);
                this_post.valid = true;
              } else {
                contents = "Video ID " + this_post.post_id + " not found.<br>\nPlease check your URL.";
                this_post.valid = false;
              }
              this_post.ready = true;
              display_post();
              global.setTimeout(cb, 10);
            });
          } else {
            contents = "Video ID " + this_post.post_id + " not found.<br>\nPlease check your URL.";
            this_post.valid = false;
            this_post.ready = true;
            display_post();
            global.setTimeout(cb, 10);
          }
        });
      }

      this.check_reshares = function () {
        var chk_found, l1, i1;
        if (this_post.post_type === PLUS_POST) {
          if (this_post.activity_id !== this_post.org_id) {
            chk_found = false;
            l1 = sources.length;
            for (i1 = 0; i1 < l1; i1++) {
              if (sources[i1].post_user === org_author && sources[i1].activity_id === this_post.org_id) {
                chk_found = true;
                break;
              }
            }
            if (!chk_found) {
              addPost(this_post.org_id);
            }
          }

          gapi.plus.people.listByActivity({"activitiyId" : this.activityId, "collection": "resharers", "maxResults": 100}).execute(function (result) {
            var i, l, item, post, chk_found, l1, i1;
            if (!!result.items) {
              l = result.items.length;
              for (i = 0; i < l; i++) {
                item = result.items[i];
                chk_found = false;
                if (this_post.post_user === item.id) {
                  chk_found = true;
                } else {
                  l1 = sources.length;
                  for (i1 = 0; i1 < l1; i1++) {
                    if (sources[i1].post_user === item.id && sources[i1].org_id === this_post.org_id) {
                      chk_found = true;
                      break;
                    }
                  }
                }

                if (!chk_found) {
                  searching_div.style.display = "block";
                  post = new Post(PLUS_POST, item.id, this_post.org_id, post_ready);
                  sources.push(post);
                }
              }
            }
          });
        }
      };
    }

    addPost = function (activity_id) {
      var i, l, chk_found, post;
      chk_found = false;
      l = sources.length;
      for (i = 0; i < l; i++) {
        if (sources[i].activity_id === activity_id) {
          chk_found = true;
          break;
        }
      }
      if (!chk_found) {
        post = new Post(PLUS_POST, "", activity_id, post_ready, false);
        sources.push(post);
      }
    };

    function addSource(source) {

      function parse_url(query) {
        var q, param, query_string;
        query_string = query.split("&");
        for (q = 0; q < query_string.length; q++) {
          if (query_string[q]) {
            param = query_string[q].split("=");
            if (param.length === 2) {
              param[1] = decodeURIComponent(param[1].replace(/\+/g, " "));
              switch (param[0].toUpperCase()) {
              case "POST":
                addPost(param[1]);
                break;
              case "URL":
              case "GSEARCH":
                addSource(param[1]);
                break;
              case "YT":
                addSource("http://youtu.be/" + param[1]);
                break;
              }
            }
          }
        }
      }

      var i, l, chk_found, post, url_parts, post_user, post_id;
      if (!source || typeof (source) !== "string") {
        source = search_input.value.trim();
      }
      search_input.value = "";
      if (source.toLowerCase().indexOf("allmyplus.com") >= 0) {
        // CT-URL
        i = source.toLowerCase().indexOf("?");
        if (i >= 0) {
          source = source.substr(i + 1);
          parse_url(source);
        }
        return;
      }
      if (source.toLowerCase().indexOf("youtube.com") >= 0 || source.toLowerCase().indexOf("youtu.be") >= 0) {
        // Youtube Video
        post_id = "";
        i = source.toLowerCase().indexOf("?v=");
        if (i < 0) {
          i = source.toLowerCase().indexOf("&v=");
        }
        if (i >= 0) {
          post_id = source.substr(i + 3);
        }
        if (post_id === "") {
          i = source.toLowerCase().indexOf("youtu.be/");
          if (i >= 0) {
            post_id = source.substr(i + 9);
          }
        }
        if (post_id === "") {
          i = source.toLowerCase().indexOf("/embed/");
          if (i >= 0) {
            post_id = source.substr(i + 7);
          }
        }
        if (post_id !== "") {
          i = post_id.indexOf("&");
          if (i >= 0) { post_id = post_id.substring(0, i); }
          i = post_id.indexOf("#");
          if (i >= 0) {
            post_id = post_id.substring(0, i);
          }
          i = post_id.indexOf("/");
          if (i >= 0) {
            post_id = post_id.substring(0, i);
          }
          i = post_id.indexOf('"');
          if (i >= 0) {
            post_id = post_id.substring(0, i);
          }
          i = post_id.indexOf("'");
          if (i >= 0) {
            post_id = post_id.substring(0, i);
          }
          chk_found = false;
          l = sources.length;
          for (i = 0; i < l; i++) {
            if (sources[i].post_user === "YT" && sources[i].post_id === post_id) {
              chk_found = true;
              break;
            }
          }
          if (!chk_found) {
            searching_div.style.display = "block";
            post = new Post(YT_POST, "YT", post_id, post_ready, false);
            sources.push(post);
          }
        }
        return;
      }
      if (source.toLowerCase().indexOf("plus.google.com") >= 0) {
        // Google Plus Post
        source = source.split("?")[0];
        url_parts = source.split("/");
        l = url_parts.length;
        if (url_parts[l - 2] === "posts" && l >= 3) {
          post_user = url_parts[l - 3];
          post_id = url_parts[l - 1];

          chk_found = false;
          l = sources.length;
          for (i = 0; i < l; i++) {
            if (sources[i].post_user === post_user && sources[i].post_id === post_id) {
              chk_found = true;
              break;
            }
          }
          if (!chk_found) {
            searching_div.style.display = "block";
            post = new Post(PLUS_POST, post_user, post_id, post_ready, false);
            sources.push(post);
          }
        }
        return;
      }

      // Google Plus Search
      post_user = "PS";
      post_id = source;
      chk_found = false;
      l = sources.length;
      for (i = 0; i < l; i++) {
        if (sources[i].post_user === post_user && sources[i].activity_id === post_id) {
          chk_found = true;
          break;
        }
      }
      if (!chk_found) {
        searching_div.style.display = "block";
        post = new Post(PLUS_SEARCH, post_user, post_id, post_ready, false);
        sources.push(post);
      }
    }

    function initialize() {
      sources_div = doc.getElementById("sources");
      tracked_div = doc.getElementById("tracked");
      search_input = doc.getElementById("ct-source-input");
      searching_div  = doc.getElementById("ct-searching");
      doc.getElementById("ct-add").onclick = addSource;
      gapi = global.gapi.client;
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
            initialize();
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