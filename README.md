# fhemfrontend-enigma2
Thx Waldmensch for initial setup

# Supportet devices:

["MAX","FHT","FS20","CUL_HM","IT","CUL_TX","CUL_WS","FBDECT","Weather","MQTT_DEVICE",
"MQTT2_DEVICE","DOIF","FRITZBOX","CUL","notify","AptToDate","GHoma", "Hyperion"]

#Setup:

° disable csrfToken
° don't use unusual stateformat's
° for https change
  conn = httplib.HTTPConnection(self.Address)
  to
  conn = httpslib.HTTPConnection(self.Address)
  
° sometimes at the first setup, there are problems with the login details

  - Telnet Vu+
  - init 4
  - edit /etc/enigma2/settings and add
   config.fhem.username=yourUsername
   config.fhem.password=yourPassword
  - init 3
