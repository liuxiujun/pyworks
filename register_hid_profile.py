#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import dbus
import dbus.service
import dbus.mainloop.glib
from gi.repository import GLib
import os
import fcntl

# —— 完整的 HID SDP Record XML，带 Public Browse Group ——
HID_SERVICE_RECORD = """<?xml version="1.0" encoding="UTF-8"?>
<record>
  <!-- Service Class ID List: HID -->
  <attribute id="0x0001">
    <sequence>
      <uuid value="0x1124"/>
    </sequence>
  </attribute>

  <!-- Protocol Descriptor List: L2CAP (PSM 0x11) + HIDP (PSM 0x13) -->
  <attribute id="0x0004">
    <sequence>
      <sequence>
        <uuid value="0x0100"/>
        <uint16 value="0x0011"/>
      </sequence>
      <sequence>
        <uuid value="0x0011"/>
        <uint16 value="0x0013"/>
      </sequence>
    </sequence>
  </attribute>

  <!-- Public Browse Group List -->
  <attribute id="0x0005">
    <sequence>
      <uuid value="0x1002"/>
    </sequence>
  </attribute>

  <!-- Language Base Attribute ID List -->
  <attribute id="0x0006">
    <sequence>
      <uint16 value="0x656e"/>
      <uint16 value="0x006a"/>
      <uint16 value="0x0100"/>
    </sequence>
  </attribute>

  <!-- Profile Descriptor List: HID Version 1.0 -->
  <attribute id="0x0009">
    <sequence>
      <sequence>
        <uuid value="0x1124"/>
        <uint16 value="0x0100"/>
      </sequence>
    </sequence>
  </attribute>

  <!-- Service Name, Provider, Description -->
  <attribute id="0x0100"><text value="Example HID Device"/></attribute>
  <attribute id="0x0101"><text value="USB > BT Keyboard"/></attribute>
  <attribute id="0x0102"><text value="Raspberry Pi"/></attribute>

  <!-- HID Device Release Number -->
  <attribute id="0x0200"><uint16 value="0x0100"/></attribute>

  <!-- HID Parser Version & Subclass -->
  <attribute id="0x0201"><uint8 value="0x00"/></attribute>
  <attribute id="0x0202"><uint8 value="0x03"/></attribute>

  <!-- Country Code -->
  <attribute id="0x0203"><uint8 value="0x40"/></attribute>

  <!-- Virtual Cable -->
  <attribute id="0x0204"><boolean value="true"/></attribute>

  <!-- Remote Wake -->
  <attribute id="0x0205"><boolean value="false"/></attribute>

  <!-- Normally Connectable -->
  <attribute id="0x0206"><boolean value="true"/></attribute>

  <!-- HID Descriptor List (Report Descriptor) -->
  <attribute id="0x0026">
    <sequence>
      <sequence>
        <uint8 value="0x22"/>
        <text encoding="hex" value="05010906A10185010905E00929E715002501750195028101950375017501050919012905150025018100C0
05010902A1010901A10085010991B0250195018105EA750295038101C0"/>
      </sequence>
    </sequence>
  </attribute>
  <!-- HID Language (English, US) -->
  <attribute id="0x0208">
    <sequence>
      <sequence>
        <uint16 value="0x0409"/>
        <uint16 value="0x0100"/>
      </sequence>
    </sequence>
  </attribute>

  <!-- Battery Power & Profile Version -->
  <attribute id="0x0209"><uint16 value="0x0640"/></attribute>
  <attribute id="0x020A"><uint16 value="0x0320"/></attribute>
</record>
"""

class HIDProfile(dbus.service.Object):
    def __init__(self, bus, path):
        super().__init__(bus, path)

    @dbus.service.method("org.bluez.Profile1", in_signature="", out_signature="")
    def Release(self):
        print("Profile1.Release() called, exiting")
        GLib.MainLoop().quit()

    @dbus.service.method("org.bluez.Profile1", in_signature="oha{sv}", out_signature="")
    def NewConnection(self, device, fd, properties):
        print(f"New HID connection from {device}")
        fd = fd.take()
        flags = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
        # TODO: handle HID I/O

    @dbus.service.method("org.bluez.Profile1", in_signature="o", out_signature="")
    def RequestDisconnection(self, device):
        print(f"RequestDisconnection from {device}")


def register_hid_profile():
    # 初始化 GLib/MainLoop
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    loop = GLib.MainLoop()

    # 连接 system bus
    bus = dbus.SystemBus()

    # —— 新增：打开蓝牙适配器的 discoverable 和 pairable ——
    adapter_path = "/org/bluez/hci0"
    adapter_obj = bus.get_object("org.bluez", adapter_path)
    adapter_props = dbus.Interface(adapter_obj, "org.freedesktop.DBus.Properties")
    # 设置为永远可发现和可配对
    adapter_props.Set("org.bluez.Adapter1", "DiscoverableTimeout", dbus.UInt32(0))
    adapter_props.Set("org.bluez.Adapter1", "Discoverable", dbus.Boolean(1))
    adapter_props.Set("org.bluez.Adapter1", "Pairable", dbus.Boolean(1))

    # 获取 ProfileManager 接口
    manager = dbus.Interface(
        bus.get_object("org.bluez", "/org/bluez"),
        "org.bluez.ProfileManager1"
    )

    # 在 D-Bus 上创建我们自己的 Profile 对象
    profile_path = "/org/bluez/hci0/hid_keyboard"
    HIDProfile(bus, profile_path)

    options = {
        "ServiceRecord": HID_SERVICE_RECORD,
        "Role": "server",
        "RequireAuthentication": False,
        "RequireAuthorization": False,
        "AutoConnect": True,
        "PSM": dbus.UInt16(0x11),
        "Channel": dbus.UInt16(0x13),
    }

    manager.RegisterProfile(
        profile_path,
        "00001124-0000-1000-8000-00805F9B34FB",
        options
    )
    print(f"HID Profile registered at {profile_path}")

    # 进入主循环，保持注册状态
    loop.run()

if __name__ == "__main__":
    register_hid_profile()

