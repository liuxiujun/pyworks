import dbus

bus = dbus.SystemBus()
manager = dbus.Interface(
    bus.get_object("org.bluez", "/org/bluez"),
    "org.bluez.ProfileManager1"
)
manager.UnregisterProfile("/org/bluez/hci0/hid_keyboard")
print("Profile /org/bluez/hid_keyboard 已注销")
