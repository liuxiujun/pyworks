# sudo apt update
# sudo apt install python3-evdev python3-dbus bluez
# pip3 install pydbus

#!/usr/bin/env python3
import os
import sys
import time
import evdev
import uinput
from evdev import InputDevice, categorize, ecodes, list_devices
from pydbus import SystemBus
from gi.repository import GLib

class BluetoothHIDService:
    """蓝牙HID服务管理"""
    def __init__(self):
        self.bus = SystemBus()
        self.hid_uuid = "00001124-0000-1000-8000-00805F9B34FB"
        self.profile_path = "/org/bluez/hid"
        self.adapter_path = self._get_adapter_path()
        
    def _get_adapter_path(self):
        """获取蓝牙适配器路径"""
        manager = self.bus.get("org.bluez", "/")
        objects = manager.GetManagedObjects()
        for path, interfaces in objects.items():
            if "org.bluez.Adapter1" in interfaces:
                print("[✓] 找到蓝牙适配器")
                return path
        raise RuntimeError("未找到蓝牙适配器")

    def register(self):
        """注册HID服务"""
        try:
            profile_manager = self.bus.get("org.bluez", "/org/bluez")
            options = {
                "Name": GLib.Variant("s", "RPiKeyboard"),
                "Service": GLib.Variant("s", self.hid_uuid),
                "Role": GLib.Variant("s", "server"),
                "Channel": GLib.Variant("q", 1),
                "AutoConnect": GLib.Variant("b", True),
                "RequireAuthentication": GLib.Variant("b", False),
                "RequireAuthorization": GLib.Variant("b", False),
            }
            profile_manager.RegisterProfile(
                self.profile_path,
                self.hid_uuid,
                options
            )
            print(f"[✓] HID服务注册成功 (UUID: {self.hid_uuid})")
            return True
        except Exception as e:
            print(f"[❌] 注册HID服务失败: {e}")
            return False

class VirtualKeyboard:
    """虚拟键盘设备"""
    def __init__(self):
        self.device = None
        self.key_map = self._create_key_map()
        self._init_device()

    def _create_key_map(self):
        """创建键码映射表"""
        return {
            # 字母键
            'KEY_A': uinput.KEY_A, 'KEY_B': uinput.KEY_B, 'KEY_C': uinput.KEY_C,
            'KEY_D': uinput.KEY_D, 'KEY_E': uinput.KEY_E, 'KEY_F': uinput.KEY_F,
            'KEY_G': uinput.KEY_G, 'KEY_H': uinput.KEY_H, 'KEY_I': uinput.KEY_I,
            'KEY_J': uinput.KEY_J, 'KEY_K': uinput.KEY_K, 'KEY_L': uinput.KEY_L,
            'KEY_M': uinput.KEY_M, 'KEY_N': uinput.KEY_N, 'KEY_O': uinput.KEY_O,
            'KEY_P': uinput.KEY_P, 'KEY_Q': uinput.KEY_Q, 'KEY_R': uinput.KEY_R,
            'KEY_S': uinput.KEY_S, 'KEY_T': uinput.KEY_T, 'KEY_U': uinput.KEY_U,
            'KEY_V': uinput.KEY_V, 'KEY_W': uinput.KEY_W, 'KEY_X': uinput.KEY_X,
            'KEY_Y': uinput.KEY_Y, 'KEY_Z': uinput.KEY_Z,

            # 数字键（主键盘区）
            'KEY_1': uinput.KEY_1, 'KEY_2': uinput.KEY_2, 'KEY_3': uinput.KEY_3,
            'KEY_4': uinput.KEY_4, 'KEY_5': uinput.KEY_5, 'KEY_6': uinput.KEY_6,
            'KEY_7': uinput.KEY_7, 'KEY_8': uinput.KEY_8, 'KEY_9': uinput.KEY_9,
            'KEY_0': uinput.KEY_0,

            # 功能键
            'KEY_ENTER': uinput.KEY_ENTER, 'KEY_ESC': uinput.KEY_ESC,
            'KEY_BACKSPACE': uinput.KEY_BACKSPACE, 'KEY_TAB': uinput.KEY_TAB,
            'KEY_SPACE': uinput.KEY_SPACE, 'KEY_CAPSLOCK': uinput.KEY_CAPSLOCK,

            # 修饰键
            'KEY_LEFTSHIFT': uinput.KEY_LEFTSHIFT, 'KEY_LEFTCTRL': uinput.KEY_LEFTCTRL,
            'KEY_LEFTALT': uinput.KEY_LEFTALT, 'KEY_LEFTMETA': uinput.KEY_LEFTMETA,
            'KEY_RIGHTSHIFT': uinput.KEY_RIGHTSHIFT, 'KEY_RIGHTCTRL': uinput.KEY_RIGHTCTRL,
            'KEY_RIGHTALT': uinput.KEY_RIGHTALT, 'KEY_RIGHTMETA': uinput.KEY_RIGHTMETA,

            # 符号键
            'KEY_MINUS': uinput.KEY_MINUS, 'KEY_EQUAL': uinput.KEY_EQUAL,
            'KEY_LEFTBRACE': uinput.KEY_LEFTBRACE, 'KEY_RIGHTBRACE': uinput.KEY_RIGHTBRACE,
            'KEY_BACKSLASH': uinput.KEY_BACKSLASH, 'KEY_SEMICOLON': uinput.KEY_SEMICOLON,
            'KEY_APOSTROPHE': uinput.KEY_APOSTROPHE, 'KEY_GRAVE': uinput.KEY_GRAVE,
            'KEY_COMMA': uinput.KEY_COMMA, 'KEY_DOT': uinput.KEY_DOT,
            'KEY_SLASH': uinput.KEY_SLASH,

            # 方向键
            'KEY_UP': uinput.KEY_UP, 'KEY_DOWN': uinput.KEY_DOWN,
            'KEY_LEFT': uinput.KEY_LEFT, 'KEY_RIGHT': uinput.KEY_RIGHT,

            # 功能键区
            'KEY_F1': uinput.KEY_F1, 'KEY_F2': uinput.KEY_F2, 'KEY_F3': uinput.KEY_F3,
            'KEY_F4': uinput.KEY_F4, 'KEY_F5': uinput.KEY_F5, 'KEY_F6': uinput.KEY_F6,
            'KEY_F7': uinput.KEY_F7, 'KEY_F8': uinput.KEY_F8, 'KEY_F9': uinput.KEY_F9,
            'KEY_F10': uinput.KEY_F10, 'KEY_F11': uinput.KEY_F11, 'KEY_F12': uinput.KEY_F12,

            # 其他常用键
            'KEY_INSERT': uinput.KEY_INSERT, 'KEY_DELETE': uinput.KEY_DELETE,
            'KEY_HOME': uinput.KEY_HOME, 'KEY_END': uinput.KEY_END,
            'KEY_PAGEUP': uinput.KEY_PAGEUP, 'KEY_PAGEDOWN': uinput.KEY_PAGEDOWN,
            'KEY_PRINT': uinput.KEY_PRINT, 'KEY_PAUSE': uinput.KEY_PAUSE,
            'KEY_SCROLLLOCK': uinput.KEY_SCROLLLOCK
        }
        

    def _init_device(self):
        """初始化虚拟输入设备"""
        try:
            self.device = uinput.Device(
                self.key_map.values(),
                name="Virtual RPi Keyboard",  # 明确设备名
                # bustype=uinput.BUS_USB,       # 指定总线类型
                vendor=0x1d6b,                # Linux Foundation
                product=0x0104                # 虚拟输入设备
            )
            time.sleep(1)  # 等待设备初始化
            print("[✓] 虚拟键盘设备已创建")
        except Exception as e:
            print(f"[❌] 初始化虚拟键盘失败: {e}")
            raise

    def send_key(self, keycode, pressed=True):
        """发送按键事件"""
        if keycode in self.key_map:
            try:
                self.device.emit(self.key_map[keycode], pressed)
                print(f"  | 按键: {keycode:12} {'按下' if pressed else '释放'}")
            except Exception as e:
                print(f"[⚠] 发送按键失败 ({keycode}): {e}")
        else:
            print(f"[⚠] 忽略未映射的按键: {keycode}")

def find_keyboard():
    """查找物理键盘设备"""
    try:
        # devices = [InputDevice(path) for path in list_devices()]
        keyboard = InputDevice("/dev/input/event0")
        # for dev in devices:
        #     print(dev)
        #     if "A4tech" in dev.name and "Mouse" not in dev.name:
        #         print(f"[✓] 找到键盘设备: {dev.name} ({dev.path})")
        #         return dev
        print(f"[✓] 找到键盘设备: {keyboard.name} ({keyboard.path})")
        return keyboard
        raise RuntimeError("未找到符合条件的键盘设备")
        return InputDevice('/dev/input/by-id/usb-H6209_A4tech_2.4G_Wireless_Device-event-kbd')
    except Exception as e:
        print(f"[❌] 查找键盘设备失败: {e}")
        raise

def check_permissions():
    """检查运行权限和系统要求"""
    if not sys.platform.startswith('linux'):
        raise RuntimeError("此脚本仅支持Linux系统")
    
    if os.geteuid() != 0:
        raise RuntimeError("请使用sudo运行此脚本")

    # 检查uinput模块
    if not os.path.exists("/dev/uinput"):
        raise RuntimeError("uinput设备不存在，请执行: sudo modprobe uinput")

def main():
    try:
        # 1. 检查权限
        check_permissions()
        
        # 2. 初始化HID服务
        hid_service = BluetoothHIDService()
        if not hid_service.register():
            return

        # 3. 查找物理键盘
        keyboard = find_keyboard()
        # physical_caps = keyboard.capabilities().get(ecodes.EV_KEY, [])
        # all_keys = list([
        #     k for k in physical_caps 
        #     if k in ecodes.keys.keys()  # 过滤有效键码
        # ])
        # 获取所有有效的uinput键码常量
        # all_keys = []
        # for keycode in physical_caps:
        #     try:
        #         # 1. 通过evdev键码获取键名（如30 -> 'KEY_A'）
        #         key_name = ecodes.KEY[keycode]
        #         print(key_name)
        #         # 2. 通过键名获取对应的uinput常量（如'KEY_A' -> uinput.KEY_A）
        #         if hasattr(uinput, key_name):
        #             all_keys.append(getattr(uinput, key_name))
        #         else:
        #             print(f"[⚠] uinput缺少对应键码: {key_name}")
        #     except KeyError:
        #         print(f"[⚠] 忽略未知的evdev键码: {keycode}")

        # print(list(all_keys))

        # 4. 初始化虚拟键盘
        vkbd = VirtualKeyboard()

        print("\n[状态] 服务运行中 (Ctrl+C退出)...")
        print("-"*50)
        
        # 5. 主事件循环
        for event in keyboard.read_loop():
            if event.type == ecodes.EV_KEY:
                key_event = categorize(event)
                vkbd.send_key(
                    key_event.keycode,
                    key_event.keystate == key_event.key_down
                )

    except KeyboardInterrupt:
        print("\n[退出] 用户中断")
    except Exception as e:
        print(f"\n[错误] 致命错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
