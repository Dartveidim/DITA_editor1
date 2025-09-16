import os
import glob
import zipfile
import logging
import xml.etree.ElementTree as ET
import config


class Docx:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        try:
            docx_file = self.locate_docx()
        except FileNotFoundError:
            self.logger.error("Could not find the .docx file")
            raise FileNotFoundError

        self.f = zipfile.ZipFile(docx_file)
        doc = self.f.read('word/document.xml')
        footnotes = self.f.read('word/footnotes.xml')
        self.rels = self.f.read('word/_rels/document.xml.rels')
        self.files = self.ZipFile.infolist(self.f)

        self.id_to_path = dict()

        self.process_rels()

        self.ns = {
            'w': "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
            'a': "http://schemas.openxmlformats.org/drawingml/2006/main",
            'pic': "http://schemas.openxmlformats.org/drawingml/2006/picture",
            'r': "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
        }

        self.document = ET.fromstring(doc)
        self.footnotes = {}
        self.process_footnotes(footnotes)
        self.save_images()

    def locate_docx(self):
        try:
            file = glob.glob('./*.docx')[0]
        except IndexError:
            raise FileNotFoundError
        return file

    def save_images(self):
        for file in self.files:
            if 'word/media/image' in file.filename:
                file_name = file.filename.replace("word/media/", "")
                dir = f"{config.output_dir}/{config.document_type}/images"
                try:
                    os.makedirs(dir)
                except FileExistsError:
                    pass
                with open(f"{dir}/{file_name}", "wb") as img_file:
                    img_file.write(self.f.read(file.filename))

    def process_rels(self):
        root = ET.fromstring(self.rels)
        for rel in root.iter("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}Relationships"):
            id = rel.attrib['Id']
            image_path = rel.attrib['Target']
            type = rel.attrib['Type']
            if "image" in type:
                self.id_to_path[id] = image_path

    def process_footnotes(self, footnotes):
        root = ET.fromstring(footnotes)
        for footnote in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}footnote'):
            fn_el = ET.Element('fn')
            footnote_id = footnote.attrib['{http://schemas.openxmlformats.org/wordprocessingml/2006/main}id']
           
            for p in footnote.findall('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
                p_el = ET.Element('p')
                footnote_p = ""
                for t_el in p.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
                    footnote_p = f"""{footnote_p}{t_el.text}"""
                p_el.text = footnote_p
                fn_el.append(p_el)
            self.footnotes[footnote_id] = fn_el