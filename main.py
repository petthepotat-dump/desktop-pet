import sys
import time
import psutil
import asyncio

from qasync import QEventLoop
from PyQt5.QtWidgets import QApplication

from source.window import TransparentWindow
from source import desktop, settings, signal


# ============================================ #
# use pyobc `callLater1 to periodically update PyQt
async def run_pyqt():
    global start_time
    start_time = time.time() - settings.DELTA
    while True:
        settings.DELTA = time.time() - start_time

        app.processEvents()
        signal_handler.iterate_signals()

        window.update_state()

        start_time = time.time()
        await asyncio.sleep(1.0 / settings.FPS)


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

    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    # Schedule the run_pyqt coroutine
    asyncio.ensure_future(run_pyqt())

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        print("Closing application")
        loop.close()
