import sys
import time

from PyQt5.QtWidgets import QApplication

from PyObjCTools.AppHelper import callLater

from source.window import TransparentWindow
from source import desktop, settings, signal


# ============================================ #


# Main application
if __name__ == "__main__":
    # create signal handler
    signal_handler = signal.SignalHandler()

    # initialize settings
    settings.init()
    app = QApplication(sys.argv)

    # Create and show the transparent window
    # this also creates status bar app
    window = TransparentWindow()
    window.show()

    start_time = time.time() - settings.DELTA

    # use pyobc `callLater1 to periodically update PyQt
    def run_pyqt():
        global start_time
        settings.DELTA = time.time() - start_time

        app.processEvents()
        signal_handler.iterate_signals()
        window.update_state()

        start_time = time.time()
        callLater(1.0 / settings.FPS, run_pyqt)
        # print("running pyqt" + str(time.time() - settings.START_TIME))

    run_pyqt()

    from PyObjCTools.AppHelper import runEventLoop

    runEventLoop()

    # sys.exit(app.exec_())
