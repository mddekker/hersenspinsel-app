# 📍 iPhone Locatie Spoof

Bepaal handmatig waar je iPhone "denkt" dat hij is. De gekozen locatie geldt
**systeembreed**: álle apps (Kaarten, Weer, WhatsApp live-locatie, Find My, enz.)
zien die locatie, totdat je 'm wist of de telefoon herstart. **Geen jailbreak nodig.**

> ⚠️ Dit draait op **je eigen computer** (Mac, Windows of Linux), met je iPhone
> via een **USB-kabel** aangesloten. Het werkt *niet* als losse app op de iPhone
> zelf — iOS staat dat niet toe — en dus ook niet vanuit de cloud.

Onder water gebruikt het tool het open-source project
[`pymobiledevice3`](https://github.com/doronz88/pymobiledevice3), dat Apple's
eigen **Developer-locatiesimulatie** aanstuurt.

---

## Installeren

Je hebt **Python 3.9+** nodig.

```bash
pip install -r requirements-locatie.txt
```

Per besturingssysteem nog dit:

- **macOS** — werkt meteen (Apple Mobile Device-ondersteuning zit erin).
- **Windows** — installeer **iTunes** (voor de Apple-USB-driver).
- **Linux** — installeer `usbmuxd` (`sudo apt install usbmuxd`).

## Eenmalig klaarzetten op de iPhone

1. **Sluit de iPhone met USB aan** en tik op **Vertrouwen** in de pop-up.
2. Zet **Developer Mode** aan: *Instellingen → Privacy en beveiliging →
   Ontwikkelaarsmodus* (vanaf iOS 16; de telefoon herstart hierna).
3. **Alleen iOS 17 en nieuwer**: open een **aparte terminal** en start de tunnel —
   laat die terminal open staan:
   - **macOS / Linux:** `sudo pymobiledevice3 remote tunneld`
   - **Windows:** open PowerShell **als administrator** (rechtermuisklik →
     *Als administrator uitvoeren*) en draai zónder sudo:
     `pymobiledevice3 remote tunneld`

   (Op iOS 16 en lager is deze stap *niet* nodig.)

## Starten

```bash
streamlit run iphone_locatie_spoof.py
```

Er opent een venster in je browser. Daarin:

1. **Verbind je iPhone** → klik *Zoek aangesloten iPhones*.
2. **Kies je locatie** → zoek een adres, tik op de kaart, of typ coördinaten.
3. **Activeer** → *Stel deze locatie in*. Met *Herstel echte locatie* zet je
   alles weer terug.

## Goed om te weten

- **iOS 17+**: de simulatie blijft alleen actief zolang het tool draait. Sluit je
  het venster of de tunnel-terminal, dan valt je iPhone terug op de echte GPS.
- **iOS 16 en lager**: de neplocatie blijft staan tot je hem wist of de iPhone
  herstart.
- Werkt alleen via USB; over wifi lukt de locatiesimulatie niet.

## Gebruik

Bedoeld voor je **eigen toestel** en je eigen privacy. Houd je aan de
gebruiksvoorwaarden van de apps die je gebruikt en aan de lokale wetgeving.
