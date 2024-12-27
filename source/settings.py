import sys
import json
import time

# ============================================================================== #
# constants

SETTINGS_FILE = "assets/settings.json"

DEBUG = False
FPS = 16
DELTA = 1 / FPS
WORLD_DELTA = 2

NAME_KEY = "name"
ANIMATION_KEY = "animations"

IDLE_ANIMATION = "idle"
MOVE_ANIMATION = "move"
RUN_ANIMATION = "run"
FALL_ANIMATION = "fall"

CHARACTER_WIDTH = 100
CHARACTER_HEIGHT = 100

MINIMUM_WINDOW_WIDTH = 100
MINIMUM_WINDOW_HEIGHT = 100

# other contants


ICON_PATH = "assets/icon.png"
START_TIME = time.time()
ILLEGAL_WINDOW_NAMES = [
    # windows
    "Program Manager",
    "Start",
    "Settings",
    "Microsoft Store",
    # mac
    "Screenshot",
    "Notification Center",
    "Control Center",
]
MANDATORY_WINDOW_NAMES = ["Dock", "Finder", "SystemUIServer"]

APPLICATION_NAME = "DesktopPet"

# ============================================================================== #
# functions


# initialization functions
def init():
    # initialize constants
    with open(SETTINGS_FILE, "r") as file:
        settings = json.load(file)

    # set debug mode
    global DEBUG
    DEBUG = settings["DEBUG"]

    # set key names
    global NAME_KEY, ANIMATION_KEY
    NAME_KEY = settings["NAME_KEY"]
    ANIMATION_KEY = settings["ANIMATION_KEY"]

    # set animation names
    global IDLE_ANIMATION, MOVE_ANIMATION, RUN_ANIMATION, FALL_ANIMATION
    IDLE_ANIMATION = settings["IDLE_ANIMATION"]
    MOVE_ANIMATION = settings["MOVE_ANIMATION"]
    RUN_ANIMATION = settings["RUN_ANIMATION"]
    FALL_ANIMATION = settings["FALL_ANIMATION"]

    # window settings
    global CHARACTER_WIDTH, CHARACTER_HEIGHT
    CHARACTER_WIDTH = settings["CHARACTER_WIDTH"]
    CHARACTER_HEIGHT = settings["CHARACTER_HEIGHT"]

    # minimum window size
    global MINIMUM_WINDOW_WIDTH, MINIMUM_WINDOW_HEIGHT
    MINIMUM_WINDOW_WIDTH = settings["MINIMUM_WINDOW_WIDTH"]
    MINIMUM_WINDOW_HEIGHT = settings["MINIMUM_WINDOW_HEIGHT"]

    # set fps
    global FPS, DELTA, WORLD_DELTA
    FPS = settings["FPS"]
    DELTA = 1 / FPS
    WORLD_DELTA = settings["WORLD_DELTA"]
