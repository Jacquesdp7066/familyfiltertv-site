// Consent banner + Google Analytics 4, loaded only after the visitor accepts.
//
// Dormant by default: while GA4_ID is empty this script does nothing at all (no banner, no network,
// no storage). To switch it on, paste the GA4 Measurement ID below (looks like G-ABC123XYZ9) and
// update the privacy policy first (draft wording is in docs/seo/IMPLEMENTATION_REPORT.md).
//
// Rules this file keeps:
//   - Nothing from Google is requested before the visitor presses Accept.
//   - Reject is as easy as Accept: same size, same row, one click.
//   - Do Not Track and Global Privacy Control count as Reject, with no banner (same as hit.js).
//   - The choice is kept in this browser only (localStorage "fftv-consent"), and can be changed
//     from the "Analytics choices" link in the footer.
//   - No advertising features: Google signals and ad personalisation are off.
//   - A click on a Google Play link is a store click, never a download or an install.
(function () {
  "use strict";

  var GA4_ID = ""; // TODO(Jacques): paste the GA4 Measurement ID here, e.g. "G-ABC123XYZ9"

  var KEY = "fftv-consent";
  var PLAY_URL = "https://play.google.com/store/apps/details?id=com.familyfiltertv.app";
  var loaded = false;

  if (!/^G-[A-Z0-9]{6,}$/.test(GA4_ID)) return;

  function get() { try { return localStorage.getItem(KEY); } catch (e) { return null; } }
  function set(v) { try { localStorage.setItem(KEY, v); } catch (e) { /* private mode: choice lasts this page only */ } }

  try {
    var dnt = [navigator.doNotTrack, window.doNotTrack, navigator.msDoNotTrack];
    for (var i = 0; i < dnt.length; i++) if (dnt[i] === "1" || dnt[i] === "yes" || dnt[i] === 1) return;
    if (navigator.globalPrivacyControl === true) return;
  } catch (e) { return; }

  // ---- Google Analytics (only ever called after Accept) ----
  function gtag() { window.dataLayer.push(arguments); }

  function loadGA() {
    if (loaded) return;
    loaded = true;
    window["ga-disable-" + GA4_ID] = false;
    window.dataLayer = window.dataLayer || [];
    gtag("consent", "default", {
      analytics_storage: "granted", ad_storage: "denied", ad_user_data: "denied", ad_personalization: "denied"
    });
    gtag("js", new Date());
    gtag("config", GA4_ID, { allow_google_signals: false, allow_ad_personalization_signals: false });
    var s = document.createElement("script");
    s.async = true;
    s.src = "https://www.googletagmanager.com/gtag/js?id=" + encodeURIComponent(GA4_ID);
    document.head.appendChild(s);
  }

  function stopGA() {
    window["ga-disable-" + GA4_ID] = true;
    // Remove the cookies Google set while the visitor had accepted.
    var host = location.hostname, parts = host.split("."), domains = [host, "." + host];
    if (parts.length > 2) domains.push("." + parts.slice(-2).join("."));
    document.cookie.split(";").forEach(function (c) {
      var name = c.split("=")[0].trim();
      if (/^_ga($|_)/.test(name) || /^_gid$/.test(name)) {
        domains.forEach(function (d) {
          document.cookie = name + "=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/; domain=" + d;
        });
        document.cookie = name + "=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/";
      }
    });
  }

  function track(name, params) {
    if (!loaded || get() !== "granted") return;
    params = params || {};
    params.page_path = location.pathname;
    gtag("event", name, params);
  }

  // ---- Events: store clicks, trial CTA clicks, video engagement ----
  function onClick(ev) {
    var a = ev.target && ev.target.closest ? ev.target.closest("a[href]") : null;
    if (!a) return;
    var href = a.getAttribute("href") || "";
    var where = a.getAttribute("data-cta") || "link";
    if (href.indexOf(PLAY_URL) === 0) {
      track("play_store_click", { link_location: where });
      if (where.indexOf("trial") === 0) track("cta_trial_click", { link_location: where });
    } else if (/\.apk(\?|#|$)/i.test(href) || /(^|\/)apk\/?(\?|#|$)/.test(href)) {
      track("direct_install_click", { link_location: where });
    }
  }

  var seen = new WeakMap();
  function videoName(v) {
    return (v.getAttribute("data-video-name") || v.getAttribute("aria-label") || v.currentSrc.split("/").pop() || "video").slice(0, 100);
  }
  function isDecorative(v) { return v.id === "hero-loop" || (v.muted && v.loop); }

  function onPlay(ev) {
    var v = ev.target;
    if (!v || v.tagName !== "VIDEO" || isDecorative(v)) return;
    var s = seen.get(v) || {};
    if (!s.played) { s.played = true; seen.set(v, s); track("video_play", { video_title: videoName(v) }); }
  }
  function onTime(ev) {
    var v = ev.target;
    if (!v || v.tagName !== "VIDEO" || isDecorative(v) || !v.duration) return;
    var s = seen.get(v) || {}, pct = Math.floor((v.currentTime / v.duration) * 100);
    [25, 50, 75].forEach(function (m) {
      if (pct >= m && !s[m]) { s[m] = true; seen.set(v, s); track("video_progress", { video_title: videoName(v), video_percent: m }); }
    });
  }
  function onEnded(ev) {
    var v = ev.target;
    if (!v || v.tagName !== "VIDEO" || isDecorative(v)) return;
    track("video_progress", { video_title: videoName(v), video_percent: 100 });
  }

  function listen() {
    document.addEventListener("click", onClick, true);
    document.addEventListener("auxclick", onClick, true);
    // media events do not bubble; capture on document catches every <video>
    document.addEventListener("play", onPlay, true);
    document.addEventListener("timeupdate", onTime, true);
    document.addEventListener("ended", onEnded, true);
  }

  // ---- Banner ----
  var banner = null;

  function close() { if (banner && banner.parentNode) banner.parentNode.removeChild(banner); banner = null; }

  function choose(v) {
    var was = get();
    set(v);
    close();
    if (v === "granted") loadGA();
    else if (was === "granted" || loaded) stopGA();
    updateFooterLink();
  }

  function open() {
    if (banner) return;
    banner = document.createElement("div");
    banner.className = "consent";
    banner.setAttribute("role", "region");
    banner.setAttribute("aria-label", "Analytics choice");
    banner.innerHTML =
      '<p class="consent-text"><strong>Analytics, only if you say yes.</strong> We would like to use Google Analytics to ' +
      'see which pages and buttons people use, so we can improve this site. It stays off unless you accept. ' +
      '<a href="/privacy.html">Privacy policy</a>.</p>' +
      '<div class="consent-actions">' +
      '<button type="button" class="consent-btn" data-choice="denied">Reject</button>' +
      '<button type="button" class="consent-btn" data-choice="granted">Accept</button>' +
      '</div>';
    banner.addEventListener("click", function (e) {
      var b = e.target.closest ? e.target.closest("button[data-choice]") : null;
      if (b) choose(b.getAttribute("data-choice"));
    });
    document.body.appendChild(banner);
  }

  function updateFooterLink() { /* link text stays the same; kept for future state labels */ }

  function footerLink() {
    var nav = document.querySelector(".foot-nav");
    if (!nav || nav.querySelector("[data-consent-open]")) return;
    var a = document.createElement("a");
    a.href = "#analytics-choices";
    a.setAttribute("data-consent-open", "");
    a.textContent = "Analytics choices";
    a.addEventListener("click", function (e) { e.preventDefault(); open(); });
    nav.appendChild(a);
  }

  function start() {
    footerLink();
    var c = get();
    if (c === "granted") { loadGA(); }
    else if (c !== "denied") { open(); }
    listen();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();
})();
