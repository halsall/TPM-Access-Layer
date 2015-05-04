#!/usr/bin/env python
# -*- coding:utf-8 -*- 


##############################################################################
## license :
##============================================================================
##
## File :        TPM_DS.py
## 
## Project :     AAVS Tango TPM Driver
##
## This file is part of Tango device class.
## 
## Tango is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
## 
## Tango is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
## 
## You should have received a copy of the GNU General Public License
## along with Tango.  If not, see <http://www.gnu.org/licenses/>.
## 
##
## $Author :      andrea.demarco$
##
## $Revision :    $
##
## $Date :        $
##
## $HeadUrl :     $
##============================================================================
##            This file is generated by POGO
##    (Program Obviously used to Generate tango Object)
##
##        (c) - Software Engineering Group - ESRF
##############################################################################

"""A Tango device server for the TPM board."""

__all__ = ["TPM_DS", "TPM_DSClass", "main"]

__docformat__ = 'restructuredtext'

import PyTango
import sys
# Add additional import
#----- PROTECTED REGION ID(TPM_DS.additionnal_import) ENABLED START -----#
from PyTango import Util, Attr, SpectrumAttr
from PyTango._PyTango import DevFailed
from accesslayer import *
from definitions import *
from types import *
import pickle
#----- PROTECTED REGION END -----#	//	TPM_DS.additionnal_import

## Device States Description
## UNKNOWN : 

class TPM_DS (PyTango.Device_4Impl):

    #--------- Add you global variables here --------------------------
    #----- PROTECTED REGION ID(TPM_DS.global_variables) ENABLED START -----#
    global tpm_instance
    tpm_instance = None

    # State flow definitions - allowed states for each command
    state_list = {
        'loadFirmWareBlocking': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'getRegisterList': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'getDeviceList': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'Connect': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'Disconnect': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'getFirmwareList': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'getRegisterInfo': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'createScalarAttribute': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'createVectorAttribute': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'readRegister': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'writeRegister': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'generateAttributes': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'flushAttributes': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'readAddress': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'writeAddress': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'readDevice': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'writeDevice': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'setBoardState': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'addCommand': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'removeCommand': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    }

    def checkStateFlow(self, fnName):
        """ Checks if the current state the device is in one of the states in a given list of allowed states for a paticular function.

        :param : Name of command to be executed
        :type: String
        :return: True if allowed, false if not.
        :rtype: PyTango.DevBoolean """

        # get allowed states for this command
        fnAllowedStates = self.state_list(fnName)
        allowed = not(self.get_state() in fnAllowedStates)
        return allowed

    def getDevice(self, name):
        """ Extract device name from provided register name, if present """
        try:
            device = name.split('.')[0].upper()
            if device == "BOARD":
                return Device.Board
            elif device == "FPGA1":
                return Device.FPGA_1
            elif device == "FPGA2":
                return Device.FPGA_2
            else:
                return None
        except:
            return None

    def read_GeneralScalar(self, attr):
        """ A method that reads from a scalar attribute.

        :param attr: The attribute to read from.
        :type: PyTango.DevAttr
        :return: The read data.
        :rtype: PyTango.DevULong """
        self.info_stream("Reading attribute %s", attr.get_name())
        arguments = {}
        dev = self.getDevice(attr.get_name())
        arguments['device'] = dev.value
        arguments['register'] = attr.get_name()
        arguments['words'] = 1
        arguments['offset'] = 0
        args = str(arguments)
        values_array = self.readRegister(args)  #get actual value by reading from register
        attr.set_value(values_array[0]) # readRegister returns an array, so a scalar requires a read from 0'th location

    def write_GeneralScalar(self, attr):
        """ A method that writes to a scalar attribute.

        :param attr: The attribute to write to.
        :type: PyTango.DevAttr
        :return: Success or failure.
        :rtype: PyTango.DevBoolean """
        self.info_stream("Writing attribute %s", attr.get_name())
        data = attr.get_write_value()
        arguments = {}
        dev = self.getDevice(attr.get_name())
        arguments['device'] = dev.value
        arguments['register'] = attr.get_name()
        arguments['offset'] = 0
        arguments['values'] = data
        args = str(arguments)
        self.writeRegister(args)

    def read_GeneralVector(self, attr):
        """ A method that reads from a scalar attribute.

        :param attr: The attribute to read from.
        :type: PyTango.DevAttr
        :return: The read data.
        :rtype: PyTango.DevVarULongArray """
        self.info_stream("Reading attribute %s", attr.get_name())
        arguments = {}
        dev = self.getDevice(attr.get_name())
        arguments['device'] = dev.value
        arguments['register'] = attr.get_name()
        arguments['words'] = 1
        arguments['offset'] = 0
        args = str(arguments)
        values_array = self.readRegister(args)  #get actual values by reading from register
        attr.set_value(values_array) # readRegister returns an array

    def write_GeneralVector(self, attr):
        """ A method that writes to a vector attribute.

        :param attr: The attribute to write to.
        :type: PyTango.DevAttr
        :return: Success or failure.
        :rtype: PyTango.DevBoolean """
        self.info_stream("Writting attribute %s", attr.get_name())
        data = attr.get_write_value()
        arguments = {}
        dev = self.getDevice(attr.get_name())
        arguments['device'] = dev.value
        arguments['register'] = attr.get_name()
        arguments['offset'] = 0
        arguments['values'] = data
        args = str(arguments)
        self.writeRegister(args)

    #----- PROTECTED REGION END -----#	//	TPM_DS.global_variables

    def __init__(self,cl, name):
        PyTango.Device_4Impl.__init__(self,cl,name)
        self.debug_stream("In __init__()")
        TPM_DS.init_device(self)
        #----- PROTECTED REGION ID(TPM_DS.__init__) ENABLED START -----#
        #self.tpm_instance = None
        #----- PROTECTED REGION END -----#	//	TPM_DS.__init__
        
    def delete_device(self):
        self.debug_stream("In delete_device()")
        #----- PROTECTED REGION ID(TPM_DS.delete_device) ENABLED START -----#
        
        #----- PROTECTED REGION END -----#	//	TPM_DS.delete_device

    def init_device(self):
        self.debug_stream("In init_device()")
        self.get_device_properties(self.get_device_class())
        self.attr_boardState_read = 0
        #----- PROTECTED REGION ID(TPM_DS.init_device) ENABLED START -----#
        self.info_stream("Starting device initialization...")
        self.set_state(PyTango.DevState.UNKNOWN)
        self.tpm_instance = TPM(ip="127.0.0.1", port=10000)
        self.setBoardState(BoardState.INIT.value)
        self.info_stream("Device has been initialized.")
        #----- PROTECTED REGION END -----#	//	TPM_DS.init_device

    def always_executed_hook(self):
        self.debug_stream("In always_excuted_hook()")
        #----- PROTECTED REGION ID(TPM_DS.always_executed_hook) ENABLED START -----#
        
        #----- PROTECTED REGION END -----#	//	TPM_DS.always_executed_hook

    #-----------------------------------------------------------------------------
    #    TPM_DS read/write attribute methods
    #-----------------------------------------------------------------------------
    
    def read_boardState(self, attr):
        self.debug_stream("In read_boardState()")
        #----- PROTECTED REGION ID(TPM_DS.boardState_read) ENABLED START -----#
        attr.set_value(self.attr_boardStatus_read)
        #----- PROTECTED REGION END -----#	//	TPM_DS.boardState_read
        
    def is_boardState_allowed(self, attr):
        self.debug_stream("In is_boardState_allowed()")
        state_ok = not(self.get_state() in [PyTango.DevState.UNKNOWN])
        #----- PROTECTED REGION ID(TPM_DS.is_boardState_allowed) ENABLED START -----#
        state_ok = True
        #----- PROTECTED REGION END -----#	//	TPM_DS.is_boardState_allowed
        return state_ok
        
    
    
        #----- PROTECTED REGION ID(TPM_DS.initialize_dynamic_attributes) ENABLED START -----#
        
        #----- PROTECTED REGION END -----#	//	TPM_DS.initialize_dynamic_attributes
            
    def read_attr_hardware(self, data):
        self.debug_stream("In read_attr_hardware()")
        #----- PROTECTED REGION ID(TPM_DS.read_attr_hardware) ENABLED START -----#
        
        #----- PROTECTED REGION END -----#	//	TPM_DS.read_attr_hardware


    #-----------------------------------------------------------------------------
    #    TPM_DS command methods
    #-----------------------------------------------------------------------------
    
    def Connect(self, argin):
        """ Opens the connection to the device.
        
        :param argin: Device IP address and port number.
        :type: PyTango.DevString
        :return: 
        :rtype: PyTango.DevVoid """
        self.debug_stream("In Connect()")
        #----- PROTECTED REGION ID(TPM_DS.Connect) ENABLED START -----#
        arguments = eval(argin)
        ip_str = arguments['ip']
        port = arguments['port']
        self.tpm_instance.connect(ip_str, port)
        #----- PROTECTED REGION END -----#	//	TPM_DS.Connect
        
    def is_Connect_allowed(self):
        self.debug_stream("In is_Connect_allowed()")
        state_ok = not(self.get_state() in [PyTango.DevState.UNKNOWN])
        #----- PROTECTED REGION ID(TPM_DS.is_Connect_allowed) ENABLED START -----#
        state_ok = self.checkStateFlow(self.Connect.__name__)
        #----- PROTECTED REGION END -----#	//	TPM_DS.is_Connect_allowed
        return state_ok
        
    def Disconnect(self):
        """ Disconnect this device.
        
        :param : 
        :type: PyTango.DevVoid
        :return: 
        :rtype: PyTango.DevVoid """
        self.debug_stream("In Disconnect()")
        #----- PROTECTED REGION ID(TPM_DS.Disconnect) ENABLED START -----#
        self.tpm_instance.disconnect()
        #----- PROTECTED REGION END -----#	//	TPM_DS.Disconnect
        
    def is_Disconnect_allowed(self):
        self.debug_stream("In is_Disconnect_allowed()")
        state_ok = not(self.get_state() in [PyTango.DevState.UNKNOWN])
        #----- PROTECTED REGION ID(TPM_DS.is_Disconnect_allowed) ENABLED START -----#
        state_ok = self.checkStateFlow(self.Disconnect.__name__)
        #----- PROTECTED REGION END -----#	//	TPM_DS.is_Disconnect_allowed
        return state_ok
        
    def addCommand(self, argin):
        """ A generic command that adds a new command entry to the Tango device driver.
        
        :param argin: A string containing a dictionary for fields required for command creation.
        :type: PyTango.DevString
        :return: True if command creation was successful, false if not.
        :rtype: PyTango.DevBoolean """
        self.debug_stream("In addCommand()")
        argout = False
        #----- PROTECTED REGION ID(TPM_DS.addCommand) ENABLED START -----#
        #  Protect the script from exceptions raised by Tango
        try:
            # Try create a new command entry
            arguments = eval(argin)
            commandName = arguments['commandName']
            inValue = arguments['inType']
            inType = arguments['inDesc']
            outType = arguments['outType']
            outDesc = arguments['outDesc']
            allowedStates = arguments['states']

            self.state_list[commandName] = allowedStates
            self.cmd_list[commandName] = [[inType, inValue], [outType, outDesc]]
            argout = True
        except DevFailed as df:
            print("Failed to create new command entry in device server: \n%s" % df)
            argout = False
        finally:
            return argout
        #----- PROTECTED REGION END -----#	//	TPM_DS.addCommand
        return argout
        
    def is_addCommand_allowed(self):
        self.debug_stream("In is_addCommand_allowed()")
        state_ok = not(self.get_state() in [PyTango.DevState.UNKNOWN])
        #----- PROTECTED REGION ID(TPM_DS.is_addCommand_allowed) ENABLED START -----#
        state_ok = self.checkStateFlow(self.addCommand.__name__)
        #----- PROTECTED REGION END -----#	//	TPM_DS.is_addCommand_allowed
        return state_ok
        
    def createScalarAttribute(self, argin):
        """ A method that creates a new scalar attribute.
        
        :param argin: New attribute name.
        :type: PyTango.DevString
        :return: 
        :rtype: PyTango.DevVoid """
        self.debug_stream("In createScalarAttribute()")
        #----- PROTECTED REGION ID(TPM_DS.createScalarAttribute) ENABLED START -----#
        attr = Attr(argin, PyTango.DevULong)
        self.add_attribute(attr, self.read_GeneralScalar, self.write_GeneralScalar)
        #----- PROTECTED REGION END -----#	//	TPM_DS.createScalarAttribute
        
    def is_createScalarAttribute_allowed(self):
        self.debug_stream("In is_createScalarAttribute_allowed()")
        state_ok = not(self.get_state() in [PyTango.DevState.UNKNOWN])
        #----- PROTECTED REGION ID(TPM_DS.is_createScalarAttribute_allowed) ENABLED START -----#
        state_ok = self.checkStateFlow(self.createScalarAttribute.__name__)
        #----- PROTECTED REGION END -----#	//	TPM_DS.is_createScalarAttribute_allowed
        return state_ok
        
    def createVectorAttribute(self, argin):
        """ A method that creates a new vector attribute.
        
        :param argin: New attribute name.
        :type: PyTango.DevString
        :return: 
        :rtype: PyTango.DevVoid """
        self.debug_stream("In createVectorAttribute()")
        #----- PROTECTED REGION ID(TPM_DS.createVectorAttribute) ENABLED START -----#
        attr = SpectrumAttr(argin, PyTango.DevULong, PyTango.READ_WRITE, len)
        self.add_attribute(attr, self.read_GeneralVector, self.write_GeneralVector)
        #----- PROTECTED REGION END -----#	//	TPM_DS.createVectorAttribute
        
    def is_createVectorAttribute_allowed(self):
        self.debug_stream("In is_createVectorAttribute_allowed()")
        state_ok = not(self.get_state() in [PyTango.DevState.UNKNOWN])
        #----- PROTECTED REGION ID(TPM_DS.is_createVectorAttribute_allowed) ENABLED START -----#
        state_ok = self.checkStateFlow(self.createVectorAttribute.__name__)
        #----- PROTECTED REGION END -----#	//	TPM_DS.is_createVectorAttribute_allowed
        return state_ok
        
    def flushAttributes(self):
        """ A method that removes all attributes for the current firmware.
        
        :param : 
        :type: PyTango.DevVoid
        :return: 
        :rtype: PyTango.DevVoid """
        self.debug_stream("In flushAttributes()")
        #----- PROTECTED REGION ID(TPM_DS.flushAttributes) ENABLED START -----#
        register_dict = self.tpm_instance.getRegisterList()
        if register_dict is not None:
            for reg_name, entries in register_dict.iteritems():
                self.remove_attribute(reg_name)
        #----- PROTECTED REGION END -----#	//	TPM_DS.flushAttributes
        
    def is_flushAttributes_allowed(self):
        self.debug_stream("In is_flushAttributes_allowed()")
        state_ok = not(self.get_state() in [PyTango.DevState.UNKNOWN])
        #----- PROTECTED REGION ID(TPM_DS.is_flushAttributes_allowed) ENABLED START -----#
        state_ok = self.checkStateFlow(self.flushAttributes.__name__)
        #----- PROTECTED REGION END -----#	//	TPM_DS.is_flushAttributes_allowed
        return state_ok
        
    def generateAttributes(self):
        """ A method that generates dynamic attributes based on the current firmware.
        
        :param : 
        :type: PyTango.DevVoid
        :return: 
        :rtype: PyTango.DevVoid """
        self.debug_stream("In generateAttributes()")
        #----- PROTECTED REGION ID(TPM_DS.generateAttributes) ENABLED START -----#
        register_dict = self.tpm_instance.getRegisterList()
        for reg_name, entries in register_dict.iteritems():
            size = entries.get('size')
            #print reg_name, size
            if size > 1:
                self.createVectorAttribute(reg_name, size)
            else:
                self.createScalarAttribute(reg_name)
        #----- PROTECTED REGION END -----#	//	TPM_DS.generateAttributes
        
    def is_generateAttributes_allowed(self):
        self.debug_stream("In is_generateAttributes_allowed()")
        state_ok = not(self.get_state() in [PyTango.DevState.UNKNOWN])
        #----- PROTECTED REGION ID(TPM_DS.is_generateAttributes_allowed) ENABLED START -----#
        state_ok = self.checkStateFlow(self.generateAttributes.__name__)
        #----- PROTECTED REGION END -----#	//	TPM_DS.is_generateAttributes_allowed
        return state_ok
        
    def getDeviceList(self):
        """ Returns a list of devices, as a serialized python dictionary, stored as a string.
        
        :param : 
        :type: PyTango.DevVoid
        :return: Dictionary of devices.
        :rtype: PyTango.DevString """
        self.debug_stream("In getDeviceList()")
        argout = ''
        #----- PROTECTED REGION ID(TPM_DS.getDeviceList) ENABLED START -----#
        devlist = self.tpm_instance.getDeviceList()
        argout = pickle.dumps(devlist)
        #----- PROTECTED REGION END -----#	//	TPM_DS.getDeviceList
        return argout
        
    def is_getDeviceList_allowed(self):
        self.debug_stream("In is_getDeviceList_allowed()")
        state_ok = not(self.get_state() in [PyTango.DevState.UNKNOWN])
        #----- PROTECTED REGION ID(TPM_DS.is_getDeviceList_allowed) ENABLED START -----#
        state_ok = self.checkStateFlow(self.getDeviceList.__name__)
        #----- PROTECTED REGION END -----#	//	TPM_DS.is_getDeviceList_allowed
        return state_ok
        
    def getFirmwareList(self, argin):
        """ Returns a list of firmwares, as a serialized python dictionary, stored as a string.
        
        :param argin: Device on board to get list of firmware, as a string.
        :type: PyTango.DevString
        :return: Dictionary of firmwares on the board.
        :rtype: PyTango.DevString """
        self.debug_stream("In getFirmwareList()")
        argout = ''
        #----- PROTECTED REGION ID(TPM_DS.getFirmwareList) ENABLED START -----#
        arguments = eval(argin)
        device = arguments['device']
        firmware_list = self.tpm_instance.getFirmwareList(Device(device))
        argout = pickle.dumps(firmware_list)
        #----- PROTECTED REGION END -----#	//	TPM_DS.getFirmwareList
        return argout
        
    def is_getFirmwareList_allowed(self):
        self.debug_stream("In is_getFirmwareList_allowed()")
        state_ok = not(self.get_state() in [PyTango.DevState.UNKNOWN])
        #----- PROTECTED REGION ID(TPM_DS.is_getFirmwareList_allowed) ENABLED START -----#
        state_ok = self.checkStateFlow(self.getFirmwareList.__name__)
        #----- PROTECTED REGION END -----#	//	TPM_DS.is_getFirmwareList_allowed
        return state_ok
        
    def getRegisterInfo(self, argin):
        """ Gets a dictionary of information associated with a specified register.
        
        :param argin: The register name for which information will be retrieved.
        :type: PyTango.DevString
        :return: Returns a string-encoded dictionary of information.
        :rtype: PyTango.DevString """
        self.debug_stream("In getRegisterInfo()")
        argout = ''
        #----- PROTECTED REGION ID(TPM_DS.getRegisterInfo) ENABLED START -----#
        reglist = self.tpm_instance.getRegisterList()
        value = reglist.get(argin)
        argout = pickle.dumps(value)
        #----- PROTECTED REGION END -----#	//	TPM_DS.getRegisterInfo
        return argout
        
    def is_getRegisterInfo_allowed(self):
        self.debug_stream("In is_getRegisterInfo_allowed()")
        state_ok = not(self.get_state() in [PyTango.DevState.UNKNOWN])
        #----- PROTECTED REGION ID(TPM_DS.is_getRegisterInfo_allowed) ENABLED START -----#
        state_ok = self.checkStateFlow(self.getRegisterInfo.__name__)
        #----- PROTECTED REGION END -----#	//	TPM_DS.is_getRegisterInfo_allowed
        return state_ok
        
    def getRegisterList(self):
        """ Returns a list of registers and values, as a serialized python dictionary, stored as a string.
        
        :param : 
        :type: PyTango.DevVoid
        :return: List of register names.
        :rtype: PyTango.DevVarStringArray """
        self.debug_stream("In getRegisterList()")
        argout = ['']
        #----- PROTECTED REGION ID(TPM_DS.getRegisterList) ENABLED START -----#
        register_dict = self.tpm_instance.getRegisterList()
        argout = register_dict.keys()
        #----- PROTECTED REGION END -----#	//	TPM_DS.getRegisterList
        return argout
        
    def is_getRegisterList_allowed(self):
        self.debug_stream("In is_getRegisterList_allowed()")
        state_ok = not(self.get_state() in [PyTango.DevState.UNKNOWN])
        #----- PROTECTED REGION ID(TPM_DS.is_getRegisterList_allowed) ENABLED START -----#
        state_ok = self.checkStateFlow(self.getRegisterList.__name__)
        #----- PROTECTED REGION END -----#	//	TPM_DS.is_getRegisterList_allowed
        return state_ok
        
    def loadfirmwareblocking(self, argin):
        """ Blocking call to load firmware.
        
        :param argin: File path.
        :type: PyTango.DevString
        :return: 
        :rtype: PyTango.DevVoid """
        self.debug_stream("In loadfirmwareblocking()")
        #----- PROTECTED REGION ID(TPM_DS.loadfirmwareblocking) ENABLED START -----#
        arguments = eval(argin)
        device = arguments['device']
        filepath = arguments['path']
        self.flushAttributes()
        self.tpm_instance.loadFirmwareBlocking(Device(device), filepath)
        self.generateAttributes()
        #----- PROTECTED REGION END -----#	//	TPM_DS.loadfirmwareblocking
        
    def is_loadfirmwareblocking_allowed(self):
        self.debug_stream("In is_loadfirmwareblocking_allowed()")
        state_ok = not(self.get_state() in [PyTango.DevState.UNKNOWN])
        #----- PROTECTED REGION ID(TPM_DS.is_loadfirmwareblocking_allowed) ENABLED START -----#
        state_ok = self.checkStateFlow(self.is_loadfirmwareblocking.__name__)
        #----- PROTECTED REGION END -----#	//	TPM_DS.is_loadfirmwareblocking_allowed
        return state_ok
        
    def readAddress(self, argin):
        """ Reads values from a register location. Instead of a register name, the actual physical address has to be provided.
        
        :param argin: Associated register information.
        :type: PyTango.DevString
        :return: Register values.
        :rtype: PyTango.DevVarULongArray """
        self.debug_stream("In readAddress()")
        argout = [0]
        #----- PROTECTED REGION ID(TPM_DS.readAddress) ENABLED START -----#
        arguments = eval(argin)
        address = arguments['address']
        words = arguments['words']
        argout = self.tpm_instance.readAddress(address, words)
        #----- PROTECTED REGION END -----#	//	TPM_DS.readAddress
        return argout
        
    def is_readAddress_allowed(self):
        self.debug_stream("In is_readAddress_allowed()")
        state_ok = not(self.get_state() in [PyTango.DevState.UNKNOWN])
        #----- PROTECTED REGION ID(TPM_DS.is_readAddress_allowed) ENABLED START -----#
        state_ok = self.checkStateFlow(self.readAddress.__name__)
        #----- PROTECTED REGION END -----#	//	TPM_DS.is_readAddress_allowed
        return state_ok
        
    def readDevice(self, argin):
        """ Get device value.
        
        :param argin: 
            String containing:
            1) SPI Device to read from
            2) Address on device to read from
        :type: PyTango.DevString
        :return: Value of device.
        :rtype: PyTango.DevULong """
        self.debug_stream("In readDevice()")
        argout = 0
        #----- PROTECTED REGION ID(TPM_DS.readDevice) ENABLED START -----#
        arguments = eval(argin)
        device = arguments['device']
        address = arguments['address']
        argout = self.tpm_instance.readDevice(device, address)
        #----- PROTECTED REGION END -----#	//	TPM_DS.readDevice
        return argout
        
    def is_readDevice_allowed(self):
        self.debug_stream("In is_readDevice_allowed()")
        state_ok = not(self.get_state() in [PyTango.DevState.UNKNOWN])
        #----- PROTECTED REGION ID(TPM_DS.is_readDevice_allowed) ENABLED START -----#
        state_ok = self.checkStateFlow(self.readDevice.__name__)
        #----- PROTECTED REGION END -----#	//	TPM_DS.is_readDevice_allowed
        return state_ok
        
    def readRegister(self, argin):
        """ Reads values from a register location.
        
        :param argin: Associated register information.
        :type: PyTango.DevString
        :return: Register values.
        :rtype: PyTango.DevVarULongArray """
        self.debug_stream("In readRegister()")
        argout = [0]
        #----- PROTECTED REGION ID(TPM_DS.readRegister) ENABLED START -----#
        arguments = eval(argin)
        device = arguments['device']
        register = arguments['register']
        words = arguments['words']
        offset = arguments['offset']
        argout = self.tpm_instance.readRegister(Device(device), register, words, offset)
        #----- PROTECTED REGION END -----#	//	TPM_DS.readRegister
        return argout
        
    def is_readRegister_allowed(self):
        self.debug_stream("In is_readRegister_allowed()")
        state_ok = not(self.get_state() in [PyTango.DevState.UNKNOWN])
        #----- PROTECTED REGION ID(TPM_DS.is_readRegister_allowed) ENABLED START -----#
        state_ok = self.checkStateFlow(self.readRegister.__name__)
        #----- PROTECTED REGION END -----#	//	TPM_DS.is_readRegister_allowed
        return state_ok
        
    def removeCommand(self, argin):
        """ A generic command that removes a command entry from the Tango device driver.
        
        :param argin: Command name.
        :type: PyTango.DevString
        :return: True if command removal was successful, false otherwise.
        :rtype: PyTango.DevBoolean """
        self.debug_stream("In removeCommand()")
        argout = False
        #----- PROTECTED REGION ID(TPM_DS.removeCommand) ENABLED START -----#
        try:
            del self.cmd_list[argin]
            del self.state_list[argin]
            argout = True
        except DevFailed as df:
            print("Failed to remove command entry in device server: \n%s" % df)
            argout = False
        finally:
            return argout
        #----- PROTECTED REGION END -----#	//	TPM_DS.removeCommand
        return argout
        
    def is_removeCommand_allowed(self):
        self.debug_stream("In is_removeCommand_allowed()")
        state_ok = not(self.get_state() in [PyTango.DevState.UNKNOWN])
        #----- PROTECTED REGION ID(TPM_DS.is_removeCommand_allowed) ENABLED START -----#
        state_ok = self.checkStateFlow(self.removeCommand.__name__)
        #----- PROTECTED REGION END -----#	//	TPM_DS.is_removeCommand_allowed
        return state_ok
        
    def setBoardState(self, argin):
        """ Sets the board status by passing in a value.
                UNKNOWN	=  0
                INIT		=  1
                ON		=  2
                RUNNING	=  3
                FAULT		=  4
                OFF		=  5
                STANDBY	=  6
                SHUTTING_DOWN	=  7
                MAINTENANCE	=  8
                LOW_POWER	=  9
                SAFE_STATE	=  10
        
        :param argin: Board status value.
        :type: PyTango.DevLong
        :return: 
        :rtype: PyTango.DevVoid """
        self.debug_stream("In setBoardState()")
        #----- PROTECTED REGION ID(TPM_DS.setBoardState) ENABLED START -----#
        self.attr_boardState_read = argin

    def is_setBoardState_allowed(self):
        self.debug_stream("In is_setBoardState_allowed()")
        state_ok = not(self.get_state() in [PyTango.DevState.UNKNOWN])
        #----- PROTECTED REGION ID(TPM_DS.is_setBoardState_allowed) ENABLED START -----#
        state_ok = True
        #----- PROTECTED REGION END -----#	//	TPM_DS.is_setBoardState_allowed
        
    def is_setBoardState_allowed(self):
        self.debug_stream("In is_setBoardState_allowed()")
        state_ok = not(self.get_state() in [PyTango.DevState.UNKNOWN])
        #----- PROTECTED REGION ID(TPM_DS.is_setBoardState_allowed) ENABLED START -----#
        
        #----- PROTECTED REGION END -----#	//	TPM_DS.is_setBoardState_allowed
        return state_ok
        
    def writeAddress(self, argin):
        """ Writes values to a register location. The actual physical address has to be provided.
        
        :param argin: Associated register information.
        :type: PyTango.DevString
        :return: True if successful, false if not.
        :rtype: PyTango.DevBoolean """
        self.debug_stream("In writeAddress()")
        argout = False
        #----- PROTECTED REGION ID(TPM_DS.writeAddress) ENABLED START -----#
        arguments = eval(argin)
        address = arguments['address']
        values = arguments['values']
        argout = self.tpm_instance.writeAddress(address, values)
        #----- PROTECTED REGION END -----#	//	TPM_DS.writeAddress
        return argout
        
    def is_writeAddress_allowed(self):
        self.debug_stream("In is_writeAddress_allowed()")
        state_ok = not(self.get_state() in [PyTango.DevState.UNKNOWN])
        #----- PROTECTED REGION ID(TPM_DS.is_writeAddress_allowed) ENABLED START -----#
        state_ok = self.checkStateFlow(self.writeAddress.__name__)
        #----- PROTECTED REGION END -----#	//	TPM_DS.is_writeAddress_allowed
        return state_ok
        
    def writeDevice(self, argin):
        """ Set device value.
        
        :param argin: 
            A string containing the following:
            1) SPI device to write to
            2) Address on device to write to
            3) Value to write
        :type: PyTango.DevString
        :return: True if successful, false if not.
        :rtype: PyTango.DevBoolean """
        self.debug_stream("In writeDevice()")
        argout = False
        #----- PROTECTED REGION ID(TPM_DS.writeDevice) ENABLED START -----#
        arguments = eval(argin)
        device = arguments['device']
        address = arguments['address']
        value = arguments['value']
        argout = self.tpm_instance.writeDevice(device, address, value)
        #----- PROTECTED REGION END -----#	//	TPM_DS.writeDevice
        return argout
        
    def is_writeDevice_allowed(self):
        self.debug_stream("In is_writeDevice_allowed()")
        state_ok = not(self.get_state() in [PyTango.DevState.UNKNOWN])
        #----- PROTECTED REGION ID(TPM_DS.is_writeDevice_allowed) ENABLED START -----#
        state_ok = self.checkStateFlow(self.writeDevice.__name__)
        #----- PROTECTED REGION END -----#	//	TPM_DS.is_writeDevice_allowed
        return state_ok
        
    def writeRegister(self, argin):
        """ Writes values from a register location.
        
        :param argin: Associated register information.
        :type: PyTango.DevString
        :return: True if successful, false if not.
        :rtype: PyTango.DevBoolean """
        self.debug_stream("In writeRegister()")
        argout = False
        #----- PROTECTED REGION ID(TPM_DS.writeRegister) ENABLED START -----#
        arguments = eval(argin)
        device = arguments['device']
        register = arguments['register']
        values = arguments['values']
        offset = arguments['offset']
        argout = self.tpm_instance.writeRegister(Device(device), register, values, offset)
        #----- PROTECTED REGION END -----#	//	TPM_DS.writeRegister
        return argout
        
    def is_writeRegister_allowed(self):
        self.debug_stream("In is_writeRegister_allowed()")
        state_ok = not(self.get_state() in [PyTango.DevState.UNKNOWN])
        #----- PROTECTED REGION ID(TPM_DS.is_writeRegister_allowed) ENABLED START -----#
        state_ok = self.checkStateFlow(self.writeRegister.__name__)
        #----- PROTECTED REGION END -----#	//	TPM_DS.is_writeRegister_allowed
        return state_ok
        

class TPM_DSClass(PyTango.DeviceClass):
    #--------- Add you global class variables here --------------------------
    #----- PROTECTED REGION ID(TPM_DS.global_class_variables) ENABLED START -----#
    
    #----- PROTECTED REGION END -----#	//	TPM_DS.global_class_variables

    def dyn_attr(self, dev_list):
        """Invoked to create dynamic attributes for the given devices.
        Default implementation calls
        :meth:`TPM_DS.initialize_dynamic_attributes` for each device
    
        :param dev_list: list of devices
        :type dev_list: :class:`PyTango.DeviceImpl`"""
    
        for dev in dev_list:
            try:
                dev.initialize_dynamic_attributes()
            except:
                import traceback
                dev.warn_stream("Failed to initialize dynamic attributes")
                dev.debug_stream("Details: " + traceback.format_exc())
        #----- PROTECTED REGION ID(TPM_DS.dyn_attr) ENABLED START -----#
        
        #----- PROTECTED REGION END -----#	//	TPM_DS.dyn_attr

    #    Class Properties
    class_property_list = {
        }


    #    Device Properties
    device_property_list = {
        }


    #    Command definitions
    cmd_list = {
        'Connect':
            [[PyTango.DevString, "Device IP address and port number."],
            [PyTango.DevVoid, "none"]],
        'Disconnect':
            [[PyTango.DevVoid, "none"],
            [PyTango.DevVoid, "none"]],
        'addCommand':
            [[PyTango.DevString, "A string containing a dictionary for fields required for command creation."],
            [PyTango.DevBoolean, "True if command creation was successful, false if not."]],
        'createScalarAttribute':
            [[PyTango.DevString, "New attribute name."],
            [PyTango.DevVoid, "none"]],
        'createVectorAttribute':
            [[PyTango.DevString, "New attribute name."],
            [PyTango.DevVoid, "none"]],
        'flushAttributes':
            [[PyTango.DevVoid, "none"],
            [PyTango.DevVoid, "none"]],
        'generateAttributes':
            [[PyTango.DevVoid, "none"],
            [PyTango.DevVoid, "none"]],
        'getDeviceList':
            [[PyTango.DevVoid, "none"],
            [PyTango.DevString, "Dictionary of devices."]],
        'getFirmwareList':
            [[PyTango.DevString, "Device on board to get list of firmware, as a string."],
            [PyTango.DevString, "Dictionary of firmwares on the board."]],
        'getRegisterInfo':
            [[PyTango.DevString, "The register name for which information will be retrieved."],
            [PyTango.DevString, "Returns a string-encoded dictionary of information."]],
        'getRegisterList':
            [[PyTango.DevVoid, "none"],
            [PyTango.DevVarStringArray, "List of register names."]],
        'loadfirmwareblocking':
            [[PyTango.DevString, "File path."],
            [PyTango.DevVoid, "none"]],
        'readAddress':
            [[PyTango.DevString, "Associated register information."],
            [PyTango.DevVarULongArray, "Register values."]],
        'readDevice':
            [[PyTango.DevString, "String containing:\n1) SPI Device to read from\n2) Address on device to read from"],
            [PyTango.DevULong, "Value of device."]],
        'readRegister':
            [[PyTango.DevString, "Associated register information."],
            [PyTango.DevVarULongArray, "Register values."]],
        'removeCommand':
            [[PyTango.DevString, "Command name."],
            [PyTango.DevBoolean, "True if command removal was successful, false otherwise."]],
        'setBoardState':
            [[PyTango.DevLong, "Board status value."],
            [PyTango.DevVoid, "none"]],
        'writeAddress':
            [[PyTango.DevString, "Associated register information."],
            [PyTango.DevBoolean, "True if successful, false if not."]],
        'writeDevice':
            [[PyTango.DevString, "A string containing the following:\n1) SPI device to write to\n2) Address on device to write to\n3) Value to write"],
            [PyTango.DevBoolean, "True if successful, false if not."]],
        'writeRegister':
            [[PyTango.DevString, "Associated register information."],
            [PyTango.DevBoolean, "True if successful, false if not."]],
        }


    #    Attribute definitions
    attr_list = {
        'boardState':
            [[PyTango.DevLong,
            PyTango.SCALAR,
            PyTango.READ]],
        }


def main():
    try:
        py = PyTango.Util(sys.argv)
        py.add_class(TPM_DSClass,TPM_DS,'TPM_DS')

        U = PyTango.Util.instance()
        U.server_init()
        U.server_run()

    except PyTango.DevFailed,e:
        print '-------> Received a DevFailed exception:',e
    except Exception,e:
        print '-------> An unforeseen exception occured....',e

if __name__ == '__main__':
    main()