from plugins import *
from interface import *
import logging
import inspect
import ctypes
import sys
import re

# --------------- Helpers ------------------------------
DeviceNames = { Device.Board : "Board", Device.FPGA_1 : "FPGA 1", Device.FPGA_2 : "FPGA 2" }
# ------------------------------------------------------

# Wrap functionality for a TPM board
class FPGABoard(object):
    """ Class which wraps LMC functionality for generic FPGA boards """

    # Class constructor
    def __init__(self, **kwargs):
        """ Class constructor for FPGABoard"""

        # Set defaults
        self._registerList = None
        self._firmwareList = None
        self._fpga_board    = 0
        self._deviceList   = None
        self.id            = None
        self.status        = Status.NotConnected
        self._programmed   = False
        self._logger       = None
        self._string_id    = "Board"

        # List all available subclasses of FirmwareBlock (plugins)
        self._available_plugins = []
        for plugin in [cls.__name__ for cls in sys.modules['plugins'].FirmwareBlock.__subclasses__()]:
            constr = eval(plugin).__init__.__dict__
            friendly_name = plugin
            if "_friendly_name" in constr:
                friendly_name = constr['_friendly_name']
            self._available_plugins.append((plugin, friendly_name))
            
        self._loaded_plugins = { }

        # Override to make this compatible with IPython
        self.__methods__        = None
        self.trait_names        = None
        self._getAttributeNames = None
        self.__members__        = None

        # Used by __setattr__ to know how to handle new attributes
        self.__initialised = True  

        # Check if FPGA board type is specified
        self._fpga_board = kwargs.get('fpgaBoard', None)
        if self._fpga_board is None:
            raise LibraryError("No BoarMake specified in FPGABoard initialiser")

        # Check if filepath is included in arguments
        filepath = kwargs.get('library', None)

        # Initialise library
        initialise_library(filepath)

        # Initialise logging (use default logger which can be set externally)
        self._logger = logging.getLogger('dummy')
        ch = logging.StreamHandler()
        ch.setLevel(logging.WARNING)
        formatter = logging.Formatter('%(levelname)s\t%(asctime)s\t %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        ch.setFormatter(formatter)
        self._logger.addHandler(ch)

        # Check if ip and port are defined in arguments
        ip   = kwargs.get('ip', None)
        port = kwargs.get('port', None)

        # If so, the connect immediately
        if ip is not None and port is not None:
            self.connect(ip, port)

    # ----------------------------- High-level functionality -------------------------

    def initialise(self, config):
        """ Method for explicit initialisation. This is called by instrument when
            a configuration file is provided
        :param config: Configuration dictionary
        """

        self._string_id = config['id']

        # Configure logging
        if 'log' in config and eval(config['log']):
            self._logger = logging.getLogger()  # Get default logger
        else:
            self._logger = logging.getLogger('dummy')

        # Check if board is already connected, and if not, connect
        if self.id is None:
            if 'ip' not in config and 'port' not in config:
                raise LibraryError("IP and port are required for initialisation")
            self.connect(config['ip'], int(config['port']))

        # Check if firmware was defined in config
        if 'firmware' not in config:
            raise BoardError("Firmware must be specified in configuration file")

        #TODO: Make this generic to any board
        self.load_firmware_blocking(Device.FPGA_1, config['firmware'])

        #TODO: Perform board-specific intialisation , if any

        # Load plugins if not already loaded
        if len(self._loaded_plugins) == 0:
            # Check if any plugins are required
            if 'plugins' in config:
                for k, v in config['plugins'].iteritems():
                    # Load and initialise plugins
                    self.load_plugin(k)
                    getattr(self, k).initialise(**v)

    def status_check(self):
        """ Perform board and firmware status checks
        :return: Status
        """

        # Run generic board test
        status = self.get_status()
        if status is not Status.OK:
            return status

        # Loop over all plugins and perform checks
        if not all([getattr(self, plugin).status_check() == Status.OK
                    for plugin in self._loaded_plugins  ]):
            return Status.FirmwareError

        # All check succesful, return
        return Status.OK

    # -------------------------- Firmware plugin functionality -----------------------
    def load_plugin(self, plugin):
        """ Loads a firmware block plugin and incorporates its functionality
        :param plugin: Plugin class name
        """

        # Check if module is available
        if plugin not in [a for a,b in self._available_plugins]:
            raise LibraryError("Module %s is not available" % plugin)

        # Check if plugin is compatible with board make
        constr = eval(plugin).__init__.__dict__
        if "_compatible_boards" in constr:
            if self._fpga_board not in constr['_compatible_boards']:
                raise LibraryError("Plugin %s is not compatible with %s" % (plugin, self._fpga_board))
        else:
            self._logger.warn(self.log("Plugin %s does not specify board compatability" % plugin))

        # Check if friendly name was defined for this plugin
        friendly_name = plugin
        if "_friendly_name" not in constr:
            self._logger.warn(self.log("Plugin %s does not specify a friendly name" % plugin))
        else:
            friendly_name = constr['_friendly_name']

        # Get list of class methods and remove those availale in superclass
        methods = [name for name, mtype in
                   inspect.getmembers(eval(plugin), predicate=inspect.ismethod)
                   if name not in
                   [a for a, b in inspect.getmembers(FirmwareBlock, predicate=inspect.ismethod)] ]

        # Create plugin instances
        instance = globals()[plugin](self)
        self.__dict__[friendly_name] = instance

        # Plugin loaded, add to list
        self._loaded_plugins[friendly_name] = []

        # Import plugin function
        for method in methods:
            # Link class method to function pointer
            # self.__dict__[method] = getattr(instance, method)

            # Add metadata to be able to distigiush class from plugin methods
            # self.__dict__[method].__dict__['_plugin_method'] = True

            # Bookeeping
            self._logger.debug(self.log("Detected method %s from plugin %s" % (method, plugin)))
            self._loaded_plugins[friendly_name].append(method)

        self._logger.info(self.log("Added plugin %s to class instance" % plugin))

    def unload_plugin(self, plugin):
        """ Unload plugin from instance
        :param plugin: Plugin name
        """

        # Check if plugin has been loaded
        if plugin in self._loaded_plugins.keys():
            # Go over plugin methods and remove from instance
            for method in self._loaded_plugins[plugin]:
                del self.__dict__[method]
                self._logger.debug(self.log("Removed method %s of plugin %s from class instance" % (method, plugin)))

            # Remove from list of loaded plugins
            del self._loaded_plugins[plugin]
            self._logger.info(self.log("Removed plugin %s from class instance" % plugin))

        else:
            self._logger.info(self.log("Plugin %s was not loaded." % plugin))

    def get_available_plugins(self):
        """ Get list of availabe plugins
        :return: List of plugins
        """
        return self._available_plugins

    def get_loaded_plugins(self):
        """ Get the list of loaded plugins with associated methods
        :return: List of loaded plugins
        """
        return self._loaded_plugins

    # ---------------------------- FPBA Board functionality --------------------------

    def connect(self, ip, port):
        """ Connect to board
        :param ip: Board IP
        :param port: Port to connect to
        """

        # Check if IP is valid, and if a hostname is provided, check whether it
        # exists and get IP address
        import socket
        try:
            socket.inet_aton(ip)
        except socket.error:
            try:
                ip = socket.gethostbyname(ip)
            except socket.gaierror:
                raise BoardError("Provided IP address (%s) is invalid or does not exist")

        # Connect to board
        board_id = call_connect_board(self._fpga_board.value, ip, port)
        if board_id == 0:
            self.status = Status.NetworkError
            raise BoardError("Could not connect to board with ip %s" % ip)
        else:
            self._logger.info(self.log("Connected to board %s, received ID %d" % (ip, board_id)))
            self.id = board_id
            self.status = Status.OK

    def disconnect(self):
        """ Disconnect from board """

        # Check if board is connected
        if self.id is None:
            self._logger.warn(self.log("Call disconnect on board which was not connected"))

        ret = call_disconnect_board(self.id)
        if ret == Error.Success:
            self._registerList = None
            self._logger.info(self.log("Disconnected from board with ID %s" % self.id))
            self.id = None

    def get_status(self):
        """ Get board status
        :return: Status
        """
        return call_get_status(self.id)

    def get_firmware_list(self, device):
        """ Get list of firmware on board
        :param device: Device on board to get list of firmware
        :return: List of firmware
        """

        # Check if board is connected
        if self.id is None:
            raise LibraryError("Call get_firmware_list for board which is not connected")

        # Call getFirmware on board
        self._firmwareList = call_get_firmware_list(self.id, device)
        self._logger.debug(self.log("Called get_firmware_list"))

        return self._firmwareList

    def load_firmware_blocking(self, device, filepath):
        """ Blocking call to load firmware
         :param device: Device on board to load firmware to
         :param filepath: Path to firmware
         """
        
        # Check if device argument is of type Device
        if not type(device) is Device:
            raise LibraryError("Device argument for load_firmware_blocking should be of type Device")

        # All OK, call function
        self.status = Status.LoadingFirmware
        err = call_load_firmware_blocking(self.id, device, filepath)
        self._logger.debug(self.log("Called load_firmware_blocking"))

        # If call succeeded, get register and device list
        if err == Error.Success:
            self._programmed = True
            self.status = Status.OK
            self.get_register_list()
            self.get_device_list()
            self._logger.info(self.log("Successfuly loaded firmware %s on board" % filepath))
        else:
            self._programmed = False
            self.status = Status.LoadingFirmwareError
            raise BoardError("load_firmware_blocking failed on board")

    def get_register_list(self):
        """ Get list of registers """

        # Check if register list has already been acquired, and if so return it
        if self._registerList is not None:
            return self._registerList

        # Check if device is programmed
        if not self._programmed:
            raise LibraryError("Cannot get_register_list from board which has not been programmed")

        # Call function
        self._registerList = call_get_register_list(self.id)
        self._logger.debug(self.log("Called get_register_list on board"))

        # All done, return
        return self._registerList

    def get_device_list(self):
        """ Get list of SPI devices """

        # Check if register list has already been acquired, and if so return it
        if self._deviceList is not None:
            return self._deviceList

        # Call function
        self._deviceList = call_get_device_list(self.id)
        self._logger.debug(self.log("Called get_device_list"))

        # All done, return
        return self._deviceList

    def read_register(self, device, register, n = 1, offset = 0):
        """" Get register value
         :param device: Device on board to read register from
         :param register: Register name
         :param n: Number of words to read
         :param offset: Memory address offset to read from
         :return: Values
         """

        # Perform basic checks
        if not self._checks():    
            return

        # Check if device argument is of type Device
        if not type(device) is Device:
            raise LibraryError("Device argument for read_register should be of type Device")

        # Call function
        values = call_read_register(self.id, device, self._remove_device(register), n, offset)
        self._logger.debug(self.log("Called read_register"))

        # Check if value succeeded, otherwise return
        if values.error == Error.Failure.value:
            raise BoardError("Failed to read_register %s from board" % register)

        # Read succeeded, wrap data and return
        valPtr = ctypes.cast(values.values, ctypes.POINTER(ctypes.c_uint32))

        self._logger.debug(self.log("Called read_register on board"))

        if n == 1:
            return valPtr[0]
        else:
            return [valPtr[i] for i in range(n)]

    def write_register(self, device, register, values, offset = 0):
        """ Set register value
         :param device: Device on board to write register to
         :param register: Register name
         :param values: Values to write
         :param offset: Memory address offset to write to
         """

        # Perform basic checks
        if not self._checks():    
            return

        # Check if device argument is of type Device
        if not type(device) is Device:
           raise LibraryError("Device argument for write_register should be of type Device")

        # Call function and return
        err = call_write_register(self.id, device, self._remove_device(register), values, offset)
        self._logger.debug(self.log("Called write_register"))
        if err == Error.Failure:
            raise BoardError("Failed to write_register %s on board" % register)

    def read_address(self, address, n = 1):
        """" Get register value
         :param address: Memory address to read from
         :param n: Number of words to read
         :return: Values
         """

        # Call function and return
        ret = call_read_address(self.id, address, n)
        self._logger.debug(self.log("Called read_address"))
        if ret == Error.Failure:
            raise BoardError("Failed to read_address %s on board" % hex(address))
        else:
            return ret

    def write_address(self, address, values):
        """ Set register value
         :param address: Memory address to write to
         :param values: Values to write
         """

        # Call function and return
        err = call_write_address(self.id, address, values)
        self._logger.debug(self.log("Called write_address"))
        if err == Error.Failure:
            raise BoardError("Failed to write_address %s on board" % hex(address))

    def read_device(self, device, address):
        """" Get device value
         :param device: SPI Device to read from
         :param address: Address on device to read from
         :return: Value
         """
    
        # Check if device is in device list
        if device not in self._deviceList:
            raise LibraryError("Device argument for read_device should be of type Device")

        # Call function and return
        ret = call_read_device(self.id, device, address)
        self._logger.debug(self.log("Called read_device"))
        if ret == Error.Failure:
            raise BoardError("Failed to read_device %s, %s on board" % (device, hex(address)))
        else:
            return ret

    def write_device(self, device, address, value):
        """ Set device value
        :param device: SPI device to write to
        :param address: Address on device to write to
        :param value: Value to write
        """

        # Check if device is in device list
        if device not in self._deviceList:
            raise LibraryError("Device argument for write_device should be of type Device")

        # Call function and return
        ret = call_write_device(self.id, device, address, value)
        self._logger.debug(self.log("Called write_device"))
        if ret == Error.Failure:
            raise BoardError("Failed to write_device %s, %s on board" % (device, hex(address)))

    def list_register_names(self):
        """ Print list of register names """

        if not self._programmed:
            return

        # Run checks
        if not self._checks():
            return

        # Split register list into devices
        registers = { }
        for k, v in self._registerList.iteritems():
            if v['device'] not in registers.keys():
                registers[v['device']] = []
            registers[v['device']].append(k)

        # Loop over all devices
        for k, v in registers.iteritems():
            print DeviceNames[k]
            print '-' * len(DeviceNames[k])
            for regname in sorted(v):
                print '\t' + str(regname)

    def list_device_names(self):
        """ Print list of SPI device names """
        
        # Run check
        if not self._checks():
            return

        # Loop over all SPI devices
        print "List of SPI Devices"
        print "-------------------"
        for k in self._deviceList:
            print k

    def find_register(self, string, display = False):
        """ Return register information for provided search string
         :param string: Regular expression to search against
         :param display: True to output result to console
         :return: List of found registers
         """
        
        # Run checks
        if not self._checks():
            return

        # Go through all registers and store the name of registers
        # which generate a match
        matches = []
        for k, v in self._registerList.iteritems():
            if re.search(string, k) is not None:
                matches.append(v)

        # Display to screen if required
        if display:
            string = "\n"
            for v in sorted(matches, key = lambda l : l['name']):
                string += '%s:\n%s\n'            % (v['name'], '-' * len(v['name']))
                string += 'Address:\t%s\n'       % (hex(v['address']))
                string += 'Type:\t\t%s\n'        % str(v['type'])
                string += 'Device:\t\t%s\n'      % str(v['device'])
                string += 'Permission:\t%s\n'    % str(v['permission'])
                string += 'Bitmask:\t0x%X\n'     % v['bitmask']
                string += 'Bits:\t\t%d\n'        % v['bits']
                string += 'Size:\t\t%d\n'        % v['size']
                string += 'Description:\t%s\n\n' % v['description']

            print string

        # Return matches
        return matches

    def find_device(self, string, display = False):
        """ Return SPI device information for provided search string
         :param string: Regular expression to search against
         :param display: True to output result to console
         :return: List of found devices
         """

        # Run check
        if not self._check():
            return

        # Loop over all devices
        matches = []
        for k, v in self._deviceList:
            if re.match(string, k) is not None:
                matches.append(v)

        # Display to screen if required
        if display:
            string = "\n"
            for v in sorted(matches, key = lambda l : l['name']):
                string += 'Name: %s, spi_sclk: %d, spi_en: %d\n' % (v['name'], v['spi_sclk'], v['spi_en'])
            print string

        # Return matches
        return matches

    def __len__(self):
        """ Override __len__, return number of registers """
        if self._registerList is not None:
            return len(self._registerList.keys())

    def _checks(self):
        """ Check prior to function calls """

        # Check if board is connected
        if self.id is None:
            raise LibraryError("Cannot perform operation on unconnected board")

        # Check if device is programmed
        if not self._programmed:
            raise LibraryError("Cannot getRegisterList from board which has not been programmed")

        # Check if register list has been populated
        if self._registerList is None:
            self.get_register_list()

        return True

    def log(self, string):
        """ Format string for logging output
        :param string: String to log
        :return: Formatted string
        """
        return "%s (%s)" % (string, self._string_id)

    @staticmethod
    def _get_device(name):
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
            
    @staticmethod
    def _remove_device(name):
        """ Extract device name from register
            :param name: Register name
            :return: Register name without device
        """

        try:
            device = name.split('.')[0].upper()
            if device in ["BOARD", "FPGA1", "FPGA2"]:
                return '.'.join(name.split('.')[1:])
            else:
                return name
        except Exception:
            return name

# ================================== TPM Board ======================================
class TPM(FPGABoard):
    """ FPGABoard subclass for communicating with a TPM board """

    def __init__(self, **kwargs):
        """ Class constructor """
        kwargs['fpgaBoard'] = BoardMake.TpmBoard
        super(TPM, self).__init__(**kwargs)

    def __getitem__(self, key):
        """ Override __getitem__, return value from board """

        # Run checks
        if not self._checks():
            return

        # Check if the specified key is a memory address or register name
        if type(key) is int:
            return self.read_address(key)

        # Checkl if the specified key is a tuple, in which case we are reading from a device
        if type(key) is tuple:
            if len(key) == 2:
                return self.read_device(key[0], key[1])
            else:
                raise LibraryError("A device name and address need to be specified for writing to SPI devices")

        elif type(key) is str:
            # Check if a device is specified in the register name
            device = self._get_device(key)
            if self._registerList.has_key(key):
                reg = self._registerList[key]
                key = '.'.join(key.split('.')[1:])
                return self.read_register(device, key, reg['size'])
        else:
            raise LibraryError("Unrecognised key type, must be register name or memory address")

        # Register not found
        raise LibraryError("Register %s not found" % key)

    def __setitem__(self, key, value):
        """ Override __setitem__, set value on board"""

        # Run checks
        if not self._checks():
            return

        # Check is the specified key is a memory address or register name
        if type(key) is int:
            return self.write_address(key, value)

        # Check if the specified key is a tuple, in which case we are writing to a device
        if type(key) is tuple:
            if len(key) == 2:
                return self.write_device(key[0], key[1], value)
            else:
                raise LibraryError("A device name and address need to be specified for writing to SPI devices")

        elif type(key) is str:      
            # Check if device is specified in the register name
            device = self._get_device(key)
            if self._registerList.has_key(key):
                key = '.'.join(key.split('.')[1:])
                return self.write_register(device, key, value)
        else:
            raise LibraryError("Unrecognised key type, must be register name or memory address")

        # Register not found
        raise LibraryError("Register %s not found" % key)

    def __str__(self):
        """ Override __str__ to print register information in a human readable format """

        if not self._programmed:
            return ""

        # Run checks
        if not self._checks():
            return

        # Split register list into devices
        registers = { }
        for k, v in self._registerList.iteritems():
            if v['device'] not in registers.keys():
                registers[v['device']] = []
            registers[v['device']].append(v)

        # Loop over all devices
        string  = "Device%sRegister%sAddress%sBitmask\n" % (' ' * 2, ' ' * 27, ' ' * 8)
        string += "------%s--------%s-------%s-------\n" % (' ' * 2, ' ' * 27, ' ' * 8)
    
        for k, v in registers.iteritems():
            for reg in sorted(v, key = lambda k : k['name']):
                regspace = ' ' * (35 - len(reg['name']))
                adspace  = ' ' * (15 - len(hex(reg['address'])))
                string += '%s\t%s%s%s%s0x%08X\n' % (DeviceNames[k], reg['name'], regspace, hex(reg['address']), adspace, reg['bitmask'])

        # Add SPI devices
        if len(self._deviceList) > 0:
            string += "\nSPI Devices\n"
            string += "-----------\n"

        for v in sorted(self._deviceList.itervalues(), key = lambda k : k['name']):
            string += 'Name: %s\tspi_sclk: %d\tspi_en: %d\n' % (v['name'], v['spi_sclk'], v['spi_en'])

        # Return string representation
        return string

# ================================= ROACH Board ====================================
class Roach(FPGABoard):
    """ FPGABoard subclass for communicating with a ROACH board """

    def __init__(self, *args, **kwargs):
        """ Class constructor """
        kwargs['fpgaBoard'] = BoardMake.RoachBoard
        super(Roach, self).__init__(**kwargs)

    def connect(self, ip, port):
        """ Add functionality to connect in order to check whether the
            roach is already programmed
        :param ip: ROACH IP
        :param port: port
        """

        # Connect to board
        super(Roach, self).connect(ip, port)

        # Check if ROACH is programmed (has any registers loaded)
        self._programmed = True
        if len(self.get_register_list()) == 0:
            self._programmed = False

    def get_register_list(self):
        """ Add functionality to getRegisterList in order to map register names 
            as python attributes """

        # Populate register list
        super(Roach, self).get_register_list()

        # Check if any register are present
        if self._registerList is None:
            return None

        # The super class will prepend the device type to the register name.
        # Since everyting on the roach is controlled by a single entity,
        # we don't need this. Remove prepended device type
        newRegList = { }
        for k in self._registerList.keys():
            newKey = k.replace("fpga1.", "")
            newRegList[newKey] = self._registerList[k]
            newRegList[newKey]['name'] = newKey
        self._registerList = newRegList

        return self._registerList

    def get_firmware_list(self):
        """ Roach helper for getFirmwareList """
        return super(Roach, self).get_firmware_list(Device.FPGA_1)

    def read_register(self, register, n = 1, offset = 0):
        """ Roach helper for readRegister """
        return super(Roach, self).read_register(Device.FPGA_1, register, n, offset)

    def write_register(self, register, values, offset = 0):
        """ Roach helper for writeRegister"""
        return super(Roach, self).write_register(Device.FPGA_1, register, values, offset)

    def load_firmware_blocking(self, boffile):
        """ Roach helper for loadFirmwareBlocking """
        return super(Roach, self).load_firmware_blocking(Device.FPGA_1, boffile)

    def loadFirmware(self, boffile):
       """ Roach helpder for loadFirmware """
       return super(Roach, self).loadFirmware(Device.FPGA_1, boffile)

    def read_address(self, address, n = 1):
        """ Roach helper for readAddress """
        print "Read memory address not supported for ROACH"

    def write_address(self, address, values):
        """ Roach helper for writeAddress """
        print "Write memory address not supported for ROACH"

    def write_device(self, device, address, value):
        """ Roach helper for writeDevice """
        print "Write device is not supported for ROACH"

    def read_device(self, device, address):
        """ Roach helper for readDevice """
        print "Read device is not supported for ROACH"

    def __getitem__(self, key):
        """ Override __getitem__, return value from board """

        # Run checks
        if not self._checks():
            return

        # Check if register is valid
        if type(key) is str:
            if self._registerList.has_key(key):
                return self.read_register(key, self._registerList[key]['size'])
        else:
            raise LibraryError("Unrecognised key type, must be register name or memory address")

        # Register not found
        raise LibraryError("Register '%s' not found" % key)

    def __setitem__(self, key, value):
        """ Override __setitem__, set value on board"""

        # Run checks
        if not self._checks():
            return

        if type(key) is str:      
            # Check if register is valid
            if self._registerList.has_key(key):
                return self.write_register(key, value)
        else:
            raise LibraryError("Unrecognised key type, must be register name or memory address")

        # Register not found
        raise LibraryError("Register '%s' not found" % key)

    def __getattr__(self, name):
        """ Override __getattr__, get value from board """
        if name in self.__dict__:
            return self.__dict__[name]
        elif self._registerList is not None and name in self._registerList:
            return self.read_register(name)
        else:
            raise AttributeError("Register %s not found" % name)

    def __setattr__(self, name, value):
        """ Override __setattr__, set value on board"""
        if name in self.__dict__:
            self.__dict__[name] = value
        # Allow attributes to be defined normally during initialisation
        elif not self.__dict__.has_key('_FPGABoard__initialised'):
            return  dict.__setattr__(self, name, value)
        elif self._registerList is not None and name in self._registerList:
            self.write_register(name, value)
        else:
            raise AttributeError("Register %s not found % name")

    def __str__(self):
        """ Override __str__ to print register information in a human readable format """
        super(Roach, self).list_register_names()
        return ""

# -------------- Logging Functionality --------------------

# Note: Do not run the code below! (temp)
if __name__ == "__main__":
    # Simple TPM test
    # tpm = TPM(ip="127.0.0.1", port=10000)
    # tpm.loadFirmwareBlocking(Device.FPGA_1, "/home/lessju/map.xml")
    # tpm['fpga1.regfile.block2048b'] = [1] * 512
    # print tpm['fpga1.regfile.block2048b']
    # tpm.disconnect()
    #
    # # Simple ROACH test
    # roach = Roach(ip="192.168.100.2", port=7147)
    # roach.getFirmwareList()
    # roach.loadFirmwareBlocking("fenggbe.bof")
    # roach.amp_EQ0_coeff_bram = range(4096)
    # print roach.readRegister('amp_EQ0_coeff_bram', 4096)
    # roach.disconnect()

    pass
