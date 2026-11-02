# Lokale EHEIM-Schnittstelle und HA-Anbindung

Für die Einrichtung genügt die [Anleitung im README](../README.md).
Hier stehen die Ergebnisse der Geräteuntersuchung vom 1. November 2026
und die Ansatzpunkte für Erweiterungen.

## Bestätigtes Gerät

| Eigenschaft | Am Gerät beobachtet |
| --- | --- |
| Modell | EHEIM professionel 5e 350, Typ 2274 |
| Firmware und Weboberfläche | jeweils 1.03.2 |
| Gerätefamilie | `USRDTA.version = 4` |
| Filtermodell | `FILTER_DATA.version = 74` |
| HTTP | `http://<host>/`, Status 200 |
| WebSocket | `ws://<host>/ws`, Port 80 |
| Modus während der Untersuchung | manuell, `pumpMode = 16` |
| Pumpe | aktiv, `filterActive = 1` |
| Pumpenfrequenz | `freq = 3500`, entspricht 35 Hz |

Die Verbindung gelang ohne Anmeldung. Die Herstelleroberfläche fordert das
WebSocket-Unterprotokoll `eheim` an. Die geprüfte Python-Bibliothek verbindet
sich ohne diese Angabe; auch das akzeptierte dieses Gerät.

## Durchgeführte Prüfung

1. Die Startseite und ihr JavaScript-Bündel `lib/allJSFiles.js` lokal abgerufen.
   Das Bündel kommt gzip-komprimiert und enthält die Protokollimplementierung
   der Herstelleroberfläche.
2. Eine WebSocket-Verbindung geöffnet und nur eingehende Pakete ausgewertet.
3. Die in HA 2026.10.4 verwendete Bibliothek `eheimdigital==1.7.1` geladen.
   Sie erkannte das Gerät als `EheimDigitalFilter` und las vollständige Statusdaten.
4. Über dieselbe Bibliothek zweimal `GET_USRDTA` und `GET_FILTER_DATA`
   angefordert und erneut vollständige Filterdaten empfangen.

Ausgehende Pakete waren auf diese beiden Leseanfragen begrenzt. Pumpensteuerung,
Moduswechsel und andere Schreibbefehle wurden nicht am Gerät getestet.
Eine Installation in deiner Home-Assistant-Instanz war nicht Teil der Prüfung.
Das wiederholbare [Diagnosewerkzeug](../scripts/probe_filter.py) verwendet
die eingebettete Variante dieser Bibliothek und gibt nur ausgewählte Statusfelder aus.

## Protokoll

Beim Verbindungsaufbau schickte der Filter automatisch `USRDTA`, `CLOCK`,
`NET_ST`, `NET_AP`, `MESH_NETWORK` und `FILTER_DATA`.
Ein Frame kann ein einzelnes JSON-Objekt oder eine Liste von Objekten enthalten;
die Python-Bibliothek verarbeitet beide Formen.

Eine weitere Statusabfrage hat diese Form. `<Geräte-MAC>` steht für das
Feld `from` aus dem empfangenen `USRDTA`-Paket:

```json
{"title": "GET_FILTER_DATA", "to": "<Geräte-MAC>", "from": "USER"}
```

Die Geräteübersicht lässt sich mit folgendem Paket abfragen:

```json
{"title": "GET_USRDTA", "to": "ALL", "from": "USER"}
```

`MESH_NETWORK` nennt weitere EHEIM-Geräte hinter dem Hauptgerät.
Während dieser Prüfung wurde genau ein Gerät erkannt.

Die initialen Netzwerkpakete enthalten unter anderem die Feldnamen `stPW`
und `apPW`. Ihre Werte wurden nicht ausgegeben oder im Projekt gespeichert.
Für Diagnoseberichte nur ausgewählte Statusfelder verwenden; vollständige
Verbindungsprotokolle können Zugangsdaten enthalten.

### Relevante Felder in `FILTER_DATA`

| Feld | Bedeutung oder Auswertung |
| --- | --- |
| `filterActive` | Pumpenzustand, 0 oder 1 |
| `freq` | aktuelle Pumpenfrequenz, durch 100 teilen für Hz |
| `freqSoll` | Sollfrequenz des manuellen Modus, durch 100 teilen für Hz |
| `sollStep` | Index in der modellspezifischen Tabelle für konstanten Durchfluss |
| `dfsFaktor` | Faktor für die Durchflussberechnung der Weboberfläche, auch bei laufender Pumpe zeitweise 0 |
| `dfs` | Rohwert; nicht unverändert als Liter pro Stunde verwenden |
| `serviceHour` | verbleibende Stunden bis zur Wartung |
| `runTime` | Betriebsdauer in Minuten laut Python-Bibliothek |
| `turnOffTime` | verbleibende Ausschaltzeit in Sekunden |
| `turnTimeFeeding` | verbleibende Fütterungspause in Sekunden |
| `pumpMode & 0xFF` | Betriebsmodus |
| `pumpMode & 0x0F00` | Fehlerbits der Herstelleroberfläche |
| `pumpMode & 0xF000` | Kalibrierungsbits der Herstelleroberfläche |

Die beobachteten 4.320 Wartungsstunden sind der Gerätestand zum Messzeitpunkt.
Eine Aussage über den tatsächlichen Verschmutzungszustand folgt daraus nicht.

### Durchfluss und Leistung

Die Weboberfläche berechnet zunächst folgenden Basiswert in l/h:

```text
floor(freq * dfsFaktor * 60 / 1_000_000)
```

Die Felder `freq` und `dfsFaktor` kamen am selben Filter in zwei Messungen so an,
beide im manuellen Modus bei laufender Pumpe:

| Messung | `freq` | `dfsFaktor` | `dfs` | Basiswert |
| --- | --- | --- | --- | --- |
| 1. November 2026 | 3500 | 683 | 239 | 143 l/h |
| 2. November 2026 | 3500 | 0 | 0 | 0 l/h |

Der Rohwert `dfs` ist daher kein unmittelbar übernehmbarer l/h-Sensor.
Wann der Filter `dfsFaktor` liefert, ist nicht geklärt. Auch das aus Core
übernommene Testpaket hat im manuellen Modus `dfsFaktor = 0`.
Das Diagnosewerkzeug nennt den berechneten Wert `estimated_flow_lph`.
Eine unabhängige Messung des tatsächlichen Wasserdurchflusses liegt nicht vor.

Was die Filterseite der Oberfläche (`com/fltr/t/filterOverview.html`) als Zahl
anzeigt, hängt vom Modus ab:

| Modus | `pumpMode & 0xFF` | Anzeige |
| --- | --- | --- |
| Konstanter Durchfluss | 1 | Durchfluss-Tabellenwert zu `sollStep`, ab `freq >= maxFreq` der Basiswert |
| Bio | 4 | wie konstanter Durchfluss |
| Puls | 8 | keine Zahl |
| Manuell | 16 | kein Durchfluss, Drehzahl in Prozent der höchsten Tabellenfrequenz |

Die Integration bildet diese Anzeige nicht nach. Sie gibt den Basiswert aus.
Ergibt er bei laufender Pumpe 0, liefert sie den Nennwert der aktuellen Frequenz.
Dafür paart sie die beiden Tabellen `getFrqTable` und `getDSTTableMetric` Stufe
für Stufe und interpoliert zwischen den Stufen. Diese Paarung ist eine Annahme
der Integration: Die Oberfläche rechnet Frequenz und Durchfluss nicht ineinander
um. Der Nennwert berücksichtigt keine Verschmutzung. Beim 350er ergibt er für
35 Hz 400 l/h, also deutlich mehr als die 143 l/h aus der ersten Messung.

Auch die Leistungsanzeige der Oberfläche stammt aus einer Berechnung anhand
von Frequenz und `dfsFaktor`. Sie belegt keine Leistungsmessung in Watt.

## Vorhandene Home-Assistant-Integration

Die offizielle Integration heißt `eheimdigital`. Das
[Manifest von HA 2026.10.4](https://github.com/home-assistant/core/blob/2026.10.4/homeassistant/components/eheimdigital/manifest.json)
bindet `eheimdigital==1.7.1` ein. Die Bibliothek ist auf
[PyPI](https://pypi.org/project/eheimdigital/1.7.1/) verfügbar; ihre Quellen liegen auf
[Codeberg](https://codeberg.org/autinerd/eheimdigital).

Der [Coordinator](https://github.com/home-assistant/core/blob/2026.10.4/homeassistant/components/eheimdigital/coordinator.py)
verwaltet eine gemeinsame WebSocket-Verbindung und fordert Aktualisierungen an.
Das ist lokales Polling über WebSocket. Die
[HA-Dokumentation](https://www.home-assistant.io/integrations/eheimdigital/)
nennt standardmäßig 15 Sekunden zwischen den Abfragen.

Für den professionel 5e ist im geprüften Quellstand Folgendes implementiert:

| HA-Plattform | Funktionen | Versionsgebundene Quelle |
| --- | --- | --- |
| `sensor` | Pumpenfrequenz, verbleibende Wartungsstunden | [sensor.py](https://github.com/home-assistant/core/blob/2026.10.4/homeassistant/components/eheimdigital/sensor.py) |
| `switch` | Pumpe ein/aus | [switch.py](https://github.com/home-assistant/core/blob/2026.10.4/homeassistant/components/eheimdigital/switch.py) |
| `select` | manuell, konstanter Durchfluss, Puls, Bio; Sollwerte für diese Modi | [select.py](https://github.com/home-assistant/core/blob/2026.10.4/homeassistant/components/eheimdigital/select.py) |
| `number` | Dauer hoher/niedriger Pulse, System-LED-Helligkeit | [number.py](https://github.com/home-assistant/core/blob/2026.10.4/homeassistant/components/eheimdigital/number.py) |
| `time` | Tages- und Nachtbeginn im Bio-Modus | [time.py](https://github.com/home-assistant/core/blob/2026.10.4/homeassistant/components/eheimdigital/time.py) |

Die Bibliothek liefert auch Betriebsdauer und Pausenrestzeiten. Im geprüften
`sensor.py` fehlen dafür jedoch Entitäten. Die laufende HA-Dokumentationsseite
listet diese bereits auf. Bei der Entscheidung über Erweiterungen deshalb
die tatsächlich installierte HA-Version mit ihrem Quellstand abgleichen.
Der Fehlersensor für classicVARIO in derselben Datei gilt nicht für den 5e.

## Konkreter Entwicklungsweg

Die vorhandene Integration zuerst mit dem Filter einrichten. Für die bisher
geprüften Grundfunktionen ist ein eigener Protokollclient nicht erforderlich.
Für fehlende Funktionen bieten sich folgende Erweiterungen an:

1. **Betriebsdauer und Pausenrestzeiten.** Die vorhandenen Properties
   `operating_time`, `turn_off_time` und `turn_feeding_time` als Sensoren in
   der HA-Integration ergänzen, falls sie in der installierten Version noch fehlen.
2. **Fehlerstatus des 5e.** Die Fehlerbits in der Bibliothek auswerten und in HA
   einen Sensor ergänzen. Die Geräteoberfläche unterscheidet Rotorfehler
   `0x0200`, Luft `0x0300` und Temperaturfehler `0x0500`.
   Hier beobachtet wurde nur der fehlerfreie Zustand 0.
3. **Geschätzter Durchfluss.** Die Umrechnung in der Bibliothek ergänzen und als
   HA-Sensor für Volumendurchfluss ausgeben. Einheiten und Verhalten in den
   verschiedenen Modi anhand der Herstelleroberfläche prüfen.

Zusätzliche Properties gehören in `eheimdigital`, die Zuordnung zu Entitäten
in die HA-Integration. Deren vorhandenen Coordinator weiterverwenden.
Die [HA-Anleitung zum Datenabruf](https://contributors.home-assistant.io/core/integrations/fetching-data/)
beschreibt die gemeinsame Aktualisierung mehrerer Entitäten.

Die Custom Integration enthält diese Erweiterungen und die Gerätebibliothek.
Ab Version 0.2.0 verwendet sie die eigene Domain `eheimdigital_plus`. Die
bestätigte Migration erhält bestehende Geräte und Entitäts-IDs. Die
[Wechselanleitung](migration.md) beschreibt den Ablauf.

Die [Entwicklungsanleitung](development.md) beschreibt die automatisierten
Prüfungen. Schreibfunktionen und weitere Filtermodelle wurden nicht an echter
Hardware getestet. Ein Test gegen eine laufende Home-Assistant-Instanz
steht ebenfalls noch aus.
