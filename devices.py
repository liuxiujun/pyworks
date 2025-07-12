from evdev import InputDevice, list_devices

# 打印所有设备详细信息
for dev_path in list_devices():
    dev = InputDevice(dev_path)
    print(f"\n设备路径: {dev.path}")
    print(f"设备名称: {dev.name}")
    print(f"支持的事件类型: {dev.capabilities()}")

