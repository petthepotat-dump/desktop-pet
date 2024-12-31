import Quartz
import time

from PyQt5.QtCore import QTimer

from pygame import Rect
from source import settings, utils


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
        self.windows: ["Window"] = []

        # create a timer to update valid windows
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(1000 // settings.FPS)
        self.update()

        # desktop screen dimensions
        self.screen = Quartz.CGMainDisplayID()
        self.screen_width = Quartz.CGDisplayPixelsWide(self.screen)
        self.screen_height = Quartz.CGDisplayPixelsHigh(self.screen)

    def iter_active_windows(self):
        for window in self.windows:
            if window.active:
                yield window

    def get_active_windows(self):
        return [x for x in self.windows if x.active]

    def update(self):
        # grab all windows + update valid windows
        all_windows = get_active_windows()

        # reset all available windows
        self.windows = []
        for window in all_windows:
            item = Window(
                window["area"],
                window["pid"],
                window["name"],
                window["owner"],
                1000 - window["wid"],
                window["global"],
                window["mandatory"],
            )
            item.on_screen = True
            self.windows.append(item)
        self.windows.sort(key=lambda x: -x.layer)

        # =============================== #
        # print(f"TIME: {time.time()-settings.START_TIME} | updating the world")

        # for w in get_active_windows():
        #     print(w["name"], w["owner"], w["pid"], w["layer"], w["wid"])

        # print out all active window layers and owners
        win_array = [x for x in self.windows if x.on_screen]
        # for w in win_array:
        #     print(w)

        # for each window, check if its behind another window (determine validity)
        # first is lowest -- forward checkc
        for i in range(len(win_array)):
            victim = win_array[i]

            victim_rect = Rect(
                max(victim.area.x, 0) + 1,
                max(victim.area.y, 0) + 1,
                victim.area.w + min(0, victim.area.x) - 2,
                victim.area.h + min(0, victim.area.y) - 2,
            )

            # check if behind another window
            for j in range(i):
                container = win_array[j]
                if container.is_mandatory:
                    continue

                container_rect = Rect(
                    max(container.area.x, 0),
                    max(container.area.y, 0),
                    container.area.w + min(0, container.area.x),
                    container.area.h + min(0, container.area.y),
                )
                # check
                if (
                    container_rect.contains(victim_rect)
                    and container.layer > victim.layer
                ):
                    victim.active = False
                    break
            else:
                # print(f"activated: {victim.owner}")
                victim.active = True
        # end

        # print active windows
        # print("ACTIVE WINDOWS")
        # for w in self.iter_active_windows():
        #     print(w)

    def move_pet(self, pet: "PetObject"):
        """Move the pet object"""
        hit = {"top": False, "right": False, "bottom": False, "left": False}
        pet._vel.y += pet.MS

        blocks = [window.area for window in self.iter_active_windows()]

        # Separating Axis Theorem
        # x-axis
        pet._pos.x += pet._vel.x * settings.DELTA
        pet._rect.x = pet._pos.x

        # y-axis
        pet._pos.y += pet._vel.y * settings.DELTA
        pet._rect.y = pet._pos.y

        for rect in blocks:
            # check if collide with top line or bottom line
            top = Rect(rect.x, rect.y, rect.w, 1)
            bottom = Rect(rect.x, rect.y + rect.h, rect.w, 1)
            # top line
            if pet._rect.colliderect(top):
                if pet._vel.y > 0:
                    hit["bottom"] = True
                    pet._vel.y = 0
                    pet._pos.y = top.top - pet._rect.h + 1
                else:
                    hit["top"] = True
                    pet._vel.y = 0
                    pet._pos.y = top.bottom - 1
            # bottom line
            if pet._rect.colliderect(bottom):
                if pet._vel.y > 0:
                    hit["bottom"] = True
                    pet._vel.y = 0
                    pet._pos.y = bottom.top - pet._rect.h + 1
                else:
                    hit["top"] = True
                    pet._vel.y = 0
                    pet._pos.y = bottom.bottom - 1
        # restriction #1 - cannot fall out of bottom of screen
        if pet._rect.bottom >= self.screen_height:
            hit["bottom"] = True
            pet._vel.y = 0
            pet._rect.bottom = self.screen_height - 1

        # lerp
        pet._vel.xy *= 0.7

        print(pet._pos, pet._vel, time.time() - settings.START_TIME)

        return hit
