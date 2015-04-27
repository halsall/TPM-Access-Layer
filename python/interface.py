from enum import Enum
import ctypes

# --------------- Enumerations --------------------------

class Error(Enum):
    """ Error enumeration """
    Success = 0
    Failure = -1
    NotImplemented = -2

class Device(Enum):
    """ Device enumeration """
    Board = 1
    FPGA_1 = 2
    FPGA_2 = 4

class BoardMake(Enum):
    """ BoardMake enumeration """
    TpmBoard      = 1
    RoachBoard    = 2
    Roach2Board   = 3
    UniboardBoard = 4

class Status(Enum):
    """ Status enumeration """
    OK = 0
    LoadingFirmware = -1
    ConfigError = -2
    BoardError = -3
    NotConnected = -4
    NetworkError = -5

class RegisterType(Enum):
    """ RegisterType enumeration """
    Sensor = 1
    BoardRegister = 2
    FirmwareRegister = 3
    SPIDevice = 4
    Component = 5

class Permission(Enum):
    """ Permission enumeration """
    Read      = 1
    Write     = 2
    ReadWrite = 3

# --------------- Structures --------------------------
class Values(object):
    """ Class representing VALUES struct """
    def __init__(self, values, error):
        self.values = values
        self.error = error

class RegisterInfo(object):
    """ Class representing REGSTER)INFO struct """
    def __init__(self, name, address, reg_type, device, permission, bitmask, bits, size, desc):
        self.name = name
        self.address = address
        self.type = reg_type
        self.device = device
        self.permission = permission
        self.bitmask = bitmask
        self.bits = bits
        self.value = value
        self.size = size
        self.desc = desc

class SPIDeviceInfo(object):
    """ Class representing SPI_DEVICE_INFO struct """
    def __init__(self, name, spi_sclk, spi_en):
        self.name     = name
        self.spi_sclk = spi_sclk
        self.spi_en   = spi_en

# ------ ctype wrapper to library structures ----------
class ValuesStruct(ctypes.Structure):
    """ Class representing VALUES struct """
    _fields_ = [
        ('values', ctypes.POINTER(ctypes.c_uint32)),
        ('error', ctypes.c_int)
    ]

class RegisterInfoStruct(ctypes.Structure):
    """ Class REGISTER_INFO struct """
    _fields_ = [
        ('name',        ctypes.c_char_p),
        ('address',     ctypes.c_uint32),
        ('type',        ctypes.c_int),
        ('device',      ctypes.c_int),
        ('permission',  ctypes.c_int),
        ('bitmask',     ctypes.c_uint32),
        ('bits',        ctypes.c_uint32),
        ('value',       ctypes.c_uint32),
        ('size',        ctypes.c_uint32),
        ('description', ctypes.c_char_p)
    ]

class SPIDeviceInfoStruct(ctypes.Structure):
    """ Class representing SPI_DEVICE_INFO struct """
    _fields_ = [
        ('name',     ctypes.c_char_p),
        ('spi_sclk', ctypes.c_uint32),
        ('spi_en',   ctypes.c_uint32)
    ]

# ------------- Wrap library calls ---------------------------

# Global store for interface object
library = None

def initialiseLibrary(filepath = None):
    """ Wrap access library shared library functionality in ctypes
    :param filepath: Path to library path
    :return: None
    """
    global library

    # Load access layer shared library
    if filepath is None:
        _library = "libboard"
    else:
        _library = filepath

    # Load library
    library = ctypes.CDLL(_library + ".so")

    # Define connect function
    library.connectBoard.argtypes = [ctypes.c_uint32, ctypes.c_char_p, ctypes.c_uint16]
    library.connectBoard.restype  = ctypes.c_uint32

    # Define disconnect function
    library.disconnectBoard.argtypes = [ctypes.c_uint32]
    library.disconnectBoard.restype  = ctypes.c_int

    # Define getFirmware function
    library.getFirmware.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
    library.getFirmware.restype = ctypes.POINTER(ctypes.c_char_p)

    # Define loadFirmwareBlocking function
    library.loadFirmwareBlocking.argtypes =  [ctypes.c_uint32, ctypes.c_int, ctypes.c_char_p]
    library.loadFirmwareBlocking.restype = ctypes.c_int

    # Define loadFirmwareBlocking function
    library.loadFirmware.argtypes =  [ctypes.c_uint32, ctypes.c_int, ctypes.c_char_p]
    library.loadFirmware.restype = ctypes.c_int

    # Define getRegisterList function
    library.getRegisterList.argtypes = [ctypes.c_uint32, ctypes.POINTER(ctypes.c_int)]
    library.getRegisterList.restype = ctypes.POINTER(RegisterInfoStruct)

    # Define readRegister function
    library.readRegister.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint32]
    library.readRegister.restype = ValuesStruct

    # Define writeRegister function
    library.writeRegister.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint32, ctypes.c_uint32]
    library.writeRegister.restype = ctypes.c_int

    # Define readRegister function
    library.readAddress.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
    library.readAddress.restype = ValuesStruct

    # Define writeRegister function
    library.writeAddress.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint32]
    library.writeAddress.restype = ctypes.c_int

    # Define getDeviceList function
    library.getDeviceList.argtypes = [ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32)]
    library.getDeviceList.restype = ctypes.POINTER(SPIDeviceInfoStruct)

    # Define readDevice function
    library.readDevice.argtypes = [ctypes.c_uint32, ctypes.c_char_p, ctypes.c_uint32]
    library.readDevice.restype = ValuesStruct

    # Define writeDevice function
    library.writeDevice.argtypes = [ctypes.c_uint32, ctypes.c_char_p, ctypes.c_uint32, ctypes.c_uint32]
    library.writeDevice.restype = ctypes.c_int

    # Define freeMemory function
    library.freeMemory.argtypes = [ctypes.c_void_p]

# ------------- Function wrappers to library ---------------------------

def callConnectBoard(board_type, ip, port):
    """ Call connect board
    :param board_type: Board type to connect to
    :param ip: IP address of board
    :param port: port number to connect to
    :return: Integer ID representation of board
    """
    global library
    return library.connectBoard(board_type, ip, port)

def callDisconnectBoard(board_id):
    """
    :param board_id: ID of board to disconnect from
    :return: Success or Failure
    """
    global library
    return Error(library.disconnectBoard(board_id))

def callGetFirmwareList(board_id, device):
    """
    :param board_id: ID of board to query
    :param device: Device on board to query
    :return: List of firmware available on board
    """
    global library

    # Create an integer and extract it's address
    INTP = ctypes.POINTER(ctypes.c_int)
    num  = ctypes.c_int(0)
    addr = ctypes.addressof(num)
    ptr  = ctypes.cast(addr, INTP)

    # Call library function
    firmware = library.getFirmware(board_id, device.value, ptr)

    # Process all firmware
    firmwareList = [firmware[i] for i in range(num.value)]

    # Free firmware pointer
    library.freeMemory(firmware)

    return firmwareList

def callLoadFirmwareBlocking(board_id, device, filepath):
    """ Load firmware on board in blocking mode
    :param board_id: ID of board to communicate with
    :param device: Device on board to load firmware onto
    :param filepath: Filepath or name of firmware to load
    :return: Success or Failure
    """
    global library
    return Error(library.loadFirmwareBlocking(board_id, device.value, filepath))

def callLoadFirmware(board_id, device, filepath):
    """ Load firmware on board in async mode
    :param board_id: ID of board to communicate with
    :param device: Device on board to load firmware onto
    :param filepath: Filepath or name of firmware to load
    :return: Success or Failure
    """
    global library
    return Error(library.loadFirmware(board_id, device.value, filepath))

def callGetRegisterList(board_id):
    """ Get list of available registers on board
    :param board_id: ID of board to query
    :return: List of registers
    """
    global library

    # Create an integer and extract it's address
    INTP = ctypes.POINTER(ctypes.c_int)
    num  = ctypes.c_int(0)
    addr = ctypes.addressof(num)
    ptr  = ctypes.cast(addr, INTP)

    # Call function
    registers = library.getRegisterList(board_id, ptr)

    # Create device map for register names
    names = { Device.Board : "board", Device.FPGA_1 : "fpga1", Device.FPGA_2 : "fpga2" }

    # Wrap register formats and return
    registerList = { }
    for i in range(num.value):
        dev = Device(registers[i].device)
        reg = {
            'name'        : '%s.%s' % (names[dev], registers[i].name),
            'address'     : registers[i].address,
            'type'        : RegisterType(registers[i].type),
            'device'      : dev,
            'permission'  : Permission(registers[i].permission),
            'size'        : registers[i].size,
            'bitmask'     : registers[i].bitmask,
            'bits'        : registers[i].bits,
            'value'       : registers[i].value,
            'description' : registers[i].description
        }
        registerList["%s.%s" % (names[dev], registers[i].name)] = reg

    # Free up memory on board
    library.freeMemory(registers)

    return registerList

def callGetDeviceList(board_id):
    """
    :param board_id: ID of board to query
    :return: List of devices
    """
    global library

    # Create an integer and extract it's address
    INTP = ctypes.POINTER(ctypes.c_uint32)
    num  = ctypes.c_uint32(0)
    addr = ctypes.addressof(num)
    ptr  = ctypes.cast(addr, INTP)

    # Call function
    devices = library.getDeviceList(board_id, ptr)

    # Wrap register formats and return
    deviceList = { }
    for i in range(num.value):
        reg = {
            'name'      : devices[i].name,
            'spi_en'    : devices[i].spi_en,
            'spi_sclk'  : devices[i].spi_sclk
        }
        deviceList[reg['name']] = reg

    # Free up memory on board
    library.freeMemory(devices)

    return deviceList

def callReadRegister(board_id, device, register, n = 1, offset = 0):
    """
    :param board_id: ID of board to operate upon
    :param device: Device on board to operate upon
    :param register: Register name
    :param n: Number of words to read
    :param offset: Address offset
    :return: Memory-mapped values
    """
    global library

    # Call function and return
    return library.readRegister(board_id, device.value, register, n, offset)


def callWriteRegister(board_id, device, register, values, offset = 0):
    """
    :param board_id: ID of board to operate upon
    :param device: Device on board to operate upon
    :param register: Register name
    :param values: Value to write to board
    :param offset: Address offset
    :return: Success or Failure
    """
    global library

    # Check if we have a single value or list of values
    if type(values) is not list:

        # Create an integer and extract it's address
        INTP = ctypes.POINTER(ctypes.c_uint32)
        num  = ctypes.c_uint32(values)
        addr = ctypes.addressof(num)
        ptr  = ctypes.cast(addr, INTP)

        err = library.writeRegister(board_id, device.value, register, ptr, 1, offset)
        return err

    elif type(values) is list:
        n = len(values)
        vals = (ctypes.c_uint32 * n) (*values)
        return Error(library.writeRegister(board_id, device.value, register, vals, n, offset))
    else:
        return Error.Failure

def callReadAddress(board_id, address, n = 1):
    """ Read form address on board
    :param board_id: ID of board to operate upon
    :param address: Memory address to read from
    :param n: Number of words to read
    :return: Memory-mapped values
    """
    global library

    # Call function
    values = library.readAddress(board_id, address, n)

    # Check if value succeeded, othewise rerturn
    if values.error == Error.Failure.value:
        return Error.Failure

    # Read successful, wrap data and return
    valPtr = ctypes.cast(values.values, ctypes.POINTER(ctypes.c_uint32))

    if n == 1:
        return valPtr[0]
    else:
        return [valPtr[i] for i in range(n)]

def callWriteAddress(board_id, address, values):
    """ Write to address on board
    :param board_id: ID of board to operate upon
    :param address: Memory address to write to
    :param values: Values to write to memory
    :return: Success or Failure
    """
    global library

    # Check if we have a single value or list of values
    if type(values) is not list:

        # Create an integer and extract it's address
        INTP = ctypes.POINTER(ctypes.c_uint32)
        num  = ctypes.c_uint32(values)
        addr = ctypes.addressof(num)
        ptr  = ctypes.cast(addr, INTP)

        return Error(library.writeAddress(board_id, address, ptr, 1))

    elif type(values) is list:
        n = len(values)
        vals = (ctypes.c_uint32 * n) (*values)
        return Error(library.writeAddress(board_id, address, vals, n))
    else:
        return Error.Failure

def callReadDevice(board_id, device, address):
    """ Read from an SPI device
    :param board_id: ID of board to operate upon
    :param device: Device on board to operate upon
    :param address: Address on device to read from
    :return: Values
    """
    global library

    # Call function
    values = library.readDevice(board_id, device, address)

    # Check if value succeeded, otherwise reture
    if values.error == Error.Failure.value:
        return Error.Failure

    # Read succeeded, wrap data and return
    valPtr = ctypes.cast(values.values, ctypes.POINTER(ctypes.c_uint32))

    # Return value
    return valPtr[0]

def callWriteDevice(board_id, device, address, value):
    """
    :param board_id: ID of board to operate upon
    :param device: Device on board to operate upon
    :param address: Address on device to write to
    :param value: Value to write
    :return: Success of Failure
    """
    global library

    # Call function
    return Error(library.writeDevice(board_id, device, address, value))