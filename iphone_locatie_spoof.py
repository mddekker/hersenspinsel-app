"""
iPhone Locatie Spoof — bestuur de GPS-locatie van je iPhone vanaf je laptop.

⚠️  BELANGRIJK: deze app draait LOKAAL op je eigen computer (Mac/Windows/Linux),
    NIET in de cloud. Je hangt je iPhone met een USB-kabel aan diezelfde computer.

Het zet de locatie systeembreed: álle apps op je iPhone (Kaarten, WhatsApp
live-locatie, Find My, enz.) zien dan de locatie die jij hier kiest, totdat je
'm wist of de telefoon herstart. Geen jailbreak nodig.

Onder water gebruikt deze app het open-source `pymobiledevice3` via de
officiële Developer-locatiesimulatie van Apple.

Start met:
    pip install -r requirements-locatie.txt
    streamlit run iphone_locatie_spoof.py
"""

import json
import socket
import subprocess
import sys
import tempfile
import time

import streamlit as st

# --- Optionele afhankelijkheden (app blijft werken zonder kaart/zoeken) ---
try:
    import folium
    from streamlit_folium import st_folium

    HEEFT_KAART = True
except Exception:
    HEEFT_KAART = False

try:
    from geopy.geocoders import Nominatim

    HEEFT_GEOCODER = True
except Exception:
    HEEFT_GEOCODER = False


# pymobiledevice3 tunneld luistert standaard hier (nodig voor iOS 17+)
TUNNELD_HOST, TUNNELD_PORT = "127.0.0.1", 49151

# Het commando om pymobiledevice3 aan te roepen met dezelfde Python-omgeving
PMD3 = [sys.executable, "-m", "pymobiledevice3"]


st.set_page_config(page_title="iPhone Locatie", page_icon="📍", layout="centered")


# --------------------------------------------------------------------------- #
#  Hulpfuncties: praten met pymobiledevice3                                    #
# --------------------------------------------------------------------------- #
def run_cmd(args: list[str], timeout: int = 30) -> tuple[int, str]:
    """Draai een kort pymobiledevice3-commando en geef (returncode, output)."""
    try:
        res = subprocess.run(
            PMD3 + args,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return res.returncode, (res.stdout or "") + (res.stderr or "")
    except FileNotFoundError:
        return 127, "pymobiledevice3 niet gevonden. Installeer met: pip install pymobiledevice3"
    except subprocess.TimeoutExpired:
        return 124, "Time-out — duurt te lang. Hangt de iPhone er nog aan en is hij ontgrendeld?"


def lijst_apparaten() -> tuple[list[dict], str]:
    """Geef de aangesloten iPhones terug (en eventueel een foutmelding)."""
    rc, out = run_cmd(["usbmux", "list"], timeout=20)
    if rc != 0:
        return [], out.strip()
    try:
        data = json.loads(out)
        return (data if isinstance(data, list) else [data]), ""
    except json.JSONDecodeError:
        return [], "Kon het antwoord van pymobiledevice3 niet lezen:\n" + out.strip()


def ios_hoofdversie(versie: str | None) -> int:
    """Haal het hoofdversienummer uit bv. '17.4.1' -> 17."""
    try:
        return int(str(versie).split(".")[0])
    except (ValueError, AttributeError):
        return 0


def tunneld_actief() -> bool:
    """Controleer of `pymobiledevice3 remote tunneld` draait (iOS 17+)."""
    try:
        with socket.create_connection((TUNNELD_HOST, TUNNELD_PORT), timeout=1.0):
            return True
    except OSError:
        return False


def _udid_args(udid: str | None) -> list[str]:
    return ["--udid", udid] if udid else []


def stop_actieve_simulatie() -> None:
    """Beëindig een lopend iOS 17+ simulatieproces (locatie valt terug op echt)."""
    proc = st.session_state.get("dvt_proc")
    if proc and proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
    st.session_state["dvt_proc"] = None


def stel_locatie_in(lat: float, lon: float, ios: int, udid: str | None) -> tuple[bool, str]:
    """Zet de gekozen locatie op de iPhone. Kiest automatisch de juiste methode."""
    if ios >= 17:
        # iOS 17+: het 'set'-proces moet BLIJVEN DRAAIEN, anders valt de locatie
        # direct terug op echt. We starten het op de achtergrond en houden het vast.
        if not tunneld_actief():
            return False, (
                "tunneld draait nog niet. Open een aparte terminal en start:\n\n"
                "    sudo pymobiledevice3 remote tunneld\n\n"
                "Laat die terminal open staan en probeer het hier opnieuw."
            )
        stop_actieve_simulatie()
        cmd = PMD3 + ["developer", "dvt", "simulate-location"] + _udid_args(udid)
        cmd += ["set", "--", str(lat), str(lon)]
        logf = tempfile.NamedTemporaryFile(
            mode="w+", suffix=".log", prefix="pmd3_loc_", delete=False
        )
        proc = subprocess.Popen(
            cmd, stdout=logf, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL
        )
        time.sleep(2.5)  # even wachten of het meteen crasht
        if proc.poll() is not None:
            logf.flush()
            with open(logf.name) as f:
                fout = f.read().strip()
            return False, fout or "Het simulatieproces stopte direct. Staat Developer Mode aan?"
        st.session_state["dvt_proc"] = proc
        return True, "Locatie ingesteld en actief (sessie blijft open in de achtergrond)."

    # iOS 16 en lager: instellen en klaar — de locatie blijft staan tot je wist.
    cmd = ["developer", "simulate-location"] + _udid_args(udid) + ["set", "--", str(lat), str(lon)]
    rc, out = run_cmd(cmd)
    if rc != 0:
        return False, out.strip() or "Onbekende fout bij het instellen."
    return True, "Locatie ingesteld."


def wis_locatie(ios: int, udid: str | None) -> tuple[bool, str]:
    """Herstel de echte GPS-locatie."""
    if ios >= 17:
        stop_actieve_simulatie()
        return True, "Simulatie gestopt — je iPhone gebruikt weer de echte locatie."
    cmd = ["developer", "simulate-location"] + _udid_args(udid) + ["clear"]
    rc, out = run_cmd(cmd)
    if rc != 0:
        return False, out.strip() or "Onbekende fout bij het wissen."
    return True, "Echte locatie hersteld."


# --------------------------------------------------------------------------- #
#  Sessietoestand                                                              #
# --------------------------------------------------------------------------- #
st.session_state.setdefault("apparaten", [])
st.session_state.setdefault("device_idx", 0)
st.session_state.setdefault("lat", 52.3676)  # standaard: Amsterdam
st.session_state.setdefault("lon", 4.9041)
st.session_state.setdefault("dvt_proc", None)
st.session_state.setdefault("melding", None)


# --------------------------------------------------------------------------- #
#  UI                                                                          #
# --------------------------------------------------------------------------- #
st.title("📍 iPhone Locatie")
st.caption(
    "Bepaal handmatig waar je iPhone denkt te zijn. Werkt systeembreed voor "
    "álle apps. Draai dit op je eigen computer met de iPhone via USB aangesloten."
)

with st.expander("ℹ️  Eenmalige voorbereiding op je iPhone"):
    st.markdown(
        """
1. **Sluit je iPhone met een USB-kabel** aan op deze computer en tik op
   **Vertrouwen** in het pop-upvenster.
2. Zet **Developer Mode** aan: *Instellingen → Privacy en beveiliging →
   Ontwikkelaarsmodus* (vanaf iOS 16; daarna herstart de telefoon).
3. **Alleen voor iOS 17 en nieuwer**: open een aparte terminal en start de
   tunnel (laat die terminal open staan):
   ```
   sudo pymobiledevice3 remote tunneld
   ```
"""
    )

st.divider()

# --- Stap 1: apparaat vinden ------------------------------------------------ #
st.subheader("1 · Verbind je iPhone")
if st.button("🔍 Zoek aangesloten iPhones", use_container_width=True):
    apparaten, fout = lijst_apparaten()
    st.session_state["apparaten"] = apparaten
    st.session_state["device_idx"] = 0
    if fout:
        st.error(fout)
    elif not apparaten:
        st.warning("Geen apparaat gevonden. Zit de kabel erin en is de telefoon ontgrendeld + vertrouwd?")

apparaten = st.session_state["apparaten"]
ios = 0
udid = None
if apparaten:
    labels = [
        f"{d.get('DeviceName') or 'iPhone'} — iOS {d.get('ProductVersion', '?')} "
        f"({d.get('ProductType', '?')})"
        for d in apparaten
    ]
    idx = st.radio(
        "Gevonden apparaten",
        range(len(apparaten)),
        format_func=lambda i: labels[i],
        index=min(st.session_state["device_idx"], len(apparaten) - 1),
    )
    st.session_state["device_idx"] = idx
    gekozen = apparaten[idx]
    ios = ios_hoofdversie(gekozen.get("ProductVersion"))
    udid = gekozen.get("Identifier") or gekozen.get("UniqueDeviceID")
    # Bij meerdere apparaten richten we het commando expliciet op de gekozen iPhone
    if len(apparaten) <= 1:
        udid = None

    if ios >= 17:
        if tunneld_actief():
            st.success(f"✅ iOS {gekozen.get('ProductVersion')} · tunnel draait — klaar voor gebruik.")
        else:
            st.warning(
                f"iOS {gekozen.get('ProductVersion')} heeft een tunnel nodig. "
                "Start in een aparte terminal: `sudo pymobiledevice3 remote tunneld`"
            )
    else:
        st.success(f"✅ iOS {gekozen.get('ProductVersion')} gevonden — klaar voor gebruik.")

st.divider()

# --- Stap 2: locatie kiezen ------------------------------------------------- #
st.subheader("2 · Kies je locatie")

if HEEFT_GEOCODER:
    zoek = st.text_input("Zoek op adres of plaats", placeholder="bv. Eiffeltoren, Parijs")
    if st.button("Zoek adres", disabled=not zoek):
        try:
            geo = Nominatim(user_agent="iphone-locatie-spoof").geocode(zoek, timeout=10)
            if geo:
                st.session_state["lat"] = round(geo.latitude, 6)
                st.session_state["lon"] = round(geo.longitude, 6)
                st.success(f"Gevonden: {geo.address}")
            else:
                st.warning("Niets gevonden voor die zoekterm.")
        except Exception as e:  # noqa: BLE001
            st.error(f"Zoeken mislukt: {e}")

c1, c2 = st.columns(2)
st.session_state["lat"] = c1.number_input(
    "Breedtegraad (latitude)", value=float(st.session_state["lat"]), format="%.6f"
)
st.session_state["lon"] = c2.number_input(
    "Lengtegraad (longitude)", value=float(st.session_state["lon"]), format="%.6f"
)

if HEEFT_KAART:
    st.caption("Of tik op de kaart om een plek te kiezen:")
    m = folium.Map(
        location=[st.session_state["lat"], st.session_state["lon"]], zoom_start=12
    )
    folium.Marker(
        [st.session_state["lat"], st.session_state["lon"]], tooltip="Virtuele locatie"
    ).add_to(m)
    uit = st_folium(m, height=360, width=None, key="kaart")
    if uit and uit.get("last_clicked"):
        nieuw_lat = round(uit["last_clicked"]["lat"], 6)
        nieuw_lon = round(uit["last_clicked"]["lng"], 6)
        if (nieuw_lat, nieuw_lon) != (st.session_state["lat"], st.session_state["lon"]):
            st.session_state["lat"] = nieuw_lat
            st.session_state["lon"] = nieuw_lon
            st.rerun()
else:
    st.info("Tip: `pip install streamlit-folium folium` voegt een klikbare kaart toe.")

st.divider()

# --- Stap 3: activeren ------------------------------------------------------ #
st.subheader("3 · Activeer")

actief = st.session_state.get("dvt_proc") and st.session_state["dvt_proc"].poll() is None
if actief:
    st.info("🟢 Er draait nu een actieve locatiesimulatie (iOS 17+).")

b1, b2 = st.columns(2)
if b1.button(
    "📍 Stel deze locatie in",
    type="primary",
    use_container_width=True,
    disabled=not apparaten,
):
    ok, bericht = stel_locatie_in(
        st.session_state["lat"], st.session_state["lon"], ios, udid
    )
    st.session_state["melding"] = ("success" if ok else "error", bericht)
    st.rerun()

if b2.button("↩️ Herstel echte locatie", use_container_width=True, disabled=not apparaten):
    ok, bericht = wis_locatie(ios, udid)
    st.session_state["melding"] = ("success" if ok else "error", bericht)
    st.rerun()

melding = st.session_state.get("melding")
if melding:
    soort, tekst = melding
    (st.success if soort == "success" else st.error)(tekst)

st.caption(
    "Gebruik dit alleen op je eigen toestel en houd je aan de voorwaarden van de "
    "apps die je gebruikt."
)
