import sys
import time
from PyQt5.QtCore import Qt, QTimer, QEvent
from PyQt5.QtGui import QColor, QPainter, QMovie
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QLabel,
    QVBoxLayout,
    QWidget,
    QToolBar,
    QAction,
)

from AppKit import (
    NSApplication,
    NSApp,
    NSImage,
    NSStatusBar,
    NSVariableStatusItemLength,
    NSMenuItem,
    NSMenu,
)
from PyObjCTools.AppHelper import runEventLoop


from source import pet, desktop, settings, signal


# ============================================ #
# the main window object


class TransparentWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # grab size of monitor
        self.screen = QApplication.primaryScreen()
        # w, h = self.screen.size().width(), self.screen.size().height()
        w, h = 100, 100
        self.setWindowTitle(settings.APPLICATION_NAME)

        # Set up the window
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            # | Qt.WindowTransparentForInput
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(0, 0, w, h)

        self.status_bar = StatusBarApp()

        # ============================================ #
        # the world
        self.world = desktop.World()

        # the header toolbar

        # the pet
        self.pet = pet.PetObject(self, "assets/pet.json")
        self.installEventFilter(self.pet)

        # ============================================ #
        # event handlers
        signal.SignalHandler.add_receiver("hide", self.receive_hide_event)
        signal.SignalHandler.add_receiver("show", self.receive_show_event)

    # ============================================ #
    # event handlers

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            signal.SignalHandler.add_signal("custom", {})

    def receive_hide_event(self, args):
        self.hide()

    def receive_show_event(self, args):
        self.show()

    def update_state(self):

        self.pet.update_state()

        # move the window around on the screen
        self.move(self.pet._rect.x, self.pet._rect.y)

        # draw self
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)

        # clear surface
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        painter.fillRect(self.rect(), Qt.transparent)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

        if settings.DEBUG:
            # draw overlay
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QColor(0, 0, 0, 30))
            painter.setPen(Qt.NoPen)
            painter.drawRect(self.rect())

            # draw rectangles around all active windows within the desktop
            painter.setPen(QColor(255, 255, 255, 255))
            painter.setBrush(QColor(0, 0, 0, 0))
            for window in self.world.iter_active_windows():
                area = window.area
                # draw rect
                painter.drawRect(area.x, area.y, area.w, area.h)


# supporting application
class StatusBarApp:
    def __init__(self):
        self.app = NSApplication.sharedApplication()

        # create status bar item
        self.status_bar = NSStatusBar.systemStatusBar()
        self.status_item = self.status_bar.statusItemWithLength_(
            NSVariableStatusItemLength
        )

        # set icon for status bar item
        icon = NSImage.alloc().initWithContentsOfFile_(settings.ICON_PATH)

        icon.setSize_((18, 18))
        self.status_item.button().setImage_(icon)

        # create menu for the status bar item
        self.menu = NSMenu()
        self.create_menu()

        # attach menu to status bar item
        self.status_item.setMenu_(self.menu)

    def create_menu(self):
        # create menu items
        self.quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Quit", "terminate:", ""
        )
        self.menu.addItem_(self.quit_item)

        # create hide item
        self.hide_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Hide", "hideevent:", ""
        )
        self.hide_item.setTarget_(self)
        self.menu.addItem_(self.hide_item)

        # create show item
        self.show_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Show", "showevent:", ""
        )
        self.show_item.setTarget_(self)
        self.menu.addItem_(self.show_item)

        # create reset item
        self.reset_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Reset", "resetevent:", ""
        )
        self.reset_item.setTarget_(self)
        self.menu.addItem_(self.reset_item)

    # ============================================ #
    # event handlers

    def hideevent_(self, sender):
        # print("event received")
        signal.SignalHandler.add_signal("hide", {})

    def showevent_(self, sender):
        # print("event received", sender)
        signal.SignalHandler.add_signal("show", {})

    def resetevent_(self, sender):
        signal.SignalHandler.add_signal("reset", {})
