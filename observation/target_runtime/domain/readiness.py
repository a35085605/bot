from enum import Enum


class TargetAvailability(str, Enum):
    UNKNOWN = "unknown"
    MISSING = "missing"
    AVAILABLE = "available"


class ControlChannelKind(str, Enum):
    DESKTOP_WINDOW = "desktop_window"
    ADB = "adb"


class ControlChannelStatus(str, Enum):
    UNKNOWN = "unknown"
    UNAVAILABLE = "unavailable"
    BLOCKED = "blocked"
    READY = "ready"


class ControlCapability(str, Enum):
    POINTER = "pointer"
    KEYBOARD = "keyboard"
    TEXT = "text"
    BACK = "back"


class FocusStatus(str, Enum):
    UNKNOWN = "unknown"
    TARGET = "target"
    OTHER = "other"
    NONE = "none"


class AdbDeviceStatus(str, Enum):
    UNKNOWN = "unknown"
    MISSING = "missing"
    UNAUTHORIZED = "unauthorized"
    OFFLINE = "offline"
    ONLINE = "online"
