import os
import glob
import zipfile
import logging
import xml.etree.ElementTree as ET
import dita.config.config as config


class Docx:
    """
    Класс для работы с Word-документом (.docx).
    Загружает архив DOCX, извлекает XML-структуру документа, сноски, изображения и связи.
    """

    def __init__(self):
        # Логгер для вывода ошибок и отладки
        self.logger = logging.getLogger(__name__)
        try:
            # Находим путь к первому .docx файлу в текущей папке
            docx_path = self._locate_docx()
        except FileNotFoundError:
            self.logger.error("Could not find the .docx file")
            raise FileNotFoundError

        # Открываем DOCX как zip-архив
        self.archive: zipfile.ZipFile = zipfile.ZipFile(docx_path)

        # Читаем содержимое нужных XML-файлов из архива
        document_xml: bytes = self.archive.read('word/document.xml')     # основной текст
        footnotes_xml: bytes = self.archive.read('word/footnotes.xml')   # сноски
        self.rels_xml: bytes = self.archive.read('word/_rels/document.xml.rels')  # связи (картинки, объекты)

        # Список всех файлов в архиве (для поиска медиа) внутри docx
        self.files: list[zipfile.ZipInfo] = self.archive.infolist()

        # Словарь для хранения соответствий ID → путь к файлу (media/image5.png)
        self.id_to_path: dict[str, str] = {}

        # Обрабатываем связи (rels), чтобы заполнить словарь id_to_path
        self._process_rels()

        # Словарь пространств имён XML, используется при поиске элементов через XPath
        self.ns: dict[str, str] = {
            'w': "http://schemas.openxmlformats.org/wordprocessingml/2006/main",      # основной текст Word
            'a': "http://schemas.openxmlformats.org/drawingml/2006/main",             # объекты DrawingML
            'pic': "http://schemas.openxmlformats.org/drawingml/2006/picture",        # изображения
            'r': "http://schemas.openxmlformats.org/officeDocument/2006/relationships" # связи
        }

        # XML-дерево основного документа Word
        self.document: ET.Element = ET.fromstring(document_xml)
        
        # Словарь сносок: footnote_id → XML-элемент сноски
        self.footnotes: dict[str, ET.Element] = {}
        self._process_footnotes(footnotes_xml)
        
        # Сохраняем все изображения из архива в локальную папку проекта
        self._save_images()

    def _locate_docx(self) -> str:
        """
        Ищет первый .docx файл в текущей директории.
        
        Возвращает:
            str: путь к файлу .docx
        """
        try:
            docx_path: str = glob.glob('./*.docx')[0]  # берём первый попавшийся .docx
        except IndexError:
            raise FileNotFoundError
        return docx_path

    def _save_images(self):
        """
        Извлекает изображения из DOCX и сохраняет их в папку:
        {output_dir}/{document_type}/images
        """
        for arc_file in self.files:
            # Ищем файлы, в имени которых есть "word/media/image"
            if 'word/media/image' in arc_file.filename:
                file_name: str = arc_file.filename.replace("word/media/", "")
                
                # Директория для сохранения
                output_dir: str = f"{config.output_dir}/{config.document_type}/images"
                os.makedirs(output_dir, exist_ok=True)
                
                # Записываем картинку на диск
                with open(f"{output_dir}/{file_name}", "wb") as img_file:
                    img_file.write(self.archive.read(arc_file.filename))

    def _process_rels(self):
        """
        Парсит файл связей document.xml.rels и формирует словарь:
        rId → путь к файлу.
        """
        root = ET.fromstring(self.rels_xml)

        for rel in root.iter("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}Relationship"):
            rel_id: str = rel.attrib['Id']      # уникальный ID связи, например "rId23"
            target_path: str = rel.attrib['Target']  # путь к файлу внутри docx
            rel_type: str = rel.attrib['Type']  # тип связи (например, image, hyperlink и т.д.)
            
            # Если это изображение → добавляем в словарь
            if "image" in rel_type:
                self.id_to_path[rel_id] = target_path

    def _process_footnotes(self, footnotes_xml: bytes):
        """
        Парсит файл footnotes.xml, добавляет сноски в self.footnotes.
        
        Формат:
            self.footnotes = {
                "1": <fn>...</fn>,
                "2": <fn>...</fn>
            }
        """
        root = ET.fromstring(footnotes_xml)

        for footnote in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}footnote'):
            fn_el = ET.Element('fn')  # создаём свой элемент <fn> для хранения

            # ID сноски (обычно число в строке)
            footnote_id: str = footnote.attrib['{http://schemas.openxmlformats.org/wordprocessingml/2006/main}id']

            # Каждая сноска может содержать несколько абзацев
            for p in footnote.findall('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
                p_el = ET.Element('p')  # абзац внутри сноски
                footnote_text: str = ""

                for t_el in p.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
                    footnote_text = f"""{footnote_text}{t_el.text}"""
                
                p_el.text = footnote_text
                fn_el.append(p_el)

            # Сохраняем в словарь
            self.footnotes[footnote_id] = fn_el