# Weitere Sensoren einreichen

Alle fünf Ergänzungen sind implementiert und lokal getestet. Zusätzlich zum
bereits eingereichten Betriebsdauersensor sind folgende Beiträge vorbereitet:

| Sensor | Umsetzung | Voraussetzung für den HA-PR |
| --- | --- | --- |
| Verbleibende Ausschaltzeit | Vorhandene Bibliotheks-Property als Dauer in Sekunden, Anzeige in Minuten | Sofort mit bestehender Bibliotheksversion möglich |
| Verbleibende Fütterungspause | Vorhandene Bibliotheks-Property als Dauer in Sekunden, Anzeige in Minuten | Sofort mit bestehender Bibliotheksversion möglich |
| Fehlerstatus | Neue Bibliotheks-Property und HA-Enumsensor | Veröffentlichung der erweiterten Bibliothek |
| Geschätzter Durchfluss | Neue Bibliotheks-Property und HA-Sensor für Volumendurchfluss | Veröffentlichung der erweiterten Bibliothek |
| Geschätzte Leistungsaufnahme | Neue Bibliotheks-Property und HA-Leistungssensor | Veröffentlichung der erweiterten Bibliothek |

Durchfluss und Leistung sind berechnete Werte. Die Grundlagen stehen in der
[Protokollanalyse](../docs/protocol.md). Der Leistungsalgorithmus wurde anhand
der JavaScript-Funktion aus der Weboberfläche des Filters nachgebildet.
Der Fehlerstatus umfasst Rotorfehler, Luft und Temperaturfehler. Unbekannte
Fehlerbits bekommen einen eigenen Zustand; Kalibrierungsbits erzeugen keinen
Fehleralarm.

## Änderungen prüfen

Die Pakete sind nach den zuständigen Repositories aufgeteilt:

1. Bibliothek `eheimdigital`, eingereicht als
   [Codeberg-PR #10](https://codeberg.org/autinerd/eheimdigital/pulls/10):
   [Diff](eheimdigital-library-status.patch) und
   [PR-Beschreibung](eheimdigital-library-status-pr.md).
   Ausgangspunkt ist Commit `55f3cd026f2349e8a5188a8788c2722e626d4998`.
2. Die beiden Pausensensoren in Home Assistant:
   [Diff](eheimdigital-pause-sensors.patch) und
   [PR-Beschreibung](eheimdigital-pause-sensors-pr.md).
3. Fehlerstatus, Durchfluss und Leistung in Home Assistant:
   [Diff zusätzlich zu den Pausensensoren](eheimdigital-derived-sensors.patch)
   und [PR-Beschreibung](eheimdigital-derived-sensors-pr.md).

Für die gemeinsame Durchsicht gibt es außerdem den
[gesamten HA-Diff für alle fünf Sensoren](eheimdigital-all-additional-sensors.patch).
Die Patches enthalten synthetische Testdaten, keine WLAN-Zugangsdaten und
keine Geräteadresse des Nutzers.

Die HA-Ergänzung für die drei neuen Bibliothekswerte ist ein getesteter Entwurf.
Diese Properties sind in der veröffentlichten Bibliothek 1.7.1 noch nicht
vorhanden. Der lokale Test verwendet einen selbst gebauten Wheel aus dem
geänderten Quellcode. Die Version im HA-Manifest wurde nicht auf eine erfundene
Releaseversion gesetzt. Nach einer Veröffentlichung muss Home Assistant die
neue Bibliothek zunächst in einem eigenen Abhängigkeits-PR übernehmen.
Danach kann der Feature-PR für diese drei Sensoren folgen.

## Validierung

| Prüfung | Ergebnis |
| --- | --- |
| Bibliothek | 39 Tests erfolgreich |
| Bibliothekstypen | Strenge Mypy-Prüfung beider geänderter Quellmodule erfolgreich |
| Leistungsformel | 1.629 Werte gegen die separat ausgeführte Herstellerimplementierung geprüft |
| Ausschalt- und Fütterungspause mit unveränderter Bibliothek | 83 HA-Tests und 107 Snapshots erfolgreich |
| Alle fünf Sensoren mit lokal gebauter Bibliothek | 94 HA-Tests und 113 Snapshots erfolgreich |
| HA-Prüfungen | Ruff, Formatierung, Codespell, Prettier, Mypy, Pylint und hassfest erfolgreich |

Ruff für die Bibliothek läuft mit der bestehenden Konfiguration und
`--extend-ignore PLR0911`. Die ausgeblendete Meldung über sieben Rückgaben in
`types.py` wurde auch im unveränderten Ausgangsstand nachgewiesen.
Die vorhandenen Pytest-Warnungen sind in den Testergebnissen enthalten.

Die Gegenproben veränderten absichtlich Fehlerbitmaske, Durchflussumrechnung,
Leistungskoeffizient, Behandlung einer ungültigen Leistungskurve und das
Kopieren eingehender Pakete. Die zugehörigen Tests wurden jeweils rot.
Dasselbe gilt in HA für eine falsche Zeiteinheit und entfernte Sensorzuordnungen.
Danach wurden die Änderungen wiederhergestellt und die Tests erfolgreich ausgeführt.

Eine [Abfrage am echten Filter](additional-sensors-observation.json) bestätigt
das Lesen aller neuen Properties im normalen Betrieb. Fehlerzustände und
Pausen wurden mit synthetischen Paketen geprüft. Der Filter wurde dafür nicht
umgeschaltet oder angehalten.

## Lokale Arbeitsstände

- `/tmp/ha-eheim-eheimdigital-library`, Branch
  `feat/professionel5e-status-sensors`: Bibliotheksänderungen und Tests.
- `/tmp/ha-eheim-home-assistant-core`, Branch
  `feat/eheimdigital-pause-sensors`: eigenständiger Beitrag für die beiden Restzeiten.
- Im selben HA-Checkout, Branch `feat/eheimdigital-derived-sensors`: zusätzlicher
  Entwurf für Fehlerstatus, Durchfluss und Leistung. Die Testumgebung verwendet
  den lokalen Bibliotheks-Wheel unter `/tmp/ha-eheim-local-wheels`.

## Stand der Einreichungen

Der Bibliotheksbeitrag ist über den Codeberg-Account `hilman2` als
[PR #10](https://codeberg.org/autinerd/eheimdigital/pulls/10) eingereicht.
Sein Head ist `aa9be592a72deb2a770ba22b6bb9c6f13acaf997`, der Fork liegt unter
`hilman2/eheimdigital`. Die beiden HA-Pausensensoren können unabhängig davon
über GitHub eingereicht werden.

Die neuen HA-Diffs und PR-Beschreibungen benötigen die persönliche Prüfung
durch den Nutzer. Das verlangt Home Assistants
[AI_POLICY.md](https://github.com/home-assistant/core/blob/dev/AI_POLICY.md).
Die entsprechenden Bestätigungen in diesen neuen PR-Vorlagen sind noch offen.
Die frühere Freigabe bezog sich auf den bereits veröffentlichten
[Betriebsdauer-PR](https://github.com/home-assistant/core/pull/189828).
