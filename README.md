# fhemfrontend-enigma2
Thx Waldmensch for initial setup

# Supportet devices

['MAX','FHT','FS20','CUL_HM','IT','CUL_TX','CUL_WS','FBDECT','Weather','MQTT_DEVICE',
'MQTT2_DEVICE','DOIF','FRITZBOX','CUL','notify','AptToDate','GHoma','Hyperion','HUEDevice','dummy',
'ESPEasy','pilight_switch','pilight_temp']

# Setup

- static csrfToken is ok. Dynamic not till yet.
- Don't use unusual stateFormat's.
- Sometimes at the first setup, there are problems with logindetails, so:

> Telnet Vu+

> init 4

> edit /etc/enigma2/settings and add 

> config.fhem.username=yourUsername

> config.fhem.password=yourPassword

> init 3

- It is essential to have both, 98_JsonList.pm and 98_JsonList2.pm at server
  in/opt/fhem/FHEM. Rights set to 0666.
  Group set to dialout and owner is Fhem.
- Please set for best compatibility with HUEGroup the following in fhem for each group.

> attr yourHUEGroup userattr createActionReadings:1,0 createGroupReadings:1,0

# TODO

- <del>autoswitch- or manualswitch for http/https</del>
- <del>add csrfToken</del> 
- full switch to jsonlist2+
- add more devices
- ...
