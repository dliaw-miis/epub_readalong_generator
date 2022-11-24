#!/usr/bin/python

import argparse
import logging
import mimetypes
import os
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import zipfile

class EpubReadalongGenerator:
        
    @staticmethod
    def generate_readalong(epub_filepath: str, audio_filepath: str):
        try:
            folder_path, _ = os.path.split(epub_filepath)
            logging.info(epub_filepath)
            with zipfile.ZipFile(epub_filepath, 'r') as epub, TemporaryDirectory() as working_dir:
                epub.extractall(working_dir)
                logging.info("Extracted epub")

                EpubReadalongGenerator.add_audio_file(working_dir, audio_filepath)

                xhtml_files = EpubReadalongGenerator.get_xhtml_files(working_dir)
                EpubReadalongGenerator.add_smil_files(working_dir, xhtml_files)
        except Exception as error:
            logging.error(error)

    @staticmethod
    def add_audio_file(working_dir: TemporaryDirectory, src_audio_filepath: str):
        epub_audio_dir = os.path.join(working_dir, "OEBPS", "audio")
        logging.info(epub_audio_dir)
        if not os.path.exists(epub_audio_dir):
            os.mkdir(epub_audio_dir)
            logging.debug("created audio dir")
        _, audio_filename = os.path.split(src_audio_filepath)
        destination_audio_filepath = os.path.join(epub_audio_dir, audio_filename)
        logging.debug(src_audio_filepath)
        logging.debug(destination_audio_filepath)
        shutil.copy(src_audio_filepath, destination_audio_filepath)

    @staticmethod
    def get_xhtml_files(working_dir: TemporaryDirectory)-> list[str]:
        xhtml_files = []
        epub_text_dir = os.path.join(working_dir, "OEBPS", "text")
        for root, _, files in os.walk(epub_text_dir):
            for f in files:
                filetype, _ = mimetypes.guess_type(f)
                if filetype == "application/xhtml+xml":
                    xhtml_files.append(os.path.join(root, f))
        logging.debug(xhtml_files)
        return xhtml_files

    @staticmethod
    def add_smil_files(working_dir: TemporaryDirectory, xhtml_files: list[str]):
        epub_smil_dir = os.path.join(working_dir, "OEBPS", "smil")
        if not os.path.exists(epub_smil_dir):
            os.mkdir(epub_smil_dir)
            logging.debug("created smil dir")
        for file in xhtml_files:
            logging.debug(file)
            filestem = Path(file).stem
            logging.debug(filestem)
            page_smil_filepath = os.path.join(epub_smil_dir, filestem + ".smil")
            shutil.copy("resources/template.smil", page_smil_filepath)
            logging.debug(page_smil_filepath)



if __name__ == "__main__":
    # TODO: Implement argparse
    # options_parser = argparse.ArgumentParser()
    # options_parser.add_argument("--pages", type=str, required=False, help="Pages to do (<format example here>)")

    # EpubReadlongGenerator.do_something()
    # args = options_parser.parse_args()
    # print(args)

    logging.basicConfig(level=logging.DEBUG)
    EpubReadalongGenerator.generate_readalong("./test/The Fire Engine Book_original copy.epub", "test/audio.m4a")
