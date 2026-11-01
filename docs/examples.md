# Automationen mit Filterzuständen

Ersetze die Entitäts-IDs in diesen Beispielen durch die Werte deiner Geräteseite.
Die Beispiele verwenden normale HA-Aktionen und Auslöser.

## Niedrigen geschätzten Durchfluss melden

Dieses Beispiel meldet einen Wert unter 80 l/h, wenn er mindestens zehn Minuten
anliegt. Wähle den Grenzwert passend zu deinem Aquarium. Die Bedingung prüft,
ob der Pumpenschalter eingeschaltet ist.

```yaml
alias: EHEIM Durchfluss prüfen
triggers:
  - trigger: numeric_state
    entity_id: sensor.filter_estimated_flow_rate
    below: 80
    for: "00:10:00"
conditions:
  - condition: state
    entity_id: switch.filter
    state: "on"
actions:
  - action: persistent_notification.create
    data:
      title: EHEIM Filter
      message: Der geschätzte Durchfluss liegt seit zehn Minuten unter 80 l/h.
```

## Luft im Filter melden

Der Sensor zeigt in der deutschen Oberfläche einen übersetzten Text an.
Der Zustand für die Automation bleibt `air_in_filter`.

```yaml
alias: EHEIM Luft im Filter
triggers:
  - trigger: state
    entity_id: sensor.filter_error_code
    to: air_in_filter
actions:
  - action: persistent_notification.create
    data:
      title: EHEIM Filter
      message: Das Gerät meldet Luft im Filter. Prüfe den Filter.
```

## Filtermodus im Dashboard wählen

Füge den Pumpenschalter, die Auswahl **Filtermodus**, den geschätzten Durchfluss
und die verbleibende Wartungszeit in eine Entitätenkarte ein. Der Filtermodus
kann direkt an seiner Auswahlentität eingestellt werden. Die
[Referenz](reference.md) beschreibt die gerätespezifischen Funktionen.
