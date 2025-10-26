# -*- coding: utf-8 -*-
# Файл отвечает за создание и сохранение DITA-карт (map) и BookMap для документации
import xml.etree.ElementTree as ET
import dita.config.config as config
import os

# Глобальный элемент bookmap, который будет хранить структуру всей книги
bookmap = ET.Element('bookmap') # корневой элемент BookMap (главный контейнер всей книги)
booktitle = ET.SubElement(bookmap, 'booktitle') # элемент заголовка книги
mainbooktitle = ET.SubElement(booktitle, 'mainbooktitle') # основной заголовок книги

def save_map(map_root):
    """
    Сохраняет отдельную карту (map) документа в формате DITA.
    Также добавляет ссылку на карту в глобальный bookmap.
    
    Параметры:
        map_root (xml.etree.ElementTree.Element): корневой элемент карты (map)
    """
    global bookmap # используем глобальный bookmap для добавления ссылок на новые карты
    try:
        # Извлечение идентификатора и заголовка навигации из первого topicref
        map_id = map_root.find('topicref').attrib['keys'] # ищет первый элемент <topicref> внутри карты (map_id — уникальный ключ карты, нужен для идентификации и сохранения файла)
        map_navtitle  = map_root.find('topicref').attrib['navtitle'] # заголовок для навигации (будет отображаться в BookMap)
        map_root.set('id', map_id) # добавляем id к корневой карте
        map_root.set('xml:lang', 'ru')
    except Exception as e:
        print('Could not extract keys element from the first topic') # если не удалось получить атрибуты

    # Автоматическое форматирование XML с отступами
    ET.indent(map_root)
    
    # Заголовок DITA файла (header)
    header = b"""<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE map PUBLIC "-//OASIS//DTD DITA Map//EN" "map.dtd">\n"""
    map_txt = ET.tostring(map_root, encoding='utf-8') # сериализация XML в байты

    # Папка для сохранения карты
    dir = f"{config.output_dir}/{config.document_type}"
    os.makedirs(dir, exist_ok=True)   # создание папки, если не существует

    # Сохраняем карту в файл
    with open(f'{dir}/{map_id}.ditamap', 'xb') as f: # 'xb' — создать новый файл, если существует, ошибка
        f.write(header)
        f.write(map_txt)

    # В зависимости от типа карты (приложение или глава) добавляем в bookmap
    if map_id.startswith('appendix'):
        # Для приложений создается элемент <appendix>
        appendix = ET.SubElement(bookmap, 'appendix')
        mapref = ET.SubElement(appendix, 'mapref')
        mapref.set('navtitle', map_navtitle)
        mapref.set('href', f'{config.document_type}/{map_id}.ditamap') # путь к файлу карты для BookMap
        mapref.set('format', 'ditamap')
        mapref.set('importance', 'required')
    else:
        # Для обычных глав создается элемент <chapter>
        _add_chapter(map_navtitle, f'{config.document_type}/{map_id}.ditamap')

def _add_chapter(navtitle: str, href: str):
    """
    Добавляет новую главу в глобальный bookmap.
    Используется как для save_map, так и напрямую.
    """
    chapter = ET.SubElement(bookmap, 'chapter')
    chapter.set('navtitle', navtitle)
    chapter.set('href', href)
    chapter.set('format', 'ditamap')
    return chapter

def save_bookmap():
    """
    Сохраняет глобальный bookmap, который содержит структуру всей книги.
    """
    dir = f'{config.output_dir}' # папка вывода
    os.makedirs(dir, exist_ok=True)
    
    # Заголовок BookMap файла (header)
    header = b"""<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE bookmap PUBLIC "-//OASIS//DTD DITA BookMap//EN" "bookmap.dtd">\n"""
    
    ET.indent(bookmap) # форматирование XML
    bookmap_txt = ET.tostring(bookmap, encoding='utf-8')
    
    # Сохраняем глобальный bookmap в файл (сохраняем BookMap с именем, соответствующим типу документа (config.document_type))
    with open(f'{dir}/{config.document_type}.ditamap', 'xb') as f:
        f.write(header)
        f.write(bookmap_txt)