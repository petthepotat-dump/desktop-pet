import os
import json
import random

from PyQt5.QtWidgets import QLabel, QVBoxLayout
from PyQt5.QtCore import QObject, Qt
from PyQt5.QtGui import QMovie

from source import settings, desktop

from pygame import Rect
from pygame.math import Vector2


# ============================================================================== #


# ============================================================================== #


class PetAnimationCache:
    def __init__(self, filename: str):
        self.filename = filename

        # open file
        with open(filename, "r") as file:
            self.metadata = json.load(file)
        self.parent_folder = os.path.join(os.getcwd(), self.metadata["parent_folder"])

        # load items into cache
        self.cache = {}
        for key, val in self.metadata[settings.ANIMATION_KEY].items():
            # multiple items
            self.cache[key] = [QMovie(os.path.join(self.parent_folder, v)) for v in val]
            # [print(os.path.join(self.parent_folder, v)) for v in val]

        print(self.cache)

    def get(self, key: str) -> QMovie:
        return self.cache[key]


class PetObject(QLabel):
    MS = 10

    def __init__(self, parent, pet_data: str):
        super().__init__(parent)
        self.animation_cache = PetAnimationCache(pet_data)
        self.active_movie_name = "idle"
        self.active_movie = None

        # create label
        self._pos = Vector2((200, 800))
        self._rect = Rect(0, 0, settings.CHARACTER_WIDTH, settings.CHARACTER_HEIGHT)
        self._vel = Vector2()

        # select a movie
        self.active_movie = random.choice(
            list(self.animation_cache.get(self.active_movie_name))
        )
        self.setMovie(self.active_movie)
        self.active_movie.start()

        self._timer = 0

        # ============================================ #
        # setup world interaction

        pass

    def update_animation(self, new_ani):
        if new_ani == self.active_movie_name:
            return
        self.active_movie.stop()
        self.active_movie = random.choice(list(self.animation_cache.get(new_ani)))
        self.setMovie(self.active_movie)
        self.active_movie.start()
        self.active_movie_name = new_ani

    def update_animation_isotope(self):
        self.active_movie.stop()
        self.active_movie = self.animation_cache.get(new_ani)[0]
        self.setMovie(self.active_movie)
        self.active_movie.start()

    def update_and_render(self):
        # is a state machine -- update all states!
        windows = desktop.get_active_windows()
        blocks = [window["area"] for window in windows]

        # if not touching down should fall down

        #  TOP RIGHT BOTTOM LEFT
        hit = [0, 0, 0, 0]
        self._vel.y = self.MS

        # ------------------------- #
        # animation clock timer
        if self._timer > 2.5:  # 2.5 seconds
            self._timer = 0
            # change animation
            self.update_animation_isotope()

        # ------------------------- #
        # perform movement with respect to each axis independently

        # x axis
        self._pos.x += self._vel.x * settings.DELTA
        self._rect.x = self._pos.x

        # y axis
        self._pos.y += self._vel.y * settings.DELTA
        self._rect.y = self._pos.y
        for rect in blocks:
            # check if collide with top line or bottom line
            top = Rect(rect.x, rect.y, rect.w, 1)
            bottom = Rect(rect.x, rect.y + rect.h, rect.w, 1)
            # top line
            if self._rect.colliderect(top):
                if self._vel.y > 0:
                    hit[2] = 1
                    self._vel.y = 0
                    self._pos.y = top.top - self._rect.h + 1
                else:
                    hit[0] = 1
                    self._vel.y = 0
                    self._pos.y = top.bottom - 1
            # bottom line
            if self._rect.colliderect(bottom):
                if self._vel.y > 0:  # down
                    hit[2] = 1
                    self._vel.y = 0
                    self._pos.y = bottom.top - self._rect.h + 1
                else:  # up
                    hit[0] = 1
                    self._vel.y = 0
                    self._pos.y = bottom.bottom - 1
        # restriction #1 - cannot fall out of bottom of screen
        if self._rect.bottom >= self.parentWidget().height():
            hit[2] = 1
            self._vel.y = 0
            self._rect.bottom = self.parentWidget().height()

        # ------------------------- #
        # conditional animation
        if hit[2] == 1:
            self.update_animation("idle")
        else:
            self.update_animation("fall")

        # update geometry
        self.setGeometry(self._rect.x, self._rect.y, self._rect.w, self._rect.h)
        print(hit, self._rect, self._vel)
