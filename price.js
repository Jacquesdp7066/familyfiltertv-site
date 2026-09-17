// Shows Google Play's listed price for the visitor's country. The static page already
// reads US$14.99, so if anything here fails the page stays correct.
// Prices come only from data/prices.json (exported from the Play Developer API); nothing is converted.
(function () {
  "use strict";

  var STORE_KEY = "fftv-price-country";

  // Time zone -> region. Covers the largest markets; anything else falls through to the language guess.
  var ZONES = {
    "Africa/Johannesburg": "ZA", "Africa/Windhoek": "NA", "Africa/Gaborone": "BW", "Africa/Harare": "ZW",
    "Africa/Maputo": "MZ", "Africa/Lusaka": "ZM", "Africa/Maseru": "LS", "Africa/Mbabane": "SZ",
    "Africa/Lagos": "NG", "Africa/Nairobi": "KE", "Africa/Accra": "GH", "Africa/Cairo": "EG",
    "Africa/Casablanca": "MA", "Africa/Kampala": "UG", "Africa/Dar_es_Salaam": "TZ",
    "America/New_York": "US", "America/Chicago": "US", "America/Denver": "US", "America/Phoenix": "US",
    "America/Los_Angeles": "US", "America/Anchorage": "US", "Pacific/Honolulu": "US",
    "America/Detroit": "US", "America/Indiana/Indianapolis": "US", "America/Boise": "US",
    "America/Toronto": "CA", "America/Vancouver": "CA", "America/Edmonton": "CA", "America/Winnipeg": "CA",
    "America/Halifax": "CA", "America/St_Johns": "CA", "America/Regina": "CA",
    "America/Mexico_City": "MX", "America/Monterrey": "MX", "America/Tijuana": "MX", "America/Cancun": "MX",
    "America/Sao_Paulo": "BR", "America/Manaus": "BR", "America/Fortaleza": "BR", "America/Recife": "BR",
    "America/Bahia": "BR", "America/Belem": "BR",
    "America/Argentina/Buenos_Aires": "AR", "America/Buenos_Aires": "AR", "America/Bogota": "CO",
    "America/Santiago": "CL", "America/Lima": "PE",
    "Europe/London": "GB", "Europe/Dublin": "IE", "Europe/Berlin": "DE", "Europe/Paris": "FR",
    "Europe/Madrid": "ES", "Europe/Rome": "IT", "Europe/Amsterdam": "NL", "Europe/Brussels": "BE",
    "Europe/Zurich": "CH", "Europe/Vienna": "AT", "Europe/Stockholm": "SE", "Europe/Oslo": "NO",
    "Europe/Copenhagen": "DK", "Europe/Helsinki": "FI", "Europe/Warsaw": "PL", "Europe/Prague": "CZ",
    "Europe/Lisbon": "PT", "Europe/Athens": "GR", "Europe/Bucharest": "RO", "Europe/Budapest": "HU",
    "Europe/Istanbul": "TR", "Europe/Moscow": "RU", "Europe/Kiev": "UA", "Europe/Kyiv": "UA",
    "Asia/Kolkata": "IN", "Asia/Calcutta": "IN", "Asia/Karachi": "PK", "Asia/Dhaka": "BD",
    "Asia/Jakarta": "ID", "Asia/Manila": "PH", "Asia/Ho_Chi_Minh": "VN", "Asia/Saigon": "VN",
    "Asia/Bangkok": "TH", "Asia/Kuala_Lumpur": "MY", "Asia/Singapore": "SG", "Asia/Tokyo": "JP",
    "Asia/Seoul": "KR", "Asia/Shanghai": "CN", "Asia/Hong_Kong": "HK", "Asia/Taipei": "TW",
    "Asia/Dubai": "AE", "Asia/Riyadh": "SA", "Asia/Jerusalem": "IL", "Asia/Tel_Aviv": "IL",
    "Australia/Sydney": "AU", "Australia/Melbourne": "AU", "Australia/Brisbane": "AU",
    "Australia/Perth": "AU", "Australia/Adelaide": "AU", "Australia/Hobart": "AU", "Australia/Darwin": "AU",
    "Pacific/Auckland": "NZ"
  };

  // Launch ladder (#153): a time-limited discount for the first 200 subscribers per tier.
  // Fetched only after prices.json resolves; any failure, timeout, or open:false leaves
  // this block hidden and the rest of the page exactly as it is without it.
  var LADDER_URL = "https://europe-west1-familyfiltertv.cloudfunctions.net/launchLadderState";
  var LADDER_TIMEOUT_MS = 4000;

  var box = document.getElementById("price-country");
  var input = document.getElementById("price-country-input");
  var list = document.getElementById("price-country-list");
  var annual = document.getElementById("price-annual");
  var devices = document.getElementById("price-devices");
  var noteCountry = document.getElementById("price-note-country");
  var launchBox = document.getElementById("price-launch");
  var launchPct = document.getElementById("price-launch-pct");
  var launchSeats = document.getElementById("price-launch-seats");
  var launchPrice = document.getElementById("price-launch-price");
  var launchEnd = document.getElementById("price-launch-end");
  if (!box || !input || !list || !annual || !devices || !window.fetch || !window.Intl) return;
  var launchReady = !!(launchBox && launchPct && launchSeats && launchPrice && launchEnd);

  var names;
  try { names = new Intl.DisplayNames(["en"], { type: "region" }); } catch (e) { names = null; }
  function countryName(code) {
    try { return (names && names.of(code)) || code; } catch (e) { return code; }
  }

  function money(price, region) {
    var whole = Math.round(price.amount) === price.amount;
    var opts = { style: "currency", currency: price.currency };
    if (whole) { opts.minimumFractionDigits = 0; opts.maximumFractionDigits = 0; }
    try {
      return new Intl.NumberFormat("en-" + region, opts).format(price.amount);
    } catch (e) {
      try { return new Intl.NumberFormat("en", opts).format(price.amount); }
      catch (e2) { return price.currency + " " + price.amount; }
    }
  }

  // Local fixture for testing the ladder without touching the (not-yet-live) endpoint:
  // ?ladderFixture=1 -> data/ladder-fixture.json (open); ?ladderFixture=closed ->
  // data/ladder-fixture-closed.json; any other value -> data/ladder-fixture-<value>.json.
  function ladderFixtureUrl() {
    var m = /[?&]ladderFixture=([^&]*)/.exec(window.location.search);
    if (!m) return null;
    var v = decodeURIComponent(m[1] || "");
    return (!v || v === "1") ? "data/ladder-fixture.json" : "data/ladder-fixture-" + v + ".json";
  }

  function fetchWithTimeout(url, ms) {
    if (!window.AbortController) return fetch(url, { cache: "no-cache" });
    var ctrl = new AbortController();
    var timer = setTimeout(function () { ctrl.abort(); }, ms);
    function done(v) { clearTimeout(timer); return v; }
    return fetch(url, { cache: "no-cache", signal: ctrl.signal }).then(
      function (r) { return done(r); },
      function (e) { done(); throw e; }
    );
  }

  function round2(n) { return Math.round(n * 100) / 100; }

  function ladderEndDate(iso) {
    try {
      return new Intl.DateTimeFormat("en-GB", {
        day: "numeric", month: "long", year: "numeric", timeZone: "Africa/Johannesburg"
      }).format(new Date(iso));
    } catch (e) { return ""; }
  }

  function storedChoice() {
    try { return localStorage.getItem(STORE_KEY); } catch (e) { return null; }
  }
  function storeChoice(code) {
    try { localStorage.setItem(STORE_KEY, code); } catch (e) { /* private mode: ignore */ }
  }

  function guess(regions) {
    var saved = storedChoice();
    if (saved && regions[saved]) return saved;
    try {
      var zone = Intl.DateTimeFormat().resolvedOptions().timeZone;
      if (zone && regions[ZONES[zone]]) return ZONES[zone];
    } catch (e) { /* no time zone */ }
    var langs = navigator.languages || (navigator.language ? [navigator.language] : []);
    for (var i = 0; i < langs.length; i++) {
      var m = /[-_]([A-Za-z]{2})(?:$|[-_])/.exec(langs[i]);
      if (m && regions[m[1].toUpperCase()]) return m[1].toUpperCase();
    }
    return "US";
  }

  fetch("data/prices.json", { cache: "no-cache" })
    .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(function (data) {
      var regions = data && data.regions;
      if (!regions || !regions.US) return;

      var entries = Object.keys(regions).map(function (code) {
        return { code: code, name: countryName(code) };
      }).sort(function (a, b) { return a.name.localeCompare(b.name, "en"); });

      var byName = {};
      entries.forEach(function (e) {
        var opt = document.createElement("option");
        opt.value = e.name;
        list.appendChild(opt);
        byName[e.name.toLowerCase()] = e.code;
      });

      var selectedCode = null;
      var ladderState = null; // set once launchLadderState succeeds and open:true; else stays null

      function renderLadder() {
        if (!launchReady) return;
        var ladder = ladderState && selectedCode && regions[selectedCode] &&
          ladderState.ladders && ladderState.ladders[selectedCode === "ZA" ? "ZA" : "WORLD"];
        if (!ladderState || ladderState.open !== true || !ladder || !(ladder.percentOff > 0)) {
          launchBox.hidden = true;
          return;
        }
        var isZA = selectedCode === "ZA";
        var annualPrice = regions[selectedCode].annual;
        var firstYearAmount = round2(annualPrice.amount * (1 - ladder.percentOff / 100));
        var firstYearText = money({ amount: firstYearAmount, currency: annualPrice.currency }, selectedCode);
        if (!isZA) firstYearText = "about " + firstYearText;
        var renewalText = money(annualPrice, selectedCode);

        launchPct.textContent = ladder.percentOff + "%";
        launchSeats.textContent = ladder.seatsLeftInTier + " of " + ladderState.seatsPerTier +
          " seats left at this price " + (isZA ? "in South Africa" : "for the rest of the world") + ".";
        launchPrice.textContent = firstYearText + " for your first year, then " + renewalText +
          " a year. 14-day free trial first.";
        launchEnd.textContent = "Ends " + ladderEndDate(ladderState.endsAt) + ".";
        launchBox.hidden = false;
      }

      function show(code) {
        var p = regions[code];
        input.value = countryName(code);
        annual.textContent = money(p.annual, code);
        devices.textContent = "A 4th, 5th or 6th device adds " + money(p.device4, code) + ", " +
          money(p.device5, code) + " or " + money(p.device6, code) + " a year.";
        if (noteCountry) noteCountry.textContent = " for the selected country";
        selectedCode = code;
        renderLadder();
      }

      // While typing, only a full country name counts; a two-letter code is accepted on commit.
      function pick(allowCode) {
        var v = input.value.trim().toLowerCase();
        var code = byName[v] || (allowCode && regions[v.toUpperCase()] ? v.toUpperCase() : null);
        if (!code) return false;
        show(code);
        storeChoice(code);
        return true;
      }

      var current = guess(regions);
      show(current);
      box.hidden = false;

      if (launchReady) {
        fetchWithTimeout(ladderFixtureUrl() || LADDER_URL, LADDER_TIMEOUT_MS)
          .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
          .then(function (data) { ladderState = data; renderLadder(); })
          .catch(function () { ladderState = null; renderLadder(); });
      }

      input.addEventListener("input", function () { pick(false); });
      input.addEventListener("change", function () {
        if (!pick(true)) {
          var saved = storedChoice();
          show(saved && regions[saved] ? saved : current);
        }
      });
      input.addEventListener("focus", function () { input.select(); });
    })
    .catch(function () { /* keep the static US price */ });
})();
