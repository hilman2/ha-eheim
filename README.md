<img src="custom_components/eheimdigital_plus/brand/icon.png" width="64" height="64" alt="">

# EHEIM Digital Plus

Lokale Home-Assistant-Integration für EHEIM-Digital-Geräte. Sie basiert auf Core
2026.10.4 und enthält die Gerätebibliothek vollständig. Ein externes
`eheimdigital`-Paket wird nicht benötigt.

[In HACS öffnen](https://my.home-assistant.io/redirect/hacs_repository/?owner=hilman2&repository=ha-eheim&category=integration)
· [Releases](https://github.com/hilman2/ha-eheim/releases)
· [Prüfungen](https://github.com/hilman2/ha-eheim/actions/workflows/validate.yml)

Zusätzlich zu den übernommenen Core-Funktionen stehen für den professionel 5e
Betriebsdauer, Ausschaltzeit, Fütterungspause, Fehlerstatus, geschätzter
Durchfluss und geschätzte Leistungsaufnahme zur Verfügung. Durchfluss und
Leistung sind berechnete Werte der Geräte-Weboberfläche.

## Installieren

Du brauchst Home Assistant ab 2026.10.4 und eine lokale Verbindung zum
EHEIM-Hauptgerät. Die automatisierten Tests verwenden HA 2026.10.4.

1. Öffne HACS und füge `https://github.com/hilman2/ha-eheim` unter
   **Benutzerdefinierte Repositories** mit Typ **Integration** hinzu.
2. Lade **EHEIM Digital Plus** herunter und starte Home Assistant neu.
3. Öffne **Einstellungen > Geräte & Dienste > Integration hinzufügen**.
4. Wähle **EHEIM Digital Plus** und gib den Hostnamen oder die IP-Adresse deines
   Hauptgeräts ein. Du kannst auch die automatische Netzwerkerkennung bestätigen.

Ab HA 2026.11 übernimmt der integrierte Marketplace die Rolle von HACS;
derselbe Link funktioniert weiterhin. Eine Anmeldung am EHEIM-Gerät ist nicht nötig.

Für die manuelle Installation entpackst du das ZIP aus den Releases in dein
HA-Konfigurationsverzeichnis. Danach muss
`custom_components/eheimdigital_plus/manifest.json` vorhanden sein. Starte HA neu.

## Von der bisherigen Integration wechseln

Version 0.2.0 hat die eigene Domain `eheimdigital_plus`. Sie ersetzt die
Core-Integration nicht. Bei einem Wechsel von Core oder unserer Version 0.1.0
kann sie bestehende Geräte und Entitäts-IDs nach Bestätigung übernehmen.

Die [Wechselanleitung](docs/migration.md) beschreibt die Schritte. Deaktiviere
die bisherige Einrichtung, bevor du Plus für dasselbe Hauptgerät einrichtest.

## Funktionen und Hilfe

- [Geräte, Funktionen und Einstellungen](docs/reference.md)
- [Ausfälle beheben und Diagnose herunterladen](docs/troubleshooting.md)
- [Beispiele für Automationen](docs/examples.md)
- [Gold-Prüfmatrix und Testabdeckung](docs/quality.md)
- [Entwicklung und Installationspakete](docs/development.md)

Die System-LED-Steuerung ist als selten benötigte Konfiguration standardmäßig
deaktiviert. Du kannst sie auf der Geräteseite unter den deaktivierten Entitäten
aktivieren. Die sechs zusätzlichen Filtersensoren sind standardmäßig aktiv.

## Entfernen

Entferne die Plus-Einrichtung unter **Einstellungen > Geräte & Dienste**.
Deinstalliere danach das Repository in HACS beziehungsweise im Marketplace.
Bei manueller Installation entfernst du `custom_components/eheimdigital_plus`.
Starte HA danach neu.

Die Core-Integration bleibt unabhängig davon verfügbar. Nach einer Übernahme
steht die bisherige Einrichtung deaktiviert weiter in HA; die von Plus übernommenen
Entitäts-IDs werden bei einer erneuten Core-Einrichtung nicht automatisch zurückübernommen.
Details stehen in der [Wechselanleitung](docs/migration.md).

## Herkunft

Der HA-Code steht unter Apache-2.0, die eingebettete Bibliothek unter MIT.
Quellstände und Änderungen stehen in der
[NOTICE](custom_components/eheimdigital_plus/NOTICE). Die
[Protokollanalyse](docs/protocol.md) und bisherigen
[Core-Beiträge](contributions/README.md) dokumentieren die Geräteuntersuchung.
