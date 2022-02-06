# SL Sensor

Prototype for a sensor that can be used for text to speech and a Lovelace card.

## Getting an API key

This integration uses the https://www.trafiklab.se/api/trafiklab-apis/sl/departures-4/ API

You will need to get both an API key and the site_id for your location using the API provided by traficlab.se. 

To update the departure time you will need to call the `homeassistant.update_entity` on the departure sensor before the value is updated. See the Text To Speech example below.

## SL Card
https://github.com/MalteGruber/storstockholms_lokaltrafik_card

## Configuration

Each departure is added as a sensor like this

```yaml
sensor:
  - platform: storstockholms_lokaltrafik
    api_key: "YOUR KEY HERE"
    name: "metros_north"
    direction: 1
    site_id: 9264
    transport_kind: "Metro"

  - platform: storstockholms_lokaltrafik
    api_key: "YOUR KEY HERE"
    name: "metros_south"
    direction: 2
    site_id: 9264
    transport_kind: "Metro"

```



## Text to speech for saying a departure

```yaml
action:
  #This is critical for getting the latest value, do not try to run without!
  - service: homeassistant.update_entity
    target:
      entity_id: sensor.metros_north
  #The value is now avalible for us to use, change to fit your needs
  - service: tts.google_translate_say
    data:
      entity_id: media_player.living_room_speaker
      message: ' Mot stan {{ states.sensor.metros_north.attributes.spoken_departure }}'
      language: sv
```


