# -*- coding: utf-8 -*-
"""
Модуль topic.py
---------------

Утилиты для создания и сохранения DITA-топиков.

Сохранена исходная структура функций и логика, изменены только имена переменных
на более явные и добавлены подробные комментарии.

Функции:
    - save_topic(output_dir, topic_id, topic_txt)
    - validate_id(output_dir, candidate_id)
    - create_topic(title)
"""

import os
import re
import logging

import dita.config.config as config
from dita.utils.translit import get_proper_id
from dita.utils.id_generators import gen_id

logger = logging.getLogger(__name__)

def save_topic(output_dir: str, topic_id: str, topic_txt: str) -> None:
    """
    Сохраняет топик в файл <output_dir>/<topic_id>.dita.

    Структура блока такая же, как и в исходном коде: попытка открыть файл в режиме 'x'
    (создать новый), при исключении — печать ошибки, иначе — запись и закрытие файла.

    Аргументы:
        output_dir (str): директория для сохранения (будет использована как есть).
        topic_id (str): идентификатор топика (используется как имя файла без расширения).
        topic_txt (str): контент DITA-топика (строка с XML).
    """
    try:
        # Формируем путь и пытаемся создать новый файл
        path = f"{output_dir}/{topic_id}.dita" # абсолютный путь к файлу топика
        # Пытаемся создать новый файл (режим 'x' — ошибка, если уже существует)
        f = open(path, "x", encoding='utf-8')
    except Exception as e:
        # Если ошибка (например, файл существует или нет прав) — выводим исключение
        print(e)
    else:
        # Записываем текст топика и закрываем файл
        f.write(topic_txt) # записываем XML контент в файл
        f.close() # закрываем файловый объект

def validate_id(output_dir: str, unique_id: str) -> str:
    """
    Проверяет уникальность идентификатора в указанной директории.
    Если файл с таким именем уже существует — добавляет или увеличивает числовой суффикс (_1, _2, ...).

    Аргументы:
        output_dir (str): путь до папки, где будут храниться DITA-топики.
        candidate_id (str): исходное имя идентификатора (например, 'intro' или 'chapter1').

    Возвращает:
        str: уникальный идентификатор (возможно с добавленным суффиксом).
    """
    
    try:
        # Пытаемся создать папку для хранения топиков, если её нет
        os.makedirs(output_dir) # создаёт папку, если не существует
    except FileExistsError:
        # Если уже существует — ничего страшного
        pass

    while os.path.exists(f"{output_dir}/{unique_id}.dita"):
        logger.debug(f"Файл с именем {unique_id} уже существует. Appending '_N'...")
        # m — результат поиска числового суффикса _N в конце имени
        m = re.search(r'\_(\d+)$', unique_id)
        if m is not None:
            inc = int(m.group(1)) # число в конце id (например 2 из '_2')
            full_inc = m.group(0) # строка суффикса (например "_2")
            inc = inc + 1 # увеличиваем номер
            id_base = unique_id.rstrip(full_inc) # базовая часть id без суффикса
            unique_id = f"{id_base}_{inc}" # формируем новый id, например "chapter_3"
        else:
            unique_id = f"{unique_id}_1" # если суффикса нет, добавляем "_1"
    return unique_id # возвращаем уникальный идентификатор

def create_topic(title: str):
    topic_id = gen_id(title) # см. dita.utils.id_generators

    # Формируем путь до директории, где хранятся топики
    output_dir = f"{config.output_dir}/{config.document_type}/topic"  # абсолютный путь к папке topic

    # Формируем XML-содержимое топика в формате DITA
    topic_txt = F"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE concept PUBLIC "-//OASIS//DTD DITA Concept//EN" "concept.dtd">
<concept id="{topic_id}" xml:lang="ru">
  <title>{title}</title>
  <conbody>
    <p></p>
  </conbody>
</concept>""" # XML шаблон DITA-концепта

    # Сохраняем топик на диск
    save_topic(output_dir, topic_id, topic_txt) # вызов функции сохранения файла

    # Возвращаем итоговый идентификатор
    return topic_id