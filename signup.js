// Launch-updates sign-up. The form ships with the `hidden` attribute and stays hidden unless the
// endpoint answers a quick reachability check, so the live site never shows a form that cannot work.
// Posts JSON {email, source, website} to SIGNUP_URL. `website` is the honeypot: real people never see
// or fill it, and the server drops anything that does. Same host and region pattern as price.js.
(function () {
  "use strict";

  var SIGNUP_URL = "https://europe-west1-familyfiltertv.cloudfunctions.net/signup";
  var CHECK_TIMEOUT_MS = 4000;
  var POST_TIMEOUT_MS = 10000;

  var blocks = document.querySelectorAll("[data-signup]");
  if (!blocks.length || !window.fetch) return;

  function request(url, opts, ms) {
    if (!window.AbortController) return fetch(url, opts);
    var ctrl = new AbortController();
    var timer = setTimeout(function () { ctrl.abort(); }, ms);
    opts.signal = ctrl.signal;
    return fetch(url, opts).then(
      function (r) { clearTimeout(timer); return r; },
      function (e) { clearTimeout(timer); throw e; }
    );
  }

  // Reachable = the endpoint answers a HEAD with 2xx/204, or 405 (it exists but only takes POST).
  // A 404, a network failure, a CORS refusal or a timeout all leave the form hidden.
  function reachable() {
    return request(SIGNUP_URL, { method: "HEAD", cache: "no-store" }, CHECK_TIMEOUT_MS).then(
      function (r) { return r.ok || r.status === 405; },
      function () { return false; }
    );
  }

  function wire(block) {
    var form = block.querySelector("form");
    var email = block.querySelector("input[type=email]");
    var trap = block.querySelector("input[name=website]");
    var button = block.querySelector("button");
    var status = block.querySelector(".signup-status");
    var thanks = block.querySelector(".signup-thanks");
    if (!form || !email || !trap || !button || !status || !thanks) return;
    var source = block.getAttribute("data-source") || "site";

    function say(text, isError) {
      status.textContent = text;
      status.classList.toggle("signup-error", !!isError);
    }

    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var value = email.value.trim();
      if (!/^[^\s@]+@[^\s@.]+(\.[^\s@.]+)+$/.test(value)) {
        say("That does not look like an email address. Please check it and try again.", true);
        email.focus();
        return;
      }
      button.disabled = true;
      email.readOnly = true;
      say("Sending...", false);
      request(SIGNUP_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: value, source: source, website: trap.value })
      }, POST_TIMEOUT_MS).then(function (r) {
        if (!r.ok) throw new Error(r.status);
        form.hidden = true;
        status.textContent = "";
        thanks.hidden = false;
        thanks.focus();
      }).catch(function () {
        button.disabled = false;
        email.readOnly = false;
        say("Sorry, that did not go through. Please try again in a minute, or email jacquesjdupreez@gmail.com and we will add you.", true);
      });
    });
  }

  reachable().then(function (ok) {
    if (!ok) return;
    for (var i = 0; i < blocks.length; i++) {
      wire(blocks[i]);
      blocks[i].hidden = false;
    }
  });
})();
