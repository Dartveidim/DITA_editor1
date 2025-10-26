# -*- coding: utf-8 -*-
"""
Модуль с функциями генерации уникальных идентификаторов для различных типов элементов DITA.
Все функции используют общую базу — get_proper_id из dita.utils.translit.
"""

from dita.utils.translit import get_proper_id
from dita.core.topic import validate_id
import dita.config.config as config
import os


def gen_id(title: str) -> str:
    """
    Базовая функция генерации ID для топиков (topic).
    """
    base_id = get_proper_id(title)
    output_dir = f"{config.output_dir}/{config.document_type}/topic"
    return validate_id(output_dir, base_id)


def gen_tab_id(title: str) -> str:
    """
    Генерация ID для таблиц (table_...).
    """
    base_id = get_proper_id(title)
    output_dir = f"{config.output_dir}/{config.document_type}/table"
    unique_id = validate_id(output_dir, base_id)
    return f"table_{unique_id}"


def gen_img_id(title: str) -> str:
    """
    Генерация ID для изображений (img_...).
    """
    base_id = get_proper_id(title)
    output_dir = f"{config.output_dir}/{config.document_type}/sp"
    unique_id = validate_id(output_dir, base_id)
    return f"img_{unique_id}"
