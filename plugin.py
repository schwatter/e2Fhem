
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
	
from enigma import getDesktop, eTimer, eListbox, eLabel, eListboxPythonMultiContent, gFont, eRect, eSize, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_HALIGN_CENTER, RT_VALIGN_CENTER, RT_VALIGN_TOP, RT_WRAP, BT_SCALE
from Components.GUIComponent import GUIComponent

ELEMENTS = ["MAX","FHT","FS20","CUL_HM","IT","CUL_TX","CUL_WS","FBDECT","Weather","MQTT_DEVICE","MQTT2_DEVICE","DOIF","FRITZBOX","CUL","notify","AptToDate","GHoma","Hyperion"] #actual supported types - leave as it is

MAX_LIMITS = [5.0, 30.0]
MAX_SPECIALS = ["eco","comfort","boost","auto","off","on"]

FHT_LIMITS = [6.0, 30.0]
FHT_SPECIALS = ["off","on"]

FS20_LIMITS = [6.0, 30.0]
FS20_SPECIALS= ["off","on","dim06%","dim25%","dim50%","dim75%","dim100%"]

CUL_HM_LIMITS = [6.0, 30.0]
CUL_HM_SPECIALS = ["off","on"]

FBDECT_SPECIALS = ["off","on","toggle","blink"]
IT_SPECIALS = ["off","on"]
MQTT_SPECIALS = ["off","on"]
MQTT2_SPECIALS = ["off","on"]
GHoma_SPECIALS = ["off","on"]
Hyperion_SPECIALS = ["off","on","dim06%","dim25%","dim50%","dim75%","dim100%"]
DOIF_SPECIALS = ["cmd_2","cmd_1","cmd_3","cmd_4","cmd_5","cmd_6","cmd_7","cmd_8","disable","enable","initialize"]
AptToDate_SPECIALS = ["repoSync"]


config.fhem = ConfigSubsection()
config.fhem.serverip = ConfigIP(default = [0,0,0,0])
config.fhem.port = ConfigInteger(default=8083, limits=(8000, 9000))
config.fhem.username = ConfigText(default="yourName")
config.fhem.password = ConfigText(default="yourPass")
config.fhem.grouping = ConfigSelection(default="ROOM", choices = [("TYPE", _("Type")), ("ROOM", _("Room"))])

class MainScreen(Screen):
	desktopSize = getDesktop(0).size()
	if desktopSize.width() >= 1920:
		skin = """
		<screen position="300,645" size="1390,430" name="fhem" title="FHEM Haussteuerung" >
			<widget name="titleMenu1" position="10,20" size="150,30" valign="center" halign="left" font="Regular;30"/>
			<eLabel name="bgMenu1" position="9,49" size="252,334" backgroundColor="#808080" zPosition="0"/>
			<widget name="Menu1" position="10,50" size="250,332" scrollbarMode="showOnDemand" zPosition="1"/>
			<widget name="titleMenu2" position="280,20" size="150,30" valign="center" halign="left" font="Regular;30"/>
			<eLabel name="bgMenu2" position="279,49" size="502,334" backgroundColor="#808080" zPosition="0"/>
			<widget name="Menu2" position="280,50" size="500,332" scrollbarMode="showOnDemand" zPosition="1"/>
			<widget name="titleDetails" position="800,20" size="580,30" valign="center" halign="left" font="Regular;30"/>
			<eLabel name="bgDetails" position="799,49" size="582,182" backgroundColor="#808080" zPosition="0"/>
			<widget name="details" position="800,50" size="580,180" zPosition="1"/>
			<eLabel name="bgSetBox" position="799,259" size="582,122" backgroundColor="#808080" zPosition="0"/>
			<widget name="set_Title" position="800,260" size="580,40" valign="center" halign="center" font="Regular;25" zPosition="1"/>
			<widget name="set_ArrowLeft" position="800,301" size="100,79" valign="center" halign="center" font="Regular;30" zPosition="1"/>
			<widget name="set_Text" position="900,301" size="380,79" valign="center" halign="center" font="Regular;30" zPosition="1"/>
			<widget name="set_ArrowRight" position="1280,301" size="100,79" valign="center" halign="center" font="Regular;30" zPosition="1"/>
			<widget name="spinner" position="600,390" size="140,40" valign="center" halign="right" font="Regular;25" foregroundColor="white" zPosition="1"/>
			<ePixmap position="10,390" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap position="150,390" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<ePixmap position="290,390" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
			<ePixmap position="430,390" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
			<widget source="key_red" render="Label" position="10,390" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget source="key_green" render="Label" position="150,390" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget source="key_yellow" render="Label" position="290,390" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget source="key_blue" render="Label" position="430,390" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget backgroundColor="#808080" font="Regular; 22" position="830,395" render="Label" size="180,25" source="global.CurrentTime" transparent="1" valign="bottom" halign="right" zPosition="3" foregroundColor="white">
				<convert type="ClockToText">Format:%A,</convert>
			</widget>
			<widget backgroundColor="#808080" font="Regular; 22" position="1030,395" render="Label" size="180,25" source="global.CurrentTime" transparent="1" valign="bottom" halign="left" zPosition="3" foregroundColor="white">
				<convert type="ClockToText">Format:%d. %B -</convert>
			</widget>
			<widget source="global.CurrentTime" render="Label" position="1200,395" size="190,50" font="Regular; 22" halign="left" valign="top" foregroundColor="white" backgroundColor="#808080" transparent="1">
				<convert type="ClockToText">WithSeconds</convert>
			</widget>
		</screen>"""
	else:
		skin = """
		<screen position="5,265" size="1270,450" name="fhem" title="FHEM Haussteuerung" >
			<widget name="titleMenu1" position="10,20" size="150,25" valign="center" halign="left" font="Regular;25"/>
			<eLabel name="bgMenu1" position="9,49" size="252,337" backgroundColor="#808080" zPosition="0"/>
			<widget name="Menu1" position="10,50" size="250,335" scrollbarMode="showOnDemand" zPosition="1"/>
			<widget name="titleMenu2" position="280,20" size="150,25" valign="center" halign="left" font="Regular;25"/>
			<eLabel name="bgMenu2" position="279,49" size="502,337" backgroundColor="#808080" zPosition="0"/>
			<widget name="Menu2" position="280,50" size="500,335" scrollbarMode="showOnDemand" zPosition="1"/>
			<widget name="titleDetails" position="800,20" size="460,25" valign="center" halign="left" font="Regular;25"/>
			<eLabel name="bgDetails" position="799,49" size="462,202" backgroundColor="#808080" zPosition="0"/>
			<widget name="details" position="800,50" size="460,200" zPosition="1"/>
			<eLabel name="bgSetBox" position="799,279" size="462,122" backgroundColor="#808080" zPosition="0"/>
			<widget name="set_Title" position="800,280" size="460,40" valign="center" halign="center" font="Regular;25" zPosition="1"/>
			<widget name="set_ArrowLeft" position="800,321" size="100,79" valign="center" halign="center" font="Regular;25" zPosition="1"/>
			<widget name="set_Text" position="880,321" size="300,79" valign="center" halign="center" font="Regular;25" zPosition="1"/>
			<widget name="set_ArrowRight" position="1160,321" size="100,79" valign="center" halign="center" font="Regular;25" zPosition="1"/>
			<widget name="spinner" position="600,410" size="140,40" valign="center" halign="right" font="Regular;25" foregroundColor="white" zPosition="1"/>
			<ePixmap position="10,410" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap position="150,410" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<ePixmap position="290,410" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
			<ePixmap position="430,410" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
			<widget source="key_red" render="Label" position="10,410" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget source="key_green" render="Label" position="150,410" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget source="key_yellow" render="Label" position="290,410" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget source="key_blue" render="Label" position="430,410" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget backgroundColor="#808080" font="Regular; 22" position="780,415" render="Label" size="180,25" source="global.CurrentTime" transparent="1" valign="bottom" halign="right" zPosition="3" foregroundColor="white">
				<convert type="ClockToText">Format:%A,</convert>
			</widget>
			<widget backgroundColor="#808080" font="Regular; 22" position="970,415" render="Label" size="180,25" source="global.CurrentTime" transparent="1" valign="bottom" halign="left" zPosition="3" foregroundColor="white">
				<convert type="ClockToText">Format:%d. %B -</convert>
			</widget>
			<widget source="global.CurrentTime" render="Label" position="1095,415" size="190,50" font="Regular; 22" halign="left" valign="top" foregroundColor="white" backgroundColor="#808080" transparent="1">
				<convert type="ClockToText">WithSeconds</convert>
			</widget>
		</screen>"""
		

	def __init__(self, session, args = None):
		self.session = session
		Screen.__init__(self, session)
				
		self.onLayoutFinish.append(self.startRun)
		self.grouping = str(config.fhem.grouping.value)
		
		self["set_Title"] = Label("Neue Solltemperatur")
		self["set_ArrowLeft"] = Label("<")
		self["set_ArrowRight"] = Label(">")
		self["set_Text"] = Label()
		self["details"] = ElementList()
		self["titleMenu1"] = Label()
		self["titleMenu2"] = Label("Element")
		self["titleDetails"] = Label()
		self["spinner"] = Label("")
		
		self["Menu2"] = ElementList() 
		self["Menu2"].connectSelChanged(self.selChanged)
		self["Menu2"].selectionEnabled(0)
		self["Menu1"] = ElementList()
		self["Menu1"].connectSelChanged(self.selChanged)
		self["Menu1"].selectionEnabled(1)
		self.selectedListObject = self["Menu1"]
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
		self["key_red"] = StaticText(_("Exit"))
		self["key_green"] = StaticText(_("Transmit"))
		self["key_yellow"] = StaticText(_("Refresh"))
 		self["key_blue"] = StaticText(_("Setup"))
		
		self["actions"] = ActionMap(["FHEM_Actions"],
		{
				"key_ok": self.key_ok_Handler,
				"key_num_left": self.key_num_left_Handler,
				"key_num_right": self.key_num_right_Handler,
				"key_channel_down": self.key_num_left_Handler,
				"key_channel_up": self.key_num_right_Handler,
				"key_0": self.key_0_Handler,
				"key_green": self.key_green_Handler,
				"key_yellow": self.key_yellow_Handler,
				"key_blue": self.key_menu_Handler,
				"key_red": self.close,
				"key_menu": self.key_menu_Handler,
				"key_cancel": self.close,
				"key_left": self.key_left_right_Handler,
				"key_right": self.key_left_right_Handler,
				"key_up": self.key_Up_Handler,
				"key_down": self.key_Down_Handler
		}, -1)
		
	def closeme(self):
		self.isRunning = 0
		self.close
	
	def saveconfig(self):
		config.fhem.serverip.save()
		config.fhem.port.save()
		config.fhem.username.save()
		config.fhem.password.save()
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
			self.selectedListObject = self["Menu2"]	
			self["Menu1"].selectionEnabled(0)
			self["Menu2"].selectionEnabled(1)
			self.listSelectionChanged()
		else:
			self.selList = 0
			self.selectedListObject = self["Menu1"]	
			self["Menu1"].selectionEnabled(1)
			self["Menu2"].selectionEnabled(0)
			#clear Details
			self["set_Title"].setText("")
			self["set_Text"].setText("")
			self["titleDetails"].setText("")
			self["details"].setList([], 3)

		
	def startRun(self):
		server = "%d.%d.%d.%d" % tuple(config.fhem.serverip.value)
		if server == "0.0.0.0":
			return
		self.isRunning = 1
		self.reload_Screen()
		self["Menu2"].selectionEnabled(0)
		self["Menu1"].selectionEnabled(1)
		self["details"].selectionEnabled(0)
		self.selList = 0
		self.selectedListObject = self["Menu1"]
		
	def selChanged(self):
		self.listSelTimer.start(200, True)
			
	def listSelectionChanged(self):
		print "FHEM-debug: %s -- %s" % ("listSelectionChanged", "enter")
		if self.selList == 0:
			
			try:
				typedef = self["Menu1"].l.getCurrentSelection()[0]
			except:
				return
			
			#avoid racecondition
			if self.typedef == typedef:
				return
			else:
				self.typedef = typedef
			
			list = []

			if self.grouping == "TYPE":
				self["titleMenu1"].setText("Typ")
				for element in self.container.getElementsByType([typedef]):
					list.append((element,))

			if self.grouping == "ROOM":
				self["titleMenu1"].setText("Raum")
				for element in self.container.getElementsByRoom([typedef]):
					list.append((element,))
					
			self["Menu2"].setList(list, 2)
			
		else:

			try:
				selectedElement = self["Menu2"].l.getCurrentSelection()[0]
			except:
				return
				
			print "FHEM-debug: %s -- %s" % ("listSelectionChanged", selectedElement.Name)
			
			if selectedElement.getType() in ["FHT", "MAX", "CUL_HM"]:			
				if selectedElement.getSubType() == "thermostat":
					self["titleDetails"].setText("Details für " + selectedElement.getAlias())
					
					list = []
					list.append((["Solltemperatur:",selectedElement.getDesiredTemp() + " °C"],))
					list.append((["Isttemperatur:",selectedElement.getMeasuredTemp() + " °C"],))
					list.append((["Thermostat:",selectedElement.getActuator() + " %"],))
					list.append((["Timestamp:",selectedElement.getLastrcv()],))
					list.append((["Batterie:",selectedElement.getBattery()],))
					self["details"].setList(list, 3)
					
					self["set_Text"].setText(selectedElement.getDesiredTemp() + " °C")
					self["set_Title"].setText("Neue Solltemperatur")
				
				elif selectedElement.getSubType() == "THSensor":
					self["titleDetails"].setText("Details für " + selectedElement.getAlias())
					
					list = []
					list.append((["Holzkessel:",selectedElement.getMeasuredTemp() + " °C"],))
					list.append((["Warmwasser:",selectedElement.getMeasuredTemp1() + " °C"],))
					list.append((["Timestamp:",selectedElement.getLastrcv1()],))
					list.append((["Batterie:",selectedElement.getBattery()],))
					self["details"].setList(list, 3)
				
				elif selectedElement.getSubType() == "switch":
					self["titleDetails"].setText("Details für " + selectedElement.getAlias())
				
					list = []
					list.append((["Einschaltstatus:",selectedElement.getReadingState()],))
					list.append((["Timestamp:",selectedElement.getLastrcv2()],))
					self["details"].setList(list, 3)
				
					self["set_Title"].setText("Neuer Schaltstatus")
					self["set_Text"].setText(selectedElement.getReadingState())
			
			elif selectedElement.getType() in ["CUL_TX"]:
				self["titleDetails"].setText("Details für " + selectedElement.getAlias())
				
				list = []
				list.append((["Temperatur:",selectedElement.getMeasuredTemp() + " °C"],))
				list.append((["Luftfeuchte:",selectedElement.getHumidity() + " %"],))
				if selectedElement.getPressure() != "no prop":
					list.append((["Luftdruck:",selectedElement.getPressure() + " mBar"],))
				self["details"].setList(list, 3)
				
				self["set_Title"].setText("")
				self["set_Text"].setText("")
				
			elif selectedElement.getType() in ["Weather"]:
				self["titleDetails"].setText("Details für " + selectedElement.getAlias())
				
				list = []
				list.append((["Temperatur:",selectedElement.getMeasuredTemp() + " °C"],))
				list.append((["Luftfeuchte:",selectedElement.getHumidity() + " %"],))
				list.append((["Windstärke:",selectedElement.getWind() + " km/h"],))
				if selectedElement.getPressure() != "no prop":
					list.append((["Luftdruck:",selectedElement.getPressure() + " mBar"],))
				self["details"].setList(list, 3)
				
				self["set_Title"].setText("")
				self["set_Text"].setText("")
			
			elif selectedElement.getType() in ["FS20", "FBDECT", "IT", "DOIF", "GHoma", "Hyperion"]:
				self["titleDetails"].setText("Details für " + selectedElement.getAlias())
				
				list = []
				list.append((["Einschaltstatus:",selectedElement.getReadingState()],))
				self["details"].setList(list, 3)
				
				self["set_Title"].setText("Neuer Schaltstatus")
				self["set_Text"].setText(selectedElement.getReadingState())
			
			elif selectedElement.getType() in ["MQTT_DEVICE", "MQTT2_DEVICE"]:
				self["titleDetails"].setText("Details für " + selectedElement.getAlias())
				
				list = []
				list.append((["Einschaltstatus:",selectedElement.getReadingState()],))
				list.append((["Strom:",selectedElement.getENERGYCurrent() + " A"],))
				list.append((["Leistung:",selectedElement.getENERGYPower() + " W"],))
				list.append((["Energie heute:",selectedElement.getENERGYToday() + " kWh"],))
				list.append((["Energie insgesamt:",selectedElement.getENERGYTotal() + " kWh"],))
				self["details"].setList(list, 3)
				
				self["set_Title"].setText("Neuer Schaltstatus")
				self["set_Text"].setText(selectedElement.getReadingState())
			
			elif selectedElement.getType() in ["FRITZBOX", "CUL", "notify"]:
				self["titleDetails"].setText("Details für " + selectedElement.getAlias())
				
				list = []
				list.append((["State:",selectedElement.getReadingState()],))
				self["details"].setList(list, 3)
				
				self["set_Title"].setText("")
				self["set_Text"].setText("")
			
			elif selectedElement.getType() in ["AptToDate"]:
				self["titleDetails"].setText("Details für " + selectedElement.getAlias())
				
				list = []
				list.append((["State:",selectedElement.getReadingState()],))
				list.append((["Updates:",selectedElement.getUpdateAvState()],))
				list.append((["repoSync:",selectedElement.getRepoSync()],))
				self["details"].setList(list, 3)
				
				self["set_Title"].setText("AptToDate")
				self["set_Text"].setText(selectedElement.getReadingState())
			
			elif selectedElement.getSubType() == "switch":
				self["titleDetails"].setText("Details für " + selectedElement.getAlias())
				
				list = []
				list.append((["Einschaltstatus:",selectedElement.getReadingState()],))
				self["details"].setList(list, 3)
				
				self["set_Title"].setText("Neuer Schaltstatus")
				self["set_Text"].setText(selectedElement.getReadingState())
				
			elif selectedElement.getSubType() in ["THSensor"]:
				self["titleDetails"].setText("Details für " + selectedElement.getAlias())
				
				list = []
				list.append((["Temperatur:",selectedElement.getMeasuredTemp() + " °C"],))
				list.append((["Luftfeuchte:",selectedElement.getHumidity() + " %"],))
				if selectedElement.getPressure() != "no prop":
					list.append((["Luftdruck:",selectedElement.getPressure() + " mBar"],))
				list.append((["Batterie:",selectedElement.getBattery()],))
				self["details"].setList(list, 3)
				
				self["set_Title"].setText("")
				self["set_Text"].setText("")
				
			elif selectedElement.getType() in ["CUL_HM"] and electedElement.getSubType() != "thermostat":
				self["titleDetails"].setText("Details für " + selectedElement.getAlias())
				
				list = []
				list.append((["unbek. HM subtype:", selectedElement.getSubType()],))
				list.append((["Bitte JSON für:", selectedElement.Name],))
				list.append((["im Forum posten",""],))
				self["details"].setList(list, 3)
				
				self["set_Title"].setText("- - -")
				self["set_Text"].setText("0")
	
	
	def key_0_Handler(self):
		pass
		
	
	def key_num_left_Handler(self):
		if self.selList == 1:
			selectedElement = self["Menu2"].l.getCurrentSelection()[0]
			if selectedElement.getSubType() == "thermostat":
				if self.is_number(self["set_Text"].getText()):
					actvalue = float(self["set_Text"].getText())
					limits = selectedElement.getLimits()
					if actvalue > limits[0]:
						self["set_Text"].setText(str(actvalue - 0.5))
				else:
					self["set_Text"].setText(str(float(selectedElement.getDesiredTemp()) - 0.5))
		
	def key_num_right_Handler(self):
		if self.selList == 1:
			selectedElement = self["Menu2"].l.getCurrentSelection()[0]
			if selectedElement.getSubType() == "thermostat":
				if self.is_number(self["set_Text"].getText()):
					actvalue = float(self["set_Text"].getText())
					limits = selectedElement.getLimits()
					if actvalue < limits[1]:
						self["set_Text"].setText(str(actvalue + 0.5))
				else:
					self["set_Text"].setText(str(float(selectedElement.getDesiredTemp()) + 0.5))
		
	def key_green_Handler(self):
		if self.selList == 1:
			selectedElement = self["Menu2"].l.getCurrentSelection()[0]
			
			try:
				if self["set_Text"].getText() != "":
					if selectedElement.getType() in ["FHT", "MAX", "CUL_HM"]:
						if selectedElement.getSubType() == "thermostat":
							self.container.updateElementByName(selectedElement.Name, self["set_Text"].getText())
					
					elif selectedElement.getType() in ["CUL_HM" ,"FS20", "IT", "MQTT_DEVICE", "MQTT2_DEVICE", "DOIF", "AptToDate", "GHoma", "Hyperion"]:
						self.container.updateElementByName(selectedElement.Name, self["set_Text"].getText())
					
					self.container.updateElementByName(selectedElement.Name, self["set_Text"].getText())
					self.setSpinner(True)
					self.refreshTimer.start(500, True)
			except:
				pass
		
	def key_yellow_Handler(self):
		self.setSpinner(True)
		self.refreshTimer.start(500, True)
		
	def key_ok_Handler(self):
		if self.selList == 1:
			selectedElement = self["Menu2"].l.getCurrentSelection()[0]
			specials = selectedElement.getSpecials()
			actvalue = self["set_Text"].getText()
			if self.is_number(actvalue):
				self["set_Text"].setText(specials[0])
			else:
				for idx, svalue in enumerate(specials):
					if svalue == actvalue:
						if idx < len(specials) - 1:
							self["set_Text"].setText(specials[idx + 1])
						
						else:
							self["set_Text"].setText(specials[0])
							
						return

					elif not actvalue:
						if idx < len(specials) - 1:
							self["set_Text"].setText(specials[idx + 1])
					
					else:
						self["set_Text"].setText(specials[0])
					
	
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
		
		if self.grouping == "TYPE":
			for listentry in self.container.getTypes():
				list.append((listentry,))
			self["Menu1"].setList(list, 0)
		elif self.grouping == "ROOM":
			for listentry in self.container.getRooms():
				list.append((listentry,))
			self["Menu1"].setList(list, 1)	
		
		self.selList = 0
		self.selectedListObject = self["Menu1"]	
		self["Menu1"].selectionEnabled(1)
		self["Menu2"].selectionEnabled(0)
		#clear Details
		self["set_Title"].setText("")
		self["set_Text"].setText("")
		self["titleDetails"].setText("")
		self["details"].setList([], 3)
			
		self.listSelectionChanged()
		#self.refreshTimer.start(1000, True)
		print "FHEM-debug: %s -- %s" % ("reload_Screen", "done")
	
	def	setSpinner(self, enabled):
		if enabled:
			self["spinner"].setText("load...")
		else:
			self["spinner"].setText("")
		
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
			name="FHEM Haussteuerung",
			description="Plugin zur Steuerung von FHEM",
			where = PluginDescriptor.WHERE_PLUGINMENU,
			icon="fhem.png",
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
		print "FHEM-debug: %s -- %s" % ("getLimits", self.getType())
		if self.getType() == "FHT":
			return FHT_LIMITS
		elif self.getType() == "MAX":
			return MAX_LIMITS
		elif self.getType() == "CUL_HM":
			return CUL_HM_LIMITS
		else:
			return [0,0]
			
	def getSpecials(self):
		print "FHEM-debug: %s -- %s" % ("getSpecials", self.getType())
		if self.getType() == "FHT":
			return FHT_SPECIALS
		elif self.getType() == "IT":
			return IT_SPECIALS
		elif self.getType() == "MAX":
			return MAX_SPECIALS
		elif self.getType() == "CUL_HM":
			return CUL_HM_SPECIALS
		elif self.getType() == "FS20":
			return FS20_SPECIALS
		elif self.getType() == "FBDECT":
			return FBDECT_SPECIALS
		elif self.getType() == "MQTT_DEVICE":
			return MQTT_SPECIALS
		elif self.getType() == "MQTT2_DEVICE":
			return MQTT2_SPECIALS
		elif self.getType() == "DOIF":
			return DOIF_SPECIALS
		elif self.getType() == "AptToDate":
			return AptToDate_SPECIALS
		elif self.getType() == "GHoma":
			return GHoma_SPECIALS
		elif self.getType() == "Hyperion":
			return Hyperion_SPECIALS	
		else:
			return ["0"]
	
		
	def getType(self):
		return str(self.Data["Internals"]["TYPE"])
		
	def getRoom(self):
		try:
			return str(self.Data["Attributes"]["room"]).split(',')
		except:
			return ('')
		
	def getReadings(self):
		return self.Data["Readings"]
		
	def getAttributes(self):
		return self.Data["Attributes"]
	
	def getInternals(self):
		return self.Data["Internals"]
		
	def getAlias(self):
		try:
			if self.Data["Attributes"]["alias"] is not None:
				return str(self.Data["Attributes"]["alias"])
			else:
				return self.Name
		except:
			return self.Name
			
	def getDesiredTemp(self):
		type = self.getType()
		try:
			if type in ["FHT","CUL_HM"]:
				return str(self.Data["Readings"]["desired-temp"]["Value"])
			elif type == "MAX":
				if str(self.Data["Readings"]["desiredTemperature"]["Value"]) == "off":
					return "0"
				else:	
					return str(self.Data["Readings"]["desiredTemperature"]["Value"])
			else: 
				return "no def"
		except:
			return "no prop"
	
	def getPressure(self):
		type = self.getType()
		try:
			return str(self.Data["Readings"]["pressure"]["Value"])
		except:
			return "no prop"
			
	def getHumidity(self):
		type = self.getType()
		try:
			if type in ["FHT"]:
				return "no prop"
			elif type in ["CUL_HM"] and self.getSubType() == "thermostat":
				return str(self.Data["Readings"]["humidity"]["Value"])
			elif type in ["CUL_HM"] and self.getSubType() == "THSensor":
				return str(self.Data["Readings"]["humidity"]["Value"])
			elif type in ["CUL_TX"] and self.getSubType() == "THSensor":
				return str(self.Data["Readings"]["humidity"]["Value"])	
			elif type in ["CUL_WS"] and self.getSubType() == "THSensor":
				return str(self.Data["Readings"]["humidity"]["Value"])
			elif type in ["Weather"]:
				return str(self.Data["Readings"]["humidity"]["Value"])	
			elif type in ["MAX"]:
				return "no prop"
			else: 
				return "no def"
		except:
			return "no prop"
	
	def getMeasuredTemp(self):
		type = self.getType()
		try:
			retval = "0.0"
			if type in ["FHT"]:
				retval = str(self.Data["Readings"]["measured-temp"]["Value"])
			elif type in ["CUL_HM"] and self.getSubType() == "thermostat":
				retval = str(self.Data["Readings"]["measured-temp"]["Value"])
			elif type in ["CUL_HM"] and self.getSubType() == "THSensor":
				retval = str(self.Data["Readings"]["T1"]["Value"])
			elif type in ["CUL_HM"] and self.getSubType() == "THSensor":
				retval = str(self.Data["Readings"]["temperature"]["Value"])
			elif type in ["CUL_TX"] and self.getSubType() == "THSensor":
				retval = str(self.Data["Readings"]["temperature"]["Value"])	
			elif type in ["CUL_WS"] and self.getSubType() == "THSensor":
				retval = str(self.Data["Readings"]["temperature"]["Value"])
			elif type in ["Weather"]:
				retval = str(self.Data["Readings"]["temperature"]["Value"])	
			elif type in ["MAX"]:
				retval = str(self.Data["Readings"]["temperature"]["Value"])
			else: 
				retval = "0.0"
				
			return retval
			
		except:
			return "no prop"
				
	def getMeasuredTemp1(self):
		type = self.getType()
		try:
			retval = "0.0"
			if type in ["FHT"]:
				retval = str(self.Data["Readings"]["measured-temp"]["Value"])
			elif type in ["CUL_HM"] and self.getSubType() == "thermostat":
				retval = str(self.Data["Readings"]["measured-temp"]["Value"])
			elif type in ["CUL_HM"] and self.getSubType() == "THSensor":
				retval = str(self.Data["Readings"]["T2"]["Value"])	
			elif type in ["CUL_HM"] and self.getSubType() == "THSensor":
				retval = str(self.Data["Readings"]["temperature"]["Value"])
			elif type in ["CUL_WS"] and self.getSubType() == "THSensor":
				retval = str(self.Data["Readings"]["temperature"]["Value"])
			elif type in ["MAX"]:
				retval = str(self.Data["Readings"]["temperature"]["Value"])
			else: 
				retval = "0.0"
				
			#m = re.search("\d{1,2}.\d{1,2}", retval)
			#return m.group(1)
			return retval
			
		except:
			return "no prop"
			
	def getWind(self):
		type = self.getType()
		try:
			retval = ""
			if type in ["Weather"]:
				retval = str(self.Data["Readings"]["wind"]["Value"])
			else: 
				retval = "0.0"
				
			return retval
			
		except:
			return "no prop"
	
	def getPowerstate(self):
		type = self.getType()
		try:
			retval = ""
			if type in ["CUL_HM"] and self.getSubType() == "switch":
				retval = str(self.Data["Readings"]["state"]["Value"])
			else: 
				retval = "0.0"
				
			return retval
			
		except:
			return "no prop"
	
	
	def getControlmode(self):
		type = self.getType()
		try:
			if type in ["FHT","CUL_HM","MAX"]:
				return str(self.Data["Readings"]["powerOn"]["Value"])
			else: 
				return "no def"
		except:
			return "no prop"
			
	def getActuator(self):
		type = self.getType()
		try:
			if type in ["FHT","CUL_HM"]:
				return str(self.Data["Readings"]["actuator"]["Value"])
			elif type == "MAX":
				return str(self.Data["Readings"]["valveposition"]["Value"])
			else: 
				return "no def"
		except:
			return "no prop"
			
	def getBattery(self):
		type = self.getType()
		try:
			if type in ["FHT","CUL_HM","MAX"]:
				return str(self.Data["Readings"]["battery"]["Value"])
			else: 
				return "no def"
		except:
			return "no prop"
					
	def getLastrcv(self):
		type = self.getType()
		try:
			if type in ["FHT","CUL_HM","MAX"]:
				return str(self.Data["Readings"]["measured-temp"]["Time"])
			else: 
				return "no def"
		except:
			return "no prop"
			
	def getLastrcv1(self):
		type = self.getType()
		try:
			if type in ["FHT","CUL_HM","MAX"]:
				return str(self.Data["Readings"]["T1"]["Time"])
			else: 
				return "no def"
		except:
			return "no prop"
			
	def getLastrcv2(self):
		type = self.getType()
		try:
			if type in ["FHT","CUL_HM","MAX"]:
				return str(self.Data["Readings"]["powerOn"]["Time"])
			else: 
				return "no def"
		except:
			return "no prop"
	
	
	def getReadingState(self):
		type = self.getType()
		try:
			if type == "FHT":
				return str(self.Data["Readings"]["state"]["Value"]).replace("measured-temp: ","")
			elif type == "MAX":
				return str(self.Data["Readings"]["state"]["Value"])
			elif type == "FS20":
				return str(self.Data["Readings"]["state"]["Value"])
			elif type == "IT":
				return str(self.Data["Readings"]["state"]["Value"])
			elif type == "CUL_HM":
				return str(self.Data["Readings"]["state"]["Value"])
			elif type == "MQTT_DEVICE":
				return str(self.Data["Readings"]["state"]["Value"])
			elif type == "MQTT2_DEVICE":
				return str(self.Data["Readings"]["state"]["Value"])
			elif type == "CUL_TX":
				return ""
			elif type == "CUL_WS":
				return self.getMeasuredTemp()
			elif type == "FBDECT":
				return str(self.Data["Readings"]["state"]["Value"]).replace("set_","")
			elif type == "DOIF":
				return str(self.Data["Readings"]["state"]["Value"])
			elif type == "FRITZBOX":
				return str(self.Data["Readings"]["state"]["Value"])
			elif type == "CUL":
				return str(self.Data["Readings"]["state"]["Value"])
			elif type == "notify":
				return str(self.Data["Readings"]["state"]["Value"])
			elif type == "AptToDate":
				return str(self.Data["Readings"]["state"]["Value"])
			elif type == "GHoma":
				return str(self.Data["Readings"]["state"]["Value"])	
			elif type == "Hyperion":
				return str(self.Data["Readings"]["state"]["Value"])
			else: 
				return ""
		except:
			return "no prop"
	
	def getUpdateAvState(self):
		type = self.getType()
		try:
			if type == "AptToDate":
				return str(self.Data["Readings"]["updatesAvailable"]["Value"])	
			else: 
				return ""
		except:
			return "no prop"
	
	def getRepoSync(self):
		type = self.getType()
		try:
			if type == "AptToDate":
				return str(self.Data["Readings"]["repoSync"]["Value"])	
			else: 
				return ""
		except:
			return "no prop"
			
	def getENERGYCurrent(self):
		type = self.getType()
		try:
			if type == "MQTT2_DEVICE":
				return str(self.Data["Readings"]["ENERGY_Current"]["Value"])
			elif type == "MQTT_DEVICE":
				return str(self.Data["Readings"]["ENERGY_Current"]["Value"])
			else: 
				return ""
		except:
			return "no prop"
	
	def getENERGYPower(self):
		type = self.getType()
		try:
			if type == "MQTT2_DEVICE":
				return str(self.Data["Readings"]["ENERGY_Power"]["Value"])
			elif type == "MQTT_DEVICE":
				return str(self.Data["Readings"]["ENERGY_Power"]["Value"])
			else: 
				return ""
		except:
			return "no prop"
	
	def getENERGYToday(self):
		type = self.getType()
		try:
			if type == "MQTT2_DEVICE":
				return str(self.Data["Readings"]["ENERGY_Today"]["Value"])
			elif type == "MQTT_DEVICE":
				return str(self.Data["Readings"]["ENERGY_Today"]["Value"])
			else: 
				return ""
		except:
			return "no prop"
			
	def getENERGYTotal(self):
		type = self.getType()
		try:
			if type == "MQTT2_DEVICE":
				return str(self.Data["Readings"]["ENERGY_Total"]["Value"])
			elif type == "MQTT_DEVICE":
				return str(self.Data["Readings"]["ENERGY_Total"]["Value"])	
			else: 
				return ""
		except:
			return "no prop"
	
	def getDoifSpecials(self):
		type = self.getType()
		try:
			if type == "DOIF":
				return str(self.Data["Attributes"]["cmdState"]["Value"])
			else: 
				return ""
		except:
			return "no prop"
	
			
	def getInternalsState(self):
		type = self.getType()
		try:
			if type == "FHT":
				return str(self.Data["Internals"]["protLastRcv"]["Value"]).replace("measured-temp: ","")
			elif type == "MAX":
				return str(self.Data["Internals"]["protLastRcv"]["Value"])
			elif type == "FS20":
				return str(self.Data["Internals"]["protLastRcv"]["Value"])
			elif type == "CUL_HM":
				return str(self.Data["Internals"]["protLastRcv"]["Value"])
			elif type == "CUL_WS":
				return self.getMeasuredTemp()
			elif type == "FBDECT":
				return str(self.Data["Internals"]["protLastRcv"]["Value"]).replace("set_","") 
			else: 
				return "no def"
		except:
			return "no prop"
	
	def getSubType(self):
		type = self.getType()
		if type == "CUL_HM":
			try:
				subtype = str(self.Data["Attributes"]["subType"])
			except:
				subtype = "unknown"
			return subtype
		elif type == "FHT":
			return "thermostat"
		elif type == "FS20":
			return "switch"
		elif type == "MAX":
			return "thermostat"
		elif type == "CUL_TX":	
			return "THSensor"	
		elif type == "CUL_WS":	
			return "THSensor"
		elif type == "FBDECT":	
			return str(self.Data["Internals"]["props"])	
		else:
			return "unknown"
	
	def getmodel(self):
		type = self.getType()
		if type == "CUL_HM":
			try:
				subtype = str(self.Data["Attributes"]["model"])
			except:
				subtype = "unknown"
			return subtype
		else:
			return "unknown"
	
	def getUpdateableProperty(self):
		type = self.getType()
		if type in ["FHT"]:
			return "desired-temp"
		elif type == "CUL_HM" and self.getSubType() == "switch":
			return ""
		elif type == "CUL_HM" and self.getSubType() == "thermostat":
			return "desired-temp"	
		elif type == "MAX":
			return "desiredTemperature"
		elif type == "FS20":
			return ""
		elif type == "FBDECT":
			return ""
		elif type == "IT":
			return ""	
		elif type == "MQTT_DEVICE":
			return ""
		elif type == "MQTT2_DEVICE":
			return ""
		elif type == "DOIF":
			return ""
		elif type == "AptToDate":
			return ""
		elif type == "GHoma":
			return ""
		elif type == "Hyperion":
			return ""
		
	def getUpdateCommand(self):
		type = self.getType()
		if type in ["FHT"]:
			return "/fhem?XHR=1&cmd.%s=set %s %s " % (self.Name, self.Name, self.getUpdateableProperty())
		elif type == "CUL_HM" and self.getSubType() == "switch":
			return "/fhem?XHR=1&cmd=set %s %s " % (self.Name, self.getUpdateableProperty())		
		elif type == "CUL_HM" and self.getmodel() == "HM-CC-RT-DN":
			return "/fhem?XHR=1&cmd=set %s %s " % (self.Name + "_Clima", self.getUpdateableProperty())
		elif type == "CUL_HM" and self.getmodel() == "HM-TC-IT-WM-W-EU":
			return "/fhem?XHR=1&cmd=set %s %s " % (self.Name + "_Climate", self.getUpdateableProperty())
		elif type == "MAX":
			return "/fhem?XHR=1&cmd=set %s %s " % (self.Name, self.getUpdateableProperty())
		elif type == "FS20":
			return "/fhem?XHR=1&cmd.%s=set %s %s " % (self.Name, self.Name, self.getUpdateableProperty())
		elif type == "FBDECT":
			return "/fhem?XHR=1&cmd.%s=set %s %s " % (self.Name, self.Name, self.getUpdateableProperty())
		elif type == "IT":
			return "/fhem?XHR=1&cmd.%s=set %s %s " % (self.Name, self.Name, self.getUpdateableProperty())
		elif type == "MQTT_DEVICE":
			return "/fhem?XHR=1&cmd.%s=set %s %s " % (self.Name, self.Name, self.getUpdateableProperty())
		elif type == "MQTT2_DEVICE":
			return "/fhem?XHR=1&cmd.%s=set %s %s " % (self.Name, self.Name, self.getUpdateableProperty())
		elif type == "DOIF":
			return "/fhem?XHR=1&cmd.%s=set %s %s " % (self.Name, self.Name, self.getUpdateableProperty())
		elif type == "AptToDate":
			return "/fhem?XHR=1&cmd.%s=set %s %s " % (self.Name, self.Name, self.getUpdateableProperty())
		elif type == "GHoma":
			return "/fhem?XHR=1&cmd.%s=set %s %s " % (self.Name, self.Name, self.getUpdateableProperty())
		elif type == "Hyperion":
			return "/fhem?XHR=1&cmd.%s=set %s %s " % (self.Name, self.Name, self.getUpdateableProperty())
			
	def getHMChannels(self):
		type = self.getType()
		retval = []
		if type == "CUL_HM":
			data = self.getInternals()
			for s in ["channel_01","channel_02","protState"]:
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
			for element in self.data["Results"]:
				if str(element["state"]) != "???":
					eldata = self.worker.getJson(element["name"], 1)
					if self.Type == "CUL_HM":
						try:
							el = FHEMElement(str(element["name"]), eldata["Results"][0])
							channels = el.getHMChannels()
							if channels:
								self.Elements.append(el)
						except:
							print "FHEM-debug: %s -- %s" % ("reload, error loading", element["name"])
					else:
						try:
							el = FHEMElement(str(element["name"]), eldata["Results"][0])
							self.Elements.append(el)
						except:
							print "FHEM-debug: %s -- %s" % ("reload, error loading", element["name"])
					
	def refresh(self):
		for element in self.Elements:
			self.loadElement(element.Name)
		
	def loadElement(self, name):
		if self.Elements is not None:
			for element in self.Elements:
				if element.Name == name:
					json = self.worker.getJson(name, 1)
					element.Data = json["Results"][0] 
	
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
	
		self.server = "%d.%d.%d.%d" % tuple(config.fhem.serverip.value)
		self.port = int(config.fhem.port.value)
		self.username = str(config.fhem.username.value)
		self.password = str(config.fhem.password.value)
		
		self.Address = self.server + ":" + str(self.port)
		self.Prefix = ["/fhem?XHR=1&cmd=jsonlist+","/fhem?XHR=1&cmd=jsonlist2+"]
		self.isAuth = len(self.username) + len(self.password)
		
		if self.isAuth != 0: 
			self.credentialss = self.username + ":" + self.password
			self.credentialsb = self.credentialss.encode("utf-8")
			self.credentials64 = base64.b64encode(self.credentialsb).decode("ascii")
			self.headers = { 'Authorization' : 'Basic %s' %  self.credentials64 }
		
	def getHtml(self, elements, listtype):
		conn = httplib.HTTPConnection(self.Address) #if response != 400 else httplib.HTTPSConnection(self.Address)
		try:
			if self.isAuth != 0:
				conn.request("GET", self.Prefix[listtype] + elements, headers = self.headers)
			else:
				conn.request("GET", self.Prefix[listtype] + elements)
			
			response = conn.getresponse()
			if response.status != 200:
				print "FHEM-debug: %s -- %s" % ("response", str(response.status) + " --- reason: " + response.reason)
				self.hasError = True
				return None
				
			self.hasError = False
			return response
		except:
			self.hasError = True
			return None
		
	def getJson(self, elements, listtype):
		try:
			jsonObj = json.loads(self.getHtml(elements, listtype).read())
			return jsonObj
		except:
			return None
		
	def setPropertyValue(self, command, value):
		conn = httplib.HTTPConnection(self.Address)
		message = command + value
		print "FHEM-debug: %s -- %s" % ("Message to send:", message)
		message = message.replace(" ","%20")

		

		if self.isAuth != 0:
			conn.request("GET", message, headers = self.headers)
		else:
			conn.request("GET", message)

		response = conn.getresponse()
		if response.status != 200:
			print "FHEM-debug: %s -- %s" % ("response", str(response.status) + " --- reason: " + response.reason)
			self.hasError = True
		
		print "FHEM-debug: %s -- %s" % ("Message sent", "Result: " + str(response.status) + " Reason: " + response.reason)		
		self.hasError = False

############################################     Config    #################################

class FHEM_Setup(Screen, ConfigListScreen):
	desktopSize = getDesktop(0).size()
	if desktopSize.width() >= 1920:
		skin = """
		<screen name="picshow" position="300,665" size="660,320" title="FHEM Settings" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,270" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,270" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="0,270" zPosition="1" size="140,40" font="Regular;21" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
			<widget source="key_green" render="Label" position="140,270" zPosition="1" size="140,40" font="Regular;21" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			<widget source="label" render="Label" position="10,10" size="640,40" font="Regular;24" backgroundColor="#25062748" transparent="1"  />
			<widget name="config" position="10,50" zPosition="2" size="640,200" itemHeight="38" font="Regular;24" scrollbarMode="showOnDemand" />
		</screen>"""
	else:
		skin = """
		<screen name="picshow" position="5,265" size="660,320" title="FHEM Settings" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,270" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,270" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="0,270" zPosition="1" size="140,40" font="Regular;21" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
			<widget source="key_green" render="Label" position="140,270" zPosition="1" size="140,40" font="Regular;21" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			<widget source="label" render="Label" position="10,10" size="640,40" font="Regular;24" backgroundColor="#25062748" transparent="1"  />
			<widget name="config" position="10,50" zPosition="2" size="640,200" itemHeight="38" font="Regular;24" scrollbarMode="showOnDemand" />
		</screen>"""
		
		
	def __init__(self, session):
		Screen.__init__(self, session)
		# for the skin: first try MediaPlayerSettings, then Setup, this allows individual skinning
		#self.skinName = ["PicturePlayerSetup", "Setup" ]
		self.setup_title = _("Settings")
		self.onChangedEntry = [ ]
		self.session = session

		self["actions"] = ActionMap(["SetupActions"],
			{
				"cancel": self.keyCancel,
				"save": self.keySave,
				"ok": self.keySave,
			}, -2)

		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		self["label"] = StaticText("")

		self.list = []
		ConfigListScreen.__init__(self, self.list, session = self.session, on_change = self.changedEntry)
		self.createSetup()
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.setTitle(self.setup_title)

	def createSetup(self):
		self.list = []
		self.list.append(getConfigListEntry(_("Server IP"), config.fhem.serverip))
		self.list.append(getConfigListEntry(_("Port"), config.fhem.port))
		self.list.append(getConfigListEntry(_("Username"), config.fhem.username))
		self.list.append(getConfigListEntry(_("Password"), config.fhem.password))
		self.list.append(getConfigListEntry(_("Group Elements By"), config.fhem.grouping))
		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)

	def keyRight(self):
		ConfigListScreen.keyRight(self)

	# for summary:
	def changedEntry(self):
		for x in self.onChangedEntry:
			x()

	def getCurrentEntry(self):
		return self["config"].getCurrent()[0]

	def getCurrentValue(self):
		return str(self["config"].getCurrent()[1].getText())

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
					print "FIXME in ElementList.selectionChanged"
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
		
