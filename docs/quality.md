# Prüfung gegen die HA-Gold-Kriterien

Dieses Projekt verwendet die
[Home-Assistant-Gold-Kriterien](https://contributors.home-assistant.io/core/quality-scale/rules/)
als Prüfliste für die Custom Integration. Die
[Prüfmatrix](../custom_components/eheimdigital_plus/quality_scale.yaml) nennt für
jede Bronze-, Silver- und Gold-Regel den Status und den Nachweis.

Dies ist eine Selbsteinschätzung des Projekts. Die offizielle
Integration-Quality-Scale vergibt das HA-Core-Team im Core-Review.
Das Manifest dieser Custom Integration beansprucht deshalb keine offizielle
Gold-Einstufung.

## Automatisierte Nachweise

Der Workflow [Validate](https://github.com/hilman2/ha-eheim/actions/workflows/validate.yml)
führt HACS, Hassfest, Ruff, die strenge Mypy-Prüfung und die Tests aus.
HACS läuft ohne ausgeschaltete Prüfungen.

Die Abdeckungsprüfung verlangt mehr als 95 Prozent je HA-Modul einschließlich
der gemessenen Zweige und 100 Prozent für den Config Flow. Fehlende Module im
Bericht führen ebenfalls zum Fehler. Der Befehl steht in der
[Entwicklungsanleitung](development.md).

Die eingebettete Protokollbibliothek wird im gleichen Bericht separat gemessen.
Ihre Module werden beim HA-Modul-Grenzwert nicht mitgerechnet. Damit ist der
Grenzwert keine Aussage über 95 Prozent des gesamten Repository-Codes.
Eigene Protokolltests prüfen unter anderem echte Frame-Dekodierung, Verbindungs-
und Schreibfehler, Abbruch, Wiederverbindung, Fehlerbits und die Filterberechnungen.

## Grenzen der Prüfung

Nur ein professionel 5e 350 mit Firmware 1.03.2 wurde physisch ausgelesen.
Die automatisierten Tests verwenden synthetische Geräte und simulierte
WebSockets. Es gibt keinen Testlauf gegen eine laufende Nutzer-HA-Instanz.

Markierungen als `exempt` beziehen sich auf Funktionen, die nicht vorhanden sind,
etwa eigene Automationsauslöser oder eine Anmeldung. Lokale Brand-Dateien
erfüllen die HACS-Anforderung für Custom Integrations. Sie sind kein Eintrag
im offiziellen HA-Brands-Repository.
