import gettext
import locale
from PyQt6 import uic
from PyQt6.QtCore import QSize
from PyQt6.QtWidgets import QApplication, QFileDialog, QMainWindow
import sys

from EpubReadalongGenerator import EpubReadalongGenerator

_ = gettext.gettext

# Subclass QMainWindow to customize your application's main window


class EpubReadalongGeneratorUI(QMainWindow):
    def __init__(self):
        super().__init__()

        uic.loadUi("mainwindow.ui", self)
        self.setWindowTitle(_("EPUB Readalong Generator"))
        self.epub_label.setText(_("EPUB file"))
        self.audio_label.setText(_("Audio file"))
        self.timing_label.setText(_("Timing file"))
        self.css_label.setText(_("CSS file"))
        self.range_label.setText(_("Page range"))
        self.generate_btn.setText(_("Generate"))

        # File dialog buttons
        self.epub_filedialog.clicked.connect(self.epub_file_dialog)
        self.audio_filedialog.clicked.connect(self.audio_file_dialog)
        self.timing_filedialog.clicked.connect(self.timing_file_dialog)
        self.css_filedialog.clicked.connect(self.css_file_dialog)

        # Generate button
        self.generate_btn.clicked.connect(self.generate_readalong)

    def epub_file_dialog(self):
        filename = QFileDialog.getOpenFileName(
            None, _("Select EPUB file"), filter="EPUBs (*.epub)")
        if filename is not None:
            self.epub_text.setText(filename[0])

    def audio_file_dialog(self):
        filename = QFileDialog.getOpenFileName(None, _("Select audio file"))
        if filename is not None:
            self.audio_text.setText(filename[0])

    def timing_file_dialog(self):
        filename = QFileDialog.getOpenFileName(None, _("Select timing file"))
        if filename is not None:
            self.timing_text.setText(filename[0])

    def css_file_dialog(self):
        filename = QFileDialog.getOpenFileName(
            None, _("Select CSS file"), filter="CSS (*.css)")
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
            self.statusbar.showMessage(_("No EPUB file selected!"), 10 * 1000)
        elif len(audio_filepath) == 0:
            self.statusbar.showMessage(_("No audio file selected!"), 10 * 1000)
        elif len(timing_filepath) == 0:
            self.statusbar.showMessage(
                _("No timing file selected!"), 10 * 1000)
        else:
            try:
                readalong_epub_filepath = EpubReadalongGenerator() \
                    .set_epub_filepath(epub_filepath) \
                    .set_audio_filepath(audio_filepath) \
                    .set_audio_timing_filepath(timing_filepath) \
                    .set_css_filepath(css_filepath) \
                    .set_page_range(page_range) \
                    .build()
                self.statusbar.showMessage(_("Readalong epub generated!"))
            except Exception as e:
                self.statusbar.showMessage(_("Error: {}").format(e), 10 * 1000)


if __name__ == "__main__":
    # Localization
    default_locale, _ = locale.getlocale()
    user_locale = ""
    if len(sys.argv) > 1:
        user_locale = sys.argv[1]
        print(user_locale)
    l10n = gettext.translation('messages', localedir='locales', languages=[
                               user_locale, default_locale, "en_US"], fallback=True)
    l10n.install()
    _ = l10n.gettext

    app = QApplication(sys.argv)
    window = EpubReadalongGeneratorUI()
    window.show()

    app.exec()
