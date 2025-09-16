import xml.etree.ElementTree as ET
import config
import os

bookmap = ET.Element('bookmap')
booktitle = ET.SubElement(bookmap, 'booktitle')
mainbooktitle = ET.SubElement(booktitle, 'mainbooktitle')

def save_map(map):
    global bookmap
    try:
        map_id = map.find('topicref').attrib['keys']
        map_navtitle  = map.find('topicref').attrib['navtitle']
        map.set('id', map_id)
        map.set('xml:lang', 'ru')
    except Exception as e:
        print('Could not extract keys element from the first topic')

    ET.indent(map)
    header = b"""<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE map PUBLIC "-//OASIS//DTD DITA Map//EN" "map.dtd">\n"""
    map_txt = ET.tostring(map, encoding='utf-8')


    dir = f"{config.output_dir}/{config.document_type}"
    try:
        os.makedirs(dir)
    except FileExistsError:
        pass

    with open(f'{dir}/{map_id}.ditamap', 'xb') as f:
        f.write(header)
        f.write(map_txt)

    if map_id.startswith('appendix'):
        appendix = ET.SubElement(bookmap, 'appendix')
        mapref = ET.SubElement(appendix, 'mapref')
        mapref.set('navtitle', map_navtitle)
        mapref.set('href', f'{config.document_type}/{map_id}.ditamap')
        mapref.set('format', 'ditamap')
        mapref.set('importance', 'required')
    else:
        chapter = ET.SubElement(bookmap, 'chapter')
        chapter.set('navtitle', map_navtitle)
        chapter.set('href', f'{config.document_type}/{map_id}.ditamap')
        chapter.set('format', 'ditamap')

def save_bookmap():
    dir = f'{config.output_dir}'
    try:
        os.makedirs(dir)
    except FileExistsError:
        pass
    
    header = b"""<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE bookmap PUBLIC "-//OASIS//DTD DITA BookMap//EN" "bookmap.dtd">\n"""
    ET.indent(bookmap)
    bookmap_txt = ET.tostring(bookmap, encoding='utf-8')
    with open(f'{dir}/{config.document_type}.ditamap', 'xb') as f:
        f.write(header)
        f.write(bookmap_txt)