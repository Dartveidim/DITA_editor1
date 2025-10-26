# -*- coding: utf-8 -*-
"""
Модуль table.py
---------------
Содержит классы для работы с таблицами в DITA:
    • Table — модель таблицы с методами добавления строк, ячеек, заголовков и объединений.
    • TableKeyReference — генератор карты ключей (keydef) для всех таблиц документа.

Основные изменения:
    - Переименованы неоднозначные переменные (colnum → col_count, dir → output_dir и т.д.)
    - Добавлены подробные комментарии к каждому методу.
    - Добавлены docstring-и и пояснения логики объединения ячеек.
"""

import xml.etree.ElementTree as ET
from dita.utils.translit import get_proper_id
import dita.config.config as config
import os

class Table:
    """
    Класс для представления таблицы DITA (<table>).
    Позволяет создавать структуру таблицы, добавлять строки и объединять ячейки.
    """
    def __init__(self, title="Тестовая таблица"):
        self.previous_row = None
        # Корневой элемент таблицы <table>
        self.table = ET.Element("table")

        # Элемент заголовка таблицы <title>
        self.title = ET.SubElement(self.table, "title")
        self.title.text = title

        # Элемент <tgroup> — контейнер для колонок и тела таблицы
        self.tgroup = ET.SubElement(self.table, "tgroup")
        
        # Количество колонок (устанавливается позже)
        self.colnum = None

        # Элемент <tbody> — тело таблицы (все строки)
        self.tbody = ET.SubElement(self.tgroup, "tbody")

        # Последняя строка, добавленная в таблицу (для объединения)
        self.previous_row = None

    def add_entries(self, entries: list[ET.Element]):
        """
        Обновляет последнюю строку таблицы, вставляя готовые элементы <entry> в ячейки.

        Аргументы:
            entries (list[ET.Element]): список элементов <entry> для текущей строки.
        """
        last_row = self.tbody.findall("row")[-1]  # последняя добавленная строка
        for idx, new_entry in enumerate(entries):
            if new_entry is not None:
                # Находим старую ячейку, сохраняем её атрибуты (например colspan)
                old_entry = last_row.findall("entry")[idx]
                entry_attrs = old_entry.attrib
                last_row.remove(old_entry)

                # Переносим атрибуты в новый элемент
                new_entry.attrib = entry_attrs
                last_row.insert(idx, new_entry)

    def set_title(self, title_text: str):
        """Задаёт заголовок таблицы."""
        self.title.text = title_text

    def set_id(self, table_id: str):
        """Назначает идентификатор таблицы (<table id="...">)."""
        self.table.set("id", table_id)

    def set_colnum(self, col_number: int):
        """
        Устанавливает количество колонок таблицы и создаёт соответствующие <colspec>.

        Аргументы:
            col_number (int): число колонок в таблице.
        """
        self.col_count = col_number
        self.tgroup.set("cols", str(col_number))

        # Для каждой колонки создаём <colspec>        
        for i in range(self.col_count):
            colspec = ET.Element("colspec")
            colspec.set("colnum", str(i + 1))
            colspec.set("colwidth", "1*")  # пропорциональная ширина
            colspec.set("colname", f"col{i + 1}")
            self.tgroup.insert(i, colspec)

    def add_row(self, row_cells: list[str]):
        """
        Добавляет строку <row> в таблицу.

        Аргументы:
            row_cells (list[str]): список значений для ячеек.  
                                   Возможные значения:
                                     '' — обычная пустая ячейка;
                                     'vmerged' — ячейка объединена по вертикали;
                                     число — ширина горизонтального объединения.
        """
        row = ET.SubElement(self.tbody, "row")
        for idx, cell_value in enumerate(row_cells):
            if cell_value == "vmerged":
                # Добавляем объединённую по вертикали ячейку
                self._mark_first_merged_cell(idx)
                cell_el = ET.SubElement(row, "entry")
                cell_el.set("vmerged", "")
            elif cell_value != "":
                # Горизонтальное объединение (span)
                span_value = cell_value
                cell_el = ET.SubElement(row, "entry")
                cell_el.set("namest", f"col{idx + 1}")
                cell_el.set("nameend", f"col{idx + int(span_value)}")
            else:
                # Пустая ячейка
                ET.SubElement(row, "entry")

    def _mark_first_merged_cell(self, col_index: int):
        """
        Ищет первую ячейку выше по колонке и отмечает её как начало объединения (morerows=N).

        Аргументы:
            col_index (int): индекс колонки (начиная с 0), в которой идёт объединение.
        """
        # Берём все строки, кроме текущей (последней)
        previous_rows = self.tbody.findall("row")[:-1 or None]

        # Идём снизу вверх, чтобы найти первую подходящую ячейку
        for prev_row in reversed(previous_rows):
            cells = prev_row.findall("entry")
            target_cell = cells[col_index]

            # Если ячейка уже объединена — продолжаем поиск выше
            if "vmerged" in target_cell.attrib:
                continue
            else:
                # Если ячейка уже имеет morerows — увеличиваем значение
                if "morerows" in target_cell.attrib:
                    merged_count = target_cell.attrib["morerows"]
                    target_cell.set("morerows", str(int(merged_count) + 1))
                else:
                    # Первое объединение — ставим morerows="1"
                    target_cell.set("morerows", "1")
                break

    def __str__(self):
        """
        Возвращает красиво отформатированное XML-представление таблицы.
        """
        ET.indent(self.table)
        self.clear()  # очищаем виртуальные ячейки перед выводом
        return ET.tostring(self.table, encoding="utf-8").decode("utf-8")


    def clear(self):
        """
        Удаляет все "виртуальные" ячейки <entry vmerged=""/> из таблицы.
        Используется перед экспортом, чтобы избежать дублирования.
        """
        for parent_row in self.table.findall(".//row"):
            for merged_entry in parent_row.findall(".//entry"):
                if "vmerged" in merged_entry.attrib:
                    parent_row.remove(merged_entry)

class TableKeyReference:
    """
    Создаёт DITA карту (map) с ключами для таблиц.
    Пример выходного файла:
        <map id="PROJECT-KEYLIST-TABLES">
          <title>Список ключей таблиц</title>
          <topicgroup>
            <!-- Таблица 1 -->
            <keydef keys="table_abc" href="table/table_abc.dita"/>
          </topicgroup>
        </map>
    """
    def __init__(self):
        # Корневой элемент карты <map>
        self.map = ET.Element("map")
        self.map.set("id", f"{config.document_type}-KEYLIST-TABLES")
        self.map.set("xml:lang", "ru")
        
        # Заголовок карты
        title_el = ET.SubElement(self.map, "title")
        title_el.text = "Список ключей таблиц"

        # Контейнер для всех ключей таблиц
        self.topic_group = ET.SubElement(self.map, "topicgroup")


    def add_keydef(self, table_title: str, table_id: str):
        """
        Добавляет новую запись <keydef> в карту таблиц.

        Аргументы:
            table_title (str): заголовок таблицы (используется как комментарий)
            table_id (str): уникальный идентификатор таблицы
        """
        # Комментарий с названием таблицы для читаемости XML
        comment = ET.Comment(f"{table_title}")
        self.topic_group.append(comment)

        # Определение ключа <keydef>
        keydef = ET.SubElement(self.topic_group, "keydef")
        keydef.set("keys", table_id)
        keydef.set("href", f"table/{table_id}.dita") # путь к DITA-файлу

    def save(self):
        """
        Сохраняет карту таблиц (map) в файл:
        {output_dir}/{document_type}/{document_type}-KeyList-Tables.ditamap
        """
        output_dir = f"{config.output_dir}/{config.document_type}"
        output_file = f"{config.document_type}-KeyList-Tables.ditamap"

        # Создаём выходную папку при необходимости
        os.makedirs(output_dir, exist_ok=True)

        # Заголовок XML (DTD)
        header = b"""<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE bookmap PUBLIC "-//OASIS//DTD DITA BookMap//EN" "bookmap.dtd">\n"""
        
        # Форматируем и сериализуем XML
        ET.indent(self.map)
        map_bytes = ET.tostring(self.map, encoding="utf-8")

        # Записываем на диск
        with open(f"{output_dir}/{output_file}", "wb") as f:
            f.write(header)
            f.write(map_bytes)