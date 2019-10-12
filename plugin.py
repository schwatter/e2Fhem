
#  -*- coding: utf-8 -*-
# FHEM Plugin

###########################################################################
import httplib
import base64
import json
import requests
import threading
import re
import sys
import urllib2
import urllib
import ssl
import urlparse

from Screens.Screen import Screen
from Plugins.Plugin import PluginDescriptor
from Components.Label import Label
from Components.ActionMap import ActionMap
from Components.MenuList import MenuList
from Components.Sources.StaticText import StaticText
from Components.ConfigList import ConfigListScreen
# Configuration
from Components.config import getConfigListEntry, ConfigEnableDisable, \
	ConfigYesNo, ConfigText, ConfigClock, ConfigNumber, ConfigSelection, \
	ConfigDateTime, config, NoSave, ConfigSubsection, ConfigInteger, ConfigIP, configfile
	
from enigma import getDesktop, eTimer, eListbox, eLabel, eListboxPythonMultiContent, gFont, eRect, eSize, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_HALIGN_CENTER, RT_VALIGN_CENTER, RT_VALIGN_TOP, RT_WRAP
from Components.GUIComponent import GUIComponent
from time import localtime

d1 = ['AptToDate','CUL','CUL_HM','CUL_TX','CUL_WS','DOIF','dummy','ESPEasy','FBDECT','FHEMWEB','FHT','FRITZBOX','FS20','GHoma', 'HMCCUDEV', 'HUEDevice', 'Hyperion']  #actual supported types - leave as it is
d2 = ['IT','LightScene','MAX','MQTT_DEVICE','MQTT2_DEVICE','notify','pilight_switch','pilight_temp','PRESENCE','readingsProxy','SYSMON','Weather','WOL']
ELEMENTS = d1 + d2

fhemlog = '/usr/lib/enigma2/python/Plugins/Extensions/fhem/fhem.log'
jsonData = '/usr/lib/enigma2/python/Plugins/Extensions/fhem/deviceData.json'

MAX_LIMITS 	 		= [5.0, 30.0]
MAX_SPECIALS 		= ['eco','comfort','boost','auto','off','on']

FS20_SPECIALS		= ['off','on']

DUMMY_LIMITS  		= [0, 100]
THERMO_LIMITS 		= [6.0, 30.0]

APTTODATE_SPECIALS 	= ['repoSync']
BASIC_SPECIALS 		= ['off','on']
DIMMER_SPECIALS		= ['dim0%','dim06%','dim12%','dim18%','dim25%','dim31%','dim37%','dim41%','dim43%','dim50%','dim56%','dim62%','dim68%','dim75%','dim81%','dim87%','dim93%','dim100%']
HUEDevice_SPECIALS 	= ['off','on','rgb ff0000','rgb DEFF26','rgb 0000ff','ct 490','ct 380','ct 270','ct 160']
Hyperion_SPECIALS 	= ['off','on','clearall','dim06%','dim25%','dim50%','dim75%','dim100%']
FS20_SPECIALS		= ['off','on']
SWITCH4FOUR_DU1 	= ['on1 off','on1 on']
SWITCH4FOUR_DU2 	= ['on2 off','on2 on']
SWITCH4FOUR_DU3 	= ['on3 off','on3 on']
SWITCH4FOUR_DU4 	= ['on4 off','on4 on']

config.fhem 				= ConfigSubsection()
config.fhem.httpresponse 	= ConfigSelection(default='Http', choices = [('Http', _('Http')), ('Https', _('Https'))])
config.fhem.serverip 		= ConfigIP(default = [0,0,0,0])
config.fhem.port 			= ConfigInteger(default=8083, limits=(8000, 9000))
config.fhem.username 		= ConfigText(default='yourName')
config.fhem.password 		= ConfigText(default='yourPass')
config.fhem.csrfswitch 		= ConfigSelection(default='Off', choices = [('On', _('On')), ('Off', _('Off'))])
config.fhem.csrftoken 		= ConfigText(default='yourToken')
config.fhem.grouping 		= ConfigSelection(default='ROOM', choices = [('TYPE', _('Type')), ('ROOM', _('Room'))])
config.fhem.logfileswitch 	= ConfigSelection(default='Off', choices = [('On', _('On')), ('Off', _('Off'))])
config.fhem.jsondataswitch	= ConfigSelection(default='Off', choices = [('On', _('On')), ('Off', _('Off'))])

def writeLog(svalue):
	lswitch = str(config.fhem.logfileswitch.value)
	if lswitch == 'On':
		try:
			te = localtime()
			logtime = '%02d:%02d:%02d' % (te.tm_hour, te.tm_min, te.tm_sec)
			logF = open(fhemlog, 'a')
			logF.write(str(logtime) + ' - ' + str(svalue) + '\n')
			logF.close()
	
		except:
			return None
			
def writeJson(jsonObj):
	jswitch = str(config.fhem.jsondataswitch.value)
	if jswitch == 'On':
		try:
			te = localtime()
			logtime = '%02d:%02d:%02d' % (te.tm_hour, te.tm_min, te.tm_sec)
			dataF = open(jsonData, 'a')
			dataF.write(str(logtime) + ' - ' + jsonObj + '\n')
			dataF.close()

		except:
			return None

class MainScreen(Screen):
	desktopSize = getDesktop(0).size()
	if desktopSize.width() >= 1920:
		skin = '''
		<screen position='300,645' size='1390,430' name='fhem' title='FHEM Haussteuerung' >
			<widget name='titleMenu1' position='10,20' size='150,30' valign='center' halign='left' font='Regular;30'/>
			<eLabel name='bgMenu1' position='9,49' size='252,334' backgroundColor='#808080' zPosition='0'/>
			<widget name='Menu1' position='10,50' size='250,332' scrollbarMode='showOnDemand' zPosition='1' scrollbarWidth='3'/>
			<widget name='titleMenu2' position='280,20' size='150,30' valign='center' halign='left' font='Regular;30'/>
			<eLabel name='bgMenu2' position='279,49' size='502,334' backgroundColor='#808080' zPosition='0'/>
			<widget name='Menu2' position='280,50' size='500,332' scrollbarMode='showOnDemand' zPosition='1' scrollbarWidth='3'/>
			<widget name='titleDetails' position='800,20' size='580,30' valign='center' halign='left' font='Regular;30'/>
			<eLabel name='bgDetails' position='799,49' size='582,182' backgroundColor='#808080' zPosition='0'/>
			<widget name='details' position='800,50' size='580,180' zPosition='1'/>
			<eLabel name='bgSetBox' position='799,259' size='582,122' backgroundColor='#808080' zPosition='0'/>
			<widget name='set_Title' position='800,260' size='580,40' valign='center' halign='center' font='Regular;25' zPosition='1'/>
			<widget name='set_ArrowLeft' position='800,301' size='100,79' valign='center' halign='center' font='Regular;30' zPosition='1'/>
			<widget name='set_Text' position='900,301' size='380,79' valign='center' halign='center' font='Regular;30' zPosition='1'/>
			<widget name='set_ArrowRight' position='1280,301' size='100,79' valign='center' halign='center' font='Regular;30' zPosition='1'/>
			<widget name='spinner' position='600,390' size='140,40' valign='center' halign='right' font='Regular;25' foregroundColor='white' zPosition='1'/>
			<ePixmap position='10,420' size='140,40' pixmap='/usr/lib/enigma2/python/Plugins/Extensions/fhem/buttons/red.png' transparent='1' alphatest='on' />
			<ePixmap position='150,420' size='140,40' pixmap='/usr/lib/enigma2/python/Plugins/Extensions/fhem/buttons/green.png' transparent='1' alphatest='on' />
			<ePixmap position='290,420' size='140,40' pixmap='/usr/lib/enigma2/python/Plugins/Extensions/fhem/buttons/yellow.png' transparent='1' alphatest='on' />
			<ePixmap position='430,420' size='140,40' pixmap='/usr/lib/enigma2/python/Plugins/Extensions/fhem/buttons/blue.png' transparent='1' alphatest='on' />
			<widget source='key_red' render='Label' position='10,390' zPosition='1' size='140,40' valign='center' halign='center' font='Regular;21' transparent='1' foregroundColor='white' shadowColor='black' shadowOffset='-1,-1' />
			<widget source='key_green' render='Label' position='150,390' zPosition='1' size='140,40' valign='center' halign='center' font='Regular;21' transparent='1' foregroundColor='white' shadowColor='black' shadowOffset='-1,-1' />
			<widget source='key_yellow' render='Label' position='290,390' zPosition='1' size='140,40' valign='center' halign='center' font='Regular;21' transparent='1' foregroundColor='white' shadowColor='black' shadowOffset='-1,-1' />
			<widget source='key_blue' render='Label' position='430,390' zPosition='1' size='140,40' valign='center' halign='center' font='Regular;21' transparent='1' foregroundColor='white' shadowColor='black' shadowOffset='-1,-1' />
			<widget backgroundColor='#808080' font='Regular; 22' position='830,395' render='Label' size='180,25' source='global.CurrentTime' transparent='1' valign='bottom' halign='right' zPosition='3' foregroundColor='white'>
				<convert type='ClockToText'>Format:%A,</convert>
			</widget>
			<widget backgroundColor='#808080' font='Regular; 23' position='1145,395' render='Label' size='180,25' source='global.CurrentTime' transparent='1' valign='bottom' halign='left' zPosition='3' foregroundColor='white'>
				<convert type='ClockToText'>Format:%d. %B</convert>
			</widget>
			<widget source='global.CurrentTime' render='Label' position='1030,395' size='190,50' font='Regular; 27' halign='left' valign='top' foregroundColor='white' backgroundColor='#808080' transparent='1'>
				<convert type='ClockToText'>WithSeconds</convert>
			</widget>
		</screen>'''
	else:
		skin = '''
		<screen position='5,265' size='1270,450' name='fhem' title='FHEM Haussteuerung' >
			<widget name='titleMenu1' position='10,20' size='150,25' valign='center' halign='left' font='Regular;25'/>
			<eLabel name='bgMenu1' position='9,49' size='252,337' backgroundColor='#808080' zPosition='0'/>
			<widget name='Menu1' position='10,50' size='250,335' scrollbarMode='showOnDemand' zPosition='1' scrollbarWidth='3'/>
			<widget name='titleMenu2' position='280,20' size='150,25' valign='center' halign='left' font='Regular;25'/>
			<eLabel name='bgMenu2' position='279,49' size='502,337' backgroundColor='#808080' zPosition='0'/>
			<widget name='Menu2' position='280,50' size='500,335' scrollbarMode='showOnDemand' zPosition='1' scrollbarWidth='3'/>
			<widget name='titleDetails' position='800,20' size='460,25' valign='center' halign='left' font='Regular;25'/>
			<eLabel name='bgDetails' position='799,49' size='462,202' backgroundColor='#808080' zPosition='0'/>
			<widget name='details' position='800,50' size='460,200' zPosition='1'/>
			<eLabel name='bgSetBox' position='799,279' size='462,122' backgroundColor='#808080' zPosition='0'/>
			<widget name='set_Title' position='800,280' size='460,40' valign='center' halign='center' font='Regular;25' zPosition='1'/>
			<widget name='set_ArrowLeft' position='800,321' size='100,79' valign='center' halign='center' font='Regular;25' zPosition='1'/>
			<widget name='set_Text' position='880,321' size='300,79' valign='center' halign='center' font='Regular;25' zPosition='1'/>
			<widget name='set_ArrowRight' position='1160,321' size='100,79' valign='center' halign='center' font='Regular;25' zPosition='1'/>
			<widget name='spinner' position='600,410' size='140,40' valign='center' halign='right' font='Regular;25' foregroundColor='white' zPosition='1'/>
			<ePixmap position='10,440' size='140,40' pixmap='/usr/lib/enigma2/python/Plugins/Extensions/fhem/buttons/red.png' transparent='1' alphatest='on' />
			<ePixmap position='150,440' size='140,40' pixmap='/usr/lib/enigma2/python/Plugins/Extensions/fhem/buttons/green.png' transparent='1' alphatest='on' />
			<ePixmap position='290,440' size='140,40' pixmap='/usr/lib/enigma2/python/Plugins/Extensions/fhem/buttons/yellow.png' transparent='1' alphatest='on' />
			<ePixmap position='430,440' size='140,40' pixmap='/usr/lib/enigma2/python/Plugins/Extensions/fhem/buttons/blue.png' transparent='1' alphatest='on' />
			<widget source='key_red' render='Label' position='10,410' zPosition='1' size='140,40' valign='center' halign='center' font='Regular;21' transparent='1' foregroundColor='white' shadowColor='black' shadowOffset='-1,-1' />
			<widget source='key_green' render='Label' position='150,410' zPosition='1' size='140,40' valign='center' halign='center' font='Regular;21' transparent='1' foregroundColor='white' shadowColor='black' shadowOffset='-1,-1' />
			<widget source='key_yellow' render='Label' position='290,410' zPosition='1' size='140,40' valign='center' halign='center' font='Regular;21' transparent='1' foregroundColor='white' shadowColor='black' shadowOffset='-1,-1' />
			<widget source='key_blue' render='Label' position='430,410' zPosition='1' size='140,40' valign='center' halign='center' font='Regular;21' transparent='1' foregroundColor='white' shadowColor='black' shadowOffset='-1,-1' />
			<widget backgroundColor='#808080' font='Regular; 22' position='780,415' render='Label' size='180,25' source='global.CurrentTime' transparent='1' valign='bottom' halign='right' zPosition='3' foregroundColor='white'>
				<convert type='ClockToText'>Format:%A,</convert>
			</widget>
			<widget backgroundColor='#808080' font='Regular; 22' position='970,415' render='Label' size='180,25' source='global.CurrentTime' transparent='1' valign='bottom' halign='left' zPosition='3' foregroundColor='white'>
				<convert type='ClockToText'>Format:%d. %B -</convert>
			</widget>
			<widget source='global.CurrentTime' render='Label' position='1095,415' size='190,50' font='Regular; 22' halign='left' valign='top' foregroundColor='white' backgroundColor='#808080' transparent='1'>
				<convert type='ClockToText'>WithSeconds</convert>
			</widget>
		</screen>'''
		

	def __init__(self, session, args = None):
		self.session = session
		Screen.__init__(self, session)
				
		self.onLayoutFinish.append(self.startRun)
		self.grouping = str(config.fhem.grouping.value)
		
		self['set_Title'] = Label('Neue Solltemperatur')
		self['set_ArrowLeft'] = Label('<')
		self['set_ArrowRight'] = Label('>')
		self['set_Text'] = Label()
		self['details'] = ElementList()
		self['titleMenu1'] = Label()
		self['titleMenu2'] = Label('Element')
		self['titleDetails'] = Label()
		self['spinner'] = Label('')
		
		self['Menu2'] = ElementList() 
		self['Menu2'].connectSelChanged(self.selChanged)
		self['Menu2'].selectionEnabled(0)
		self['Menu1'] = ElementList()
		self['Menu1'].connectSelChanged(self.selChanged)
		self['Menu1'].selectionEnabled(1)
		self.selectedListObject = self['Menu1']
		self.selList = 0
		
		self.listSelTimer = eTimer()
		self.listSelTimer.callback.append(self.listSelectionChanged)
		
		self.refreshTimer = eTimer()
		self.refreshTimer.callback.append(self.timerRefresh)
		
		self.refreshThread = LoadContainerBackgroundThread(self.session, self)
		
		#some flags
		self.typedef = None
		self.autorefresh = True
		self.threadIsRunning = False
		
		# Initialize Buttons
		self['key_red'] = StaticText(_('Exit'))
		self['key_green'] = StaticText(_('Transmit'))
		self['key_yellow'] = StaticText(_('Refresh'))
 		self['key_blue'] = StaticText(_('Setup'))
		
		self['actions'] = ActionMap(['FHEM_Actions'],
		{
				'key_ok': self.key_ok_Handler,
				'key_num_left': self.key_num_left_Handler,
				'key_num_right': self.key_num_right_Handler,
				'key_channel_down': self.key_num_left_Handler,
				'key_channel_up': self.key_num_right_Handler,
				'key_0': self.key_0_Handler,
				'key_green': self.key_green_Handler,
				'key_yellow': self.key_yellow_Handler,
				'key_blue': self.key_menu_Handler,
				'key_red': self.close,
				'key_menu': self.key_menu_Handler,
				'key_cancel': self.close,
				'key_left': self.key_left_right_Handler,
				'key_right': self.key_left_right_Handler,
				'key_up': self.key_Up_Handler,
				'key_down': self.key_Down_Handler
		}, -1)
		
	def closeme(self):
		self.isRunning = 0
		self.close
	
	def saveconfig(self):
		config.fhem.serverip.save()
		config.fhem.port.save()
		config.fhem.username.save()
		config.fhem.password.save()
		config.fhem.csrftoken.save()
		config.fhem.grouping.save() 
 		configfile.save()

		
	def key_menu_Handler(self):
		self.session.openWithCallback(self.setConf, FHEM_Setup)
		
	def setConf(self):
		self.saveconfig()
		self.grouping = str(config.fhem.grouping.value)
		self.startRun()
		
	def key_Up_Handler(self):
		self.selectedListObject.up()
	
	def key_Down_Handler(self):
		self.selectedListObject.down()
		
	def key_left_right_Handler(self):
		if self.selList == 0:
			self.selList = 1
			self.selectedListObject = self['Menu2']	
			self['Menu1'].selectionEnabled(0)
			self['Menu2'].selectionEnabled(1)
			self.listSelectionChanged()
		else:
			self.selList = 0
			self.selectedListObject = self['Menu1']	
			self['Menu1'].selectionEnabled(1)
			self['Menu2'].selectionEnabled(0)
			#clear Details
			self['set_Title'].setText('')
			self['set_Text'].setText('')
			self['titleDetails'].setText('')
			self['details'].setList([], 3)

		
	def startRun(self):
		server = '%d.%d.%d.%d' % tuple(config.fhem.serverip.value)
		if server == '0.0.0.0':
			return
		self.isRunning = 1
		self.reload_Screen()
		self['Menu2'].selectionEnabled(0)
		self['Menu1'].selectionEnabled(1)
		self['details'].selectionEnabled(0)
		self.selList = 0
		self.selectedListObject = self['Menu1']
		
	def selChanged(self):
		self.listSelTimer.start(200, True)
			
	def listSelectionChanged(self):
		writeLog('FHEM-debug: %s -- %s' % ('listSelectionChanged', 'enter'))
		if self.selList == 0:
			
			try:
				typedef = self['Menu1'].l.getCurrentSelection()[0]
			except:
				return
			
			#avoid racecondition
			if self.typedef == typedef:
				return
			else:
				self.typedef = typedef
			
			list = []

			if self.grouping == 'TYPE':
				self['titleMenu1'].setText('Typ')
				for element in self.container.getElementsByType([typedef]):
					list.append((element,))

			if self.grouping == 'ROOM':
				self['titleMenu1'].setText('Raum')
				for element in self.container.getElementsByRoom([typedef]):
					list.append((element,))
					
			self['Menu2'].setList(list, 2)
			
		else:

			try:
				selectedElement = self['Menu2'].l.getCurrentSelection()[0]
			except:
				return
				
			writeLog('FHEM-debug: %s -- %s' % ('listSelectionChanged', selectedElement.Name))
			
			if selectedElement.getType() in ['FHT', 'MAX', 'CUL_HM']:			
				if selectedElement.getSubType() == 'thermostat':
					self['titleDetails'].setText('Details für ' + selectedElement.getAlias())
					
					list = []
					list.append((['Solltemperatur:',selectedElement.getDesiredTemp() + ' °C'],))
					list.append((['Isttemperatur:',selectedElement.getMeasuredTemp() + ' °C'],))
					list.append((['Thermostat:',selectedElement.getActuator() + ' %'],))
					list.append((['Timestamp:',selectedElement.getLastrcv()],))
					list.append((['Batterie:',selectedElement.getBattery()],))
					self['details'].setList(list, 3)
					
					self['set_Text'].setText(selectedElement.getDesiredTemp() + ' °C')
					self['set_Title'].setText('Neue Solltemperatur')
				
				elif selectedElement.getSubType() == 'THSensor':
					self['titleDetails'].setText('Details für ' + selectedElement.getAlias())
					
					list = []
					list.append((['TempSensor1:',selectedElement.getMeasuredTemp() + ' °C'],))
					list.append((['TempSensor2:',selectedElement.getMeasuredTemp1() + ' °C'],))
					list.append((['Timestamp:',selectedElement.getLastrcv1()],))
					list.append((['Batterie:',selectedElement.getBattery()],))
					self['details'].setList(list, 3)
				
				elif selectedElement.getSubType() == 'switch':
					self['titleDetails'].setText('Details für ' + selectedElement.getAlias())
				
					list = []
					list.append((['Einschaltstatus:',selectedElement.getReadingState()],))
					list.append((['Timestamp:',selectedElement.getLastrcv2()],))
					self['details'].setList(list, 3)
				
					self['set_Title'].setText('Neuer Schaltstatus')
					self['set_Text'].setText(selectedElement.getReadingState())
					
			elif selectedElement.getType() in ['HMCCUDEV']:
				if selectedElement.getSubType() == 'thermostat':
					self['titleDetails'].setText('Details für ' + selectedElement.getAlias())
					
					list = []
					list.append((['Solltemperatur:',selectedElement.getDesiredTemp() + ' °C'],))
					list.append((['Isttemperatur:',selectedElement.getMeasuredTemp() + ' °C'],))
					list.append((['Mode:',selectedElement.getControlmode()],))
					list.append((['Thermostat:',selectedElement.getActuator() + ' %'],))
					list.append((['Timestamp:',selectedElement.getLastrcv()],))
					list.append((['Batterie:',selectedElement.getBattery()],))
					self['details'].setList(list, 3)
					
					self['set_Text'].setText(selectedElement.getDesiredTemp() + ' °C')
					self['set_Title'].setText('Neue Solltemperatur')
			
			elif selectedElement.getType() in ['CUL_TX','ESPEasy','pilight_temp']:
				self['titleDetails'].setText('Details für ' + selectedElement.getAlias())
				
				list = []
				list.append((['Temperatur:',selectedElement.getMeasuredTemp() + ' °C'],))
				list.append((['Luftfeuchte:',selectedElement.getHumidity() + ' %'],))
				if selectedElement.getPressure() != 'no prop':
					list.append((['Luftdruck:',selectedElement.getPressure() + ' hPa'],))
				self['details'].setList(list, 3)
				
				self['set_Title'].setText('')
				self['set_Text'].setText('')
				
			elif selectedElement.getType() in ['Weather']:
				self['titleDetails'].setText('Details für ' + selectedElement.getAlias())
				
				list = []
				list.append((['Temperatur:',selectedElement.getMeasuredTemp() + ' °C'],))
				list.append((['Luftfeuchte:',selectedElement.getHumidity() + ' %'],))
				list.append((['Windstärke:',selectedElement.getWind() + ' km/h'],))
				if selectedElement.getPressure() != 'no prop':
					list.append((['Luftdruck:',selectedElement.getPressure() + ' hPa'],))
				self['details'].setList(list, 3)
				
				self['set_Title'].setText('')
				self['set_Text'].setText('')
			
			elif selectedElement.getType() in ['FS20','IT','DOIF','GHoma','Hyperion','dummy','pilight_switch','LightScene','readingsProxy','WOL']:
				self['titleDetails'].setText('Details für ' + selectedElement.getAlias())
				
				list = []
				list.append((['Einschaltstatus:',selectedElement.getReadingState()],))
				self['details'].setList(list, 3)
				
				self['set_Title'].setText('Neuer Schaltstatus')
				self['set_Text'].setText(selectedElement.getReadingState())
			
			elif selectedElement.getType() in ['HUEDevice']:
				self['titleDetails'].setText('Details für ' + selectedElement.getAlias())
				
				list = []
				list.append((['Einschaltstatus:',selectedElement.getReadingState()],))
				list.append((['Helligkeit:',selectedElement.getBri()],))
				self['details'].setList(list, 3)
				
				self['set_Title'].setText('Neuer Schaltstatus')
				self['set_Text'].setText(selectedElement.getReadingState())
			
			elif selectedElement.getType() in ['MQTT_DEVICE', 'MQTT2_DEVICE']:
				if selectedElement.getENERGYTotal() == 'no prop':
					self['titleDetails'].setText('Details für ' + selectedElement.getAlias())
					
					list = []
					list.append((['Einschaltstatus:',selectedElement.getReadingState()],))
					list.append((['Present:',selectedElement.getPresent()],))
					self['details'].setList(list, 3)
					
					self['set_Title'].setText('Neuer Schaltstatus')
					self['set_Text'].setText(selectedElement.getReadingState())
					
				elif selectedElement.getENERGYCurrent() != 'no prop':
					self['titleDetails'].setText('Details für ' + selectedElement.getAlias())
					
					list = []
					list.append((['Einschaltstatus:',selectedElement.getReadingState()],))
					list.append((['Strom:',selectedElement.getENERGYCurrent() + ' A'],))
					list.append((['Leistung:',selectedElement.getENERGYPower() + ' W'],))
					list.append((['Energie heute:',selectedElement.getENERGYToday() + ' kWh'],))
					list.append((['Energie insgesamt:',selectedElement.getENERGYTotal() + ' kWh'],))
					list.append((['Present:',selectedElement.getPresent()],))
					self['details'].setList(list, 3)
					
					self['set_Title'].setText('Neuer Schaltstatus')
					self['set_Text'].setText(selectedElement.getReadingState())
			
			elif selectedElement.getType() in ['FBDECT']:
				self['titleDetails'].setText('Details für ' + selectedElement.getAlias())
				
				list = []
				list.append((['Einschaltstatus:',selectedElement.getReadingState()],))
				list.append((['Mode:',selectedElement.getControlmode()],))
				list.append((['Leistung:',selectedElement.getENERGYPower()],))
				list.append((['Energie insgesamt:',selectedElement.getENERGYTotal()],))
				list.append((['Temperatur:',selectedElement.getMeasuredTemp() + ' °C'],))
				list.append((['Present:',selectedElement.getPresent()],))
				self['details'].setList(list, 3)
				
				self['set_Title'].setText('Neuer Schaltstatus')
				self['set_Text'].setText(selectedElement.getReadingState())
			
			elif selectedElement.getType() in ['FRITZBOX', 'CUL', 'notify', 'PRESENCE']:
				self['titleDetails'].setText('Details für ' + selectedElement.getAlias())
				
				list = []
				list.append((['State:',selectedElement.getReadingState()],))
				self['details'].setList(list, 3)
				
				self['set_Title'].setText('')
				self['set_Text'].setText('')
			
			elif selectedElement.getType() in ['AptToDate']:
				self['titleDetails'].setText('Details für ' + selectedElement.getAlias())
				
				list = []
				list.append((['State:',selectedElement.getReadingState()],))
				list.append((['Updates:',selectedElement.getUpdateAvState()],))
				list.append((['repoSync:',selectedElement.getRepoSync()],))
				self['details'].setList(list, 3)
				
				self['set_Title'].setText('AptToDate')
				self['set_Text'].setText(selectedElement.getReadingState())
				
			elif selectedElement.getType() in ['SYSMON']:
				self['titleDetails'].setText('Details für ' + selectedElement.getAlias())
				
				list = []
				list.append((['cpu_freq:',selectedElement.getCPUfreq() + ' MHz'],))
				list.append((['cpu_temp:',selectedElement.getCPUtemp() + ' °C'],))
				self['details'].setList(list, 3)
				
				self['set_Title'].setText('SYSMON')
				self['set_Text'].setText(selectedElement.getUptime())
			
			elif selectedElement.getSubType() == 'switch':
				self['titleDetails'].setText('Details für ' + selectedElement.getAlias())
				
				list = []
				list.append((['Einschaltstatus:',selectedElement.getReadingState()],))
				self['details'].setList(list, 3)
				
				self['set_Title'].setText('Neuer Schaltstatus')
				self['set_Text'].setText(selectedElement.getReadingState())
				
			elif selectedElement.getSubType() in ['THSensor']:
				self['titleDetails'].setText('Details für ' + selectedElement.getAlias())
				
				list = []
				list.append((['Temperatur:',selectedElement.getMeasuredTemp() + ' °C'],))
				list.append((['Luftfeuchte:',selectedElement.getHumidity() + ' %'],))
				if selectedElement.getPressure() != 'no prop':
					list.append((['Luftdruck:',selectedElement.getPressure() + ' hPa'],))
				list.append((['Batterie:',selectedElement.getBattery()],))
				self['details'].setList(list, 3)
				
				self['set_Title'].setText('')
				self['set_Text'].setText('')
				
			elif selectedElement.getType() in ['CUL_HM'] and electedElement.getSubType() != 'thermostat':
				self['titleDetails'].setText('Details für ' + selectedElement.getAlias())
				
				list = []
				list.append((['unbek. HM subtype:', selectedElement.getSubType()],))
				list.append((['Bitte JSON für:', selectedElement.Name],))
				list.append((['im Forum posten',''],))
				self['details'].setList(list, 3)
				
				self['set_Title'].setText('- - -')
				self['set_Text'].setText('0')
	
	
	def key_0_Handler(self):
		pass
		
	def key_1_Handler(self):
		if self.selList == 1:
			selectedElement = self['Menu2'].l.getCurrentSelection()[0]
			if selectedElement.getType() in ['dummy','CUL_HM']:
				specials = selectedElement.getSpecials1()
				actvalue = self['set_Text'].getText()
				if self.is_number(actvalue):
					self['set_Text'].setText(specials[0])
				else:
					for idx, svalue in enumerate(specials):
						if svalue == actvalue:
							if idx < len(specials) - 1:
								self['set_Text'].setText(specials[idx + 1])
							
							else:
								self['set_Text'].setText(specials[0])
								
							return

						elif not actvalue:
							if idx < len(specials) - 1:
								self['set_Text'].setText(specials[idx + 1])
						
						else:
							self['set_Text'].setText(specials[0])
						
	def key_2_Handler(self):
		if self.selList == 1:
			selectedElement = self['Menu2'].l.getCurrentSelection()[0]
			if selectedElement.getType() in ['dummy','CUL_HM']:
				specials = selectedElement.getSpecials2()
				actvalue = self['set_Text'].getText()
				if self.is_number(actvalue):
					self['set_Text'].setText(specials[0])
				else:
					for idx, svalue in enumerate(specials):
						if svalue == actvalue:
							if idx < len(specials) - 1:
								self['set_Text'].setText(specials[idx + 1])
							
							else:
								self['set_Text'].setText(specials[0])
								
							return

						elif not actvalue:
							if idx < len(specials) - 1:
								self['set_Text'].setText(specials[idx + 1])
						
						else:
							self['set_Text'].setText(specials[0])
		
	def key_3_Handler(self):
		if self.selList == 1:
			selectedElement = self['Menu2'].l.getCurrentSelection()[0]
			if selectedElement.getType() in ['dummy','CUL_HM']:
				specials = selectedElement.getSpecials3()
				actvalue = self['set_Text'].getText()
				if self.is_number(actvalue):
					self['set_Text'].setText(specials[0])
				else:
					for idx, svalue in enumerate(specials):
						if svalue == actvalue:
							if idx < len(specials) - 1:
								self['set_Text'].setText(specials[idx + 1])
							
							else:
								self['set_Text'].setText(specials[0])
								
							return

						elif not actvalue:
							if idx < len(specials) - 1:
								self['set_Text'].setText(specials[idx + 1])
						
						else:
							self['set_Text'].setText(specials[0])
						
	def key_4_Handler(self):
		if self.selList == 1:
			selectedElement = self['Menu2'].l.getCurrentSelection()[0]
			if selectedElement.getType() in ['dummy','CUL_HM']:
				specials = selectedElement.getSpecials4()
				actvalue = self['set_Text'].getText()
				if self.is_number(actvalue):
					self['set_Text'].setText(specials[0])
				else:
					for idx, svalue in enumerate(specials):
						if svalue == actvalue:
							if idx < len(specials) - 1:
								self['set_Text'].setText(specials[idx + 1])
							
							else:
								self['set_Text'].setText(specials[0])
								
							return

						elif not actvalue:
							if idx < len(specials) - 1:
								self['set_Text'].setText(specials[idx + 1])
						
						else:
							self['set_Text'].setText(specials[0])
	
	def key_num_left_Handler(self):
		if self.selList == 1:
			selectedElement = self['Menu2'].l.getCurrentSelection()[0]
			if selectedElement.getSubType() == 'thermostat':
				if self.is_number(self['set_Text'].getText()):
					actvalue = float(self['set_Text'].getText())
					limits = selectedElement.getLimits()
					if actvalue > limits[0]:
						self['set_Text'].setText(str(actvalue - 0.5))
				else:
					self['set_Text'].setText(str(float(selectedElement.getDesiredTemp()) - 0.5))
					
			elif selectedElement.getType() in ['dummy'] and selectedElement.getSetlistslider() == 'state:slider,0,1,100':
				if self.is_number(self['set_Text'].getText()):
					actvalue = int(self['set_Text'].getText())
					limits = selectedElement.getLimits()
					if actvalue > limits[0]:
						try:
							self['set_Text'].setText(str(actvalue - 5))
						except ValueError:
							pass
		
			elif selectedElement.getType() in ['FS20','HUEDevice','Hyperion']:
				specials = selectedElement.getSpecials0()
				actvalue = self['set_Text'].getText()
				if self.is_number(actvalue):
					self['set_Text'].setText(specials[1])
				else:
					for idx, svalue in enumerate(specials):
						if svalue == actvalue:
							if idx < len(specials) + 1:
								self['set_Text'].setText(specials[idx - 1])
							
							else:
								self['set_Text'].setText(specials[1])
								
							return

						elif not actvalue:
							if idx < len(specials) + 1:
								self['set_Text'].setText(specials[idx - 1])
						
						else:
							self['set_Text'].setText(specials[1])	
		
	def key_num_right_Handler(self):
		if self.selList == 1:
			selectedElement = self['Menu2'].l.getCurrentSelection()[0]
			if selectedElement.getSubType() == 'thermostat':
				if self.is_number(self['set_Text'].getText()):
					actvalue = float(self['set_Text'].getText())
					limits = selectedElement.getLimits()
					if actvalue < limits[1]:
						self['set_Text'].setText(str(actvalue + 0.5))
				else:
					self['set_Text'].setText(str(float(selectedElement.getDesiredTemp()) + 0.5))
					
			elif selectedElement.getType() in ['dummy'] and selectedElement.getSetlistslider() == 'state:slider,0,1,100':
				if self.is_number(self['set_Text'].getText()):
					actvalue = int(self['set_Text'].getText())
					limits = selectedElement.getLimits()
					if actvalue < limits[1]:
						try:
							self['set_Text'].setText(str(actvalue + 5))
						except ValueError:
							pass
							
			elif selectedElement.getType() in ['FS20','HUEDevice','Hyperion']:
				specials = selectedElement.getSpecials0()
				actvalue = self['set_Text'].getText()
				if self.is_number(actvalue):
					self['set_Text'].setText(specials[0])
				else:
					for idx, svalue in enumerate(specials):
						if svalue == actvalue:
							if idx < len(specials) - 1:
								self['set_Text'].setText(specials[idx + 1])
							
							else:
								self['set_Text'].setText(specials[0])
								
							return

						elif not actvalue:
							if idx < len(specials) - 1:
								self['set_Text'].setText(specials[idx + 1])
						
						else:
							self['set_Text'].setText(specials[0])
		
	def key_green_Handler(self):
		if self.selList == 1:
			selectedElement = self['Menu2'].l.getCurrentSelection()[0]
			
			try:
				if self['set_Text'].getText() != '':
					self.container.updateElementByName(selectedElement.Name, self['set_Text'].getText())
					self.setSpinner(True)
					self.refreshTimer.start(500, True)
			except:
				pass
		
	def key_yellow_Handler(self):
		self.setSpinner(True)
		self.refreshTimer.start(500, True)
		
	def key_ok_Handler(self):
		if self.selList == 1:
			selectedElement = self['Menu2'].l.getCurrentSelection()[0]
			specials = selectedElement.getSpecials()
			actvalue = self['set_Text'].getText()
			if self.is_number(actvalue):
				self['set_Text'].setText(specials[0])
			else:
				for idx, svalue in enumerate(specials):
					if svalue == actvalue:
						if idx < len(specials) - 1:
							self['set_Text'].setText(specials[idx + 1])
						
						else:
							self['set_Text'].setText(specials[0])
							
						return

					elif not actvalue:
						if idx < len(specials) - 1:
							self['set_Text'].setText(specials[idx + 1])
					
					else:
						self['set_Text'].setText(specials[0])
					
	
	def timerRefresh(self):
		if self.threadIsRunning:
			self.refreshTimer.start(500, True)
		else:
			self.threadIsRunning = True
			self.refreshThread.run()
			
	
	def reload_Screen(self):
	
		#.refreshTimer.stop()
		self.container = FHEMContainer()
		self.container.reloadContainer()
		
		list = []
		
		if self.grouping == 'TYPE':
			for listentry in self.container.getTypes():
				list.append((listentry,))
			self['Menu1'].setList(list, 0)
		elif self.grouping == 'ROOM':
			for listentry in self.container.getRooms():
				list.append((listentry,))
			self['Menu1'].setList(list, 1)	
		
		self.selList = 0
		self.selectedListObject = self['Menu1']	
		self['Menu1'].selectionEnabled(1)
		self['Menu2'].selectionEnabled(0)
		#clear Details
		self['set_Title'].setText('')
		self['set_Text'].setText('')
		self['titleDetails'].setText('')
		self['details'].setList([], 3)
			
		self.listSelectionChanged()
		#self.refreshTimer.start(1000, True)
		writeLog('FHEM-debug: %s -- %s' % ('reload_Screen', 'done'))
	
	def	setSpinner(self, enabled):
		if enabled:
			self['spinner'].setText('load...')
		else:
			self['spinner'].setText('')
		
	def is_number(self, s):
		try:
			float(s)
			return True
		except ValueError:
			return False

###########################################################################

def main(session, **kwargs):
	session.open(MainScreen)

###########################################################################

def Plugins(**kwargs):
	return PluginDescriptor(
			name='FHEM Haussteuerung',
			description='Plugin zur Steuerung von FHEM',
			where = PluginDescriptor.WHERE_PLUGINMENU,
			icon='fhem.png',
			fnc=main)

class LoadContainerBackgroundThread(threading.Thread):
	def __init__(self, session, sender):
		threading.Thread.__init__(self)
		self.session = session
		self.sender = sender
	def run(self):
		self.sender.container.refreshContainer()
		self.sender.listSelectionChanged()
		self.sender.setSpinner(False)
		self.sender.threadIsRunning = False
		
# This class holds a single FHEM Element			
class FHEMElement(object):
	def __init__(self, name, data):
		self.Name = name
		self.Data = data

	def getLimits(self):
		writeLog('FHEM-debug: %s -- %s' % ('getLimits', self.getType()))
		if self.getType() == 'FHT':
			return THERMO_LIMITS
		elif self.getType() == 'MAX':
			return MAX_LIMITS
		elif self.getType() == 'CUL_HM':
			return THERMO_LIMITS
		elif self.getType() == 'HMCCUDEV':
			return THERMO_LIMITS
		elif self.getType() == 'FS20':
			return THERMO_LIMITS
		elif self.getType() == 'dummy':
			return DUMMY_LIMITS
		else:
			return [0,0]
			
	def getSpecials(self):
		writeLog('FHEM-debug: %s -- %s' % ('getSpecials', self.getType()))
		if self.getType() == 'FHT':
			return BASIC_SPECIALS
		elif self.getType() == 'IT':
			return IT_SPECIALS
		elif self.getType() == 'MAX':
			return MAX_SPECIALS
		elif self.getType() == 'CUL_HM':
			return BASIC_SPECIALS
		elif self.getType() == 'FS20':
			return FS20_SPECIALS
		elif self.getType() == 'FBDECT':
			return BASIC_SPECIALS
		elif self.getType() == 'MQTT_DEVICE':
			return BASIC_SPECIALS
		elif self.getType() == 'MQTT2_DEVICE':
			return BASIC_SPECIALS
		elif self.getType() == 'DOIF' and self.getCmdState() == '':
			return self.getPossibleSets()
		elif self.getType() == 'DOIF':
			return self.getCmdState()	
		elif self.getType() == 'AptToDate':
			return APTTODATE_SPECIALS
		elif self.getType() == 'GHoma':
			return GHoma_SPECIALS
		elif self.getType() == 'Hyperion':
			return Hyperion_SPECIALS
		elif self.getType() == 'HUEDevice':
			return HUEDevice_SPECIALS
		elif self.getType() == 'dummy' and self.getWebcmdstate() == 'state':
			return self.getSetlist()
		elif self.getType() == 'dummy':	
			return self.getWebcmd()
		elif self.getType() == 'pilight_switch':
			return BASIC_SPECIALS
		elif self.getType() == 'LightScene':
			return self.getPossibleSets()
		elif self.getType() == 'readingsProxy':
			return self.getSetlist()
		elif self.getType() == 'WOL':
			return BASIC_SPECIALS
		else:
			return ['']
			
	def getSpecials0(self):
		writeLog('FHEM-debug: %s -- %s' % ('getSpecials0', self.getType()))
		if self.getType() == 'HUEDevice':
			return DIMMER_SPECIALS
		elif self.getType() == 'FS20':
			return DIMMER_SPECIALS
		elif self.getType() == 'Hyperion':
			return DIMMER_SPECIALS
		else:
			return ['']
			
	def getSpecials1(self):
		writeLog('FHEM-debug: %s -- %s' % ('getSpecials1', self.getType()))
		if self.getType() == 'dummy':
			return SWITCH4FOUR_DU1
		elif self.getType() == 'CUL_HM' and self.getModel() in ['HM-LC-SW4-BA-PCB','HM-LC-Sw4-DR','HM-LC-Sw4-SM','HM-LC-SW2-FM','HM-LC-Sw2PB-FM']:
			return self.getChannel1()
		else:
			return ['']
	
	def getSpecials2(self):
		writeLog('FHEM-debug: %s -- %s' % ('getSpecials2', self.getType()))
		if self.getType() == 'dummy':	
			return SWITCH4FOUR_DU2
		elif self.getType() == 'CUL_HM' and self.getModel() in ['HM-LC-SW4-BA-PCB','HM-LC-Sw4-DR','HM-LC-Sw4-SM','HM-LC-SW2-FM','HM-LC-Sw2PB-FM']:
			return self.getChannel2()
		else:
			return ['']
			
	def getSpecials3(self):
		writeLog('FHEM-debug: %s -- %s' % ('getSpecials3', self.getType()))
		if self.getType() == 'dummy':	
			return SWITCH4FOUR_DU3
		elif self.getType() == 'CUL_HM' and self.getModel() in ['HM-LC-SW4-BA-PCB','HM-LC-Sw4-DR','HM-LC-Sw4-SM']:
			return self.getChannel3()
		else:
			return ['']
			
	def getSpecials4(self):
		writeLog('FHEM-debug: %s -- %s' % ('getSpecials4', self.getType()))
		if self.getType() == 'dummy':	
			return SWITCH4FOUR_DU4
		elif self.getType() == 'CUL_HM' and self.getModel() in ['HM-LC-SW4-BA-PCB','HM-LC-Sw4-DR','HM-LC-Sw4-SM']:
			return self.getChannel4()
		else:
			return ['']
	
	def getType(self):
		return str(self.Data['Internals']['TYPE'])
		
	def getRoom(self):
		try:
			return str(self.Data['Attributes']['room']).split(',')
		except:
			return ('')
	
	def getInternals(self):
		return self.Data['Internals']
	
	def getReadings(self):
		return self.Data['Readings']
		
	def getAttributes(self):
		return self.Data['Attributes']
	
	def getChannel1(self):
		try:
			return str(self.Data['Internals']['channel_01']+ ' on').split(':') + str(self.Data['Internals']['channel_01']+ ' off').split(':')
		except:
			return ('')
			
	def getChannel2(self):
		try:
			return str(self.Data['Internals']['channel_02']+ ' on').split(':') + str(self.Data['Internals']['channel_02']+ ' off').split(':')
		except:
			return ('')	
			
	def getChannel3(self):
		try:
			return str(self.Data['Internals']['channel_03']+ ' on').split(':') + str(self.Data['Internals']['channel_03']+ ' off').split(':')
		except:
			return ('')	
			
	def getChannel4(self):
		try:
			return str(self.Data['Internals']['channel_04']+ ' on').split(':') + str(self.Data['Internals']['channel_04']+ ' off').split(':')
		except:
			return ('')	
	
	def getWebcmd(self):
		try:
			return str(self.Data['Attributes']['webCmd']).split(':')
		except:
			return ('')
	
	def getSetlist(self):
		try:
			return str(self.Data['Attributes']['setList']).replace(':',' ').replace(',',' ').replace('state', '').split()
		except:
			return ('')
	
	def getWebcmdstate(self):
		try:
			return str(self.Data['Attributes']['webCmd'])
		except:
			return ('')
		
	def getPossibleSets(self):
		if self.getType() in ['dummy', 'DOIF']:
			try:
				return str(self.Data['PossibleSets']).replace(':noArg',' ').split()
			except:
				return ('')
		elif self.getType() == 'LightScene':
			try:
				return str(self.Data['PossibleSets']).split('scene',1)[1].replace(':',' ').replace(',',' ').split('all')[0].split()
			except:
				return ('')
				
	def getCmdState(self):
		try:
			return str(self.Data['Attributes']['cmdState']).split('|')
		except:
			return ''

	def getAlias(self):
		try:
			if self.Data['Attributes']['alias'] is not None:
				return str(self.Data['Attributes']['alias'])
			else:
				return self.Name
		except:
			return self.Name
		
	def getBri(self):
		try:
			return str(self.Data['Readings']['pct']['Value'])
		except:
			return ('')
			
	def getDesiredTemp(self):
		type = self.getType()
		try:
			if type in ['FHT','CUL_HM']:
				return str(self.Data['Readings']['desired-temp']['Value'])
			elif type in ['HMCCUDEV']:
				return str(self.Data['Readings']['4.SET_TEMPERATURE']['Value'])
			elif type == 'MAX':
				if str(self.Data['Readings']['desiredTemperature']['Value']) == 'off':
					return '0'
				else:	
					return str(self.Data['Readings']['desiredTemperature']['Value'])
			else: 
				return 'no def'
		except:
			return 'no prop'
	
	def getPressure(self):
		type = self.getType()
		try:
			return str(self.Data['Readings']['pressure']['Value'])
		except:
			return 'no prop'
			
	def getHumidity(self):
		type = self.getType()
		try:
			if type in ['FHT']:
				return 'no prop'
			elif type in ['CUL_HM'] and self.getSubType() == 'thermostat':
				return str(self.Data['Readings']['humidity']['Value'])
			elif type in ['CUL_HM'] and self.getModel() == 'HM-TC-IT-WM-W-EU':
				return str(self.Name + '_Climate'['Readings']['humidity']['Value'])
			elif type in ['CUL_HM'] and self.getSubType() == 'THSensor':
				return str(self.Data['Readings']['humidity']['Value'])
			elif type in ['CUL_TX'] and self.getSubType() == 'THSensor':
				return str(self.Data['Readings']['humidity']['Value'])	
			elif type in ['CUL_WS'] and self.getSubType() == 'THSensor':
				return str(self.Data['Readings']['humidity']['Value'])
			elif type in ['Weather']:
				return str(self.Data['Readings']['humidity']['Value'])
			elif type in ['ESPEasy']:
				return str(self.Data['Readings']['humidity']['Value'])
			elif type in ['pilight_temp']:
				return str(self.Data['Readings']['humidity']['Value'])
			elif type in ['MAX']:
				return 'no prop'
			else: 
				return 'no def'
		except:
			return 'no prop'
	
	def getMeasuredTemp(self):
		type = self.getType()
		try:
			retval = '0.0'
			if type in ['FHT']:
				retval = str(self.Data['Readings']['measured-temp']['Value'])
			elif type in ['CUL_HM'] and self.getSubType() == 'thermostat':
				retval = str(self.Data['Readings']['measured-temp']['Value'])
			elif type in ['CUL_HM'] and self.getSubType() == 'THSensor':
				retval = str(self.Data['Readings']['T1']['Value'])
			elif type in ['CUL_HM'] and self.getSubType() == 'THSensor':
				retval = str(self.Data['Readings']['temperature']['Value'])
			elif type in ['HMCCUDEV'] and self.getSubType() == 'thermostat':
				retval = str(self.Data['Readings']['4.ACTUAL_TEMPERATURE']['Value'])
			elif type in ['CUL_TX'] and self.getSubType() == 'THSensor':
				retval = str(self.Data['Readings']['temperature']['Value'])	
			elif type in ['CUL_WS'] and self.getSubType() == 'THSensor':
				retval = str(self.Data['Readings']['temperature']['Value'])
			elif type in ['Weather']:
				retval = str(self.Data['Readings']['temperature']['Value'])	
			elif type in ['MAX']:
				retval = str(self.Data['Readings']['temperature']['Value'])
			elif type in ['ESPEasy']:
				retval = str(self.Data['Readings']['temperature']['Value'])
			elif type in ['pilight_temp']:
				retval = str(self.Data['Readings']['temperature']['Value'])
			elif type in ['FBDECT']:
				retval = str(self.Data['Readings']['temperature']['Value']).replace('C','')
			else: 
				retval = '0.0'
				
			return retval
			
		except:
			return 'no prop'
				
	def getMeasuredTemp1(self):
		type = self.getType()
		try:
			retval = '0.0'
			if type in ['FHT']:
				retval = str(self.Data['Readings']['measured-temp']['Value'])
			elif type in ['CUL_HM'] and self.getSubType() == 'thermostat':
				retval = str(self.Data['Readings']['measured-temp']['Value'])
			elif type in ['CUL_HM'] and self.getSubType() == 'THSensor':
				retval = str(self.Data['Readings']['T2']['Value'])	
			elif type in ['CUL_HM'] and self.getSubType() == 'THSensor':
				retval = str(self.Data['Readings']['temperature']['Value'])
			elif type in ['CUL_WS'] and self.getSubType() == 'THSensor':
				retval = str(self.Data['Readings']['temperature']['Value'])
			elif type in ['MAX']:
				retval = str(self.Data['Readings']['temperature']['Value'])
			else: 
				retval = '0.0'
				
			return retval
			
		except:
			return 'no prop'
			
	def getWind(self):
		type = self.getType()
		try:
			retval = ''
			if type in ['Weather']:
				retval = str(self.Data['Readings']['wind']['Value'])
			else: 
				retval = '0.0'
				
			return retval
			
		except:
			return 'no prop'
	
	def getPresent(self):
		type = self.getType()
		try:
			retval = ''
			if type in ['MQTT2_DEVICE']:
				retval = str(self.Data['Readings']['LWT']['Value'])
			elif type in ['FBDECT']:
				return str(self.Data['Readings']['present']['Value'])
			else: 
				retval = '0.0'
				
			return retval
			
		except:
			return 'no prop'
	
	def getControlmode(self):
		type = self.getType()
		try:
			if type in ['FHT','CUL_HM','MAX']:
				return str(self.Data['Readings']['powerOn']['Value'])
			elif type in ['HMCCUDEV']:
				return str(self.Data['Readings']['4.CONTROL_MODE']['Value'])
			elif type in ['FBDECT']:
				return str(self.Data['Readings']['mode']['Value'])
			else: 
				return 'no def'
		except:
			return 'no prop'
			
	def getActuator(self):
		type = self.getType()
		try:
			if type in ['FHT','CUL_HM']:
				return str(self.Data['Readings']['actuator']['Value'])
			elif type == 'HMCCUDEV':
				return str(self.Data['Readings']['4.VALVE_STATE']['Value'])
			elif type == 'MAX':
				return str(self.Data['Readings']['valveposition']['Value'])
			else: 
				return 'no def'
		except:
			return 'no prop'
			
	def getBattery(self):
		type = self.getType()
		try:
			if type in ['FHT','CUL_HM','MAX']:
				return str(self.Data['Readings']['battery']['Value'])
			elif type in ['HMCCUDEV']:
				return str(self.Data['Readings']['4.BATTERY_STATE']['Value'])
			else: 
				return 'no def'
		except:
			return 'no prop'
					
	def getLastrcv(self):
		type = self.getType()
		try:
			if type in ['FHT','CUL_HM','MAX']:
				return str(self.Data['Readings']['measured-temp']['Time'])
			elif type in ['HMCCUDEV']:
				return str(self.Data['Readings']['state']['Time'])
			else: 
				return 'no def'
		except:
			return 'no prop'
			
	def getLastrcv1(self):
		type = self.getType()
		try:
			if type in ['FHT','CUL_HM','MAX']:
				return str(self.Data['Readings']['T1']['Time'])
			else: 
				return 'no def'
		except:
			return 'no prop'
			
	def getLastrcv2(self):
		type = self.getType()
		try:
			if type in ['FHT','CUL_HM','MAX']:
				return str(self.Data['Readings']['powerOn']['Time'])
			else: 
				return 'no def'
		except:
			return 'no prop'
	
	def getReadingState(self):
		type = self.getType()
		try:
			if type == 'FHT':
				return str(self.Data['Readings']['state']['Value']).replace('measured-temp: ','')
			elif type == 'MAX':
				return str(self.Data['Readings']['state']['Value'])
			elif type == 'FS20':
				return str(self.Data['Readings']['state']['Value'])
			elif type == 'IT':
				return str(self.Data['Readings']['state']['Value'])
			elif type == 'CUL_HM':
				return str(self.Data['Readings']['state']['Value'])
			elif type == 'HMCCUDEV':
				return str(self.Data['Internals']['ccudevstate'])
			elif type == 'MQTT_DEVICE':
				return str(self.Data['Readings']['state']['Value'])
			elif type == 'MQTT2_DEVICE':
				return str(self.Data['Readings']['state']['Value'])
			elif type == 'CUL_TX':
				return ''
			elif type == 'CUL_WS':
				return self.getMeasuredTemp()
			elif type == 'FBDECT':
				return str(self.Data['Readings']['state']['Value']).replace('set_','')
			elif type == 'DOIF':
				return str(self.Data['Readings']['state']['Value'])
			elif type == 'FRITZBOX':
				return str(self.Data['Readings']['state']['Value'])
			elif type == 'CUL':
				return str(self.Data['Readings']['state']['Value'])
			elif type == 'notify':
				return str(self.Data['Readings']['state']['Value'])
			elif type == 'AptToDate':
				return str(self.Data['Readings']['state']['Value'])
			elif type == 'GHoma':
				return str(self.Data['Readings']['state']['Value'])	
			elif type == 'Hyperion':
				return str(self.Data['Readings']['state']['Value'])
			elif type == 'HUEDevice' and self.getGroup() == 'HUEGroup':
				return str('dim') + str(self.Data['Readings']['pct']['Value'] + '%')
			elif type == 'HUEDevice':
				return str(self.Data['Readings']['state']['Value'])
			elif type == 'dummy':
				return str(self.Data['Internals']['STATE'])
			elif type == 'ESPEasy':
				return str(self.Data['Readings']['state']['Value'])
			elif type == 'pilight_temp':
				return str(self.Data['Readings']['state']['Value'])
			elif type == 'pilight_switch':
				return str(self.Data['Readings']['state']['Value'])
			elif type == 'LightScene':
				return str(self.Data['Readings']['state']['Value'])
			elif type == 'readingsProxy':
				return str(self.Data['Readings']['state']['Value'])
			elif type == 'PRESENCE':
				return str(self.Data['Readings']['state']['Value'])
			elif type == 'WOL':
				return str(self.Data['Readings']['state']['Value'])
			elif type == 'SYSMON':
				return str(self.Data['Internals']['STATE'])
			else: 
				return ''
		except:
			return 'no prop'
	
	def getUpdateAvState(self):
		type = self.getType()
		try:
			if type == 'AptToDate':
				return str(self.Data['Readings']['updatesAvailable']['Value'])	
			else: 
				return ''
		except:
			return 'no prop'
	
	def getRepoSync(self):
		type = self.getType()
		try:
			if type == 'AptToDate':
				return str(self.Data['Readings']['repoSync']['Value'])	
			else: 
				return ''
		except:
			return 'no prop'
			
	def getCPUfreq(self):
		type = self.getType()
		try:
			if type == 'SYSMON':
				return str(self.Data['Readings']['cpu_freq']['Value'])	
			else: 
				return ''
		except:
			return 'no prop'
		
	def getCPUtemp(self):
		type = self.getType()
		try:
			if type == 'SYSMON':
				return str(self.Data['Readings']['cpu_temp']['Value'])	
			else: 
				return ''
		except:
			return 'no prop'
			
	def getUptime(self):
		type = self.getType()
		try:
			if type == 'SYSMON':
				return str(self.Data['Readings']['fhemuptime_text']['Value'])	
			else: 
				return ''
		except:
			return 'no prop'
			
	def getENERGYCurrent(self):
		type = self.getType()
		try:
			if type == 'MQTT2_DEVICE':
				return str(self.Data['Readings']['ENERGY_Current']['Value'])
			elif type == 'MQTT_DEVICE':
				return str(self.Data['Readings']['ENERGY_Current']['Value'])
			else: 
				return ''
		except:
			return 'no prop'
	
	def getENERGYPower(self):
		type = self.getType()
		try:
			if type == 'MQTT2_DEVICE':
				return str(self.Data['Readings']['ENERGY_Power']['Value'])
			elif type == 'MQTT_DEVICE':
				return str(self.Data['Readings']['ENERGY_Power']['Value'])
			elif type == 'FBDECT':
				return str(self.Data['Readings']['power']['Value'])
			else: 
				return ''
		except:
			return 'no prop'
	
	def getENERGYToday(self):
		type = self.getType()
		try:
			if type == 'MQTT2_DEVICE':
				return str(self.Data['Readings']['ENERGY_Today']['Value'])
			elif type == 'MQTT_DEVICE':
				return str(self.Data['Readings']['ENERGY_Today']['Value'])
			else: 
				return ''
		except:
			return 'no prop'
			
	def getENERGYTotal(self):
		type = self.getType()
		try:
			if type == 'MQTT2_DEVICE':
				return str(self.Data['Readings']['ENERGY_Total']['Value'])
			elif type == 'MQTT_DEVICE':
				return str(self.Data['Readings']['ENERGY_Total']['Value'])
			elif type == 'FBDECT':
				return str(self.Data['Readings']['energy']['Value'])
			else: 
				return ''
		except:
			return 'no prop'
	
	def getInternalsState(self):
		type = self.getType()
		try:
			if type == 'FHT':
				return str(self.Data['Internals']['protLastRcv']['Value']).replace('measured-temp: ','')
			elif type == 'MAX':
				return str(self.Data['Internals']['protLastRcv']['Value'])
			elif type == 'FS20':
				return str(self.Data['Internals']['protLastRcv']['Value'])
			elif type == 'CUL_HM':
				return str(self.Data['Internals']['protLastRcv']['Value'])
			elif type == 'HMCCUDEV':
				return str(self.Data['Internals']['ccudevstate']['Value'])
			elif type == 'CUL_WS':
				return self.getMeasuredTemp()
			elif type == 'FBDECT':
				return str(self.Data['Internals']['protLastRcv']['Value']).replace('set_','') 
			else: 
				return 'no def'
		except:
			return 'no prop'
	
	def getSubType(self):
		type = self.getType()
		if type == 'CUL_HM':
			try:
				subtype = str(self.Data['Attributes']['subType'])
			except:
				subtype = 'unknown'
			return subtype
		elif type == 'HMCCUDEV':
			try:
				subtype = str(self.Data['Attributes']['subType'])
			except:
				subtype = 'unknown'
		elif type == 'FHT':
			return 'thermostat'
		elif type == 'FS20':
			return 'switch'
		elif type == 'MAX':
			return 'thermostat'
		elif type == 'CUL_TX':	
			return 'THSensor'	
		elif type == 'CUL_WS':	
			return 'THSensor'
		elif type == 'FBDECT':	
			return str(self.Data['Internals']['props'])	
		else:
			return 'unknown'
	
	def getModel(self):
		type = self.getType()
		if type == 'CUL_HM':
			try:
				subtype = str(self.Data['Attributes']['model'])
			except:
				subtype = 'unknown'
			return subtype
		elif type == 'HMCCUDEV':
			return str(self.Data['Internals']['ccutype'])
		else:
			return 'unknown'
	
	def getGroup(self):
		type = self.getType()
		if type == 'HUEDevice':
			try:
				subtype = str(self.Data['Attributes']['group'])
			except:
				subtype = 'unknown'
			return subtype
		else:
			return 'unknown'
	
	def getUpdateableProperty(self):
		type = self.getType()
		if type in ['FHT']:
			return 'desired-temp'
		elif type == 'CUL_HM' and self.getSubType() == 'switch':
			return ''
		elif type == 'CUL_HM' and self.getSubType() == 'thermostat':
			return 'desired-temp'
		elif type == 'HMCCUDEV' and self.getSubType() == 'thermostat':
			return 'control'
		elif type == 'MAX':
			return 'desiredTemperature'
		elif type == 'FS20':
			return ''
		elif type == 'FBDECT':
			return ''
		elif type == 'IT':
			return ''	
		elif type == 'MQTT_DEVICE':
			return ''
		elif type == 'MQTT2_DEVICE':
			return ''
		elif type == 'DOIF':
			return ''
		elif type == 'AptToDate':
			return ''
		elif type == 'GHoma':
			return ''
		elif type == 'Hyperion':
			return ''
		elif type == 'HUEDevice':
			return ''
		elif type == 'dummy':
			return ''
		elif type == 'pilight_switch':
			return ''
		elif type == 'LightScene':
			return ''
		elif type == 'readingsProxy':
			return ''
		elif type == 'WOL':
			return ''
		
	def getUpdateCommand(self):
		type = self.getType()
		if type in ['FHT']:
			return '/fhem?XHR=1&cmd=set %s %s ' % (self.Name,  self.getUpdateableProperty())
		elif type == 'CUL_HM' and self.getModel() in ['HM-LC-SW4-BA-PCB','HM-LC-Sw4-DR','HM-LC-Sw4-SM','HM-LC-SW2-FM','HM-LC-Sw2PB-FM']:
			return '/fhem?XHR=1&cmd=set %s' % (self.getUpdateableProperty())
		elif type == 'CUL_HM' and self.getSubType() == 'switch':
			return '/fhem?XHR=1&cmd=set %s %s ' % (self.Name, self.getUpdateableProperty())		
		elif type == 'CUL_HM' and self.getModel() == 'HM-CC-RT-DN':
			return '/fhem?XHR=1&cmd=set %s %s ' % (self.Name + '_Clima', self.getUpdateableProperty())
		elif type == 'CUL_HM' and self.getModel() == 'HM-TC-IT-WM-W-EU':
			return '/fhem?XHR=1&cmd=set %s %s ' % (self.Name + '_Climate', self.getUpdateableProperty())
		elif type == 'HMCCUDEV' and self.getSubType() == 'thermostat':
			return '/fhem?XHR=1&cmd=set %s %s ' % (self.Name, self.getUpdateableProperty())
		elif type == 'MAX':
			return '/fhem?XHR=1&cmd=set %s %s ' % (self.Name, self.getUpdateableProperty())
		elif type == 'FS20':
			return '/fhem?XHR=1&cmd=set %s %s ' % (self.Name, self.getUpdateableProperty())
		elif type == 'FBDECT':
			return '/fhem?XHR=1&cmd=set %s %s ' % (self.Name, self.getUpdateableProperty())
		elif type == 'IT':
			return '/fhem?XHR=1&cmd=set %s %s ' % (self.Name, self.getUpdateableProperty())
		elif type == 'MQTT_DEVICE':
			return '/fhem?XHR=1&cmd=set %s %s ' % (self.Name, self.getUpdateableProperty())
		elif type == 'MQTT2_DEVICE':
			return '/fhem?XHR=1&cmd=set %s %s ' % (self.Name, self.getUpdateableProperty())
		elif type == 'DOIF':
			return '/fhem?XHR=1&cmd=set %s %s ' % (self.Name, self.getUpdateableProperty())
		elif type == 'AptToDate':
			return '/fhem?XHR=1&cmd=set %s %s ' % (self.Name, self.getUpdateableProperty())
		elif type == 'GHoma':
			return '/fhem?XHR=1&cmd=set %s %s ' % (self.Name, self.getUpdateableProperty())
		elif type == 'Hyperion':
			return '/fhem?XHR=1&cmd=set %s %s ' % (self.Name, self.getUpdateableProperty())
		elif type == 'HUEDevice':
			return '/fhem?XHR=1&cmd=set %s %s ' % (self.Name, self.getUpdateableProperty())
		elif type == 'dummy':
			return '/fhem?XHR=1&cmd=set %s %s ' % (self.Name, self.getUpdateableProperty())
		elif type == 'pilight_switch':
			return '/fhem?XHR=1&cmd=set %s %s ' % (self.Name, self.getUpdateableProperty())
		elif type == 'LightScene':
			return '/fhem?XHR=1&cmd=set %s scene %s ' % (self.Name, self.getUpdateableProperty())
		elif type == 'readingsProxy':
			return '/fhem?XHR=1&cmd=set %s %s ' % (self.Name, self.getUpdateableProperty())
		elif type == 'WOL':
			return '/fhem?XHR=1&cmd=set %s %s ' % (self.Name, self.getUpdateableProperty())
			
	def getHMChannels(self):
		type = self.getType()
		retval = []
		if type == 'CUL_HM':
			data = self.getInternals()
			for s in ['channel_01','channel_02','protState']:
				if data.get(s):
					retval.append(s)
		return retval
			
# This class holds a room			
class FHEMElementCollection(object):
	def __init__(self, type):
		self.Type = type
		self.worker = WebWorker()
		self.Elements = []
		self.data = None
		self.reload()
		
	def reload(self):
		self.data = self.worker.getJson(self.Type, 0)
		if self.data is not None:
			for element in self.data['Results']:
				if str(element['state']) != '???':
					eldata = self.worker.getJson(element['name'], 1)
					if self.Type == 'CUL_HM':
						try:
							el = FHEMElement(str(element['name']), eldata['Results'][0])
							channels = el.getHMChannels()
							if channels:
								self.Elements.append(el)
						except:
							writeLog('FHEM-debug: %s -- %s' % ('reload, error loading', element['name']))
					else:
						try:
							el = FHEMElement(str(element['name']), eldata['Results'][0])
							self.Elements.append(el)
						except:
							writeLog('FHEM-debug: %s -- %s' % ('reload, error loading', element['name']))
					
	def refresh(self):
		for element in self.Elements:
			self.loadElement(element.Name)
		
	def loadElement(self, name):
		try:
			if self.Elements is not None:
				for element in self.Elements:
					if element.Name == name:
						json = self.worker.getJson(name, 1)
						element.Data = json['Results'][0]
		except:
			writeLog('FHEM-debug: %s -- %s' % ('reload, error loading', element.Data))
	
	def getData(self):
		return self.Data
		
	def getElementsCount(self):
		return len(self.Elements)
		
	def getElementByName(self, name):
		for element in self.Elements:
			if element.Name == name:
				return element
		
	def updateElement(self, command, value):
		self.worker.setPropertyValue(command, value)
		
	
		
		
class FHEMContainer(object):
	def __init__(self):
		self.List = []
		
	def reloadContainer(self):
		for element in ELEMENTS:
			self.List.append(FHEMElementCollection(element))
			
	def refreshContainer(self):
		for col in self.List:
			col.refresh()
		
	def getElementByName(self, name):
		containerId = 0
		selectedElement = None
		for containerId, element in enumerate(self.List):
			if selectedElement is None:
				selectedElement = element.getElementByName(name)
				
		return ([selectedElement, containerId])
	
	def getTypes(self):
		list = []
		for fhemelementcollection in self.List:
			if fhemelementcollection.Type not in list and fhemelementcollection.getElementsCount() > 0:
					list.append(fhemelementcollection.Type)
		return list
	
	def getRooms(self):
		list = []
		for fhemelementcollection in self.List:
			for element in fhemelementcollection.Elements:
				rooms = element.getRoom()
				for room in rooms:
					if room not in list:
						list.append(room)
						list.sort()
		return list	
	
	def getElementsByType(self, typearray):
		list = []
		for fhemelementcollection in self.List:
			for element in fhemelementcollection.Elements:
				if element.getType() in typearray:
					list.append(element)
		return list
	
	def getElementsByRoom(self, roomarray):
		list = []
		for fhemelementcollection in self.List:
			for element in fhemelementcollection.Elements:
				rooms = element.getRoom()
				for room in rooms:
					if room in roomarray:
						list.append(element)
		return list
		
	def updateElementByName(self, elementname, value):
		containerId = 0
		selectedElement = None
		for containerId, element in enumerate(self.List):
			if selectedElement is None:
				selectedElement = element.getElementByName(elementname)
				
		self.List[containerId].updateElement(selectedElement.getUpdateCommand(), value)
		
		
class WebWorker(object):
	
	def __init__(self):
	
		self.hasError = False
	
		self.httpres = str(config.fhem.httpresponse.value)
		self.server = '%d.%d.%d.%d' % tuple(config.fhem.serverip.value)
		self.port = int(config.fhem.port.value)
		self.username = str(config.fhem.username.value)
		self.password = str(config.fhem.password.value)
		self.csrfswitch = str(config.fhem.csrfswitch.value)
		self.csrftoken = str(config.fhem.csrftoken.value)
		
		self.Address = self.server + ':' + str(self.port)
		self.Prefix = ['/fhem?XHR=1&cmd=jsonlist+','/fhem?XHR=1&cmd=jsonlist2+']
		self.isAuth = len(self.username) + len(self.password)
		self.basicToken = '&fwcsrf=' + self.csrftoken
		
		if self.isAuth != 0: 
			self.credentialss = self.username + ':' + self.password
			self.credentialsb = self.credentialss.encode('utf-8')
			self.credentials64 = base64.b64encode(self.credentialsb).decode('ascii')
			self.headers = { 'Authorization' : 'Basic %s' %  self.credentials64 }
		
	def getHtml(self, elements, listtype):
		if self.httpres == 'Http':
			try:
				conn = httplib.HTTPConnection(self.Address, timeout=10)
				if self.isAuth != 0:
					if self.csrfswitch == 'On':
						conn.request('GET', self.Prefix[listtype] + elements + self.basicToken, headers = self.headers)
					elif self.csrfswitch == 'Off':
						conn.request('GET', self.Prefix[listtype] + elements, headers = self.headers)
				else:
					conn.request('GET', self.Prefix[listtype] + elements)
			
				response = conn.getresponse()
				if response.status != 200:
					writeLog('FHEM-debug: %s -- %s' % ('response', str(response.status) + ' --- reason: ' + response.reason))
				
				self.hasError = False
				return response
			except:
				self.hasError = True
				return None
				
		else:
			try:
				conn = httplib.HTTPSConnection(self.Address, timeout=10)
				if self.isAuth != 0:
					if self.csrfswitch == 'On':
						conn.request('GET', self.Prefix[listtype] + elements + self.basicToken, headers = self.headers)
					elif self.csrfswitch == 'Off':
						conn.request('GET', self.Prefix[listtype] + elements, headers = self.headers)
				else:
					conn.request('GET', self.Prefix[listtype] + elements)
			
				response = conn.getresponse()
				if response.status != 200:
					writeLog('FHEM-debug: %s -- %s' % ('response', str(response.status) + ' --- reason: ' + response.reason))
				
				self.hasError = False
				return response
			except:
				self.hasError = True
				return None
		
	def getJson(self, elements, listtype):
		try:
			jsonObj = json.loads(self.getHtml(elements, listtype).read().replace('\n', ''))
			# write jsondata also to file in fhemfolder, when switch is on
			writeJson('FHEM-jsonDebug: %s -- %s' % ('response', str(jsonObj)))
			return jsonObj
		except ValueError:
			# print "error loading JSON"
			writeLog("error loading JSON")
		
	def setPropertyValue(self, command, value):
		if self.httpres == 'Http':
			conn = httplib.HTTPConnection(self.Address)
			message = command + value
			writeLog('FHEM-debug: %s -- %s' % ('Message to send:', message))
			message = message.replace(' ','%20')

		

			if self.isAuth != 0:
				if self.csrfswitch == 'On':
					conn.request('GET', message + self.basicToken, headers = self.headers)
				elif self.csrfswitch == 'Off':
					conn.request('GET', message, headers = self.headers)	
			else:
				conn.request('GET', message)

			response = conn.getresponse()
			if response.status != 200:
				writeLog('FHEM-debug: %s -- %s' % ('response', str(response.status) + ' --- reason: ' + response.reason))
				self.hasError = True
		
			writeLog('FHEM-debug: %s -- %s' % ('Message sent', 'Result: ' + str(response.status) + ' Reason: ' + response.reason))			
			self.hasError = False
		
		else:
			conn = httplib.HTTPSConnection(self.Address)
			message = command + value
			writeLog('FHEM-debug: %s -- %s' % ('Message to send:', message))
			message = message.replace(' ','%20')

		

			if self.isAuth != 0:
				if self.csrfswitch == 'On':
					conn.request('GET', message + self.basicToken, headers = self.headers)
				elif self.csrfswitch == 'Off':
					conn.request('GET', message, headers = self.headers)	
			else:
				conn.request('GET', message)

			response = conn.getresponse()
			if response.status != 200:
				writeLog('FHEM-debug: %s -- %s' % ('response', str(response.status) + ' --- reason: ' + response.reason))
				self.hasError = True
		
			writeLog('FHEM-debug: %s -- %s' % ('Message sent', 'Result: ' + str(response.status) + ' Reason: ' + response.reason))	
			self.hasError = False

############################################     Config    #################################

class FHEM_Setup(Screen, ConfigListScreen):
	desktopSize = getDesktop(0).size()
	if desktopSize.width() >= 1920:
		skin = '''
		<screen position='300,600' size='660,470' title='FHEM Settings' >
			<ePixmap pixmap='/usr/lib/enigma2/python/Plugins/Extensions/fhem/buttons/red.png' position='0,460' size='140,40' alphatest='on' />
			<ePixmap pixmap='/usr/lib/enigma2/python/Plugins/Extensions/fhem/buttons/green.png' position='140,460' size='140,40' alphatest='on' />
			<ePixmap pixmap='/usr/lib/enigma2/python/Plugins/Extensions/fhem/buttons/yellow.png' position='280,460' size='140,40' alphatest='on' />
			<ePixmap pixmap='/usr/lib/enigma2/python/Plugins/Extensions/fhem/buttons/blue.png' position='420,460' size='140,40' alphatest='on' />
			<widget source='key_red' render='Label' position='0,433' zPosition='1' size='140,40' font='Regular;21' halign='center' valign='center' backgroundColor='#9f1313' transparent='1' />
			<widget source='key_green' render='Label' position='140,433' zPosition='1' size='140,40' font='Regular;21' halign='center' valign='center' backgroundColor='#1f771f' transparent='1' />
			<widget source='key_yellow' render='Label' position='280,433' zPosition='1' size='140,40' font='Regular;21' halign='center' valign='center' backgroundColor='#1f771f' transparent='1' />
			<widget source='key_blue' render='Label' position='420,433' zPosition='1' size='140,40' font='Regular;21' halign='center' valign='center' backgroundColor='#1f771f' transparent='1' />
			<widget source='label' render='Label' position='10,10' size='640,40' font='Regular;24' backgroundColor='#25062748' transparent='1'  />
			<widget name='config' position='10,35' zPosition='2' size='640,390' itemHeight='38' font='Regular;24' scrollbarMode='showOnDemand' scrollbarWidth='3' />
		</screen>'''
	else:
		skin = '''
		<screen position='5,265' size='660,320' title='FHEM Settings' >
			<ePixmap pixmap='/usr/lib/enigma2/python/Plugins/Extensions/fhem/buttons/red.png' position='0,312' size='140,40' alphatest='on' />
			<ePixmap pixmap='/usr/lib/enigma2/python/Plugins/Extensions/fhem/buttons/green.png' position='140,312' size='140,40' alphatest='on' />
			<ePixmap pixmap='/usr/lib/enigma2/python/Plugins/Extensions/fhem/buttons/yellow.png' position='280,312' size='140,40' alphatest='on' />
			<ePixmap pixmap='/usr/lib/enigma2/python/Plugins/Extensions/fhem/buttons/blue.png' position='420,312' size='140,40' alphatest='on' />
			<widget source='key_red' render='Label' position='0,285' zPosition='1' size='140,40' font='Regular;21' halign='center' valign='center' backgroundColor='#9f1313' transparent='1' />
			<widget source='key_green' render='Label' position='140,285' zPosition='1' size='140,40' font='Regular;21' halign='center' valign='center' backgroundColor='#1f771f' transparent='1' />
			<widget source='key_yellow' render='Label' position='280,285' zPosition='1' size='140,40' font='Regular;21' halign='center' valign='center' backgroundColor='#1f771f' transparent='1' />
			<widget source='key_blue' render='Label' position='420,285' zPosition='1' size='140,40' font='Regular;21' halign='center' valign='center' backgroundColor='#1f771f' transparent='1' />
			<widget source='label' render='Label' position='10,10' size='640,40' font='Regular;24' backgroundColor='#25062748' transparent='1'  />
			<widget name='config' position='10,50' zPosition='2' size='640,220' itemHeight='38' font='Regular;24' scrollbarMode='showOnDemand' scrollbarWidth='3' />
		</screen>'''
		
		
	def __init__(self, session):
		Screen.__init__(self, session)
		# for the skin: first try MediaPlayerSettings, then Setup, this allows individual skinning
		#self.skinName = ['PicturePlayerSetup', 'Setup' ]
		self.setup_title = _('Settings')
		self.onChangedEntry = [ ]
		self.session = session

		self['actions'] = ActionMap(['SetupActions','FHEM_Actions'],
			{
				'cancel': self.keyCancel,
				'save': self.keySave,
				'ok': self.keySave,
				'key_yellow': self.getToken,
				'key_blue': self.restartServer,
			}, -2)

		self['key_red'] = StaticText(_('Cancel'))
		self['key_green'] = StaticText(_('OK'))
		self['key_yellow'] = StaticText(_('getToken'))
		self['key_blue'] = StaticText(_('restartServer'))
		self['label'] = StaticText('')

		self.list = []
		ConfigListScreen.__init__(self, self.list, session = self.session, on_change = self.changedEntry)
		self.createSetup()
		self.onLayoutFinish.append(self.layoutFinished)
		self.httpres = str(config.fhem.httpresponse.value)
		self.server = '%d.%d.%d.%d' % tuple(config.fhem.serverip.value)
		self.port = int(config.fhem.port.value)
		self.Address = self.server + ':' + str(self.port)
		self.username = str(config.fhem.username.value)
		self.password = str(config.fhem.password.value)
		self.csrfswitch = str(config.fhem.csrfswitch.value)
		self.csrftoken = str(config.fhem.csrftoken.value)
		self.isAuth = len(self.username) + len(self.password)
		self.basicToken = '&fwcsrf=' + self.csrftoken
		
		if self.isAuth != 0: 
			self.credentialss = self.username + ':' + self.password
			self.credentialsb = self.credentialss.encode('utf-8')
			self.credentials64 = base64.b64encode(self.credentialsb).decode('ascii')
			self.headers = { 'Authorization' : 'Basic %s' %  self.credentials64, 'Connection': 'close' }

	def layoutFinished(self):
		self.setTitle(self.setup_title)

	def createSetup(self):
		self.list = []
		self.list.append(getConfigListEntry(_('Http/Https'), config.fhem.httpresponse))
		self.list.append(getConfigListEntry(_('Server IP'), config.fhem.serverip))
		self.list.append(getConfigListEntry(_('Port'), config.fhem.port))
		self.list.append(getConfigListEntry(_('Username'), config.fhem.username))
		self.list.append(getConfigListEntry(_('Password'), config.fhem.password))
		self.list.append(getConfigListEntry(_('CsrfStatus'), config.fhem.csrfswitch))
		self.list.append(getConfigListEntry(_('CsrfToken'), config.fhem.csrftoken))
		self.list.append(getConfigListEntry(_('Group Elements By'), config.fhem.grouping))
		self.list.append(getConfigListEntry(_('logfile'), config.fhem.logfileswitch))
		self.list.append(getConfigListEntry(_('jsondata to file/ for research'), config.fhem.jsondataswitch))
		self['config'].list = self.list
		self['config'].l.setList(self.list)

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		
	def getToken(self):
		if self.isAuth != 0:
			if self.httpres == 'Http':
				try:
					r = requests.get('http://' + self.Address, headers = self.headers)
					ct = r.headers['X-FHEM-csrfToken']
					config.fhem.csrftoken.setValue(ct)
					writeLog('FHEM-debug: %s -- %s' % ('Message CSRFTOKEN: ', ct))
					self.session.open(MessageBox,_('X-FHEM-csrfToken: ') + ct,  type=MessageBox.TYPE_INFO)
				except KeyError:
					self.session.open(MessageBox,_('no X-FHEM-csrfToken present'),  type=MessageBox.TYPE_INFO)
			
			else:
				try:
					r = requests.get('https://' + self.Address, headers = self.headers, verify=False)
					ct = r.headers['X-FHEM-csrfToken']
					config.fhem.csrftoken.setValue(ct)
					writeLog('FHEM-debug: %s -- %s' % ('Message CSRFTOKEN: ', ct))
					self.session.open(MessageBox,_('X-FHEM-csrfToken: ') + ct,  type=MessageBox.TYPE_INFO)
				except KeyError:
					self.session.open(MessageBox,_('no X-FHEM-csrfToken present'),  type=MessageBox.TYPE_INFO)
		else:
			self.session.open(MessageBox,_('no logindetails present'),  type=MessageBox.TYPE_INFO)
		
	def restartServer(self):
		if self.isAuth != 0:
			if self.csrfswitch == 'static':
				if self.httpres == 'Http':
					try:
						r = requests.post('http://' + self.Address + '/fhem?cmd=shutdown+restart' + self.basicToken, headers = self.headers)
					except IOError:
						self.session.open(MessageBox,_('restart server'),  type=MessageBox.TYPE_INFO,timeout = 20)
				else:
					try:
						r = requests.post('https://' + self.Address + '/fhem?cmd=shutdown+restart' + self.basicToken, headers = self.headers, verify=False)
					except IOError:
						self.session.open(MessageBox,_('restart server'),  type=MessageBox.TYPE_INFO,timeout = 20)
			else:
				if self.httpres == 'Http':
					try:
						r = requests.post('http://' + self.Address + '/fhem?cmd=shutdown+restart', headers = self.headers)
					except IOError:
						self.session.open(MessageBox,_('restart server'),  type=MessageBox.TYPE_INFO,timeout = 20)
				else:
					try:
						r = requests.post('https://' + self.Address + '/fhem?cmd=shutdown+restart', headers = self.headers, verify=False)
					except IOError:
						self.session.open(MessageBox,_('restart server'),  type=MessageBox.TYPE_INFO,timeout = 20)
		else:
			if self.httpres == 'Http':
				try:
					r = requests.post('http://' + self.Address + '/fhem?cmd=shutdown+restart')
				except IOError:
					self.session.open(MessageBox,_('restart server'),  type=MessageBox.TYPE_INFO,timeout = 20)
			else:
				try:
					r = requests.post('https://' + self.Address + '/fhem?cmd=shutdown+restart', verify=False)
				except IOError:
					self.session.open(MessageBox,_('restart server'),  type=MessageBox.TYPE_INFO,timeout = 20)
	
	# for summary:
	def changedEntry(self):
		for x in self.onChangedEntry:
			x()

	def getCurrentEntry(self):
		return self['config'].getCurrent()[0]

	def getCurrentValue(self):
		return str(self['config'].getCurrent()[1].getText())

	def createSummary(self):
		from Screens.Setup import SetupSummary
		return SetupSummary		
		
		
#############################   custom elements #######################

class ElementList(GUIComponent, object):
	GUI_WIDGET = eListbox
	def __init__(self):
		GUIComponent.__init__(self)
		#self.scale = AVSwitch().getFramebufferScale()
		self.l = eListboxPythonMultiContent()
		desktopSize = getDesktop(0).size()
		if desktopSize.width() >= 1920:
			self.l.setFont(0, gFont('Regular', 23))
		else:
			self.l.setFont(0, gFont('Regular', 20))
		self.l.setFont(1, gFont('Regular', 19))
		self.l.setBuildFunc(self.buildEntry)
		self.l.setItemHeight(25)
		#self.onSelectionChanged = []
		selChangedCB=None
		self.onSelChanged = [ ]
		if selChangedCB is not None:
			self.onSelChanged.append(selChangedCB)
		self.pixmapCache = {}
		self.selectedID = None
		self.ListMode = 0
		self.l.setSelectableFunc(self.isSelectable)
		self.list = []
		return

	def setList(self, list, mode):
		self.ListMode = mode
		if self.ListMode == 0:
			self.l.setItemHeight(30)
		elif self.ListMode == 1:
			self.l.setItemHeight(30)
		elif self.ListMode == 2:
			self.l.setItemHeight(30)
		elif self.ListMode == 3:
			self.l.setItemHeight(30)

		self.l.setBuildFunc(self.buildEntry)
		self.l.setList(list)
		self.list = list
		
	def buildEntry(self, data):
		width = self.l.getItemSize().width()
		res = [None]
		desktopSize = getDesktop(0).size()
		if desktopSize.width() >= 1920:
			if self.ListMode == 0: #byType
				res.append((eListboxPythonMultiContent.TYPE_TEXT, 10, 5,(width - 20), 25, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, str(data)))
			elif self.ListMode == 1: #byRoom
				res.append((eListboxPythonMultiContent.TYPE_TEXT, 10, 5,(width - 20), 25, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, str(data)))
			elif self.ListMode == 2:
				res.append((eListboxPythonMultiContent.TYPE_TEXT, 10, 5,(width - 20) / 2, 25, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, str(data.getAlias())))
				res.append((eListboxPythonMultiContent.TYPE_TEXT, 10 + ((width - 20) / 2), 5, (width - 20) / 2, 25,	0, RT_HALIGN_RIGHT | RT_VALIGN_CENTER, str(data.getReadingState())))
			elif self.ListMode == 3:
				res.append((eListboxPythonMultiContent.TYPE_TEXT, 10, 5,(width - 20) + 50 / 2, 25, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, str(data[0])))
				res.append((eListboxPythonMultiContent.TYPE_TEXT, 10 + ((width - 20) / 3) + 100, 5, ((width - 20) / 2) - 5, 25,	0, RT_HALIGN_RIGHT | RT_VALIGN_CENTER, str(data[1])))
		
			return res
		else:
			if self.ListMode == 0: #byType
				res.append((eListboxPythonMultiContent.TYPE_TEXT, 10, 5,(width - 20), 25, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, str(data)))
			elif self.ListMode == 1: #byRoom
				res.append((eListboxPythonMultiContent.TYPE_TEXT, 10, 5,(width - 20), 25, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, str(data)))
			elif self.ListMode == 2:
				res.append((eListboxPythonMultiContent.TYPE_TEXT, 10, 5,(width - 20) / 2, 25, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, str(data.getAlias())))
				res.append((eListboxPythonMultiContent.TYPE_TEXT, 10 + ((width - 20) / 2), 5, (width - 20) / 2, 25,	0, RT_HALIGN_RIGHT | RT_VALIGN_CENTER, str(data.getReadingState())))
			elif self.ListMode == 3:
				res.append((eListboxPythonMultiContent.TYPE_TEXT, 10, 5,(width - 20) + 50 / 2, 25, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, str(data[0])))
				res.append((eListboxPythonMultiContent.TYPE_TEXT, 10 + ((width - 20) / 3) + 65, 5, ((width - 20) / 2) + 10, 25,	0, RT_HALIGN_RIGHT | RT_VALIGN_CENTER, str(data[1])))
			
			return res
		
	def isSelectable(self, data):
		return True
		
	def connectSelChanged(self, func):
		if not self.onSelChanged.count(func):
			self.onSelChanged.append(func)
			
	def disconnectSelChanged(self, func):
		self.onSelChanged.remove(func)
			
	def selectionChanged(self):
		for x in self.onSelChanged:
			if x is not None:
				try:
					x()
				except: # FIXME!!!
					print 'FIXME in ElementList.selectionChanged'
					pass
		
	def getCurrentSelection(self):
		cur = self.l.getCurrentSelection()
		return cur[0]
		
	def postWidgetCreate(self, instance):
		instance.setContent(self.l)
		instance.selectionChanged.get().append(self.selectionChanged)
		self.instance.setWrapAround(True)
		
	def preWidgetRemove(self, instance):
		instance.selectionChanged.get().remove(self.selectionChanged)
		instance.setContent(None)
		return
		
	def up(self):
		if self.instance is not None:
			self.instance.moveSelection(self.instance.moveUp)
		return
		
	def down(self):
		if self.instance is not None:
			self.instance.moveSelection(self.instance.moveDown)
		return
		
	def pageUp(self):
		if self.instance is not None:
			self.instance.moveSelection(self.instance.pageUp)
		return
		
	def pageDown(self):
		if self.instance is not None:
			self.instance.moveSelection(self.instance.pageDown)
		return
		
	def moveUp(self):
		if self.instance is not None:
			self.instance.moveSelection(self.instance.moveUp)
		return
		
	def moveDown(self):
		if self.instance is not None:
			self.instance.moveSelection(self.instance.moveDown)
		return
		
	def getCurrentIndex(self):
		return self.instance.getCurrentIndex()
		
	def updateListObject(self, row):
		index = self.getCurrentIndex()
		tmp = self.list[index]
		self.list[index] = (row,)
		self.l.invalidateEntry(index)
		
	def moveToIndex(self, index):
		self.instance.moveSelectionTo(index)
		
	def setMode(self, mode):
		self.mode = mode
		
	def getList(self):
		return self.list
		
	def selectionEnabled(self, enabled):
		if self.instance is not None:
			self.instance.setSelectionEnable(enabled)
		
