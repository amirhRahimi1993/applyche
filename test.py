import sys
import webbrowser
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QMenu, QInputDialog, QTextBrowser
)
from PyQt6.QtGui import  QTextCharFormat, QFont
from PyQt6.QtCore import Qt, QUrl


class RichTextBrowser(QTextBrowser):
    def __init__(self):
        super().__init__()
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_custom_context_menu)
        self.anchorClicked.connect(self.open_link_in_browser)

        # Enable editing (QTextBrowser is read-only by default)
        self.setReadOnly(False)

    def show_custom_context_menu(self, position):
        cursor = self.textCursor()
        if cursor.hasSelection():
            menu = QMenu()

            bold_action = menu.addAction("Bold")
            italic_action = menu.addAction("Italic")
            link_action = menu.addAction("Add Link")

            action = menu.exec(self.mapToGlobal(position))

            if action == bold_action:
                self.set_format(bold=True)
            elif action == italic_action:
                self.set_format(italic=True)
            elif action == link_action:
                self.add_link()
        else:
            # fallback to default
            super().contextMenuEvent

    def set_format(self, bold=False, italic=False):
        cursor = self.textCursor()
        if not cursor.hasSelection():
            return

        fmt = QTextCharFormat()
        if bold:
            fmt.setFontWeight(QFont.Weight.Bold)
        if italic:
            fmt.setFontItalic(True)

        cursor.mergeCharFormat(fmt)

    def add_link(self):
        cursor = self.textCursor()
        if not cursor.hasSelection():
            return

        url, ok = QInputDialog.getText(
            self, "Add Link", "Enter URL:"
        )

        if ok and url:
            fmt = QTextCharFormat()
            fmt.setAnchor(True)
            fmt.setAnchorHref(url)
            fmt.setForeground(Qt.GlobalColor.blue)
            fmt.setFontUnderline(True)

            cursor.mergeCharFormat(fmt)

    def open_link_in_browser(self, url: QUrl):
        webbrowser.open(url.toString())


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.editor = RichTextBrowser()
        self.setCentralWidget(self.editor)
        self.setWindowTitle("Rich Text with Clickable Links")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(600, 400)
    window.show()
    sys.exit(app.exec())
