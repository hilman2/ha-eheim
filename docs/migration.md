# Zu EHEIM Digital Plus wechseln

Ab Version 0.2.0 verwendet dieses Repository die eigene Domain
`eheimdigital_plus`. Die Version 0.1.0 verwendete noch `eheimdigital`
und ersetzte damit die Core-Integration. Der HACS-Katalog akzeptiert solche
Core-Ersetzungen nicht.

## Bestehende Einrichtung übernehmen

1. Deaktiviere die bisherige **EHEIM Digital**-Einrichtung unter
   **Einstellungen > Geräte & Dienste**. Lösche sie noch nicht.
2. Aktualisiere dieses Repository in HACS auf mindestens 0.2.0.
3. Wenn der alte Ordner `custom_components/eheimdigital` aus Version 0.1.0 noch
   vorhanden ist, entferne ihn. Der neue Ordner heißt
   `custom_components/eheimdigital_plus`.
4. Starte Home Assistant neu.
5. Füge **EHEIM Digital Plus** mit der Adresse desselben Hauptgeräts hinzu.
6. Bestätige **Bestehende Einrichtung übernehmen**.

Die Integration vergleicht die MAC-Adresse des Hauptgeräts. Sie übernimmt nur
die passende deaktivierte Einrichtung und erhält Geräte-IDs, Entitäts-IDs,
eigene Namen sowie vom Nutzer deaktivierte Entitäten. Damit bleiben bestehende
Automationen und Verlaufsdaten den gleichen Entitäts-IDs zugeordnet.

Die frühere Einrichtung bleibt deaktiviert. Sobald Plus erfolgreich läuft,
kannst du die leere alte Einrichtung entfernen. Sie wird nicht automatisch
wieder aktiviert. Ein aktiver alter Eintrag für dasselbe Hauptgerät blockiert
die Übernahme mit einer Erklärung.

## Bisherige Version noch nicht eingerichtet

Installiere Plus nach der [README](../README.md). Ohne passenden alten Eintrag
gibt es keinen Übernahmeschritt. Eine Core-Einrichtung für ein anderes Aquarium
bleibt unabhängig.

## Zurück zu Core wechseln

Deaktiviere Plus und entferne es wie in der README beschrieben. Die Übernahme
von Core zu Plus hat die Einträge in den Geräte- und Entitätsregistrierungen
verschoben. Das Aktivieren der alten Core-Einrichtung verschiebt sie nicht
automatisch zurück.

Bei einer erneuten Core-Einrichtung können neue Entitäts-IDs entstehen.
Passe dann betroffene Automationen an. Wenn du den vorherigen Zustand exakt
wiederherstellen möchtest, verwende eine HA-Sicherung von vor der Übernahme.
