// Google Play attribution: adds a Play install referrer to every Play link, so an install can be
// traced to where the visitor came from. The source is the page's ?src= word (ig, yt, tt, fb ...),
// or "site" when there is none; an optional ?c= word (same limits) becomes the campaign. It is read in the browser only to build the link; nothing is sent,
// stored or counted here. Links that already carry a referrer (the /join invite code) are left alone.
(function () {
  "use strict";
  try {
    var m = /[?&]src=([a-z0-9_-]{1,20})(?:&|#|$)/i.exec(location.search);
    var src = m ? m[1].toLowerCase() : "site";
    var c = /[?&]c=([a-z0-9_-]{1,20})(?:&|#|$)/i.exec(location.search); // per-video tag, e.g. &c=A1
    var camp = m ? (c ? c[1] : "mute-moments") : "website";
    var ref = "utm_source=" + src + "&utm_medium=" + (m ? "social" : "web") + "&utm_campaign=" + camp;
    var links = document.querySelectorAll('a[href^="https://play.google.com/store/apps/details?id=com.familyfiltertv.app"]');
    for (var i = 0; i < links.length; i++) {
      var h = links[i].getAttribute("href");
      if (h.indexOf("referrer=") === -1) links[i].setAttribute("href", h + "&referrer=" + encodeURIComponent(ref));
    }
  } catch (e) { /* never get in the way of the page */ }
})();
