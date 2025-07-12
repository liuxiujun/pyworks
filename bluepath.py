from pydbus import SystemBus

def find_bluetooth_paths():
    bus = SystemBus()
    bluez = bus.get('org.bluez', '/')
    objects = bluez.GetManagedObjects()
    
    for path, interfaces in objects.items():
        # if 'org.bluez.Device1' in interfaces:
        #     print(f"设备路径: {path}")
        #     print(f"  设备地址: {interfaces['org.bluez.Device1']['Address']}")
        #     print(f"  设备名称: {interfaces['org.bluez.Device1']['Alias']}")
        #     
        # if 'org.bluez.GattService1' in interfaces:
        #     print(f"服务路径: {path}")
        #     print(f"  服务UUID: {interfaces['org.bluez.GattService1']['UUID']}")
        #     
        # if 'org.bluez.HID1' in interfaces:
        #     print(f"HID服务路径: {path}")
        print (f"{path}")

if __name__ == "__main__":
    find_bluetooth_paths()
