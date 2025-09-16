import config
from topic import create_topic
from toc import toc
from map import save_map, save_bookmap
import xml.etree.ElementTree as ET
import os
from tables import process_tables
from docx_tables import process_tables_docx
from docx_images import process_images_docx, process_icons
from docx import Docx


def add_topic_to_map(parent, id, heading):
    new = ET.SubElement(parent, 'topicref')
    new.set('key', id)
    new.set('href', f'topic/{id}.dita')
    new.set('navtitle', heading)
    return new

def process_topics():
    toc()
    levels = []
    first_map_flag = True

    with open('doc_structure.txt', 'r', encoding='utf-8') as f:
        for line in f.readlines():
            line = line.strip('\n')
            heading = line.strip()
            level = len(line) - len(heading)
            level = int(level / 4) + 1  # определение уровня по отступу (4 пробела)

            topic_id = create_topic(heading)

            if level == 1:
                # Первый уровень заголовков
                if first_map_flag is False:
                    save_map(maproot)
                    del maproot
                first_map_flag = False
                maproot = ET.Element('map')
                parent = maproot
            else:
                # Второй уровень и глубже
                parent = levels[level - 2]

            if level > len(levels):
                # Добавляется новый уровень
                topicref = add_topic_to_map(parent, topic_id, heading)
                levels.append(topicref)
            elif level == len(levels):
                # Перезапись текущего уровня
                topicref = add_topic_to_map(parent, topic_id, heading)
                levels[level - 1] = topicref
            else:
                # Удаление лишних уровней
                while len(levels) > level:
                    removed = levels.pop()
                topicref = add_topic_to_map(parent, topic_id, heading)
                levels[level - 1] = topicref

    save_map(maproot)
    save_bookmap()


if __name__ == "__main__":
    if os.path.exists('word.txt'):
        process_topics()

    if os.path.exists('tables.txt') and not config.process_tables_in_docx:
        process_tables()

    if config.process_tables_in_docx:
        process_tables_docx()

    if config.process_images_in_docx:
        process_images_docx()

    if config.process_icons_in_docx:
        process_icons()