import pyudev
context = pyudev.Context()
for device in context.list_devices(subsystem='block', DEVTYPE='partition'):
    print(device.get('ID_FS_LABEL', 'unlabeled partition'))