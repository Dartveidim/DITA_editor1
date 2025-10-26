# -*- coding: utf-8 -*-
"""
Модуль toc.py
-------------
Отвечает за создание структуры документа (оглавления) и CSV-файла,
который связывает номера разделов, их уровни и транслитерированные идентификаторы.

Функции:
    write_csv(csv_file, section_number, section_title)
        — записывает строку в CSV-файл с номерами разделов, уровнями и ID.
    toc()
        — создаёт текстовую структуру документа (doc_structure.txt)
          и CSV-файл (Трансформация_названий_разделов.csv) на основе word.txt.
"""

import re
from dita.utils.translit import get_proper_id
import dita.config.config as config
import os

def write_csv(csv_file, section_number: str, section_title: str):
    """
    Записывает строку в CSV-файл с информацией о разделе.

    Аргументы:
        csv_file (TextIO): открытый CSV-файл для записи.
        section_number (str): номер раздела (например "1.2.3").
        section_title (str): заголовок раздела (текст строки).
    """
    # Генерация уникального идентификатора из заголовка (в латинице)
    topic_id = get_proper_id(section_title)

    # Определяем уровень вложенности по количеству точек в номере (1.2.3 -> 2)
    indent = section_number.count('.')
    # Формируем словарь для 7 уровней (r0–r6)
    indents = {f'r{i}': '' for i in range(7)}
    indents[f'r{indent}'] = section_number
    # Записываем строку в CSV, разделяя уровни точкой с запятой
    csv.write(f"""{indents['r0']};{indents['r1']};{indents['r2']};{indents['r3']};{indents['r4']};{indents['r5']};{indents['r6']};{title};{topic_id}\n""")

def toc():
    """
    Основная функция.
    Создаёт:
        - doc_structure.txt — текстовую структуру документа с отступами;
        - Трансформация_названий_разделов.csv — таблицу соответствий разделов и их ID.

    Алгоритм:
        1. Создаёт выходную папку (если не существует).
        2. Открывает файл word.txt (исходный список разделов с нумерацией).
        3. Для каждой строки:
            - определяет уровень по нумерации (1., 1.1., 1.1.1 и т.п.);
            - добавляет соответствующий отступ (4 пробела на уровень);
            - записывает в doc_structure.txt;
            - записывает в CSV с ID и номером.
    """
    # Гарантируем наличие выходной директории
    os.makedirs(config.output_dir, exist_ok=True)

    # Файлы для записи результатов
    csv_file = open(f"{config.output_dir}/Трансформация_названий_разделов.csv", "w")
    structure_file = open('doc_structure.txt', 'w', encoding='utf-8')
    
    # Читаем исходный файл word.txt (список разделов Word)
    with open('word.txt', "r", encoding='utf-8') as f:
        for line in f.readlines():
            # Проверяем, начинается ли строка с номера раздела (например "1.2.3 ")    
            match = re.search(r"^[A-Я]?[\d\.]+\s", line)
            if match is not None:
                # Считаем уровень (по количеству точек в номере)
                level_indent = m[0].count('.')
                # Заменяем нумерацию на соответствующий отступ (4 пробела на уровень)
                indented_line = re.sub(r"^[A-Я]?[\d\.]+\s", "    " * level_indent, line)
                # Записываем в структуру и CSV
                structure_file.write(indented_line)
                write_csv(csv_file, match[0].strip(), indented_line.strip())
            else:
                # Строка без нумерации (например, просто текст)
                structure_file.write(line)
                write_csv(csv_file, "", line.strip())

    # Закрываем оба выходных файла
    structure_file.close()
    csv_file.close()