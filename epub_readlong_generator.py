#!/usr/bin/python

import argparse
import logging
import mimetypes
import mutagen
import os
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import xml.etree.ElementTree as ET
import zipfile

class EpubReadalongGenerator:
    
    @staticmethod
    def generate_readalong(epub_filepath: str, audio_filepath: str):
        try:
            folder_path, _ = os.path.split(epub_filepath)
            logging.info(epub_filepath)
            # with zipfile.ZipFile(epub_filepath, 'r') as epub, "TemporaryDirectory()" as working_dir:
            with zipfile.ZipFile(epub_filepath, 'r') as epub:
                working_dir = "test/epub"
                epub.extractall(working_dir)
                logging.info("Extracted epub")

                EpubReadalongGenerator.add_audio_file(working_dir, audio_filepath)

                xhtml_stems = EpubReadalongGenerator.get_xhtml_stems(working_dir)
                EpubReadalongGenerator.add_smil_files(working_dir, xhtml_stems)
                EpubReadalongGenerator.edit_content_opf(working_dir, audio_filepath, xhtml_stems)
        except Exception as error:
            logging.error(error)

    @staticmethod
    def add_audio_file(working_dir, src_audio_filepath: str):
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
    # Assumes that all xhtml files are in OEBPS/text
    def get_xhtml_stems(working_dir)-> list[str]:
        xhtml_stems = []
        epub_text_dir = os.path.join(working_dir, "OEBPS", "text")
        for root, _, files in os.walk(epub_text_dir):
            for f in files:
                filetype, _ = mimetypes.guess_type(f)
                if filetype == "application/xhtml+xml":
                    xhtml_stems.append(Path(f).stem)
        logging.debug(xhtml_stems)
        return sorted(xhtml_stems)

    @staticmethod
    def add_smil_files(working_dir, xhtml_stems: list[str]):
        epub_smil_dir = os.path.join(working_dir, "OEBPS", "smil")
        if not os.path.exists(epub_smil_dir):
            os.mkdir(epub_smil_dir)
            logging.debug("created smil dir")
        for filestem in xhtml_stems:
            logging.debug(filestem)
            page_smil_filepath = os.path.join(epub_smil_dir, filestem + ".smil")
            shutil.copy("resources/template.smil", page_smil_filepath)
            logging.debug(page_smil_filepath)

    @staticmethod
    def edit_content_opf(working_dir, src_audio_filepath: str, xhtml_stems: list[str]):
        content_opf_filepath = os.path.join(working_dir, "OEBPS", "content.opf")
        ET.register_namespace("", "http://www.idpf.org/2007/opf")
        content_opf_tree = ET.parse(content_opf_filepath)
        root = content_opf_tree.getroot()
        logging.debug(root.text)

        # Namespace
        ns = {"opf": "http://www.idpf.org/2007/opf"}
        
        # Metadata - audio elements
        metadata_el = root.find("opf:metadata", ns)
        logging.debug(metadata_el)
        media_duration_el = ET.Element("meta")
        media_duration_el.set("property", "media:duration")
        media_length = round(mutagen.File(src_audio_filepath).info.length) # Duration in seconds
        duration_hours = media_length // 3600
        duration_minutes = (media_length % 3600) // 60
        duration_seconds = media_length % 60
        media_duration_el.text = f"{duration_hours}:{duration_minutes}:{duration_seconds}"
        media_active_class_el = ET.Element("meta")
        media_active_class_el.set("property", "media:active-class")
        media_active_class_el.set("property", "media:active-class")
        media_active_class_el.text = "media-overlay-active"
        metadata_el.append(media_duration_el)
        metadata_el.append(media_active_class_el)

        # Manifest - audio
        manifest_el = root.find("opf:manifest", ns)
        logging.debug(metadata_el)
        audio_item_el = ET.Element("item")
        audio_item_el.set("id", "audio1")
        _, audio_filename = os.path.split(src_audio_filepath)
        audio_item_el.set("href", "audio/" + audio_filename)
        filetype, _ = mimetypes.guess_type(audio_filename)
        audio_item_el.set("media-type", filetype)
        manifest_el.append(audio_item_el)

        # Manifest - smil/xhtml
        for filestem in reversed(xhtml_stems):  # Reversed so that they are added in correct order
            smil_el = ET.Element("item")
            smil_el.set("media-type", "application/smil+xml")
            smil_el.set("id", "smil_" + filestem)
            smil_el.set("href", "smil/" + filestem + ".smil")
            manifest_el.insert(0, smil_el)
            xhtml_el = manifest_el.find("opf:item[@id='" + filestem + "']", ns)
            logging.debug(xhtml_el)
            xhtml_el.set("media-overlay", "smil_" + filestem)

        content_opf_tree.write(content_opf_filepath, "utf-8", True)

        

if __name__ == "__main__":
    # TODO: Implement argparse
    # options_parser = argparse.ArgumentParser()
    # options_parser.add_argument("--pages", type=str, required=False, help="Pages to do (<format example here>)")

    # EpubReadlongGenerator.do_something()
    # args = options_parser.parse_args()
    # print(args)

    logging.basicConfig(level=logging.DEBUG)
    EpubReadalongGenerator.generate_readalong("./test/The Fire Engine Book_original copy.epub", "test/audio.m4a")
