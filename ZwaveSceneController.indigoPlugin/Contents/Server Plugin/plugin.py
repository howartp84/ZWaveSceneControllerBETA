#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################
# Copyright (c) 2016, Perceptive Automation, LLC. All rights reserved.
# http://www.indigodomo.com

#Thanks to Scott Ainsworth, a SmartThings user, who worked out how to get RFWC5 working with ST - and thus enabled me to implement
#the same logic in this plugin.  Why oh why Cooper have to defy the zwave spec I don't understand, but at least we got there in the end!

import indigo

import os
import sys

import time
import datetime
import fnmatch

# Note the "indigo" module is automatically imported and made available inside
# our global name space by the host process.

########################################
# Tiny function to convert a list of integers (bytes in this case) to a
# hexidecimal string for pretty logging.
def convertListToHexStr(byteList):
	return ' '.join(["%02X" % byte for byte in byteList])

################################################################################
class Plugin(indigo.PluginBase):
	########################################
	def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
		super(Plugin, self).__init__(pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
		self.debug = pluginPrefs.get("showDebugInfo", True)

		self.events = dict()
		self.events["cmdReceived"] = dict()

		self.fireHash = ""

		self.fireID = 0 #For sending scene commands

		self.controllerIDs = list()

		self.zedFromDev = dict()
		self.zedFromNode = dict()
		self.devFromZed = dict()
		self.devFromNode = dict()
		self.nodeFromZed = dict()
		self.nodeFromDev = dict()

	########################################
	def startup(self):
		self.debugLog(u"startup called -- subscribing to all incoming Z-Wave commands")
		indigo.zwave.subscribeToIncoming()

	def shutdown(self):
		self.debugLog(u"shutdown called")

	def closedPrefsConfigUi(self, valuesDict, userCancelled):
		# Since the dialog closed we want to set the debug flag - if you don't directly use
		# a plugin's properties (and for debugLog we don't) you'll want to translate it to
		# the appropriate stuff here.
		if not userCancelled:
			self.debug = valuesDict.get("showDebugInfo", False)
			#self.sceneDevID = valuesDict.get("sceneDevID", 200)
			#self.sceneDevNode = indigo.devices[int(self.sceneDevID)].ownerProps['address']
			#indigo.server.log("Scene Device: %s" % indigo.devices[int(self.sceneDevID)].name)
			if self.debug:
				indigo.server.log("Debug logging enabled")
			else:
				indigo.server.log("Debug logging disabled")

	def deviceStartComm(self, dev):
		if (dev.deviceTypeId == "sceneController"):
			dev.stateListOrDisplayStateIdChanged()
			devID = dev.id
			zedID = dev.ownerProps['deviceId']
			nodeID = indigo.devices[int(zedID)].ownerProps['address']

			self.zedFromDev[int(devID)] = int(zedID)
			self.zedFromNode[int(nodeID)] = int(zedID)
			self.devFromZed[int(zedID)] = int(devID)
			self.devFromNode[int(nodeID)] = int(devID)
			self.nodeFromZed[int(zedID)] = int(nodeID)
			self.nodeFromDev[int(devID)] = int(nodeID)

			self.controllerIDs.append(nodeID)

	def deviceStopComm(self, dev):
		if (dev.deviceTypeId == "sceneController"):
			devID = dev.id
			zedID = dev.ownerProps['deviceId']
			nodeID = indigo.devices[int(zedID)].ownerProps['address']

			self.zedFromDev.pop(int(devID),None)
			self.zedFromNode.pop(int(nodeID),None)
			self.devFromZed.pop(int(zedID),None)
			self.devFromNode.pop(int(nodeID),None)
			self.nodeFromZed.pop(int(zedID),None)
			self.nodeFromDev.pop(int(devID),None)

			self.controllerIDs.remove(nodeID)

	########################################
	def zwaveCommandReceived(self, cmd):
		byteList = cmd['bytes']			# List of the raw bytes just received.
		byteListStr = convertListToHexStr(byteList)
		nodeId = cmd['nodeId']			# Can be None!
		endpoint = cmd['endpoint']		# Often will be None!

		bytes = byteListStr.split()

		#if (int(bytes[5],16)) not in self.controllerIDs:
			#self.debugLog(u"Node %s is not a scene controller - ignoring" % (int(bytes[5],16)))
			#return
		#else:
			#self.debugLog(u"Node ID %s found in controllerIDs" % (int(bytes[5],16)))

		if (int(bytes[5],16) == 34):			#Add node IDs here for debugging
			self.debugLog(u"Raw RFWC5 34 command: %s" % (byteListStr))

		if (int(bytes[5],16) == 35):			#Add node IDs here for debugging
			self.debugLog(u"Raw RFWC5 35 command: %s" % (byteListStr))

		if (bytes[7] == "2B") and (bytes[8] == "01"): #Basic Scene
			actions = ["-","Click","Double-Click","Brighten Start", "Dim Start", "Brighten Stop", "Dim Stop", "Triple-Click", "Quad-Click", "Quint-Click"]
			actionMap = {1:0, 2:1, 3:7, 4:9, 5:8, 6:10, 7:2, 8:3, 9:4}
			self.debugLog(u"-----")
			self.debugLog(u"Basic Scene Command received:")
			self.debugLog(u"Raw command: %s" % (byteListStr))
			#self.debugLog(u"Address: %s" % (bytes[5])) #zero-based
			self.debugLog(u"Node:      %s" % (int(bytes[5],16)))
			self.debugLog(u"NodeID:      %s" % (nodeId))

			actionRaw = int(bytes[9],16)
			self.debugLog(u"ActionRaw: %s" % (actionRaw))
			if (actionRaw < 10):
				self.debugLog(u"Button:    %s" % (str(int(bytes[9],16))))
				self.debugLog(u"ActionID:  1")
				self.debugLog(u"Action:    %s" % (actions[1]))
				actionIn = "1"
				action = str(actionMap[int(actionIn)])
				button = str(int(bytes[9],16))
			else:
				self.debugLog(u"Button:    %s" % (str(int(bytes[9],16))[0:1]))
				self.debugLog(u"ActionID:  %s" % (str(int(bytes[9],16))[1:2]))
				self.debugLog(u"Action:    %s" % (actions[int(str(int(bytes[9],16))[1:2])]))
				actionIn = str(int(bytes[9],16))[1:2]
				action = str(actionMap[int(actionIn)])
				button = str(int(bytes[9],16))[0:1]
			self.debugLog(u"-----")

			if (int(bytes[5],16)) in self.controllerIDs: #Full Scene support
				devID = self.devFromNode[int(bytes[5],16)]
				dev = indigo.devices[int(devID)]
				lastScene = dev.states['currentScene']
				repeatCount = dev.states['repeatCount']
				repeatStart = dev.states['repeatStart']
				if (repeatStart == ""):
					repeatStart = 0
				timeDif = time.time() - float(repeatStart)
				if ((lastScene == button) and (repeatCount < 4) and (timeDif < 2000)):
					dev.updateStateOnServer("repeatCount", repeatCount+1)
				else:
					dev.updateStateOnServer("repeatCount", 0)
					dev.updateStateOnServer("repeatStart", time.time())
					self.triggerEvent("cmdReceived",bytes[5],button,action)
					self.updateDevScene(int(bytes[5],16),button,action)
			else:
				self.triggerEvent("cmdReceived",bytes[5],button,action)
				self.updateDevScene(int(bytes[5],16),button,action)

		if (bytes[6] == "05") and (bytes[7] == "5B"): #Central Scene
			if (int(bytes[10],16) > 127):
				self.debugLog(u"B10: %s" % (int(bytes[10],16)))
				x = (int(bytes[10],16)-128)
				self.debugLog(u"X10: %s" % (x))
				bytes[10] = hex(x)[2:]
				self.debugLog(u"B10: %s" % (int(bytes[10],16)))
			actions = ["Click","Release","Hold", "Double-Click", "Triple-Click", "Quad-Click", "Quint-Click"]
			actionMap = {0:0, 1:6, 2:5, 3:1, 4:2, 5:3, 6:4}
			self.debugLog(u"-----")
			self.debugLog(u"Central Scene Command received:")
			self.debugLog(u"Raw command: %s" % (byteListStr))
			#self.debugLog(u"Address: %s" % (bytes[5])) #zero-based
			#self.debugLog(u"0x03:    %s" % (int(bytes[8],16))) #This is 0x03 Report (ie not Get/Set)
			self.debugLog(u"Node:    %s" % (int(bytes[5],16)))
			self.debugLog(u"Button:  %s" % (int(bytes[11],16)))
			self.debugLog(u"ActionID:  %s" % (int(bytes[10])))
			self.debugLog(u"Action:  %s" % (actions[int(bytes[10])]))
			#self.debugLog(u"FireID:  %s" % (int(bytes[9],16)))
			self.debugLog(u"-----")

			action = str(actionMap[int(bytes[10])])
			button = str(int(bytes[11],16))
			#if (self.fireHash <> None):
				#self.debugLog(u"Hash <> none")
			#if (self.fireHash <> (str(int(bytes[9],16))[0:1] + str(int(bytes[9],16)))):
				#self.debugLog(u"Hash <> strint")
			if (self.fireHash <> None) and (self.fireHash <> (str(int(bytes[9],16))[0:1] + str(int(bytes[9],16)))):
				#self.debugLog(u"Triggering button %s, action %s" % (button,action))
				self.triggerEvent("cmdReceived",bytes[5],button,action)
				self.updateDevScene(int(bytes[5],16),button,action)
			self.fireHash = str(int(bytes[9],16))[0:1] + str(int(bytes[9],16))
			self.debugLog(self.fireHash)

		if (bytes[7] == "2C") and (bytes[8] == "02"): #Scene Actuator Conf Get (probably from Enerwave)
			self.debugLog(u"-----")
			self.debugLog(u"Actuator Config Get received:")
			self.debugLog(u"Raw command: %s" % (byteListStr))
			self.debugLog(u"Node:      %s" % (int(bytes[5],16)))
			self.debugLog(u"Scene:      %s" % (int(bytes[9],16)))

			self.updateDevScene(int(bytes[5],16),int(bytes[9],16),"")

		if (bytes[7] == "2D") and (bytes[8] == "03"): #Scene Controller Config Report
			self.debugLog(u"-----")
			self.debugLog(u"Controller Config Report received:")
			self.debugLog(u"Raw command: %s" % (byteListStr))
			self.debugLog(u"Node:      %s" % (int(bytes[5],16)))
			self.debugLog(u"Group:      %s" % (int(bytes[9],16)))
			self.debugLog(u"Scene:      %s" % (int(bytes[10],16)))

			self.updateDevScene(int(bytes[5],16),int(bytes[10],16),"")



	def triggerStartProcessing(self, trigger):
		self.debugLog(u"Start processing trigger " + unicode(trigger.name))
		self.events[trigger.pluginTypeId][trigger.id] = trigger
		#self.debugLog(str(self.events["cmdReceived"][trigger.id].pluginProps["deviceAddress"]))
		#self.debugLog(str(self.events["cmdReceived"][trigger.id].pluginProps["deviceAddress"]))
		#self.debugLog(u"-----")
		#self.debugLog(u"Model ID:" + str(indigo.devices[int(self.events["cmdReceived"][trigger.id].pluginProps["deviceAddress"])].ownerProps['zwModelId']))
		#self.debugLog(u"-----")
		#self.debugLog(str(indigo.devices[575842701]))
		#dev = indigo.devices[575842701]
		#self.debugLog(dev.ownerProps['address'])

	def triggerStopProcessing(self, trigger):
		self.debugLog(u"Stop processing trigger " + unicode(trigger.name))
		if trigger.pluginTypeId in self.events:
			if trigger.id in self.events[trigger.pluginTypeId]:
				del self.events[trigger.pluginTypeId][trigger.id]

	def triggerEvent(self,eventType,deviceAddress,deviceButton,deviceAction):
		#self.plugin.debugLog(u"triggerEvent called")
		for trigger in self.events[eventType]:
			dAddress = self.events[eventType][trigger].pluginProps["deviceAddress"]
			#self.debugLog(dAddress)
			dDev = indigo.devices[int(dAddress)]
			if (fnmatch.fnmatch(str(int(deviceAddress,16)),str(dDev.ownerProps['address']))):
				if (fnmatch.fnmatch(str(int(deviceButton)),self.events[eventType][trigger].pluginProps["deviceButton"])):
					if (fnmatch.fnmatch(str(int(deviceAction)),self.events[eventType][trigger].pluginProps["deviceAction"])):
						indigo.trigger.execute(trigger)

	#SCENE_ACTIVATION 			0x2B	43
	#SCENE_ACTUATOR_CONF		0x2C	44
	#SCENE_CONTROLLER_CONF 	0x2D	45

	#SCENE_ACTIVATION_SET			0x01

	#SCENE_CONTROLLER_CONF_SET		0x01
	#SCENE_CONTROLLER_CONF_GET		0x02
	#SCENE_CONTROLLER_CONF_REPORT	0x03

	def testGet1(self):
		self.debugLog("MenuItem Get Button 1 called")
		codeStr = [45, 2, 1]
		indigo.zwave.sendRaw(device=indigo.devices[int(self.sceneDevID)],cmdBytes=codeStr,sendMode=1)

	def testGet2(self):
		self.debugLog("MenuItem Get Button 2 called")
		codeStr = [45, 2, 2]
		indigo.zwave.sendRaw(device=indigo.devices[int(self.sceneDevID)],cmdBytes=codeStr,sendMode=1)

	def testGet3(self):
		self.debugLog("MenuItem Get Button 3 called")
		codeStr = [45, 2, 3]
		indigo.zwave.sendRaw(device=indigo.devices[int(self.sceneDevID)],cmdBytes=codeStr,sendMode=1)

	def testSet1(self):
		self.debugLog("MenuItem Set Button 1 called")
		codeStr = [45, 1, 1, 1, 0]
		indigo.zwave.sendRaw(device=indigo.devices[int(self.sceneDevID)],cmdBytes=codeStr,sendMode=1)

	def testSet2(self):
		self.debugLog("MenuItem Set Button 2 called")
		codeStr = [45, 1, 2, 2, 0]
		indigo.zwave.sendRaw(device=indigo.devices[int(self.sceneDevID)],cmdBytes=codeStr,sendMode=1)

	def testSet3(self):
		self.debugLog("MenuItem Set Button 3 called")
		codeStr = [45, 1, 3, 3, 0]
		indigo.zwave.sendRaw(device=indigo.devices[int(self.sceneDevID)],cmdBytes=codeStr,sendMode=1)

	def testHex(self):
		#cmd = {'bytes': [0x01,0x0A,0x00,0x04,0x08,0x26,0x04,0x2B,0x01,0x01,0xFF,0x21], 'nodeId': None, 'endpoint': None} #Button 1, no action
		cmd = {'bytes': [0x01,0x0A,0x00,0x04,0x00,0x26,0x04,0x2B,0x01,0x0B,0xFF,0x0D], 'nodeId': None, 'endpoint': None} #Button 1, Click
		self.zwaveCommandReceived(cmd)

	#SCENE_ACTIVATION 			0x2B	43
	#SCENE_ACTUATOR_CONF		0x2C	44
	#SCENE_CONTROLLER_CONF 	0x2D	45

	#ASSOCIATION 						0x85	133
	#ASSOCIATION_COMMAND_CONFIGURATION	0x98	152

	#ASSOCIATION_SET			0x01
	#ASSOCIATION_GET			0x02
	#ASSOCIATION_REPORT		0x03
	#ASSOCIATION_REMOVE		0x04

	#CONFIGURATION 					0x70	112
	#CONFIGURATION_SET			0x03			(Not 1 as normal!!)
	#CONFIGURATION_GET			0x04			(Not 2 as normal!!)
	#CONFIGURATION_REPORT		0x05			(Not 3 as normal!!)

	#SCENE_ACTIVATION_SET			0x01

	#SCENE_CONTROLLER_CONF_SET		0x01
	#SCENE_CONTROLLER_CONF_GET		0x02
	#SCENE_CONTROLLER_CONF_REPORT	0x03

	#SWITCH_MULTILEVEL		0x26	38

	#SWITCH_MULTILEVEL_SET		0x01
	#SWITCH_MULTILEVEL_GET		0x02
	#SWITCH_MULTILEVEL_REPORT	0x03
	#SWITCH_MULTILEVEL_START_LEVEL_CHANGE		0x04
	#SWITCH_MULTILEVEL_STOP_LEVEL_CHANGE		0x05

	#COMMAND_CLASS_INDICATOR	0x87

	#Cooper supports classes:
	#20 v1 Basic
	#21 v1 Controller_Replication
	#22 v1 Application_Status
	#85 v1 Association
	#86 v1 Version
	#87 v1 Indicator
	#2B v1 Scene_Activation
	#2D v1 Scene_Controller_Conf
	#70 v1 Configuration
	#72 v1 Manufacturer_Specific
	#77 v1 Node_Naming




	def confController(self, valuesDict, typeId):
		self.debugLog("Configure Controller menuitem called")

		selfDev = indigo.devices[int(valuesDict["deviceId"])].ownerProps['deviceId']

		indigoDev = indigo.devices[int(selfDev)]

		self.debugLog("Controller selected: " + str(indigoDev.name))

		modelNo = str(valuesDict["modelNo"])

		if (modelNo == "RFWC5"):
			buttonCount = 5
		elif (modelNo == "ZWNSC7"):
			buttonCount = 7

		for i in range(1,buttonCount+1):
			self.debugLog(u"Removing button %s Associations" % (i))	#Remove associations for Group (aka Button)
			codeStr = [133, 4, i]
			indigo.zwave.sendRaw(device=indigoDev,cmdBytes=codeStr,sendMode=1)

			self.debugLog(u"Setting button %s Associations" % (i))	#Associate Group (aka Button) i to node 1 (controller)
			codeStr = [133, 1, i, 1]
			indigo.zwave.sendRaw(device=indigoDev,cmdBytes=codeStr,sendMode=1)

			self.debugLog(u"Setting button %s Parameters" % (i))	#Set level for Parameter (aka Button!) i to 0xFF ("On")
			codeStr = [112, 3, i, 255]
			indigo.zwave.sendRaw(device=indigoDev,cmdBytes=codeStr,sendMode=1)

			self.debugLog(u"Setting button %s Scene No" % (i))	#Set Group (aka Button) i to activate Scene i, over 0 seconds. [Works for Enerwave]
			codeStr = [45, 1, i, i, 0]
			indigo.zwave.sendRaw(device=indigoDev,cmdBytes=codeStr,sendMode=1)

		errorsDict = indigo.Dict()
		return (True, valuesDict, errorsDict)

	def cmdVersion(self, valuesDict, typeId):
		self.debugLog("Get Command Version menuitem called")

		selfDev = indigo.devices[int(valuesDict["deviceId"])].ownerProps['deviceId']

		indigoDev = indigo.devices[int(selfDev)]

		self.debugLog("Controller selected: " + str(indigoDev.name))

		self.debugLog(u"Requesting switch_multilevel command version: ") #Returns zero because RFWC5 doesn't support it
		codeStr = [134, 19, 38]
		indigo.zwave.sendRaw(device=indigoDev,cmdBytes=codeStr,sendMode=1)

		self.debugLog(u"Requesting associations for group 1: ")
		codeStr = [133, 2, 1]
		indigo.zwave.sendRaw(device=indigoDev,cmdBytes=codeStr,sendMode=1)

		self.debugLog(u"Requesting associations for group 2: ")
		codeStr = [133, 2, 2]
		indigo.zwave.sendRaw(device=indigoDev,cmdBytes=codeStr,sendMode=1)

		self.debugLog(u"Requesting associations for group 3: ")
		codeStr = [133, 2, 3]
		indigo.zwave.sendRaw(device=indigoDev,cmdBytes=codeStr,sendMode=1)


	def updateDevScene(self, inNode, inButton, inAction):
		for dev in indigo.devices.iter("self"):
			dNode = indigo.devices[int(dev.ownerProps['deviceId'])].ownerProps['address']
			if (int(dNode) == int(inNode)):
				self.debugLog(u"Updating device %s with button %s" % (dev.name,inButton))
				dev.updateStateOnServer("currentScene", "Scene %s" % (inButton))

	def getScene(self,pluginAction):
		self.debugLog("getScene called")

		selfDev = indigo.devices[int(pluginAction.deviceId)].ownerProps['deviceId']

		indigoDev = indigo.devices[int(selfDev)]

		codeStr = [45, 2, 0]
		indigo.zwave.sendRaw(device=indigoDev,cmdBytes=codeStr,sendMode=1)

	def setScene(self,pluginAction):
		self.debugLog("setScene called")

		selfDev = indigo.devices[int(pluginAction.deviceId)].ownerProps['deviceId']

		indigoDev = indigo.devices[int(selfDev)]

		sceneNo = pluginAction.props["sceneNo"]

		codeStr = [43, 1, int(sceneNo), 0]

		indigo.zwave.sendRaw(device=indigoDev,cmdBytes=codeStr,sendMode=1)

	def callHomePress(self):
		self.debugLog("Call Home Position Press menuitem called")

		indigoDev = indigo.devices["Blind Office Entrance"]

		self.debugLog("Blind selected: " + str(indigoDev.name))

		self.debugLog(u"Sending Home Position command... hopefully... ")
		codeStr = [38, 5] #Press
		indigo.zwave.sendRaw(device=indigoDev,cmdBytes=codeStr,sendMode=1)

		self.fireID = self.fireID +1

	def callHomeHold(self):
		self.debugLog("Call Home Position Hold Release menuitem called")

		indigoDev = indigo.devices["Blind Office Entrance"]

		self.debugLog("Blind selected: " + str(indigoDev.name))

		self.debugLog(u"Sending Home Position command... hopefully... ")
		codeStr = [91, 3, int(self.fireID), 1, 3] #Hold
		indigo.zwave.sendRaw(device=indigoDev,cmdBytes=codeStr,sendMode=1)
		self.fireID = self.fireID +1

		codeStr = [91, 3, int(self.fireID), 2, 3] #Release
		indigo.zwave.sendRaw(device=indigoDev,cmdBytes=codeStr,sendMode=1)

		self.fireID = self.fireID +1

	def callPosition(self, valuesDict, typeId):
		self.debugLog("Call Position menuitem called")

		position = int(valuesDict["position"])

		indigoDev = indigo.devices["Blind Office Entrance"]

		self.debugLog("Blind selected: " + str(indigoDev.name))

		self.debugLog(u"Setting blind to position %s ... hopefully... " % (position))
		codeStr = [38, 1, int(position), 255] #Position, instant
		indigo.zwave.sendRaw(device=indigoDev,cmdBytes=codeStr,sendMode=1)



