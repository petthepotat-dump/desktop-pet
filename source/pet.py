import os
import json
import math
import time
import random

from PyQt5.QtWidgets import QLabel, QVBoxLayout
from PyQt5.QtCore import QObject, Qt, QTimer, QEvent
from PyQt5.QtGui import QMovie, QPainter, QTransform, QImageReader, QPixmap, QCursor

from source import settings, desktop

from pygame import Rect
from pygame.math import Vector2

from source import statemachine, settings, signal, utils
from source.statemachine import StateMachineComponent, State


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
        self.cache_imagereader = {}
        for key, val in self.metadata[settings.ANIMATION_KEY].items():
            # multiple items
            self.cache[key] = [QMovie(os.path.join(self.parent_folder, v)) for v in val]
            self.cache_imagereader[key] = [
                QImageReader(os.path.join(self.parent_folder, v)) for v in val
            ]
            self.cache[key].sort(key=lambda x: x.fileName())
            self.cache_imagereader[key].sort(key=lambda x: x.fileName())

            # print([v.fileName() for v in self.cache[key]])

        # print(self.cache)

    def get(self, key: str) -> QMovie:
        return self.cache[key]

    def get_index(self, key: str, index: int) -> QMovie:
        return self.cache[key][index]

    def get_image_reader_index(self, key: str, index: int) -> QImageReader:
        return self.cache_imagereader[key][index]


class PetObject(QLabel):
    MS = 50

    def __init__(self, parent, pet_data: str):
        super().__init__(parent)
        self.parent = parent

        self.animation_cache = PetAnimationCache(pet_data)
        self.active_movie_name = "idle"
        self.active_movie = None

        # create label
        self._pos = Vector2(
            (
                int(
                    random.randint(0, int(self.parent.world.screen_width * 0.6))
                    + self.parent.world.screen_width * 0.2
                ),
                int(
                    random.randint(0, int(self.parent.world.screen_height * 0.6))
                    + self.parent.world.screen_height * 0.2,
                ),
            )
        )
        self._rect = Rect(0, 0, settings.CHARACTER_WIDTH, settings.CHARACTER_HEIGHT)
        self._vel = Vector2()
        self._flipped = False

        # select a movie
        self.active_movie = random.choice(
            list(self.animation_cache.get(self.active_movie_name))
        )
        self.setMovie(self.active_movie)
        self.active_movie.start()

        self.backup_frame = None

        # ============================================ #
        # setup world interaction

        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)

        # features
        self.is_dragged = False
        self.drag_offset = Vector2()

        # target location
        self._target_location = None
        self.current_window = None

        # statemachine
        self.statemachine = PetStateMachine(self)
        self.statemachine.add_state(IdleState())
        self.statemachine.add_state(MoveState())
        self.statemachine.add_state(FallState())
        self.statemachine.add_state(JumpStage1())
        # self.statemachine.add_state(JumpStage2())

        self.statemachine.set_current_state("idle")

        # signal handlers
        signal.SignalHandler.add_receiver("reset", self.receive_reset_event)
        signal.SignalHandler.add_receiver("custom", self.recieve_custom_event)

    # ------------------------- #

    def recieve_custom_event(self, args):
        # create target location at mouse location
        mpos = QCursor.pos()
        twin = None
        for window in self.parent.world.get_active_windows():
            if window.area.collidepoint(mpos.x(), mpos.y()):
                twin = window
                break

        self._target_location = {
            "window": twin,
            "pos": Vector2(mpos.x(), mpos.y()),
        }

        self.statemachine.set_next_state("move")

    def receive_reset_event(self, args):
        self._pos.xy = (
            random.randint(0, self.parent.world.screen_width - self._rect.w),
            random.randint(0, self.parent.world.screen_height - self._rect.h),
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragged = True
            self.drag_offset = Vector2(event.pos().x(), event.pos().y())

    def mouseMoveEvent(self, event):
        if self.is_dragged:
            delta = event.pos()
            self._rect.x = event.globalPos().x() - self.drag_offset.x
            self._rect.y = event.globalPos().y() - self.drag_offset.y
            self._pos.xy = self._rect.topleft

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragged = False

    # ------------------------- #

    def change_rect(self, widht: int, height: int):
        self._rect.w = widht
        self._rect.h = height

    # ------------------------- #

    def update_animation(self, new_ani, index: int = -1):
        if new_ani == self.active_movie_name and index == -1:
            return
        if self.active_movie:
            self.active_movie.stop()
        if index != -1:
            self.active_movie = self.animation_cache.get_index(new_ani, index)
        else:
            self.active_movie = random.choice(list(self.animation_cache.get(new_ani)))
        self.setMovie(self.active_movie)
        self.active_movie.start()
        self.active_movie_name = new_ani

    def remove_movie(self):
        if self.active_movie:
            self.active_movie.stop()
            self.active_movie = None
            self.setMovie(None)

    def update_animation_isotope(self):
        self.active_movie.stop()
        self.active_movie = random.choice(
            list(self.animation_cache.get(self.active_movie_name))
        )
        self.setMovie(self.active_movie)
        self.active_movie.start()

    def update_state(self):
        # is a state machine -- update all states!
        windows = self.parent.world.get_active_windows()
        blocks = [window.area for window in windows]

        # update current window
        for window in windows:
            if window.area.colliderect(self._rect):
                self.current_window = window
                break

        # ------------------------- #
        # statemachine
        self.statemachine.update()

        # update geometry
        # self.setGeometry(self._rect.x, self._rect.y, self._rect.w, self._rect.h)
        # self.setGeometry(0, 0, self._rect.w, self._rect.h)

        self.update()

    def paintEvent(self, event):
        # ------------------------- #
        # draw the pet
        painter = QPainter(self)
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        painter.fillRect(self.rect(), Qt.transparent)  # Clear the background
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

        # custom draw command
        if self.active_movie != None:
            frame_pixmap = self.active_movie.currentPixmap()
            if self._flipped:
                frame_pixmap = frame_pixmap.transformed(QTransform().scale(-1, 1))
            painter.drawPixmap(0, 0, frame_pixmap)


# ============================================================================== #
# statemachine


class PetStateMachine(StateMachineComponent):
    def __init__(self, pet: "PetObject"):
        super().__init__()
        self.pet = pet


# ---------------------------- #
class IdleState(State):
    def __init__(self):
        super().__init__("idle")

        self.timer = QTimer()
        self.timer.timeout.connect(self._timer_update)

        self.idle_move_timer = QTimer()
        self.idle_move_timer.timeout.connect(self._move_timer_update)

    def __post_init__(self, statemachine: "PetStateMachine"):
        self._statemachine = statemachine

    # ---------------------------- #

    def on_enter(self):
        self._statemachine.pet.update_animation("idle")
        self.timer.start(int(3000 + (random.random() - 0.5) * 2000))
        self.idle_move_timer.start(int(8000 + (random.random() - 0.5) * 5000))
        self._statemachine.pet._target_location = None

        # set geometry
        self._statemachine.pet.setGeometry(
            0,
            0,
            self._statemachine.pet._rect.w,
            self._statemachine.pet._rect.h,
        )

        # reset parent area
        self._statemachine.pet.parent.setGeometry(
            self._statemachine.pet._rect.x,
            self._statemachine.pet._rect.y,
            self._statemachine.pet._rect.w,
            self._statemachine.pet._rect.h,
        )

        print("in idle")
        print(self._statemachine.pet._rect)

    def on_exit(self):
        self.timer.stop()
        self.idle_move_timer.stop()

    def _move_timer_update(self):
        # decide on a place to move towards
        self._statemachine.pet._target_location = self.generate_random_target()
        self._statemachine.set_next_state("move")

        print(
            "moving to:",
            self._statemachine.pet._target_location,
            "from: ",
            {
                "window": self._statemachine.pet.current_window,
                "pos": self._statemachine.pet._pos,
            },
        )

    def _timer_update(self):
        self._statemachine.pet.update_animation_isotope()

    def update(self):

        hit = self._statemachine.pet.parent.world.move_pet(self._statemachine.pet)
        if not hit["bottom"]:
            self._statemachine.set_next_state("fall")

    def generate_random_target(self) -> {"window": "pid", "pos": "Vector2"}:
        # choose inside or outside
        inside = random.choice([True, False])
        target_window = None
        if not inside or self._statemachine.pet.current_window == None:
            # find a new window
            target_window = random.choice(
                self._statemachine.pet.parent.world.get_active_windows()
            )
        else:
            target_window = self._statemachine.pet.current_window
        target_position = Vector2()
        # generate random x
        target_position.x = int(
            target_window.area.x
            + target_window.area.w * 0.2
            + random.random() * target_window.area.w * 0.6
        )

        # pick top or bottom
        ans = random.choice([True, False])
        # check if top will give valid y position
        if target_window.area.y - self._statemachine.pet._rect.h < 5:
            ans = False
        if ans:
            # top
            target_position.y = target_window.area.y - self._statemachine.pet._rect.h
        else:
            # bottom
            target_position.y = (
                target_window.area.y
                + target_window.area.h
                - self._statemachine.pet._rect.h
            )

        return {"window": target_window, "pos": target_position}


class MoveState(State):
    def __init__(self):
        super().__init__("move")

        # target location
        self.target_location = None

        # target validity timer
        self._target_validity_timer = QTimer()
        self._target_validity_timer.timeout.connect(self._target_validity_timer_update)

    def __post_init__(self, statemachine: "PetStateMachine"):
        self._statemachine = statemachine

    # ---------------------------- #

    def on_enter(self):
        self._target_validity_timer.start(200)
        self.target_location = self._statemachine.pet._target_location
        self._statemachine.pet.update_animation("run")

        # set geometry
        self._statemachine.pet.setGeometry(
            0,
            0,
            self._statemachine.pet._rect.w,
            self._statemachine.pet._rect.h,
        )

    def on_exit(self):
        self._target_validity_timer.stop()
        self.target_location = None

    def _target_validity_timer_update(self):
        # check if target is still valid
        if self._statemachine.pet._target_location["window"] != None:
            if not self._statemachine.pet._target_location["window"].active:
                self._statemachine.set_next_state("idle")

    def update(self):
        if not self.target_location:
            self._statemachine.set_next_state("idle")
            return

        # set velocity
        self._statemachine.pet._vel.x = (
            1.0
            if self.target_location["pos"].x > self._statemachine.pet._pos.x
            else -1.0
        ) * self._statemachine.pet.MS
        self._statemachine.pet._flipped = self._statemachine.pet._vel.x < 0

        # check if x error is close enough
        if abs(self.target_location["pos"].x - self._statemachine.pet._pos.x) < 10:
            self._statemachine.pet._vel.x = 0
            self._statemachine.set_next_state("idle")
            # print("reached x")

            # determine if needs to jump or not
            # check if height is at least 80% of height of windnow
            dy = self._statemachine.pet._rect.y - self.target_location["pos"].y

            if dy > self._statemachine.pet._rect.h:
                self._statemachine.set_next_state("jumpstage1")
            else:
                self._statemachine.set_next_state("idle")

        # move towards target location
        hit = self._statemachine.pet.parent.world.move_pet(self._statemachine.pet)
        # if falling
        if hit["bottom"] == False:
            self._statemachine.pet.update_animation("fall")
        else:
            self._statemachine.pet.update_animation("run")


class JumpStage1(State):
    def __init__(self):
        super().__init__("jumpstage1")
        self._orect = None

        # variables for jump length + jump height + etc
        self._jump_delta = 0
        self._start_time = 0
        self._start_height = 0

    def __post_init__(self, statemachine: "PetStateMachine"):
        self._statemachine = statemachine

    # ---------------------------- #

    def on_enter(self):
        self._statemachine.pet.update_animation("jump", index=0)
        # set animatino to specific frame = frame 25

        self._orect = self._statemachine.pet._rect.copy()
        # create new rect for new animation
        # grab a frame from the movie
        frame = self._statemachine.pet.active_movie.currentPixmap()
        self._statemachine.pet.change_rect(frame.width(), frame.height())
        # center to bottomcenter
        self._statemachine.pet._rect.bottom = self._orect.bottom
        self._statemachine.pet._rect.centerx = self._orect.centerx

        # update parent area
        self._statemachine.pet.parent.setGeometry(
            self._statemachine.pet._rect.x,
            self._statemachine.pet._rect.y,
            self._statemachine.pet._rect.w,
            self._statemachine.pet._rect.h,
        )

        # set geometry
        self._statemachine.pet.setGeometry(
            0,
            0,
            self._statemachine.pet._rect.w,
            self._statemachine.pet._rect.h,
        )

        # set start variables
        self._start_height = self._statemachine.pet._rect.y
        self._start_time = time.time()
        self._jump_end_height = 0
        self._jump_delta = 0

        # print("starting jump?")

    def on_exit(self):

        jump_rect = self._statemachine.pet._rect.copy()
        # reset pet area
        self._statemachine.pet.change_rect(
            settings.CHARACTER_WIDTH, settings.CHARACTER_HEIGHT
        )
        self._statemachine.pet._rect.bottom = jump_rect.bottom
        self._statemachine.pet._pos.y = self._statemachine.pet._rect.y
        # print(self._statemachine.pet._rect)

    def update(self):
        # on the 27th frame, we swap to other animation
        # check if movie is playing
        # print("jumping", self._statemachine.pet.active_movie.currentFrameNumber())

        self._jump_delta = time.time() - self._start_time

        # check if target location exists
        if self._statemachine.pet._target_location != None:

            # jump function
            xfac = max(
                0,
                self._statemachine.pet.active_movie.currentFrameNumber() / 24 * 0.816497
                - 0.4,
            )
            yfac = 1 - 6 * (xfac - math.sqrt(24) / 12) ** 2

            if xfac < 0.408:  # before peak
                endy = utils.lerp(
                    self._start_height,
                    self._statemachine.pet._target_location["pos"].y
                    - self._statemachine.pet._rect.h,
                    yfac,
                )
                self._jump_end_height = endy
            else:  # after peak
                endy = utils.lerp(
                    self._jump_end_height,
                    self._statemachine.pet._target_location["pos"].y
                    - self._statemachine.pet._rect.h,
                    yfac,
                )

            # print(endy, xfac)
            self._statemachine.pet._rect.y = endy
            self._statemachine.pet._pos.y = endy

        if self._statemachine.pet.active_movie.currentFrameNumber() > 24:
            self._statemachine.set_next_state("idle")


class FallState(State):
    def __init__(self):
        super().__init__("fall")

    def __post_init__(self, statemachine: "PetStateMachine"):
        self._statemachine = statemachine

    # ---------------------------- #

    def on_enter(self):
        self._statemachine.pet.update_animation("fall")

        # set geometry
        self._statemachine.pet.setGeometry(
            0,
            0,
            self._statemachine.pet._rect.w,
            self._statemachine.pet._rect.h,
        )

        # print("in fall state")
        # print(self._statemachine.pet._rect)

    def update(self):
        hit = self._statemachine.pet.parent.world.move_pet(self._statemachine.pet)
        if hit["bottom"]:
            self._statemachine.set_next_state("idle")
