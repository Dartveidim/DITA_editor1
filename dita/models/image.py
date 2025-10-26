# -*- coding: utf-8 -*-
"""
dita.utils.id_generators
Простой централизованный генератор ID для проекта.

Экспортирует:
    gen_id(base_text: str, prefix: str | None = None) -> str
    gen_img_id(title: str) -> str
    gen_tab_id(title: str) -> str

Поведение:
- Преобразует входной текст через get_proper_id (т.е. транслит/очистка).
- Добавляет префикс (если задан).
- Поддерживает уникальность в рамках текущего запуска (в памяти).
- (Опционально) есть точка, где можно добавить сохранение/загрузку множества used_ids в файл,
  если нужен постоянный счётчик между запусками.
"""

import xml.etree.ElementTree as ET
import dita.config.config as config
import os
import imghdr
import struct
from dita.utils.translit import get_proper_id
import logging
import shutil
import re
from abc import ABC, abstractmethod
from dita.utils.id_generators import gen_img_id

logger = logging.getLogger(__name__)


class ImageTopic(ABC):
    """
    Абстрактный базовый класс, представляющий DITA topic со списком изображений/фигур.

    Параметр конструктора:
        props (dict) — словарь с обязательными ключами:
            'title' : заголовок топика,
            'id'    : id топика (уникальный),
            'file'  : имя файла, в который будет записан topic (например 'project-img_list.dita').

    Внутренние атрибуты:
        self.props: dict — переданные свойства.
        self.ids: list[str] — список уже добавленных ID изображений (для проверки дубликатов).
        self.topic: ET.Element — корневой XML элемент topic.
        self.body: ET.Element — элемент body внутри topic.
        self.logger: logging.Logger — локальный логгер.
    """
    def __init__(self, props: dict):
        self.props = props
        self.ids: list[str] = []  # Список уже используемых id изображений в этом топике
        self.topic = ET.Element("topic")
        self.topic.set("id", f'{self.props["id"]}')
        self.topic.set("xml:lang", "ru")

        # Заголовок топика
        title_el = ET.SubElement(self.topic, "title")
        title_el.text = self.props["title"]

        # Блок с содержимым (куда будут добавляться fig / image)
        self.body: ET.Element = ET.SubElement(self.topic, "body")
        # Локальный логгер
        self.logger = logging.getLogger(__name__)

    def _get_image_size(self, fname: str):
        """
        Вспомогательная функция, которая пытается получить размеры изображения.
        Поддерживает PNG, GIF, JPEG.
        Возвращает: (width, height) или None при ошибке / неизвестном формате.
        """
        with open(fname, 'rb') as fhandle:
            head = fhandle.read(24)
            if len(head) != 24:
                return
            if imghdr.what(fname) == 'png':
                # PNG: байты 16:24 содержат width,height
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
        """
        Сохраняет self.topic в файл в папке {output_dir}/{document_type}/sp
        Также копирует placeholder null.png в images как _null.png (если нужно).
        """
        output_dir = f"{config.output_dir}/{config.document_type}/sp"
        out_file = f'{self.props["file"]}'

        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception:
            pass

        header = b"""<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE topic PUBLIC "-//OASIS//DTD DITA Topic//EN" "topic.dtd">\n"""
        ET.indent(self.topic)
        topic_bytes = ET.tostring(self.topic, encoding='utf-8')

        with open(f"{output_dir}/{out_file}", "wb") as f:
            f.write(header)
            f.write(topic_bytes)

        # Копируем placeholder-изображение (null.png) в папку images
        try:
            os.makedirs(f"{config.output_dir}/{config.document_type}/images")
        except FileExistsError:
            pass
        shutil.copy("null.png", f"{config.output_dir}/{config.document_type}/images/_null.png")

        @abstractmethod
        def add_image():
            """Абстрактный метод. Реализуется в наследниках."""
            pass

class ImageKeyTopic(ImageTopic):
    """
    Справочник рисунков (fig -> image). Каждый рисунок хранится как <fig id="..."><title>...</title><image href="..."/></fig>

    Использование:
        key_topic = ImageKeyTopic()
        key_topic.add_image("Заголовок рисунка", "../images/image1.png")
        key_topic.save()
    """
    def __init__(self):
        # props — свойства топика: title, id топика и имя файла
        self.props = {
            "title": "Справочник рисунков",
            "id": f"{config.document_type}-IMG_LIST",
            "file": f"{config.document_type.lower()}-img_list.dita"
        }
        super().__init__(self.props)

    def add_image(self, image_title: str, href: str):
        """
        Добавляет новую запись рисунка в справочник.

        Параметры:
            image_title: str — подпись/название рисунка (будет в <title>)
            href: str — относительный путь к файлу изображения (например "../images/image1.png")
        """
        # Генерация уникального image_id: предпочтительно используем gen_img_id (центральный генератор)
        image_id = gen_img_id(image_title) # см. dita.utils.id_generators
        # Регистрируем id (чтобы избежать дубликатов)
        self.ids.append(image_id) # см. dita.utils.id_generators

        # Создаём элемент <fig id="...">
        fig = ET.SubElement(self.body, 'fig')
        fig.set("id", image_id)

        # Заголовок рисунка внутри <fig>
        title_el = ET.SubElement(fig, "title")
        title_el.text = image_title

        # Сам элемент изображения
        image_el = ET.SubElement(fig, 'image')
        image_el.set('href', href)

        # Попытаться получить ширину изображения и записать её (ограничение 640)
        try:
            w, h = self._get_image_size(f"{config.output_dir}/{config.document_type}/images/{href.split('/')[-1]}")
            if w > 640:
                w = 640
            image.set('width', str(w))
        except Exception as e:
            pass

    def validate_id(self, candidate_id: str) -> str:
        """
        Дополнительная проверка unique id локально для этого топика.
        (Обычно не нужна, если используется gen_img_id, но оставлена для совместимости.)
        """
        while candidate_id in self.ids:
            self.logger.debug(f"An image with the id {candidate_id} already exists. Appending '_N'...")
            m = re.search(r'_(\d+)$', id)
            if m is not None:
                inc = int(m.group(1))
                full_inc = m.group(0)
                inc = inc +1
                id_base = candidate_id.rstrip(full_inc)
                candidate_id = f'{id_base}_{inc}'
            else:
                candidate_id = f"{candidate_id}_1"
        return candidate_id


class IconKeyTopic(ImageTopic):
    """
    Справочник иконок — маленьких изображений (например, 16x16/32x32).
    Иконки добавляются в блок <bodydiv> как <p><image .../></p>, только если их реальные размеры меньше порога.
    """
    def __init__(self):
        # props для справочника иконок
        self.props = {
            "title": 'Справочник иконок',
            'id': f'{config.document_type}-ICON_LIST',
            "file": f"{config.document_type.lower()}-icon_list.dita"
        }
        # Передаём self.props в базовый конструктор
        super().__init__(props)
        # Для иконок используем дополнительный контейнер bodydiv
        self.bodydiv = ET.SubElement(self.body, 'bodydiv')

    def add_image(self, image_rel_id: str, href: str):
        """
        Добавляет иконку в справочник, если её реальные размеры меньше порога (100x100).

        Параметры:
            image_rel_id: str — идентификатор (обычно rId или сгенерированный id)
            href: str — относительный путь к файлу изображения (../images/...)
        """
        # Если уже есть такой id — не добавляем дубликат
        if image_rel_id in self.ids:
            return

        try:
            w, h = self._get_image_size(f'{config.output_dir}/{config.document_type}/images/{href.split("/")[-1]}')
            # Добавляем иконку только если обе стороны меньше 100 px
            if w < 100 and h < 100:
                para = ET.SubElement(self.bodydiv, 'p')
                image = ET.SubElement(para, 'image')
                image.set("id", image_rel_id)
                image.set("href", href)
                image.set("width", "32")
                image.set("height", "32")
                self.ids.append(image_rel_id)
        except Exception:
            return