# Roldeck via je telefoon bedienen

Je Roldeck-zwembadafdekking (Starline) werkt met een radiografische handzender.
Een telefoon kan dat radiosignaal niet zelf uitzenden, dus er is een klein
stukje hardware nodig als brug. Dit project bevat alles wat je daarvoor nodig
hebt: firmware voor een ESP32-microcontroller plus een mobielvriendelijke
web-app die de ESP32 zelf serveert op je eigen wifi.

## ⚠️ Eerst: veiligheid

Een zwembadafdekking is een veiligheidsvoorziening. Iemand (of een huisdier)
die onder een sluitend roldeck terechtkomt, kan verdrinken.

- **Bedien het roldeck alleen als je het zwembad kunt zien.**
- De app is daarom als *dodemansknop* gebouwd: het roldeck beweegt alleen
  zolang je de knop op je telefoon ingedrukt houdt. Laat je los, of valt de
  wifi-verbinding weg, dan stopt het binnen een seconde.
- Geef de pincode niet aan kinderen.

## Twee routes

| | Officieel (Starline) | Doe-het-zelf (dit project) |
|---|---|---|
| Wat | [Starline Poolmanager](https://www.starlinepool.com/nl/smart-poolcontrol) met Smartpool-app, via je zwembaddealer | ESP32 + relaisbordje op een (reserve)handzender |
| Kosten | Enkele honderden euro's + installatie | ± €20–25 aan onderdelen |
| Kan ook | Waterkwaliteit, pompen, verwarming | Roldeck + de drie lichtknoppen van de zender |
| Buiten huis bereikbaar | Ja | Nee (bewust: alleen op je eigen wifi) |

Wil je geen soldeerwerk, vraag dan je dealer (Bos Zwembaden, zie de sticker in
je techniekruimte) naar de Poolmanager. De rest van deze handleiding gaat over
de doe-het-zelf-route.

## Hoe het werkt

```
Telefoon ──wifi──▶ ESP32 ──draadjes──▶ relaisbordje ──contacten──▶ knoppen van
(web-app)          (webserver)                                     de handzender
                                                                        │
                                                                   radiosignaal
                                                                        ▼
                                                              Roldeck-besturingskast
```

Het relais "drukt" elektrisch op de knop van de zender — precies hetzelfde als
een vingerdruk. De Roldeck-besturing zelf blijft dus volledig origineel en
al z'n eigen beveiligingen blijven werken.

## Boodschappenlijst

| Onderdeel | Richtprijs |
|---|---|
| ESP32 DevKit v1 (30-pins) | € 8 |
| Relaisbordje 4 kanalen, 5 V (of 2 optocouplers PC817 als je het subtiel wil) | € 6 |
| **Reserve-handzender Roldeck** (bestel bij je dealer — dan blijft je huidige zender gewoon in gebruik!) | € 40–60 |
| USB-voeding + micro-USB-kabel | € 5 |
| Dupont-draadjes, dun montagedraad, evt. printplaathoudertje/doosje | € 5 |

## Stap 1 — Handzender openen en draadjes solderen

1. Draai de **twee schroefjes** aan de achterkant los (zie je eigen foto).
2. Op de printplaat zit onder elke knop een drukschakelaartje met vier pootjes;
   twee daarvan zijn elektrisch het knop-contact. Meet met een multimeter
   (piepstand) welke twee pootjes contact maken als je de knop indrukt.
3. Soldeer aan die twee pootjes een dun draadje (per knop dus 2 draadjes):
   - Grote knop → relais kanaal 1 (COM + NO)
   - Lichtknop 1/2/3 → relais kanaal 2/3/4 (COM + NO)
   Je hoeft niet alle vier de knoppen aan te sluiten; alleen de grote knop is
   al genoeg om het roldeck te bedienen.
4. Laat de batterij gewoon in de zender zitten. De relaiscontacten zijn
   potentiaalvrij, dus de zender merkt geen verschil met een vingerdruk.
5. Boor/vijl een klein gaatje in de behuizing voor de draadjes en schroef de
   zender weer dicht. Leg de zender bij de ESP32 — binnen zendbereik van de
   besturingskast (de plek van het wandpaneel is een goed richtpunt).

## Stap 2 — ESP32 aansluiten

| ESP32-pin | Relaisbordje |
|---|---|
| VIN (5 V) | VCC |
| GND | GND |
| GPIO 26 | IN1 (grote knop) |
| GPIO 27 | IN2 (licht 1) |
| GPIO 32 | IN3 (licht 2) |
| GPIO 33 | IN4 (licht 3) |

## Stap 3 — Firmware flashen

1. Installeer de [Arduino IDE](https://www.arduino.cc/en/software).
2. Voeg het ESP32-boardpakket toe: *File → Preferences → Additional boards manager
   URLs*: `https://espressif.github.io/arduino-esp32/package_esp32_index.json`,
   daarna *Tools → Board → Boards Manager* → zoek "esp32" → installeer.
3. Open `roldeck_bridge/roldeck_bridge.ino` en vul bovenin in:
   je **wifi-naam**, **wifi-wachtwoord** en een zelfgekozen **pincode**.
4. Kies *Tools → Board → ESP32 Dev Module*, sluit de ESP32 aan via USB,
   kies de juiste poort en klik **Upload**.
5. Open de *Serial Monitor* (115200 baud): daar zie je het IP-adres zodra de
   ESP32 verbonden is.

## Stap 4 — Gebruiken op je telefoon

1. Verbind je telefoon met je eigen wifi.
2. Ga in Safari/Chrome naar **http://roldeck.local** (werkt de naam niet,
   gebruik dan het IP-adres uit de Serial Monitor).
3. Log in met je pincode.
4. Tip (iPhone): *Deel → Zet op beginscherm* — dan staat er een echte
   Roldeck-app-knop tussen je apps.

Bediening: **houd de grote knop ingedrukt** om het roldeck te bewegen
(loslaten = stoppen), tik op de lichtknoppen voor de zwembadverlichting.

## Problemen oplossen

- **`roldeck.local` werkt niet** → gebruik het IP-adres; sommige Android-
  telefoons ondersteunen geen mDNS. Geef de ESP32 eventueel een vast IP in
  je router.
- **Relais klikt, maar roldeck reageert niet** → controleer of de zender het
  nog doet met de hand (batterij?), en of je op de juiste twee pootjes van het
  drukschakelaartje zit.
- **Relais schakelt omgekeerd** (aan bij opstarten) → zet in de firmware
  `RELAY_ACTIVE_LOW` op `false`.
- **Het roldeck stopt steeds na een seconde** → je wifi-signaal bij de ESP32 is
  te zwak; de dodemansbewaking laat dan bewust los. Verplaats de ESP32 of
  verbeter de wifi-dekking.

## Waarom niet gewoon het radiosignaal namaken?

Zenders als deze gebruiken vaak een *rolling code*: elke druk zendt een andere,
eenmalige code. Opnemen en opnieuw afspelen (met bijv. een 433 MHz-zendertje)
werkt dan niet of maar één keer. Fysiek de knop "indrukken" via een relais
werkt altijd, ongeacht de codering — daarom deze aanpak.
