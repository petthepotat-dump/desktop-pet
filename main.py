import sys
from PyQt5.QtWidgets import QApplication

from source.window import TransparentWindow
from source import desktop

from source import settings


# Main application
if __name__ == "__main__":
    settings.init()
    app = QApplication(sys.argv)

    # Create and show the transparent window
    window = TransparentWindow()
    window.show()

    sys.exit(app.exec_())
