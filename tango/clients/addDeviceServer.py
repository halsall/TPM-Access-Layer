from PyTango import Database, DbDevInfo

# A reference on the Database
db = Database()

# Define device name
new_device_name = "test/tpm_board/1"

# Define the Tango Class served by this DServer
dev_info = DbDevInfo()
dev_info._class = "TPM_DS"
dev_info.server = "TPM_DS/test"

# add the device
dev_info.name = new_device_name
print("Creating device: %s" % new_device_name)
db.add_device(dev_info)



# SECOND DEVICE
# Define device name
new_device_name = "test/tpm_board/2"

# Define the Tango Class served by this DServer
dev_info = DbDevInfo()
dev_info._class = "TPM_DS"
dev_info.server = "TPM_DS/test"

# add the device
dev_info.name = new_device_name
print("Creating device: %s" % new_device_name)
db.add_device(dev_info)

