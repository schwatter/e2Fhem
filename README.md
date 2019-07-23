## fhemfrontend-enigma2

![](images/guiShot.jpg)

Thx Waldmensch for initial setup

## Supportet devices

- AptToDate
- CUL
- CUL_HM
- CUL_TX
- CUL_WS
- DOIF
- dummy
- ESPEasy
- FBDECT
- FHT
- FRITZBOX
- FS20
- GHoma
- HUEDevice
- Hyperion
- IT
- MAX
- MQTT_DEVICE
- MQTT2_DEVICE
- notify
- pilight_switch
- pilight_temp
- Weather


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
```
attr yourHUEGroup createActionReadings 1
attr yourHUEGroup createGroupReadings 1
```


## How To

- First setup details in settings.
- If connection is ok, supportet devices show up.
- If not, go to settings and activate logfile. Check for http-statuscode.
- Different devices have different functions.
- Some have full support and some have only readings. So the basics are:

1. Navigate with KeyUp, KeyDown, KeyLeft and KeyRight
2. KeyOk for on,off and specials.
3. ChannelUp and ChannelDown for dimming and temperature.
4. Num1 till Num4 for moreChannelSwitches.

DOIF / cmdState<br/>
No spaces, fill the gap for example with "_".
Or use compound words.
```
"LightNightMode|OnlyDeskLightOn|MorningLightDown|MorningLightUp"
"Coffee_cooks|Coffee_off|Coffee_finished"
"Temp_unter_48°C|Temp_ok"
"WarmWaterOk|WaterCold"
```

Dummy fourswitch example
```
defmod iconDemo dummy
attr iconDemo devStateIcon 1.on:on:on:on1+off 1.off:off:on:on1+on 2.on:on:on:on2+off 3.off:off:on:on3+on 4.on:on:on:on4+off 4.off:off:on4+on
attr iconDemo readingList on1 on2 on3 on4
attr iconDemo room 03.Wohnzimmer
attr iconDemo setList on1:on,off on2:on,off on3:on,off on4:on,off
attr iconDemo stateFormat 1:on1 2:on2 3:on3 4:on4
attr iconDemo webCmd on1:on2:on3:on4

setstate iconDemo 1:on 2:off 3:on 4:off
setstate iconDemo 2019-02-25 00:25:21 on1 on
setstate iconDemo 2019-02-24 14:43:07 on2 off
setstate iconDemo 2019-02-24 16:01:57 on3 on
setstate iconDemo 2019-02-24 16:02:05 on4 off
setstate iconDemo 2019-02-23 23:14:56 state on
```


## TODO

- <del>autoswitch- or manualswitch for http/https</del>
- <del>add static csrfToken</del>
- <del>final solution to remove HTML-Tags when stateFormat is pimped for style</del>
- add dynamic csrfToken
- full switch to jsonlist2+
- add more devices
- ...
