/*
 * Roldeck Bridge — bedien de Roldeck-zwembadafdekking via je telefoon.
 *
 * Werking: een ESP32 stuurt een relaisbordje aan. De relaiscontacten zijn
 * gesoldeerd over de drukknoppen van een (reserve)handzender van de Roldeck.
 * Als een relais sluit, is dat elektrisch identiek aan een vingerdruk op de
 * knop. De ESP32 serveert zelf een mobielvriendelijke webpagina op je
 * eigen wifi-netwerk: http://roldeck.local
 *
 * Veiligheid:
 *  - De grote Roldeck-knop werkt als dodemansknop: het relais is alleen
 *    gesloten zolang je de knop op je telefoon ingedrukt houdt EN de
 *    verbinding levend is (heartbeat). Valt de wifi weg of laat je los,
 *    dan laat het relais binnen ~0,8 seconde los.
 *  - Maximale aaneengesloten bedientijd: MAX_HOLD_MS (daarna geforceerd los).
 *  - Toegang is beveiligd met een pincode.
 *
 * Flashen: Arduino IDE met het ESP32-boardpakket. Zie ../README.md.
 */

#include <WiFi.h>
#include <WebServer.h>
#include <ESPmDNS.h>

// ======================= INSTELLINGEN — PAS DEZE AAN =======================
const char* WIFI_SSID   = "JOUW_WIFI_NAAM";
const char* WIFI_PASS   = "JOUW_WIFI_WACHTWOORD";
const char* PINCODE     = "2468";        // pincode voor toegang via de app
const char* HOSTNAME    = "roldeck";     // -> http://roldeck.local

// GPIO-pinnen van de ESP32 naar de IN-pinnen van het relaisbordje.
// Kanaal 0 = grote Roldeck-knop (dodemansbediening).
// Kanaal 1..3 = de drie kleine lichtknoppen (korte puls).
const int RELAY_PINS[4] = {26, 27, 32, 33};
const bool RELAY_ACTIVE_LOW = true;      // de meeste blauwe relaisbordjes: LOW = aan

const unsigned long HOLD_TIMEOUT_MS = 800;    // los binnen 0,8 s zonder heartbeat
const unsigned long MAX_HOLD_MS     = 120000; // nooit langer dan 2 min aaneen
const unsigned long PULSE_MS        = 400;    // duur van een "korte druk"
// ===========================================================================

WebServer server(80);

String sessionToken;                 // wordt bij opstarten willekeurig gemaakt
int  heldChannel = -1;               // kanaal dat nu vastgehouden wordt (-1 = geen)
unsigned long lastBeat = 0;          // laatste heartbeat van de telefoon
unsigned long holdStart = 0;         // begin van de vasthoud-actie
unsigned long pulseEnd[4] = {0,0,0,0};

void relayWrite(int ch, bool on) {
  digitalWrite(RELAY_PINS[ch], (on ^ RELAY_ACTIVE_LOW) ? HIGH : LOW);
}

void releaseAll() {
  for (int i = 0; i < 4; i++) relayWrite(i, false);
  heldChannel = -1;
}

String makeToken() {
  String t;
  for (int i = 0; i < 32; i++) t += String((char)('a' + (esp_random() % 26)));
  return t;
}

bool authed() {
  String cookie = server.header("Cookie");
  return sessionToken.length() && cookie.indexOf("rdtoken=" + sessionToken) >= 0;
}

// ------------------------------ Webpagina ---------------------------------
const char PAGE[] PROGMEM = R"HTML(<!doctype html>
<html lang="nl"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,user-scalable=no,viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<title>Roldeck</title>
<style>
  :root { color-scheme: dark; }
  * { margin:0; padding:0; box-sizing:border-box; -webkit-tap-highlight-color:transparent; }
  body { font-family:-apple-system,system-ui,sans-serif; background:#08131f; color:#eaf4ff;
         min-height:100vh; display:flex; flex-direction:column; align-items:center;
         padding:max(20px,env(safe-area-inset-top)) 20px 40px; user-select:none; -webkit-user-select:none; }
  h1 { font-size:22px; letter-spacing:4px; margin:10px 0 4px; color:#7fc4ff; }
  .sub { font-size:13px; color:#5b7c99; margin-bottom:26px; }
  #status { min-height:22px; font-size:15px; color:#9fd0a0; margin-bottom:18px; text-align:center; }
  #bigbtn { width:210px; height:210px; border-radius:50%;
            border:6px solid #3a5a7a; background:radial-gradient(circle at 35% 30%,#1e3a55,#0d2036);
            color:#eaf4ff; font-size:19px; font-weight:700; letter-spacing:2px;
            box-shadow:0 8px 30px rgba(0,60,120,.45); touch-action:none; }
  #bigbtn.actief { background:radial-gradient(circle at 35% 30%,#2e7d32,#124016);
                   border-color:#66bb6a; box-shadow:0 0 40px rgba(60,200,90,.5); }
  #bigbtn small { display:block; font-size:12px; font-weight:400; color:#8fb4d4; margin-top:8px; letter-spacing:0; }
  .lichten { display:flex; gap:14px; margin-top:34px; }
  .lichten button { width:92px; height:64px; border-radius:16px; border:2px solid #3a5a7a;
                    background:#0d2036; color:#cfe6ff; font-size:14px; }
  .lichten button:active { background:#1e3a55; }
  .waarschuwing { margin-top:36px; font-size:12px; color:#7c8ea0; text-align:center; max-width:320px; line-height:1.5; }
</style></head><body>
<h1>ROLDECK</h1>
<div class="sub">zwembadafdekking</div>
<div id="status">&nbsp;</div>
<button id="bigbtn">HOUD VAST<small>om het roldeck te bewegen</small></button>
<div class="lichten">
  <button data-ch="1">Licht&nbsp;1</button>
  <button data-ch="2">Licht&nbsp;2</button>
  <button data-ch="3">Licht&nbsp;3</button>
</div>
<div class="waarschuwing">⚠️ Bedien het roldeck alleen als je het zwembad kunt zien.
Laat los om direct te stoppen. Kinderen niet laten bedienen.</div>
<script>
const status = document.getElementById('status');
const big = document.getElementById('bigbtn');
let beatTimer = null;

function melding(t, kleur) { status.textContent = t; status.style.color = kleur || '#9fd0a0'; }

async function api(p) {
  const r = await fetch(p, {method:'POST'});
  if (r.status === 401) { location.href = '/login'; throw new Error('401'); }
  return r;
}

function startHold(e) {
  e.preventDefault();
  if (beatTimer) return;
  api('/api/hold?ch=0').then(() => {
    big.classList.add('actief');
    melding('Roldeck beweegt… laat los om te stoppen');
    beatTimer = setInterval(() => {
      api('/api/beat').catch(stopHold);
    }, 250);
  }).catch(() => melding('Geen verbinding', '#ff8a80'));
}

function stopHold() {
  if (beatTimer) { clearInterval(beatTimer); beatTimer = null; }
  big.classList.remove('actief');
  api('/api/release').catch(()=>{});
  melding('Gestopt');
}

big.addEventListener('pointerdown', startHold);
['pointerup','pointercancel','pointerleave'].forEach(ev => big.addEventListener(ev, stopHold));
window.addEventListener('blur', stopHold);
big.addEventListener('contextmenu', e => e.preventDefault());

document.querySelectorAll('.lichten button').forEach(b => {
  b.addEventListener('click', () => {
    api('/api/pulse?ch=' + b.dataset.ch)
      .then(() => melding(b.textContent.replace(/ /g,' ') + ' geschakeld'))
      .catch(() => melding('Geen verbinding', '#ff8a80'));
  });
});
</script></body></html>)HTML";

const char LOGIN[] PROGMEM = R"HTML(<!doctype html>
<html lang="nl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Roldeck — inloggen</title>
<style>
  body { font-family:-apple-system,system-ui,sans-serif; background:#08131f; color:#eaf4ff;
         min-height:100vh; display:flex; flex-direction:column; align-items:center;
         justify-content:center; gap:18px; }
  h1 { letter-spacing:4px; color:#7fc4ff; }
  input { font-size:28px; text-align:center; letter-spacing:10px; width:180px; padding:10px;
          border-radius:12px; border:2px solid #3a5a7a; background:#0d2036; color:#fff; }
  button { font-size:17px; padding:12px 34px; border-radius:12px; border:0; background:#1565c0; color:#fff; }
  .fout { color:#ff8a80; min-height:20px; }
</style></head><body>
<h1>ROLDECK</h1>
<div class="fout">%FOUT%</div>
<form method="POST" action="/login">
  <input name="pin" type="password" inputmode="numeric" autocomplete="off" placeholder="pincode" autofocus>
  <div style="height:14px"></div>
  <button type="submit" style="width:100%">Inloggen</button>
</form>
</body></html>)HTML";

// ------------------------------ Handlers -----------------------------------
void sendLogin(const String& fout) {
  String p = FPSTR(LOGIN);
  p.replace("%FOUT%", fout);
  server.send(200, "text/html", p);
}

void handleRoot() {
  if (!authed()) { server.sendHeader("Location", "/login"); server.send(302); return; }
  server.send_P(200, "text/html", PAGE);
}

void handleLogin() {
  if (server.method() == HTTP_POST) {
    if (server.arg("pin") == PINCODE) {
      server.sendHeader("Set-Cookie", "rdtoken=" + sessionToken + "; Max-Age=2592000; Path=/; SameSite=Strict");
      server.sendHeader("Location", "/");
      server.send(302);
    } else {
      sendLogin("Onjuiste pincode");
    }
  } else {
    sendLogin("");
  }
}

bool requireAuth() {
  if (authed()) return true;
  server.send(401, "text/plain", "unauthorized");
  return false;
}

void handleHold() {
  if (!requireAuth()) return;
  if (server.arg("ch").toInt() != 0) { server.send(400, "text/plain", "alleen kanaal 0"); return; }
  heldChannel = 0;
  holdStart = lastBeat = millis();
  relayWrite(0, true);
  server.send(200, "text/plain", "ok");
}

void handleBeat() {
  if (!requireAuth()) return;
  if (heldChannel == 0) lastBeat = millis();
  server.send(200, "text/plain", heldChannel == 0 ? "ok" : "released");
}

void handleRelease() {
  if (!requireAuth()) return;
  releaseAll();
  server.send(200, "text/plain", "ok");
}

void handlePulse() {
  if (!requireAuth()) return;
  int ch = server.arg("ch").toInt();
  if (ch < 1 || ch > 3) { server.send(400, "text/plain", "kanaal 1-3"); return; }
  relayWrite(ch, true);
  pulseEnd[ch] = millis() + PULSE_MS;
  server.send(200, "text/plain", "ok");
}

// ------------------------------ Setup/loop ---------------------------------
void setup() {
  Serial.begin(115200);
  for (int i = 0; i < 4; i++) { pinMode(RELAY_PINS[i], OUTPUT); relayWrite(i, false); }

  sessionToken = makeToken();

  WiFi.mode(WIFI_STA);
  WiFi.setHostname(HOSTNAME);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("Verbinden met wifi");
  while (WiFi.status() != WL_CONNECTED) { delay(400); Serial.print("."); }
  Serial.printf("\nVerbonden: http://%s.local  (%s)\n", HOSTNAME, WiFi.localIP().toString().c_str());

  MDNS.begin(HOSTNAME);

  const char* headers[] = {"Cookie"};
  server.collectHeaders(headers, 1);
  server.on("/", handleRoot);
  server.on("/login", handleLogin);
  server.on("/api/hold", HTTP_POST, handleHold);
  server.on("/api/beat", HTTP_POST, handleBeat);
  server.on("/api/release", HTTP_POST, handleRelease);
  server.on("/api/pulse", HTTP_POST, handlePulse);
  server.begin();
}

void loop() {
  server.handleClient();

  unsigned long now = millis();

  // Dodemans-bewaking: geen heartbeat of te lang vastgehouden -> loslaten.
  if (heldChannel == 0 &&
      (now - lastBeat > HOLD_TIMEOUT_MS || now - holdStart > MAX_HOLD_MS)) {
    releaseAll();
    Serial.println("Watchdog: relais losgelaten");
  }

  // Korte pulsen (lichtknoppen) beëindigen.
  for (int i = 1; i < 4; i++) {
    if (pulseEnd[i] && now > pulseEnd[i]) { relayWrite(i, false); pulseEnd[i] = 0; }
  }

  // Wifi kwijt? Alles loslaten en opnieuw verbinden.
  if (WiFi.status() != WL_CONNECTED) {
    releaseAll();
    WiFi.reconnect();
    delay(500);
  }
}
