import xml.etree.ElementTree as ET
import config
import os
import imghdr
import struct
from translit import get_proper_id
import logging
import shutil
import re
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ImageTopic(ABC):
    def __init__(self, vars):
        self.vars = vars
        self.ids = []
        self.topic = ET.Element("topic")
        self.topic.set("id", f'{self.vars["id"]}')
        self.topic.set("xml:lang", "ru")

        title = ET.SubElement(self.topic, "title")
        title.text = self.vars["title"]

        self.body = ET.SubElement(self.topic, "body")
        self.logger = logging.getLogger(__name__)

    def _get_image_size(self, fname):
        with open(fname, 'rb') as fhandle:
            head = fhandle.read(24)
            if len(head) != 24:
                return
            if imghdr.what(fname) == 'png':
                check = struct.unpack('>i', head[4:8])[0]
                if check != 0x0d0a1a0a:
                    return
                width, height = struct.unpack('>ii', head[16:24])
            elif imghdr.what(fname) == 'gif':
                width, height = struct.unpack('<HH', head[6:10])
            elif imghdr.what(fname) == 'jpeg':
                try:
                    fhandle.seek(0)
                    size = 2
                    ftype = 0
                    while True:
                        fhandle.seek(size, 1)
                        byte = fhandle.read(1)
                        while byte == b'\xFF':
                            byte = fhandle.read(1)
                        ftype = ord(byte)
                        if 0xC0 <= ftype <= 0xCF:
                            break
                        size = struct.unpack('>H', fhandle.read(2))[0] - 2
                    fhandle.read(3)
                    height, width = struct.unpack('>HH', fhandle.read(4))
                except Exception:
                    return
            else:
                return
            return width, height

    def save(self):
        dir = f"{config.output_dir}/{config.document_type}/sp"
        file = f'{self.vars["file"]}'

        try:
            os.makedirs(dir)
        except FileExistsError:
            pass

        header = b"""<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE topic PUBLIC "-//OASIS//DTD DITA Topic//EN" "topic.dtd">\n"""
        ET.indent(self.topic)
        topic_txt = ET.tostring(self.topic, encoding='utf-8')

        with open(f"{dir}/{file}", "wb") as f:
            f.write(header)
            f.write(topic_txt)

        try:
            os.makedirs(f"{config.output_dir}/{config.document_type}/images")
        except FileExistsError:
            pass
        shutil.copy("null.png", f"{config.output_dir}/{config.document_type}/images/_null.png")

        @abstractmethod
        def add_image():
            pass

class ImageKeyTopic(ImageTopic):
    def __init__(self):
        self.vars = {
            "title": "Справочник рисунков",
            "id": f"{config.document_type}-IMG_LIST",
            "file": f"{config.document_type.lower()}-img_list.dita"
        }
        super().__init__(self.vars)

    def add_image(self, image_title, href):
        id = get_proper_id(image_title)
        id = self.validate_id(id)
        self.ids.append(id)

        fig = ET.SubElement(self.body, 'fig')
        fig.set("id", id)

        title = ET.SubElement(fig, "title")
        title.text = image_title

        image = ET.SubElement(fig, 'image')
        image.set('href', href)

        try:
            w, h = self._get_image_size(f"{config.output_dir}/{config.document_type}/images/{href.split('/')[-1]}")
            if w > 640:
                w = 640
            image.set('width', str(w))
        except Exception as e:
            pass

    def validate_id(self, id):
        while id in self.ids:
            self.logger.debug(f"An image with the id {id} already exists. Appending '_N'...")
            m = re.search(r'_(\d+)$', id)
            if m is not None:
                inc = int(m.group(1))
                full_inc = m.group(0)
                inc = inc +1
                id_base = id.rstrip(full_inc)
                id = f'{id_base}_{inc}'
            else:
                id = f"{id}_1"
        return id


class IconKeyTopic(ImageTopic):
    def __init__(self):
        self.vars = {
            "title": 'Справочник иконок',
            'id': f'{config.document_type}-ICON_LIST',
            "file": f"{config.document_type.lower()}-icon_list.dita"
        }
        super().__init__(vars)
        self.bodydiv = ET.SubElement(self.body, 'bodydiv')

    def add_image(self, id, href):
        if id in self.ids:
            return

        try:
            w, h = self._get_image_size(f'{config.output_dir}/{config.document_type}/images/{href.split("/")[-1]}')
            if w < 100 and h < 100:
                para = ET.SubElement(self.bodydiv, 'p')
                image = ET.SubElement(para, 'image')
                image.set("id", id)
                image.set("href", href)
                image.set("width", "32")
                image.set("height", "32")
                self.ids.append(id)
        except Exception:
            return