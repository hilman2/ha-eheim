# Entwicklung und Prüfung

Die Installationsanleitung steht in der [README](../README.md).
Diese Seite beschreibt die Herkunft des Codes und lokale Prüfungen.

## Basis aktualisieren

Die Integration basiert auf Home Assistant Core 2026.10.4.
Die Protokollbibliothek liegt vollständig in
`custom_components/eheimdigital_plus/_vendor/eheimdigital/`.
Quellstände und Lizenzen stehen in der
[NOTICE](../custom_components/eheimdigital_plus/NOTICE).

Beim Übernehmen weiterer Core-Änderungen müssen die internen Bibliotheksimporte
erhalten bleiben. In `manifest.json` bleibt `requirements` leer.
Die eigenständige Domain heißt `eheimdigital_plus`. Die bestätigte Migration
übernimmt bestehende Geräte und Entitäts-IDs aus einer deaktivierten Core-Einrichtung.

Neue Texte gehören in `translations/en.json` und `translations/de.json`.
Die Dateien enthalten die fertigen Texte. Core-Platzhalter aus `strings.json`
werden von Custom Integrations nicht aufgelöst.

## Lokal prüfen

Die Entwicklungsumgebung verwendet Python 3.14 und HA 2026.10.4.
Der Lockfile hält die Testabhängigkeiten fest:

```bash
uv sync --locked --group dev
uv run pytest -q --cov=custom_components.eheimdigital_plus --cov-branch --cov-report=term-missing --cov-report=json:coverage.json
uv run python -m scripts.check_quality coverage.json
uv run ruff check custom_components scripts tests
uv run ruff format --check custom_components scripts tests
uv run mypy custom_components/eheimdigital_plus scripts
```

Die Tests laden die Custom Integration über den HA-Loader. Die Hub-Verbindung
ist durch synthetische Geräte ersetzt. Die Protokolltests prüfen auch
Fehlerbits, die berechneten Werte und eingehende Statusänderungen.
Netzwerkverbindungen sind während der Tests gesperrt.

Die Abfrage eines echten Filters ist separat und erlaubt nur die beiden
Leseanfragen `GET_USRDTA` und `GET_FILTER_DATA`:

```bash
uv run python -m scripts.probe_filter 192.168.1.50
```

## Installationspaket bauen

```bash
uv run python -m scripts.build_release
```

Das ZIP unter `dist/` enthält `custom_components/eheimdigital_plus/` einschließlich
der Bibliothek, Übersetzungen und Lizenztexte. Es kann direkt in das
HA-Konfigurationsverzeichnis entpackt werden.

Für eine HACS-Veröffentlichung werden die Dateien dieses Repositories auf
GitHub benötigt. `hacs.json` verwendet die normale Verzeichnisstruktur und
benötigt kein gesondertes Release-Asset. Ein Release-Tag muss der Version in
`manifest.json` entsprechen.

Die [Gold-Prüfmatrix](quality.md) beschreibt den Geltungsbereich der Abdeckung.
Die GitHub-Workflows führen HACS und Hassfest ohne ausgelassene Prüfungen aus.
Ein Katalog-PR wird erst nach erfolgreichen Läufen und einem anschließenden
Release eröffnet.
