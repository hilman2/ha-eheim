# Geräte, Funktionen und Einstellungen

Die [README](../README.md) beschreibt die Installation.

## Unterstützte Geräte

| Gerätefamilie | Funktionen | Prüfstand |
| --- | --- | --- |
| professionel 5e | Pumpenschalter, Betriebsmodus, Drehzahl und Durchfluss-Sollwerte, Pulszeiten, Bio-Zeiten, Statussensoren | Am professionel 5e 350, Firmware 1.03.2, lesend geprüft; weitere Modelle mit synthetischen Paketen |
| classicVARIO+e | Pumpenschalter, Modus, manuelle Drehzahl, Tages-/Nachtdrehzahl und Zeiten, Wartungszeit, Fehlerstatus | Automatisierte Tests |
| thermocontrol+e | Thermostat, Ein/Aus, Bio-/Smart-Modus, Temperaturkorrektur, Nachtabsenkung und Zeiten | Automatisierte Tests |
| classicLEDcontrol+e | Lichtkanäle, Helligkeit und Tageszyklus | Automatisierte Tests |
| reeflexUV+e | UVC-Schalter, Lampe angeschlossen, Booster, Pause, Expertenmodus, Betriebszeiten und Wartung | Automatisierte Tests |

Die Integration verbindet sich mit einem Hauptgerät und erkennt darüber weitere
Geräte im EHEIM-Mesh. Neue unterstützte Geräte erscheinen ohne Neustart.

powerLED+/LEDcontrol+-Geräte mit Protokollversion 3 sowie pHcontrol, Autofeeder,
Dosierpumpen und andere in der Tabelle nicht genannte Familien haben hier keine
HA-Entitäten. Für ein nicht unterstütztes Hauptgerät zeigt die Einrichtung einen
entsprechenden Hinweis an. Nicht jede in der Bibliothek bekannte Gerätekennung
bedeutet Unterstützung in Home Assistant.

## Zusätzliche Sensoren des professionel 5e

| Sensor | Einheit | Bedeutung |
| --- | --- | --- |
| Betriebsdauer | h | Gerätezähler, intern in Minuten empfangen |
| Verbleibende Ausschaltzeit | min | Verbleibende Dauer einer Ausschaltpause |
| Verbleibende Fütterungspause | min | Restzeit der vom Gerät gemeldeten Fütterungspause |
| Fehlerstatus | Enum | `no_error`, `rotor_stuck`, `air_in_filter`, `temperature_error` oder `unknown_error` |
| Geschätzter Durchfluss | l/h | Aus Frequenz und Gerätefaktor berechnet |
| Geschätzte Leistungsaufnahme | W | Aus der Herstellerkennlinie berechnet |

Die Anzeige des Fehlerstatus ist übersetzt. Automationen verwenden die oben
genannten Zustandswerte. Kalibrierungsbits werden nicht als Fehler interpretiert.
Eine ungültige Leistungskennlinie ergibt einen unbekannten Sensorwert.

Die Core-Sensoren für Drehzahl und verbleibende Wartungszeit bleiben ebenfalls
vorhanden. Wartungszeit und Betriebsdauer sind Gerätezähler; sie messen nicht
den Verschmutzungszustand des Filters.

## Einrichtung und Adresse ändern

Das einzige Eingabefeld ist **Host**. Es enthält den Hostnamen oder die IP-Adresse
des Hauptgeräts, ohne `http://`, Port oder Pfad. Der Standard ist
`eheimdigital.local`. Es gibt keine Zugangsdaten und keinen separaten Optionsdialog.

Unter **Einstellungen > Geräte & Dienste > EHEIM Digital Plus > Neu konfigurieren**
kannst du den Host ändern. Die neue Adresse muss zum gleichen Hauptgerät mit
derselben MAC-Adresse gehören. Wird ein bekanntes Hauptgerät unter einer neuen
Adresse entdeckt, aktualisiert die Netzwerkerkennung den gespeicherten Host.

## Aktualisierungen und Ausfälle

Der Coordinator fragt den Status alle 15 Sekunden über die gemeinsame
WebSocket-Verbindung ab. Empfangene Gerätepakete aktualisieren die Entitäten
direkt. Ein Verbindungsabbruch setzt die betroffenen Entitäten auf
`unavailable`. Die nächste Statusabfrage versucht die Wiederverbindung.

Ein Mesh-Teilnehmer ohne empfangenes Paket seit mehr als 120 Sekunden wird
ebenfalls nicht verfügbar. Du kannst ihn dann auf seiner Geräteseite löschen.
Das Hauptgerät entfernst du über die Plus-Einrichtung. Ein später wieder
auftauchender Mesh-Teilnehmer wird neu erkannt.

## Steuerung und Automationen

Die Integration bietet die normalen HA-Aktionen ihrer Plattformen an:
`switch.turn_on`, `switch.turn_off`, `select.select_option`,
`number.set_value`, `time.set_value`, `light.turn_on`, `light.turn_off`
sowie die passenden `climate`-Aktionen für Heizgeräte.

Welche davon verfügbar sind, hängt vom Gerät ab. Die Auswahlwerte und Grenzen
stehen direkt an den Entitäten. Es gibt keine zusätzlichen eigenen Aktionen,
Automationsbedingungen oder Automationsauslöser. Normale Zustands- und
Schwellenwertauslöser können verwendet werden.

Die System-LED-Helligkeit ist eine optionale Konfigurationsentität von 0 bis
100 Prozent und standardmäßig deaktiviert. Aktiviere sie auf der Geräteseite,
wenn du sie einstellen möchtest.

## Bekannte Grenzen

Durchfluss und Leistungsaufnahme sind Schätzungen. Die Herstelleroberfläche
kann je nach Filtermodus andere Durchflusswerte aus Tabellen anzeigen. Die
berechnete Leistung ersetzt keinen Stromzähler. Die Betriebsdauer ist keine
Energiemessung.

Nur der professionel 5e 350 mit Firmware 1.03.2 wurde hier physisch ausgelesen.
Steuerbefehle, Fehlerzustände und andere Geräte sind automatisiert mit
synthetischen Daten geprüft. Sie wurden nicht absichtlich am laufenden Aquarium
ausgelöst. Andere Firmwarestände können zusätzliche Abweichungen haben.

Die Verbindung verwendet lokales HTTP/WebSocket ohne Anmeldung. HA muss das
Hauptgerät im Netzwerk erreichen können; es wird kein Cloudkonto benötigt.
