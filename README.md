<img src="assets/icon.svg" width="64" height="64" alt="">

# EHEIM Digital für Home Assistant

Custom Integration auf Basis der offiziellen EHEIM-Digital-Integration aus
Home Assistant Core 2026.10.4. Die Gerätebibliothek ist vollständig enthalten.
Ein gesondertes Python-Paket oder ein Bibliotheks-Release wird nicht benötigt.

Zusätzlich zu den Core-Funktionen bietet sie für den professionel 5e:

| Sensor | Anzeige |
| --- | --- |
| Betriebsdauer | Stunden |
| Verbleibende Ausschaltzeit | Minuten |
| Verbleibende Fütterungspause | Minuten |
| Fehlerstatus | Kein Fehler, Rotor blockiert, Luft, Temperaturfehler oder unbekannter Fehler |
| Geschätzter Durchfluss | l/h |
| Geschätzte Leistungsaufnahme | W |

Durchfluss und Leistungsaufnahme sind Schätzungen nach der Geräte-Weboberfläche.
Die Leistungsaufnahme eignet sich zur Beobachtung des Betriebs und ersetzt
keinen Stromzähler. Details stehen in der [Protokollanalyse](docs/protocol.md).
Die zusätzlichen Sensoren wurden an einem professionel 5e 350 mit Firmware
1.03.2 ausgelesen. Der bisherige Funktionsumfang für andere Gerätetypen stammt
aus Core; diese Geräte wurden hier nicht physisch getestet.

## Voraussetzungen

- Home Assistant 2026.10.4 oder neuer. Die Tests verwenden 2026.10.4.
- Home Assistant erreicht das EHEIM-Hauptgerät im lokalen Netzwerk.
- HACS, der integrierte Marketplace oder eine manuelle Installation.

Diese Version verwendet dieselbe Domain `eheimdigital` wie die Core-Integration
und ersetzt deren Implementierung, solange sie installiert ist. Die Geräte,
Entitäten und bestehenden Unique IDs bleiben erhalten. Weitere Core-Änderungen
kommen erst durch ein Update dieser Custom Integration hinzu.

## Über HACS installieren

[In HACS öffnen](https://my.home-assistant.io/redirect/hacs_repository/?owner=hilman2&repository=ha-eheim&category=integration)

1. Öffne HACS und wähle im Menü **Benutzerdefinierte Repositories**.
2. Füge `https://github.com/hilman2/ha-eheim` mit Typ **Integration** hinzu.
3. Lade **EHEIM Digital** herunter und starte Home Assistant neu.
4. Eine bestehende EHEIM-Einrichtung wird weiterverwendet. Lege sie nicht erneut an.
5. Bei einer neuen Einrichtung wähle unter **Einstellungen > Geräte & Dienste >
   Integration hinzufügen** den Eintrag **EHEIM Digital** und trage die IP-Adresse
   des Hauptgeräts ein.

Ab Home Assistant 2026.11 übernimmt der integrierte Marketplace die Rolle von
HACS. Dort wird das Repository per Link hinzugefügt. Weil diese Integration
eine Core-Integration ersetzt, muss die Ersetzung bestätigt werden.
Siehe [HA-Anleitung für Custom Integrations](https://contributors.home-assistant.io/marketplace/guides/integrations/).

## Manuell installieren

1. Lade das ZIP aus den [Releases](https://github.com/hilman2/ha-eheim/releases)
   herunter und entpacke es in dein HA-Konfigurationsverzeichnis. Danach
   muss `custom_components/eheimdigital/manifest.json` dort vorhanden sein.
   Alternativ kopierst du den gesamten Ordner `custom_components/eheimdigital`
   aus diesem Repository dorthin, einschließlich `_vendor`.
2. Starte Home Assistant neu.
3. Verwende die bestehende Einrichtung oder füge **EHEIM Digital** hinzu.

Die Oberfläche verwendet Deutsch oder Englisch entsprechend der HA-Sprache.
Die neuen Diagnosesensoren findest du auf der Geräteseite.

## Zur Core-Integration zurückkehren

Entferne die heruntergeladene Integration in HACS beziehungsweise im Marketplace,
oder entferne bei manueller Installation den Ordner `custom_components/eheimdigital`.
Starte Home Assistant danach neu. Lösche die EHEIM-Einrichtung unter
**Geräte & Dienste** dafür nicht. Die Core-Integration übernimmt sie wieder.
Die zusätzlichen Sensoren stehen dort erst zur Verfügung, wenn Core sie unterstützt.

## Entwicklung und Herkunft

Die [Entwicklungsanleitung](docs/development.md) enthält Testbefehle,
die Abfrage eines echten Filters und den Bau des Installations-ZIPs.
Die bisherigen [Core-Beiträge](contributions/README.md) und die
[Protokollanalyse](docs/protocol.md) bleiben als Hintergrund erhalten.

Der HA-Code steht unter Apache-2.0, die eingebettete Bibliothek unter MIT.
Quellen, Änderungen und Lizenztexte stehen in der
[NOTICE](custom_components/eheimdigital/NOTICE).
