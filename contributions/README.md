# PR für den Betriebsdauersensor

[PR #189828](https://github.com/home-assistant/core/pull/189828) ergänzt den
Betriebsdauersensor für professionel5e-Filter. Der Beitrag ist eingereicht.
Der HA-Bot hat ihn wegen der noch ausstehenden CLA-Unterschrift als Entwurf markiert.

Die [weiteren fünf Sensoren](additional-sensors.md) sind ebenfalls implementiert
und getestet. Die getrennten Diffs und PR-Beschreibungen liegen dort zur Prüfung.

- [Vollständiger Diff](eheimdigital-operating-time.patch)
- [Ausgefüllte PR-Beschreibung](eheimdigital-operating-time-pr.md)

Titel: **Add operating time sensor to EHEIM Digital professionel5e filters**.
Ziel ist der Branch `dev` in `home-assistant/core`. Grundlage ist Commit
[`aeda28b0a24de1431fd0165ec250b957a4593192`](https://github.com/home-assistant/core/commit/aeda28b0a24de1431fd0165ec250b957a4593192).
Der PR-Branch liegt in `hilman2/core`, sein Head ist
`1977973e7fffa8eb3ff3b6b8afbe85bde678ec9b`.

## Änderung nachvollziehen

Die Bibliothek `eheimdigital==1.7.1` liefert die Betriebsdauer bereits in
Minuten über `EheimDigitalFilter.operating_time`. Die Änderung registriert
dafür eine Sensorentität in Home Assistant. Sie gehört zur Kategorie
Diagnose und zur Geräteklasse Dauer. Die native Einheit ist Minuten,
die vorgeschlagene Anzeige Stunden mit zwei Nachkommastellen.
Der vorhandene Übersetzungsschlüssel `operating_time` liefert den Namen.

Der Diff berührt drei Dateien:

- `homeassistant/components/eheimdigital/sensor.py` ergänzt die Sensorbeschreibung.
- `tests/components/eheimdigital/test_sensor.py` prüft Aktualisierungen des Sensors.
- `tests/components/eheimdigital/snapshots/test_sensor.ambr` enthält die neue
  Entität mit Kennung, Einheit und Diagnosekategorie.

Die Zustandsprüfung setzt die vom Gerät gelieferten Betriebsminuten nacheinander
auf folgende Werte und prüft die gerundete Anzeige:

| Betriebsminuten | Anzeige in Stunden |
| --- | --- |
| 1441 | 24.02 |
| 0 | 0.00 |
| 1 | 0.02 |

Die Datenerfassung läuft über den vorhandenen Coordinator und die vorhandene
Bibliothek. Die Implementierung fügt eine Beschreibung zur bestehenden
Sensorliste hinzu. Die Betriebsdauer ist in der offiziellen
[Gerätedokumentation](https://www.home-assistant.io/integrations/eheimdigital/#eheim-professionel5e)
bereits aufgeführt.

## Prüfung nachvollziehen

Der lokale Checkout liegt unter `/tmp/ha-eheim-home-assistant-core`, auf Branch
`feat/eheimdigital-operating-time`. Seine Entwicklungsumgebung wurde mit
`script/setup` eingerichtet.

```bash
uv run --no-sync pytest -q --tb=short --show-capture=no --disable-warnings tests/components/eheimdigital
```

Ergebnis auf dem eingereichten Stand: **83 Tests und 105 Snapshots erfolgreich**,
Laufzeit 5,36 Sekunden.
Die Suite meldet 100 Warnungen; Warnungen zu nicht abgewarteten `AsyncMock`-Aufrufen
traten bereits bei der Gegenprobe auf dem unveränderten Produktionscode auf.

```bash
uv run --no-sync prek run --files homeassistant/components/eheimdigital/sensor.py tests/components/eheimdigital/test_sensor.py tests/components/eheimdigital/snapshots/test_sensor.ambr
```

Ergebnis: Ruff, Formatierung, Codespell, Prettier, Mypy und Pylint erfolgreich.
Die übrigen Hooks hatten für diese Dateien nichts zu prüfen oder waren erfolgreich.

Nach einem erfolgreichen Sensortest wurde die neue Sensorbeschreibung
vorübergehend entfernt. Der Zustandsprüfung fehlte dann die Entität und sie
schlug fehl. Anschließend wurde die Änderung wiederhergestellt und die oben
genannte Integrationssuite erfolgreich ausgeführt.

## Freigabe und nächster Schritt

Diff und PR-Beschreibung wurden vor dem Einreichen vom Nutzer freigegeben. Die
[AI_POLICY.md von Home Assistant](https://github.com/home-assistant/core/blob/dev/AI_POLICY.md)
verlangt eine persönliche Prüfung und inhaltliches Verständnis durch den
Beitragenden. Die entsprechenden Bestätigungen in der PR-Vorlage sind gesetzt.

Noch offen ist die persönliche
[CLA-Unterschrift](https://home-assistant.io/developers/cla_sign_start/?pr=home-assistant/core#189828).
Danach den PR über **Ready for review** zur Prüfung freigeben.
Die Anforderung steht im
[Bot-Review](https://github.com/home-assistant/core/pull/189828#pullrequestreview-5727774504).

Der Maintainer arbeitet in [PR #177948](https://github.com/home-assistant/core/pull/177948)
an der Datenaktualisierung für spätere Zeitsensoren. Dieser vorbereitete Beitrag
ergänzt ausschließlich die Betriebsdauer als Dauerwert. Vor weiteren Änderungen
den aktuellen Stand des Branches `dev` und dieses PRs erneut abgleichen.
