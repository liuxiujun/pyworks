# File: bluetooth_hid_keyboard.py
#!/usr/bin/env python3
"""
树莓派蓝牙HID键盘桥接服务
- 读取物理2.4G键盘事件
- 通过蓝牙HID Profile 将按键事件发送到Windows
"""
import logging
import os
import signal
import sys

import dbus
from dbus.mainloop.glib import DBusGMainLoop
from dbus.service import BusName, Object, method
from evdev import InputDevice
from gi.repository import GLib
from hid_usage_map import KEYCODE_TO_USAGE

# 初始化 D-Bus 主循环
DBusGMainLoop(set_as_default=True)

# 常量
HID_UUID = "00001124-0000-1000-8001-00805F9B34FB"
PSM_CONTROL = 17  # HID Control
PSM_INTERRUPT = 19  # HID Interrupt
PROFILE_PATH = "/org/bluez/hci0/hid_keyboard"
# 动态加载外部 SDP XML 文件
HID_SERVICE_RECORD = open(os.path.join(os.path.dirname(__file__), "sdp_record.xml"), "r", encoding="utf-8").read()

# 日志配置
logging.basicConfig(level=logging.DEBUG, format="[%(levelname)s] %(message)s")


class HIDProfile(Object):
    def __init__(self, bus, path, mainloop, bus_name):
        super().__init__(bus, path, bus_name)
        self.mainloop = mainloop
        self.control_fd = None
        self.interrupt_fd = None

    @method("org.bluez.Profile1", in_signature="oha{sv}", out_signature="")
    def NewConnection(self, device, fd, props):
        psm = props.get("PSM")
        sock = fd.take()
        if int(psm) == PSM_CONTROL:
            self.control_fd = sock
            logging.info(f"Control channel connected (fd={sock})")
        elif int(psm) == PSM_INTERRUPT:
            self.interrupt_fd = sock
            logging.info(f"Interrupt channel connected (fd={sock})")
        else:
            logging.warning(f"Unknown PSM {psm}, fd={sock}")

    @method("org.bluez.Profile1", in_signature="o", out_signature="")
    def RequestDisconnection(self, device):
        for attr in ("control_fd", "interrupt_fd"):
            fd = getattr(self, attr)
            if fd:
                os.close(fd)
                setattr(self, attr, None)
                logging.info(f"Closed {attr}")

    @method("org.bluez.Profile1", in_signature="", out_signature="")
    def Release(self):
        logging.info("Profile released")
        self.mainloop.quit()


class BluetoothHIDServer:
    def __init__(self):
        self.bus = dbus.SystemBus()

        # —— 新增：打开蓝牙适配器的 discoverable 和 pairable ——
        adapter_path = "/org/bluez/hci0"
        adapter_obj = self.bus.get_object("org.bluez", adapter_path)
        adapter_props = dbus.Interface(adapter_obj, "org.freedesktop.DBus.Properties")
        # 设置为永远可发现和可配对
        adapter_props.Set("org.bluez.Adapter1", "DiscoverableTimeout", dbus.UInt32(0))
        adapter_props.Set("org.bluez.Adapter1", "Discoverable", dbus.Boolean(1))
        adapter_props.Set("org.bluez.Adapter1", "Pairable", dbus.Boolean(1))

        if not hasattr(self.bus, "_register_object_path"):
            self.bus._register_object_path = self.bus.register_object_path
            self.bus._unregister_object_path = self.bus.unregister_object_path
        self.bus_name = BusName("org.bluez", bus=self.bus)
        self.mainloop = GLib.MainLoop()
        self.profile = HIDProfile(self.bus, PROFILE_PATH, self.mainloop, self.bus_name)
        self.pm = dbus.Interface(
            self.bus.get_object("org.bluez", "/org/bluez"), "org.bluez.ProfileManager1"
        )
        signal.signal(signal.SIGINT, self._cleanup)
        signal.signal(signal.SIGTERM, self._cleanup)

    def register_profile(self):
        try:
            self.pm.UnregisterProfile(PROFILE_PATH)
        except:
            pass
        opts = {
            "ServiceRecord": HID_SERVICE_RECORD,
            "AutoConnect": dbus.Boolean(True),
            "Class": dbus.UInt32(0x002540),
        }
        self.pm.RegisterProfile(PROFILE_PATH, HID_UUID, opts)
        logging.info("HID Profile registered via SDP XML")

    def _cleanup(self, signum, frame):
        try:
            self.pm.UnregisterProfile(PROFILE_PATH)
        except:
            pass
        # 退出 GLib 循环并结束进程
        self.mainloop.quit()
        sys.exit(0)

    def add_keyboard_watch(self, keyboard, hid):
        io_channel = GLib.IOChannel.unix_new(keyboard.fd)
        GLib.io_add_watch(
            io_channel,
            GLib.IO_IN,
            lambda source, cond: [hid.process_event(ev) for ev in keyboard.read()]
            or True,
        )

    def run(self):
        logging.info("Starting mainloop... (press Ctrl+C to exit)")
        self.mainloop.run()


class VirtualHID(Object):
    def __init__(self, profile):
        self.profile = profile
        self.report_id = 1

    def send_report(self, usage, pressed):
        fd = self.profile.interrupt_fd
        if fd is None:
            logging.warning("Interrupt FD not ready")
            return
        pkt = bytes([self.report_id, 0, 0] + ([usage] if pressed else []) + [0] * 5)
        os.write(fd, pkt)
        if pressed:
            empty = bytes([self.report_id, 0, 0] + [0] * 6)
            os.write(fd, empty)
        logging.debug(f"Sent HID report {pkt.hex()}")

    def process_event(self, event):
        if event.type == 1 and event.code in KEYCODE_TO_USAGE:
            usage = KEYCODE_TO_USAGE[event.code]
            pressed = event.value == 1
            self.send_report(usage, pressed)


def main():
    if os.geteuid() != 0:
        print("Run as root (sudo)")
        sys.exit(1)
    server = BluetoothHIDServer()
    server.register_profile()
    keyboard = InputDevice("/dev/input/event0")
    logging.info(f"Using keyboard: {keyboard.name}")
    hid = VirtualHID(server.profile)
    server.add_keyboard_watch(keyboard, hid)
    server.run()


if __name__ == "__main__":
    main()
