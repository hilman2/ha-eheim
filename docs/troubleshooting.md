# Verbindung und Diagnose

Die [README](../README.md) beschreibt die Installation. Die
[Referenz](reference.md) nennt unterstützte Geräte und den Aktualisierungstakt.

## Die Einrichtung verbindet sich nicht

Prüfe, ob Home Assistant die Geräteadresse im lokalen Netzwerk erreicht.
Öffne die Adresse im Browser von einem Gerät im gleichen Netz. Trage in HA
nur den Hostnamen oder die IP-Adresse ein, ohne URL-Pfad oder Port.

Der Verbindungsversuch wartet auf die Gerätekennung. Er schlägt auch dann fehl,
wenn ein WebSocket geöffnet werden kann, das Gerät aber keine Kennung liefert.
Nach einem fehlgeschlagenen Versuch wird die Probe-Verbindung geschlossen.

Ein nicht unterstützter Gerätetyp wird gesondert gemeldet. Die
[Geräteliste](reference.md) unterscheidet die unterstützten Controllerfamilien.

## Die Übernahme ist blockiert

Deaktiviere die bisherige EHEIM-Digital-Einrichtung für dasselbe Hauptgerät.
Starte die Einrichtung von Plus danach erneut. Beide Einträge müssen dasselbe
Hauptgerät erkennen. Die [Wechselanleitung](migration.md) beschreibt den Ablauf.

## Entitäten sind nicht verfügbar

Bei einer unterbrochenen Verbindung versucht die Integration alle 15 Sekunden
erneut eine Statusabfrage. Ein erfolgreicher Geräteempfang stellt die Zustände
wieder her. Für Ausfall und Wiederverbindung wird jeweils einmal ein
Logeintrag geschrieben.

Ändert sich die Geräteadresse, kann sie über die Netzwerkerkennung automatisch
aktualisiert werden. Alternativ verwende **Neu konfigurieren** am Integrationseintrag.

Einzelne Mesh-Teilnehmer werden nach 120 Sekunden ohne Paket nicht verfügbar.
Prüfe ihre Verbindung zum EHEIM-Hauptgerät. Ein nicht mehr vorhandenes Gerät
kann auf seiner Geräteseite gelöscht werden. Ein kurzzeitiger Netzausfall löscht
keine Geräte automatisch.

## Die System-LED-Steuerung fehlt

Diese Konfigurationsentität ist standardmäßig deaktiviert. Öffne die Geräteseite,
blende deaktivierte Entitäten ein und aktiviere die System-LED-Helligkeit.
HA lädt die Einrichtung nach einer Aktivierung erneut.

## Diagnose herunterladen

Öffne **Einstellungen > Geräte & Dienste**, wähle die Plus-Einrichtung und
lade über ihr Menü die Diagnose herunter. Sie enthält ausgewählte Gerätepakete,
mit denen sich Modelle und Firmwareabweichungen untersuchen lassen.

Host, Benutzer- und API-Zugangsdaten sowie bekannte WLAN-Passwortfelder werden
ersetzt. Gerätekennungen, Modell und Statuswerte können weiterhin enthalten sein.
Prüfe die Datei, bevor du sie in einem öffentlichen Issue anhängst.

Für ein [Issue](https://github.com/hilman2/ha-eheim/issues) sind HA-Version,
Plus-Version, Modell, Firmware und die genaue Fehlermeldung hilfreich.
Rohmitschnitte der WebSocket-Verbindung können WLAN-Zugangsdaten enthalten.
