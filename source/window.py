import sys
import time
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QPainter, QMovie
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget


from source import pet, desktop, settings


class TransparentWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # grab size of monitor
        self.screen = QApplication.primaryScreen()
        w, h = self.screen.size().width(), self.screen.size().height()
        self.setWindowTitle(settings.APPLICATION_NAME)

        # Set up the window
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.WindowTransparentForInput
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)
        self.setGeometry(0, 0, w, h)

        # ============================================ #
        # the world
        self.world = desktop.World()

        # the pet
        self.pet = pet.PetObject(self, "assets/pet.json")

        # ============================================ #

        # 24 fps timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(1000 // settings.FPS)

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
