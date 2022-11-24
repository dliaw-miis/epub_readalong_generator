#!/usr/bin/python

import argparse
import logging
import os
import shutil
from tempfile import TemporaryDirectory
import zipfile

class EpubReadalongGenerator:
        
    @staticmethod
    def generate_readalong(epub_filepath: str, audio_filepath: str):
        try:
            folder_path = os.path.split(epub_filepath)
            logging.info(epub_filepath)
            with zipfile.ZipFile(epub_filepath, 'r') as epub, TemporaryDirectory() as working_dir:
                epub.extractall(working_dir)
                logging.info("Extracted epub")

                EpubReadalongGenerator.add_audio_file(audio_filepath, working_dir)
        except zipfile.BadZipFile:
            logging.error("epub file is corrupted")
        except Exception as error:
            logging.error(error)

    @staticmethod
    def add_audio_file(src_audio_filepath: str, working_dir: TemporaryDirectory):
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



if __name__ == "__main__":
    # TODO: Implement argparse
    # options_parser = argparse.ArgumentParser()
    # options_parser.add_argument("--pages", type=str, required=False, help="Pages to do (<format example here>)")

    # EpubReadlongGenerator.do_something()
    # args = options_parser.parse_args()
    # print(args)

    logging.basicConfig(level=logging.DEBUG)
    EpubReadalongGenerator.generate_readalong("./test/The Fire Engine Book_original copy.epub", "test/audio.m4a")
