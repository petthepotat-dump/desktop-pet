import sys
from PyQt5.QtWidgets import QApplication

from PyObjCTools.AppHelper import callLater

from source.window import TransparentWindow
from source import desktop
from source import settings


# ============================================ #


# Main application
if __name__ == "__main__":
    settings.init()
    app = QApplication(sys.argv)

    # Create and show the transparent window
    # this also creates status bar app
    window = TransparentWindow()
    window.show()

    # use pyobc `callLater1 to periodically update PyQt
    def run_pyqt():
        app.processEvents()
        callLater(1 / settings.FPS, run_pyqt)

    run_pyqt()

    from PyObjCTools.AppHelper import runEventLoop

    runEventLoop()

    # sys.exit(app.exec_())
