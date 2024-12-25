import Quartz
import time

from PyQt5.QtCore import QTimer

from pygame import Rect
from source import settings


def is_valid_window(window: dict) -> bool:
    """
    Check if a window is valid.
    """
    # if behind background or minimized
    if window.get("kCGWindowLayer") < 0:
        return False

    if window.get("kCGWindowName") == settings.APPLICATION_NAME:
        return False

    # if window too small
    area = window.get("kCGWindowBounds")
    if (
        area["Width"] < settings.MINIMUM_WINDOW_WIDTH
        or area["Height"] < settings.MINIMUM_WINDOW_HEIGHT
    ):
        return False

    # or not visible
    if not window.get("kCGWindowIsOnscreen", False):
        return False

    # or if part of illegal names
    if window.get("kCGWindowOwnerName", "Unknown") in settings.ILLEGAL_WINDOW_NAMES:
        return False

    return True


def is_mandatory_window(window: dict) -> bool:
    """
    Check if a window is mandatory (dock or etc).
    """
    return (
        window.get("kCGWindowOwnerName", "Unknown") in settings.MANDATORY_WINDOW_NAMES
    )


def get_active_windows(filters: int = Quartz.kCGWindowListOptionOnScreenOnly) -> list:
    """
    Get a list of active windows on the system.
    """
    # Options for listing windows (visible, on-screen, etc.)
    options = filters

    # Get the list of all windows
    window_list = Quartz.CGWindowListCopyWindowInfo(options, Quartz.kCGNullWindowID)

    # Parse and return useful information
    windows = []
    for wid, window in enumerate(window_list):
        if not is_valid_window(window):
            continue

        area = window.get("kCGWindowBounds")  # Bounds (position and size)
        rect = Rect(area["X"], area["Y"], area["Width"], area["Height"])

        window_info = {
            "name": window.get("kCGWindowName", "Unknown"),  # Window title
            "owner": window.get("kCGWindowOwnerName", "Unknown"),  # App name
            "pid": window.get("kCGWindowOwnerPID"),  # Process ID
            "area": rect,  # Area
            "wid": wid,  # Layer (z-order)
            "layer": window.get("kCGWindowLayer", 0),  # Layer (z-order)
            "global": False,  # Global window
            "mandatory": is_mandatory_window(window),  # Mandatory window
        }
        windows.append(window_info)

    return windows


# ============================================================================== #
# window


class Window:
    def __init__(
        self,
        area: "rect",
        pid: str,
        name: str,
        owner: str,
        layer: int,
        is_global: bool,
        is_mandatory: bool,
    ):
        self.pid = pid
        self.area = area
        self.name = name
        self.owner = owner
        self.layer = layer

        self.active = False
        self.on_screen = False

        self.is_global = is_global
        self.is_mandatory = is_mandatory

    def __str__(self):
        return f"Window: {self.owner:20} {self.name:20} | PID: {self.pid:5} | Active: {self.active:2} | Layer: {self.layer:5} | Rect: {str(self.area):25} | Mandatory: {self.is_mandatory:5}"


# world
class World:
    def __init__(self):
        self.windows: ("PID", "Value") = {}

        # create a timer to update valid windows
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(1000 // settings.FPS)
        self.update()

    def iter_active_windows(self):
        for pid in self.windows:
            if self.windows[pid].active:
                yield self.windows[pid]

    def get_active_windows(self):
        return [x for x in self.windows.values() if x.active]

    def update(self):
        # grab all windows + update valid windows
        all_windows = get_active_windows()

        # set all windows to inactive
        for wid in self.windows:
            self.windows[wid].active = False
            self.windows[wid].on_screen = False
        for window in all_windows:
            if window["pid"] not in self.windows:
                self.windows[window["pid"]] = Window(
                    window["area"],
                    window["pid"],
                    window["name"],
                    window["owner"],
                    1000 - window["wid"],
                    window["global"],
                    window["mandatory"],
                )
            else:
                self.windows[window["pid"]].area = window["area"]
                self.windows[window["pid"]].layer = 1000 - window["wid"]
            self.windows[window["pid"]].on_screen = True

        # =============================== #
        print(f"TIME: {time.time()-settings.START_TIME} | updating the world")

        # print out all active window layers and owners
        win_array = [x for x in self.windows.values() if x.on_screen]
        win_array.sort(key=lambda x: -x.layer)
        # for w in win_array:
        #     print(w)

        # for each window, check if its behind another window (determine validity)
        # first is lowest -- forward check
        for i in range(len(win_array)):
            victim = win_array[i]
            # check if behind another window
            for j in range(i):
                container = win_array[j]
                if container.is_mandatory:
                    continue
                # check
                if (
                    container.area.contains(victim.area)
                    and container.layer > victim.layer
                ):
                    victim.active = False
                    break
            else:
                # print(f"activated: {victim.owner}")
                victim.active = True
        # end

        # print active windows
        print("ACTIVE WINDOWS")
        for w in self.iter_active_windows():
            print(w)
