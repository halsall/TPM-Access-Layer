from enum import Enum
import ctypes, os

# --------------- Enumerations --------------------------

# Error
class Error(Enum):
    Success = 0
    Failure = -1
    NotImplemented = -2

# Device
class Device(Enum):
    Board = 1
    FPGA_1 = 2
    FPGA_2 = 4

# Status
class Status(Enum):
    OK = 0
    LoadingFirmware = -1
    ConfigError = -2
    BoardError = -3
    NotConnected = -4
    NetworkError = -5

# RegisterType
class RegisterType(Enum):
    Sensor = 1
    BoardRegister = 2
    FirmwareRegister = 3

# Permission
class Permission(Enum):
    Read      = 1
    Write     = 2
    ReadWrite = 3

# --------------- Structures --------------------------
class Value:
    def __init__(self, value, error):
        self.value = value
        self.error = error

class RegisterInfo:
    def __init__(self, name, reg_type, device, permission, size, desc):
        self.name = name    
        self.type = reg_type
        self.device = device
        self.permission = permission
        self.size = size
        self.desc = desc

# Wrap functionality for a TPM board
class TPM:

    # Define ctype wrapper to library structures
    class ValueStruct(ctypes.Structure):
        _fields_ = [
            ('value', ctypes.c_uint32),
            ('error', ctypes.c_int)
        ]

    class RegisterInfoStruct(ctypes.Structure):
        _fields_ = [    
            ('name',        ctypes.c_char_p),
            ('type',        ctypes.c_int),
            ('device',      ctypes.c_int),
            ('permission',  ctypes.c_int),
            ('size',        ctypes.c_uint32),
            ('description', ctypes.c_char_p)
        ]

    # Class constructor
    def __init__(self, *args, **kwargs):
        """ Class constructor """

        # Check if filepath is included in arguments
        filepath = kwargs.get('filepath', None)

        # Initialise library
        self._initialiseLibrary(filepath)

        # Check if ip and port are defined in arguments
        ip   = kwargs.get('ip', None)
        port = kwargs.get('port', None)

        # Set registerList to None
        self._registerList = None

        # Set ID to None
        self.id = None

        # If so, the connect immediately
        if not (ip is None and port is None):
            self.connect(ip, port)

    def connect(self, ip, port):
        """ Connect to board """
        boardId = self._tpm.connectBoard(ip, port)
        if boardId < 1:
            return Error.Failure
        else:
            self.id = boardId
            return Error.Success

    def disconnect(self):
        """ Disconnect from board """

        # Check if board is connected
        if self.id is None:
            print "Board not connected"
            return Error.Failure

        ret = Error(self._tpm.disconnect(self.id))
        if (ret == Error.Success):
            self.id = None
            self._registerList = None
        return ret

    def loadFirmwareBlocking(self, device, filepath):
        """ Blocking call to load firmware """
        
        # Check if device argument is of type Device
        if not type(device) is Device:
            print "device argument should be of type Device"
            return

        # Check if filepath is valid
        if not os.path.isfile(filepath):
            print "Invalid file path %s" % filepath
            return

        # All OK, call function
        err = Error(self._tpm.loadFirmwareBlocking(self.id, device.value, filepath))

        # If call succeeded, get register list
        if err == Error.Success:
            self.getRegisterList()

        # Return 
        return err

    def getRegisterList(self):
        """ Get list of registers """

        # Check if register list has already been acquired, and if so return it
        if self._registerList is not None:
            return self._registerList

        # Create an integer and extract it's address
        INTP = ctypes.POINTER(ctypes.c_int)
        num  = ctypes.c_int(0)
        addr = ctypes.addressof(num)
        ptr  = ctypes.cast(addr, INTP)

        # Call function
        registers = self._tpm.getRegisterList(self.id, ptr)

        # Wrap register formats and return
        registerList = {  }
        for i in range(num.value):
            reg = { }
            reg['name']        = registers[i].name
            reg['type']        = RegisterType(registers[i].type)
            reg['device']      = Device(registers[i].device)
            reg['permission']  = Permission(registers[i].permission)
            reg['size']        = registers[i].size
            reg['description'] = registers[i].description
            registerList[reg['name']] = reg

        # Store register list locally for get and set items
        self._registerList = registerList

        return registerList

    def getRegisterValue(self, device, register):
        """" Get register value """
    
        # Check if device argument is of type Device
        if not type(device) is Device:
            print "device argument should be of type Device"
            return

        # Call function
        value = self._tpm.getRegisterValue(self.id, device.value, register)

        # Wrap result and return
        return  Value(value.value, Error(value.error))

    def setRegisterValue(self, device, register, value):
        """ Set register value """

        # Check if device argument is of type Device
        if not type(device) is Device:
            print "device argument should be of type Device"
            return

        # Call function
        return Error(self._tpm.setRegisterValue(self.id, device.value, register, value))

    def listRegisterNames(self):
        """ Print list of register names """
        
        # Check if board is connected
        if self.id is None:
            print "Board not connected"
            return

        # Check if register list has been populated
        if self._registerList is None:
            self.getRegisterList(self.id)

        print '\n'.join([str(k) for k in self._registerList.keys()])

    def __getitem__(self, key):
        """ Override __getitem__, return value from board """
        if self._registerList is not None:
            if self._registerList.has_key(key):
                reg = self._registerList[key]
                val = self.getRegisterValue(reg['device'], key)
                if val.error == Error.Success:
                    return val.value
                else:
                    return None

    def __setitem__(self, key, value):
        """ Override __setitem__, set value on board"""
        if self._registerList is not None:
            if self._registerList.has_key(key):
                reg = self._registerList[key]
                return self.setRegisterValue(reg['device'], key, value)
        print "Register '%s' not found" % key       

    def __len__(self):
        """ Override __len__, return number of registers """
        if self._registerList is not None:
            return len(self._registerList.keys())

    def _initialiseLibrary(self, filepath = None):
        """ Initialise library """
       
        # Load access layer shared library
        if filepath is None:
            self._library = "/home/lessju/Code/TPM-Access-Layer/src/libboard.so"
        else:
            self._library = filepath

        if not os.path.isfile(self._library):
            print "Library (%s) not found" % self._library
            return 

        # Library found, load it
        self._tpm = ctypes.CDLL(self._library)

        # Define connect function
        self._tpm.connectBoard.argtypes = [ctypes.c_char_p, ctypes.c_uint16]
        self._tpm.connectBoard.restype  = ctypes.c_uint32

        # Define disconnect function
        self._tpm.disconnectBoard.argtypes = [ctypes.c_uint32]
        self._tpm.disconnectBoard.restype  = ctypes.c_int

        # Define loadFirmwareBlocking function
        self._tpm.loadFirmwareBlocking.argtypes =  [ctypes.c_uint32, ctypes.c_int, ctypes.c_char_p]
        self._tpm.loadFirmwareBlocking.restype = ctypes.c_int

        # Define getRegisterList function
        self._tpm.getRegisterList.argtypes = [ctypes.c_uint32, ctypes.POINTER(ctypes.c_int)]
        self._tpm.getRegisterList.restype = ctypes.POINTER(self.RegisterInfoStruct)

        # Define getRegisterValue function
        self._tpm.getRegisterValue.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_char_p]
        self._tpm.getRegisterValue.restype = self.ValueStruct

        # Define setRegisterValue function
        self._tpm.setRegisterValue.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint32]
        self._tpm.setRegisterValue.restype = ctypes.c_int

