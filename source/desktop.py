import Quartz

from pygame import Rect
from source import settings


def is_valid_window(window: dict) -> bool:
    """
    Check if a window is valid.
    """
    # if behind background or minimized
    if window.get("kCGWindowLayer") < 0:
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

    return True


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
    for window in window_list:
        if not is_valid_window(window):
            continue

        area = window.get("kCGWindowBounds")  # Bounds (position and size)
        rect = Rect(area["X"], area["Y"], area["Width"], area["Height"])

        window_info = {
            "name": window.get("kCGWindowName", "Unknown"),  # Window title
            "owner": window.get("kCGWindowOwnerName", "Unknown"),  # App name
            "pid": window.get("kCGWindowOwnerPID"),  # Process ID
            "area": rect,  # Area
            "layer": window.get("kCGWindowLayer"),  # Layer (z-order)
        }
        windows.append(window_info)

    return windows
