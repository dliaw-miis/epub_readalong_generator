#!/usr/bin/python

import argparse
import logging
from lxml import etree
from lxml.html import XHTMLParser
import mimetypes
import mutagen
import os
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import xml.etree.ElementTree as ET

class EpubReadalongGenerator:
    
    @staticmethod
    def generate_readalong(src_epub_filepath: str, audio_filepath: str, audio_timing_filepath: str):
        logging.info(src_epub_filepath)
            # with zipfile.ZipFile(epub_filepath, 'r') as epub, "TemporaryDirectory()" as working_dir:
                working_dir = "test/epub"
        shutil.unpack_archive(src_epub_filepath, working_dir, "zip")
                logging.info("Extracted epub")

                EpubReadalongGenerator.add_audio_file(working_dir, audio_filepath)
                xhtml_stems = EpubReadalongGenerator.get_xhtml_stems(working_dir)
                EpubReadalongGenerator.add_smil_files(working_dir, xhtml_stems)
                EpubReadalongGenerator.edit_content_opf(working_dir, audio_filepath, xhtml_stems)
            EpubReadalongGenerator.extract_text(working_dir, xhtml_stems, audio_timing_filepath, audio_filepath)

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
        return sorted(xhtml_stems)

    @staticmethod
    def add_smil_files(working_dir, xhtml_stems: list[str]):
        epub_smil_dir = os.path.join(working_dir, "OEBPS", "smil")
        if not os.path.exists(epub_smil_dir):
            os.mkdir(epub_smil_dir)
            logging.debug("created smil dir")
        for filestem in xhtml_stems:
            page_smil_filepath = EpubReadalongGenerator.get_smil_filepath(working_dir, filestem)
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

    @staticmethod
    def extract_text(working_dir, xhtml_stems: list[str], audio_timing_filepath: str, src_audio_filepath: str):
        logging.debug("extract_text")
        text_id = 1
        audio_timings = None
        with open(audio_timing_filepath) as timing_fp:
            audio_timings = timing_fp.readlines()

        # Loop through xhtml files and:
        # 1) Wrap individual words in spans
        # 2) Add corresponding audio timing par to smil
        for filestem in xhtml_stems:
            xhtml_filepath = EpubReadalongGenerator.get_xhtml_filepath(working_dir, filestem)
            smil_filepath = EpubReadalongGenerator.get_smil_filepath(working_dir, filestem)
            xhtml_xmltree = etree.parse(xhtml_filepath, XHTMLParser(resolve_entities=False))
            smil_xmltree = etree.parse(smil_filepath)
            text_nodes = xhtml_xmltree.xpath("//*[local-name()='body']//text()")
            smil_body = smil_xmltree.xpath("//*[local-name()='body']")[0]
            _, audio_filename = os.path.split(src_audio_filepath)
            logging.debug(text_nodes)
            
            for text in text_nodes:
                logging.debug("text: " + text)
                if not text.isspace():
                    edited_text = text
                    prev_sibling = None
                    if text.is_tail:
                        prev_sibling = text.getparent()
                        prev_sibling.tail = None    # Remove existing text so it can be wrapped
                    
                    words = edited_text.split()
                    logging.debug(words)
                    # Loop through words and create sibling spans beneath the parent
                    # Whitespace between words is attached as tail text
                    for word in words:
                        span_el = etree.Element("span")
                        span_el.set("id", "w" + str(text_id))
                        span_el.text = word
                        logging.debug(edited_text)
                        logging.debug(word)
                        word_idx = edited_text.index(word)

                        # Add timing to smil
                        par_el = etree.SubElement(smil_body, "par")
                        par_el.set("id", "par" + str(text_id))
                        par_text_el = etree.SubElement(par_el, "text")
                        par_text_el.set("src", f"../text/{filestem}.xhtml#w{text_id}")
                        par_audio_el = etree.SubElement(par_el, "audio")
                        par_audio_el.set("src", f"../audio/{audio_filename}")
                        audio_timing = audio_timings[text_id - 1].split()
                        par_audio_el.set("clipBegin", f"{audio_timing[0]}s")
                        par_audio_el.set("clipEnd", f"{audio_timing[1]}s")
                        
                        text_id += 1
                        
                        if prev_sibling is None:
                            text_parent_el = text.getparent()
                            text_parent_el.text = None  # Remove existing text so it can be wrapped
                            text_parent_el.insert(0, span_el)
                            if word_idx != 0:
                                # Whitespace before first word is parent node text, not tail
                                text_parent_el.text = edited_text[:word_idx]
                        else:
                            prev_sibling.addnext(span_el)
                            if word_idx != 0: 
                                prev_sibling.tail = edited_text[:word_idx]
                        # Remove words/whitespace which have been processed
                        edited_text = edited_text[word_idx + len(word):]
                        prev_sibling = span_el
                    if len(edited_text):
                        # Leftover whitespace
                        prev_sibling.tail = edited_text
            xhtml_xmltree.write(xhtml_filepath, encoding="utf-8", standalone=True)
            smil_xmltree.write(smil_filepath, encoding="utf-8")

    
    @staticmethod
    def get_xhtml_filepath(working_dir, filestem: str)-> str:
        return os.path.join(working_dir, "OEBPS", "text", filestem + ".xhtml")
    
    @staticmethod
    def get_smil_filepath(working_dir, filestem: str)-> str:
        return os.path.join(working_dir, "OEBPS", "smil", filestem + ".smil")    
        

if __name__ == "__main__":
    # TODO: Implement argparse
    # options_parser = argparse.ArgumentParser()
    # options_parser.add_argument("--pages", type=str, required=False, help="Pages to do (<format example here>)")

    # EpubReadlongGenerator.do_something()
    # args = options_parser.parse_args()
    # print(args)

    logging.basicConfig(level=logging.DEBUG)
    EpubReadalongGenerator.generate_readalong("./test/The Fire Engine Book_original copy.epub", "test/audio.m4a", "test/audio_full.txt")
