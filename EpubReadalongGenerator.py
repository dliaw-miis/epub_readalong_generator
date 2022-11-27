#!/usr/bin/python

import argparse
import logging
from lxml import etree
from lxml.html import XHTMLParser
import mimetypes
import mutagen
import os
from pathlib import Path
import re
import shutil
from tempfile import TemporaryDirectory


class EpubReadalongGenerator:

    range_pattern = re.compile("^\d+(_\d+)*(-\d+(_\d+)*)?$")

    def __init__(self, src_epub_filepath="", src_audio_filepath="",
                 audio_timing_filepath="", css_filepath="", page_range=""):
        self.src_epub_filepath = src_epub_filepath
        self.src_audio_filepath = src_audio_filepath
        self.audio_timing_filepath = audio_timing_filepath
        self.css_filepath = css_filepath
        self.set_page_range(page_range)
        self.epub_workdir = ""
        self.xhtml_stems = []

    def set_epub_filepath(self, src_epub_filepath):
        self.src_epub_filepath = src_epub_filepath
        return self

    def set_audio_filepath(self, src_audio_filepath):
        self.src_audio_filepath = src_audio_filepath
        return self

    def set_audio_timing_filepath(self, audio_timing_filepath):
        self.audio_timing_filepath = audio_timing_filepath
        return self

    def set_css_filepath(self, css_filepath):
        self.css_filepath = css_filepath
        return self

    def set_page_range(self, page_range):
        self.page_range = []
        patterns = page_range.split(",")
        for i in range(len(patterns)):
            patterns[i] = patterns[i].strip()
        for pattern in patterns:
            if EpubReadalongGenerator.range_pattern.match(pattern) is not None:
                range_terms = pattern.split("-")
                if len(range_terms) == 1:
                    range_terms.append(range_terms[0])  # range end = start
                range_terms[0], range_terms[1] = int(range_terms[0]), int(range_terms[1])
                # Make sure range is in ascending order
                if range_terms[0] > range_terms[1]:
                    range_terms[0], range_terms[1] = range_terms[1], range_terms[0]

                # Loop through and build ranges
                if len(self.page_range) == 0:
                    self.page_range.append(range_terms)
                else:
                    for i in range(len(self.page_range)):
                        if range_terms[1] < self.page_range[i][0]:  # Strictly less than
                            self.page_range.insert(i, range_terms)
                            break
                        # Overlapping, less than
                        elif range_terms[1] <= self.page_range[i][1]:
                            self.page_range[i][0] = min(range_terms[0], self.page_range[i][0])
                            break
                        # Overlapping, greater than
                        elif range_terms[1] > self.page_range[i][1] and range_terms[0] <= self.page_range[i][1]:
                            self.page_range[i][0] = min(range_terms[0], self.page_range[i][0])
                            self.page_range[i][1] = max(range_terms[1], self.page_range[i][1])
                            break
                        # Strictly greater than, append if at end of list
                        elif i == len(self.page_range) - 1:
                            self.page_range.append(range_terms)
                            break
            else:
                logging.warning(
                    f"set_page_range: Ignored invalid range '{pattern}'")
        
        logging.debug(self.page_range)
        logging.debug(self.page_range)
        return self

    # Extract page number from filestem. If no numbers in stem, return -1 (non-numbered page)
    def parse_page_number(self, filestem):
        start = end = -1
        for i in range(len(filestem)):
            if filestem[i].isdigit():
                if start == -1:
                    start = i
                end = i
            elif start != -1:
                break
        if start == -1:
            return -1
        
        return int(filestem[start:end + 1])
    
    def is_page_in_range(self, page_number):
        if len(self.page_range) == 0:
            return True
        in_range = False
        for r in self.page_range:
            if page_number >= r[0] and page_number <= r[1]:
                in_range = True
                break
        return in_range

    def build(self):
        logging.info(self.src_epub_filepath)
        with TemporaryDirectory() as tempdir:
            # Create temp working directory
            self.epub_workdir = os.path.join(tempdir, "epub")
            os.mkdir(self.epub_workdir)
            shutil.unpack_archive(self.src_epub_filepath,
                                  self.epub_workdir, "zip")
            logging.debug(f"Extracted epub to {self.epub_workdir}")

            self.add_audio_file()
            self.get_xhtml_stems()
            self.add_smil_files()
            self.edit_content_opf()
            self.process_text()
            self.add_css()
            return self.zip_epub()

    def add_audio_file(self):
        audio_workdir = os.path.join(self.epub_workdir, "OEBPS", "audio")
        logging.debug(audio_workdir)
        if not os.path.exists(audio_workdir):
            os.mkdir(audio_workdir)
            logging.debug(f"Created audio directory: {audio_workdir}")
        dest_audio_filepath = os.path.join(
            audio_workdir, self.get_audio_filename())
        shutil.copy(self.src_audio_filepath, dest_audio_filepath)
        logging.debug(
            f"Copied {self.src_audio_filepath} to {dest_audio_filepath}")

    def get_xhtml_stems(self) -> list[str]:
        text_workdir = os.path.join(self.epub_workdir, "OEBPS", "text")
        for root, _, files in os.walk(text_workdir):
            for f in files:
                filetype, _ = mimetypes.guess_type(f)
                if filetype == "application/xhtml+xml":
                    filestem = Path(f).stem
                    page_number = self.parse_page_number(filestem)
                    if page_number == -1 or self.is_page_in_range(page_number):
                        self.xhtml_stems.append(filestem)
        self.xhtml_stems = sorted(self.xhtml_stems)

    def add_smil_files(self):
        smil_workdir = os.path.join(self.epub_workdir, "OEBPS", "smil")
        if not os.path.exists(smil_workdir):
            os.mkdir(smil_workdir)
            logging.debug(f"Created smil directory: {smil_workdir}")
        for filestem in self.xhtml_stems:
            page_smil_filepath = self.get_smil_filepath(filestem)
            shutil.copy("resources/template.smil", page_smil_filepath)
            logging.debug(f"Created {page_smil_filepath}")

    def edit_content_opf(self):
        logging.debug("Editing content.opf")
        content_opf_filepath = os.path.join(
            self.epub_workdir, "OEBPS", "content.opf")
        content_opf_tree = etree.parse(content_opf_filepath)

        # Metadata - audio elements
        metadata_el = content_opf_tree.xpath(
            ".//*[local-name()='metadata']")[0]
        media_duration_el = etree.SubElement(metadata_el, "meta")
        media_duration_el.set("property", "media:duration")
        # Duration in seconds
        media_length = round(mutagen.File(self.src_audio_filepath).info.length)
        duration_hours = media_length // 3600
        duration_minutes = (media_length % 3600) // 60
        duration_seconds = media_length % 60
        media_duration_el.text = f"{duration_hours}:{duration_minutes}:{duration_seconds}"
        media_active_class_el = etree.SubElement(metadata_el, "meta")
        media_active_class_el.set("property", "media:active-class")
        media_active_class_el.text = "media-overlay-active"

        # Manifest - audio
        manifest_el = content_opf_tree.xpath(
            ".//*[local-name()='manifest']")[0]
        audio_item_el = etree.SubElement(manifest_el, "item")
        audio_item_el.set("id", "audio1")
        audio_filename = self.get_audio_filename()
        audio_item_el.set("href", "audio/" + audio_filename)
        filetype, _ = mimetypes.guess_type(audio_filename)
        audio_item_el.set("media-type", filetype)

        # Manifest - smil/xhtml
        # Loop through reversed list so that they are added in ascending order
        for filestem in reversed(self.xhtml_stems):
            smil_el = etree.Element("item")
            smil_el.set("media-type", "application/smil+xml")
            smil_el.set("id", "smil_" + filestem)
            smil_el.set("href", "smil/" + filestem + ".smil")
            manifest_el.insert(0, smil_el)
            xhtml_el = manifest_el.xpath(
                ".//*[local-name()='item' and @id='" + filestem + "']")[0]
            xhtml_el.set("media-overlay", "smil_" + filestem)

        content_opf_tree.write(content_opf_filepath, encoding="utf-8")

    def process_text(self):
        logging.debug("Process text")
        text_id = 1
        audio_timings = None
        with open(self.audio_timing_filepath) as timing_fp:
            audio_timings = timing_fp.readlines()

        # Loop through xhtml files and:
        # 1) Wrap individual words in spans
        # 2) Add corresponding audio timing par to smil
        for filestem in self.xhtml_stems:
            xhtml_filepath = self.get_xhtml_filepath(
                filestem)
            smil_filepath = self.get_smil_filepath(filestem)
            xhtml_xmltree = etree.parse(
                xhtml_filepath, XHTMLParser(resolve_entities=False))
            smil_xmltree = etree.parse(smil_filepath)
            text_nodes = xhtml_xmltree.xpath(
                "//*[local-name()='body']//text()")
            smil_body = smil_xmltree.xpath("//*[local-name()='body']")[0]
            audio_filename = self.get_audio_filename()
            logging.debug(text_nodes)

            for text in text_nodes:
                if not text.isspace():
                    edited_text = text
                    prev_sibling = None
                    if text.is_tail:
                        prev_sibling = text.getparent()
                        prev_sibling.tail = None    # Remove existing text so it can be wrapped

                    words = edited_text.split()
                    # Loop through words and create sibling spans beneath the parent
                    # Whitespace between words is attached as tail text
                    for word in words:
                        span_el = etree.Element("span")
                        span_el.set("id", "w" + str(text_id))
                        span_el.text = word
                        word_idx = edited_text.index(word)

                        # Add timing to smil
                        par_el = etree.SubElement(smil_body, "par")
                        par_el.set("id", "par" + str(text_id))
                        par_text_el = etree.SubElement(par_el, "text")
                        par_text_el.set(
                            "src", f"../text/{filestem}.xhtml#w{text_id}")
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
            xhtml_xmltree.write(
                xhtml_filepath, encoding="utf-8", standalone=True)
            smil_xmltree.write(smil_filepath, encoding="utf-8")

    def add_css(self):
        if len(self.css_filepath):
            with open(self.css_filepath) as new_css, \
                open(os.path.join(self.epub_workdir, "OEBPS", "styles", "style.css"), "a") as current_css:
                current_css.write("\n")
                for line in new_css.readlines():
                    current_css.write(line)

    def zip_epub(self):
        src_epub_folder, src_epub_filename = os.path.split(
            self.src_epub_filepath)
        readalong_epub_filename = Path(
            src_epub_filename).stem + "_readalong.epub"
        temp_epub_filepath = os.path.join(self.epub_workdir, "readalong.zip")
        shutil.make_archive(os.path.join(self.epub_workdir,
                            "readalong"), "zip", self.epub_workdir)
        readalong_epub_filepath = os.path.join(src_epub_folder, readalong_epub_filename)
        shutil.copyfile(temp_epub_filepath, readalong_epub_filepath)
        return readalong_epub_filepath

    def get_xhtml_filepath(self, filestem: str) -> str:
        return os.path.join(self.epub_workdir, "OEBPS", "text", filestem + ".xhtml")

    def get_smil_filepath(self, filestem: str) -> str:
        return os.path.join(self.epub_workdir, "OEBPS", "smil", filestem + ".smil")

    def get_audio_filename(self) -> str:
        _, audio_filename = os.path.split(self.src_audio_filepath)
        return audio_filename


if __name__ == "__main__":
    options_parser = argparse.ArgumentParser()
    options_parser.add_argument("epub_filepath")
    options_parser.add_argument(
        "-a", "--audio_file", type=str, required=True, help="Path to narration audio file")
    options_parser.add_argument(
        "-t", "--timing_file", type=str, required=True, help="Path to audio timing file")
    options_parser.add_argument(
        "-c", "--css_file", type=str, required=False, help="Path to CSS file")
    options_parser.add_argument(
        "-v", "--verbose", action=argparse.BooleanOptionalAction, required=False, help="Path to CSS file")
    options_parser.add_argument(
        "-r", "--range", type=str, required=False, help="Page range to process. Separate individual pages with commas, use dash to indicate ranges (ex. 1,2,5-8)")

    args = options_parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.WARN)
    EpubReadalongGenerator() \
        .set_epub_filepath(args.epub_filepath) \
        .set_audio_filepath(args.audio_file) \
        .set_audio_timing_filepath(args.timing_file) \
        .set_css_filepath(args.css_file) \
        .set_page_range(args.range) \
        .build()
