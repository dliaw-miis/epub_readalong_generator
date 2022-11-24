#!/usr/bin/python

import argparse
import logging
import os
import sys
from tempfile import TemporaryDirectory
import zipfile

class EpubReadlongGenerator:
        
    @staticmethod
    def generate_readalong(epub_filepath: str, audio_filepath: str):
        try:
            folder_path = os.path.split(epub_filepath)
            logging.info(epub_filepath)
            with zipfile.ZipFile(epub_filepath, 'r') as epub, TemporaryDirectory() as working_dir:
                epub.extractall(working_dir)
                logging.info("Extracted epub")

        except zipfile.BadZipFile:
            logging.error("epub file is corrupted")
        except:
            logging.error("Invalid epub file")


if __name__ == "__main__":
    # TODO: Implement argparse
    # options_parser = argparse.ArgumentParser()
    # options_parser.add_argument("--pages", type=str, required=False, help="Pages to do (<format example here>)")

    # EpubReadlongGenerator.do_something()
    # args = options_parser.parse_args()
    # print(args)

    logging.basicConfig(level=logging.INFO)
    EpubReadlongGenerator.generate_readalong("./test/The Fire Engine Book_original copy.epub")
