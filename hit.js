// Cookie-free page counter. Counts page views and three kinds of link clicks, nothing else.
// No cookies, no localStorage or sessionStorage, no identifiers, no query strings, no full referrer.
// Stays completely silent if Do Not Track or Global Privacy Control is on, if the endpoint does not
// answer a quick reachability check, or if anything at all goes wrong.
(function () {
  "use strict";

  var HIT_URL = "https://europe-west1-familyfiltertv.cloudfunctions.net/hit";
  var CHECK_TIMEOUT_MS = 3000;
  var PLAY_URL = "https://play.google.com/store/apps/details?id=com.familyfiltertv.app";

  try {
    // Older browsers say "yes" instead of "1"; either means the visitor opted out.
    var dnt = [navigator.doNotTrack, window.doNotTrack, navigator.msDoNotTrack];
    for (var i = 0; i < dnt.length; i++) if (dnt[i] === "1" || dnt[i] === "yes" || dnt[i] === 1) return;
    if (navigator.globalPrivacyControl === true) return;
  } catch (e) { return; }
  if (!window.fetch) return;

  var live = false; // becomes true only once the endpoint has answered the reachability check

  // Where the visitor came from, as one word. The address itself is never read beyond its host.
  function refCategory() {
    var host = "";
    try { host = new URL(document.referrer).hostname.replace(/^www\./, ""); } catch (e) { return "direct"; }
    if (!host) return "direct";
    if (host === location.hostname.replace(/^www\./, "")) return "internal";
    if (/(^|\.)(google|bing|duckduckgo|yahoo|ecosia|brave|startpage|yandex|baidu)\./.test(host) ||
        /(^|\.)(perplexity\.ai|chatgpt\.com|chat\.openai\.com|claude\.ai|gemini\.google\.com|copilot\.microsoft\.com)$/.test(host)) return "search";
    if (/(^|\.)(facebook|instagram|tiktok|youtube|youtu|reddit|x|twitter|t|linkedin|pinterest|threads|whatsapp|wa)\.(com|be|co|me|net)$/.test(host)) return "social";
    return "other";
  }

  function send(payload) {
    if (!live) return;
    try {
      var body = JSON.stringify(payload);
      // text/plain keeps this a "simple" cross-origin request, so no preflight can delay it on page exit.
      var ok = false;
      if (navigator.sendBeacon) ok = navigator.sendBeacon(HIT_URL, new Blob([body], { type: "text/plain;charset=UTF-8" }));
      if (!ok) {
        fetch(HIT_URL, { method: "POST", body: body, keepalive: true, credentials: "omit",
          headers: { "Content-Type": "text/plain;charset=UTF-8" } }).catch(function () {});
      }
    } catch (e) { /* never get in the way of the page */ }
  }

  function path() { return location.pathname; }

  function target(a) {
    var href = a.getAttribute("href") || "";
    if (href.indexOf(PLAY_URL) === 0) return "play";
    if (/\.apk(\?|#|$)/i.test(href) || /(^|\/)apk\/?(\?|#|$)/.test(href)) return "direct";
    return "";
  }

  function onClick(ev) {
    var a = ev.target && ev.target.closest ? ev.target.closest("a[href]") : null;
    if (!a) return;
    var t = target(a);
    if (t) send({ type: "click", target: t, path: path() });
  }

  function onSubmit(ev) {
    var f = ev.target;
    if (f && f.classList && f.classList.contains("signup-form")) send({ type: "click", target: "signup", path: path() });
  }

  var ctrl = window.AbortController ? new AbortController() : null;
  var timer = ctrl ? setTimeout(function () { ctrl.abort(); }, CHECK_TIMEOUT_MS) : null;
  fetch(HIT_URL, { method: "HEAD", cache: "no-store", credentials: "omit", signal: ctrl ? ctrl.signal : undefined })
    .then(function (r) {
      if (timer) clearTimeout(timer);
      if (!(r.ok || r.status === 405)) return;
      live = true;
      send({ type: "view", path: path(), ref: refCategory() });
    })
    .catch(function () { if (timer) clearTimeout(timer); });

  document.addEventListener("click", onClick, true);
  document.addEventListener("auxclick", onClick, true);
  document.addEventListener("submit", onSubmit, true);
})();
