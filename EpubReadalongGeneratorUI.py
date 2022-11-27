import sys

from PyQt6 import uic
from PyQt6.QtCore import QSize
from PyQt6.QtWidgets import QApplication, QFileDialog, QLabel, QLineEdit, QMainWindow, QPushButton, QVBoxLayout, QWidget

from EpubReadalongGenerator import EpubReadalongGenerator


# Subclass QMainWindow to customize your application's main window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("mainwindow.ui", self)
        self.setWindowTitle("EPUB Readalong Generator")

        # File dialog buttons
        self.epub_filedialog.clicked.connect(self.epub_file_dialog)
        self.audio_filedialog.clicked.connect(self.audio_file_dialog)
        self.timing_filedialog.clicked.connect(self.timing_file_dialog)
        self.css_filedialog.clicked.connect(self.css_file_dialog)

        # Generate button
        self.generate_btn.clicked.connect(self.generate_readalong)
        

    def epub_file_dialog(self):
        filename = QFileDialog.getOpenFileName(None, "Select EPUB file", filter="EPUBs (*.epub)")
        if filename is not None:
            self.epub_text.setText(filename[0])

    def audio_file_dialog(self):
        filename = QFileDialog.getOpenFileName(None, "Select audio file")
        if filename is not None:
            self.audio_text.setText(filename[0])

    def timing_file_dialog(self):
        filename = QFileDialog.getOpenFileName(None, "Select timing file")
        if filename is not None:
            self.timing_text.setText(filename[0])

    def css_file_dialog(self):
        filename = QFileDialog.getOpenFileName(None, "Select CSS file", filter="CSS (*.css)")
        if filename is not None:
            self.css_text.setText(filename[0])

    def generate_readalong(self):
        # Check required fields
        epub_filepath = self.epub_text.text().strip()
        audio_filepath = self.audio_text.text().strip()
        timing_filepath = self.timing_text.text().strip()
        css_filepath = self.css_text.text().strip()
        page_range = self.range_text.text().strip()
        if len(epub_filepath) == 0:
            self.statusbar.showMessage("No EPUB file selected!", 10 * 1000)
        elif len(audio_filepath) == 0:
            self.statusbar.showMessage("No audio file selected!", 10 * 1000)
        elif len(timing_filepath) == 0:
            self.statusbar.showMessage("No timing file selected!", 10 * 1000)
        else:
            readalong_epub_filepath = EpubReadalongGenerator() \
                .set_epub_filepath(epub_filepath) \
                .set_audio_filepath(audio_filepath) \
                .set_audio_timing_filepath(timing_filepath) \
                .set_css_filepath(css_filepath) \
                .set_page_range(page_range) \
                .build()
            self.statusbar.showMessage("Readalong epub generated!")
            
app = QApplication(sys.argv)
window = MainWindow()
window.show()

app.exec()