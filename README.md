## fhemfrontend-enigma2
Thx Waldmensch for initial setup

## Supportet devices

- MAX
- FHT
- FS20
- CUL_HM
- IT
- CUL_TX
- CUL_WS
- FBDECT
- Weather
- MQTT_DEVICE
- MQTT2_DEVICE
- DOIF
- FRITZBOX
- CUL
- notify
- AptToDate
- GHoma
- Hyperion
- HUEDevice
- dummy
- ESPEasy
- pilight_switch
- pilight_temp


## Installation

- create folder fhem : /usr/lib/enigma2/python/Plugins/Extensions/fhem/
- push all files in
- static csrfToken is ok. Dynamic not till yet.
- stateFormat : Doublequotes (") inside HTML-Tags break matching device. Use singlequotes (')
- Sometimes at the first setup, there are problems with logindetails, so:

1. Telnet Vu+
2. init 4
3. edit /etc/enigma2/settings and add 
4. config.fhem.username=yourUsername
5. config.fhem.password=yourPassword
6. init 3

- It is essential to have both, 98_JsonList.pm and 98_JsonList2.pm at server
  in/opt/fhem/FHEM. Rights set to 0666.
  Group set to dialout and owner is Fhem.

- Please set for best compatibility with HUEGroup the following in fhem for each group.
> attr yourHUEGroup createActionReadings 1
> attr yourHUEGroup createGroupReadings 1


## TODO

- <del>autoswitch- or manualswitch for http/https</del>
- <del>add static csrfToken</del>
- <del>final solution to remove HTML-Tags when stateFormat is pimped for style</del>
- add dynamic csrfToken
- full switch to jsonlist2+
- add more devices
- ...
