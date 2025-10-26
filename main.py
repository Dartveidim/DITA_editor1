import dita.config.config as config
from dita.core.topic import create_topic
from dita.core.toc import toc
from dita.core.map import save_map, save_bookmap
import xml.etree.ElementTree as ET
import os
from dita.core.tables import process_tables
from dita.services.docx_tables import process_tables_docx
from dita.services.docx_images import process_images_docx, process_icons
from dita.services.docx import Docx


def add_topic_to_map(parent_element: ET.Element, topic_id: str, topic_title: str) -> ET.Element:
    """
    Добавляет ссылку на DITA-топик в карту (map) XML.
    
    Параметры:
        parent_element: родительский XML-элемент (map или topicref)
        topic_id: уникальный идентификатор топика
        topic_title: заголовок топика (navtitle)
    
    Возвращает:
        Элемент topicref, добавленный в map
    """
    topicref_element = ET.SubElement(parent_element, 'topicref')
    topicref_element.set('keys', topic_id)
    topicref_element.set('href', f'topic/{topic_id}.dita')
    topicref_element.set('navtitle', topic_title)
    return topicref_element

def process_topics():
    """
    Основная функция обработки тем документа:
    1. Создает оглавление из doc_structure.txt
    2. Генерирует DITA-топики
    3. Формирует карты (map) с уровневой структурой
    """
    # Генерация файла структуры документа и CSV
    toc()
    
    topic_levels = []  # стек для отслеживания текущих уровней заголовков
    is_first_map = True  # флаг для создания первой карты

    with open('doc_structure.txt', 'r', encoding='utf-8') as structure_file:
        for line in structure_file.readlines():
            line_clean = line.strip('\n')
            heading = line_clean.strip()
            
            # Вычисление уровня заголовка по отступу (4 пробела = 1 уровень)
            indent_length = len(line_clean) - len(heading)
            heading_level = int(indent_length / 4) + 1  # определение уровня по отступу (4 пробела)

            # Создание уникального DITA-топика
            topic_id = create_topic(heading)

            if heading_level == 1:
                # Заголовки первого уровня создают новую карту
                if not is_first_map:
                    save_map(current_map_root)
                    del current_map_root  # удаляем старую карту из памяти
                is_first_map = False
                current_map_root = ET.Element('map')  # корень новой карты
                parent_element = current_map_root
            else:
                # Для второго и более глубокого уровней берем родителя из стека
                parent_element = topic_levels[heading_level - 2]

            if heading_level > len(topic_levels):
                # Добавляется новый уровень
                topicref_element = add_topic_to_map(parent_element, topic_id, heading)
                topic_levels.append(topicref_element)
            elif heading_level == len(topic_levels):
                # Перезапись текущего уровня
                topicref_element = add_topic_to_map(parent_element, topic_id, heading)
                topic_levels[heading_level - 1] = topicref_element
            else:
                # Удаление лишних уровней
                while len(topic_levels) > heading_level:
                    removed = topic_levels.pop()
                topicref_element = add_topic_to_map(parent_element, topic_id, heading)
                topic_levels[heading_level - 1] = topicref_element

    save_map(current_map_root) # вызов функции, которая сохраняет текущую DITA-карту (map) в файл
    save_bookmap() # Сохранение глобальной BookMap с ссылками на все карты


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