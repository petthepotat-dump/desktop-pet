from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt5.QtCore import Qt


class TransparentWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.WindowTransparentForInput
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(100, 100, 800, 600)

        # Create a label to visualize the window (optional)
        self.label = QLabel("Transparent Window", self)
        self.label.setGeometry(100, 100, 500, 500)
        self.label.setStyleSheet(
            "background-color: rgba(0, 0, 0, 50); color: white; font-size: 16px;"
        )
        self.label.setAttribute(Qt.WA_TransparentForMouseEvents, False)


if __name__ == "__main__":
    app = QApplication([])
    window = TransparentWindow()
    window.show()
    app.exec_()
