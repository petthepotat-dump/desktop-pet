import time
import win32gui
import win32process
import win32con
import psutil

import ctypes

from PyQt5.QtCore import QTimer

from pygame import Rect
from source import settings, utils


def is_valid_window(hwnd) -> bool:
    """
    Check if a window is valid.
    """
    # Check if the window is visible
    if not win32gui.IsWindowVisible(hwnd):
        return False

    # Check if window is minimized
    if win32gui.IsIconic(hwnd):
        return False

    # Get window title
    window_text = win32gui.GetWindowText(hwnd)
    if not window_text or window_text == settings.APPLICATION_NAME:
        return False

    # Get window rectangle
    rect = win32gui.GetWindowRect(hwnd)
    width = rect[2] - rect[0]
    height = rect[3] - rect[1]
    if width < settings.MINIMUM_WINDOW_WIDTH or height < settings.MINIMUM_WINDOW_HEIGHT:
        return False

    # Check if window is part of illegal names
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    process = psutil.Process(pid)
    if process.name() in settings.ILLEGAL_WINDOW_NAMES:
        return False

    return True


def is_mandatory_window(hwnd: dict) -> bool:
    """
    Check if a window is mandatory (dock or etc).
    """
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    process = psutil.Process(pid)
    return process.name() in settings.MANDATORY_WINDOW_NAMES


def get_active_windows():
    """
    Get a list of active windows on the system.
    """

    def callback(hwnd, windows):
        if is_valid_window(hwnd):
            rect = win32gui.GetWindowRect(hwnd)
            window_info = {
                "name": win32gui.GetWindowText(hwnd),
                "owner": psutil.Process(
                    win32process.GetWindowThreadProcessId(hwnd)[1]
                ).name(),
                "pid": win32process.GetWindowThreadProcessId(hwnd)[1],
                "area": Rect(rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1]),
                "wid": hwnd,
                "layer": win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE),
                "global": False,
                "mandatory": is_mandatory_window(hwnd),
            }
            windows.append(window_info)
        return True

    windows = []
    win32gui.EnumWindows(callback, windows)
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
        user32 = ctypes.windll.user32
        self.screen_width = user32.GetSystemMetrics(0)
        self.screen_height = user32.GetSystemMetrics(1)

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
                window["wid"],
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

        # print(pet._pos, pet._vel, time.time() - settings.START_TIME)

        return hit
