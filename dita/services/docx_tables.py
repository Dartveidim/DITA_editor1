import logging
import re
import xml.etree.ElementTree as ET
import dita.config.config as config
from dita.models.table import Table, TableKeyReference
from dita.utils.translit import get_proper_id
from dita.core.topic import validate_id

logger = logging.getLogger(__name__)


def table_label(paragraph):
    """
    Извлекает чистый заголовок таблицы из абзаца Word.
    
    Аргументы:
        paragraph (ET.Element): абзац (<w:p>) из XML Word-документа
    
    Если абзац не соответствует шаблону "Таблица N – ...", возвращает 'ПЕРЕИМЕНУЙ МЕНЯ'.
    """
    # Извлекаем все текстовые элементы <w:t> из абзаца
    text_elements = paragraph.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t')
    
    # Собираем весь текст в один блок
    label_text = ""
    for t in text_elements:
        label_text = f"{label_text}{t.text}"

    # Регулярное выражение для "Таблица N – Заголовок"
    tab_pattern = re.compile("""^Таблица[\s]*[А-Я]?[\d\.]+[\s]*[\—\-\–\—][\s]*""")
    match = tab_pattern.match(label_text)
    if match is None:
        # Если заголовок не распознан, возвращаем заглушку
        label_text = "ПЕРЕИМЕНУЙ МЕНЯ"
    else:
        # Убираем префикс "Таблица N –" и лишние пробелы
        label_text = tab_pattern.sub('', label_text).strip()
    return label_text


def _column_number(table):
    """
    Подсчитывает количество колонок в таблице Word.

    Аргументы:
        table (ET.Element): элемент <w:tbl>

    Возвращает:
        int: количество колонок
    """
    # Находим все элементы <w:gridCol>, которые определяют колонки
    cols = table.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}gridCol')
    return len(cols)


def _row_number(table):
    """
    Подсчитывает количество рядов в таблице Word.

    Аргументы:
        table (ET.Element): элемент <w:tbl>

    Возвращает:
        int: количество рядов
    """
    # Находим все строки таблицы <w:tr>
    rows = table.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tr')
    return len(rows)


def vmerged(cell):
    """
    Проверяет, является ли ячейка таблицы частью вертикально объединённой области.

    Аргументы:
        cell (ET.Element): ячейка <w:tc>

    Возвращает:
        bool: True если ячейка объединена вертикально, False иначе
    """
    # Проверяем наличие тега <w:vMerge>
    vMerge = cell.find('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}vMerge')
    if vMerge is not None:
        # Если атрибут val равен "restart" – начало объединения
        if '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val' in vMerge.attrib.keys():
            if vMerge.attrib['{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val'] == "restart":
                return False
            else:
                # Если val не указан, значит это продолжение объединения
                return True
        else:
            return True
    else:
        return False


def gridspan(cell):
    """
    Возвращает количество колонок, которые занимает ячейка (gridSpan).

    Аргументы:
        cell (ET.Element): ячейка <w:tc>

    Возвращает:
        str | None: количество колонок или None
    """
    span = cell.find('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}gridSpan')
    if span is not None:
        return span.attrib['{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val']
    else:
        return None

def _empty_table(title):
    """
    Создаёт пустую таблицу с одной ячейкой и заголовком.

    Аргументы:
        title (str): заголовок таблицы

    Возвращает:
        Table: объект пустой таблицы
    """
    # Создаём объект таблицы Table
    tbl = Table(title)

    # Добавляем одну пустую строку с одной ячейкой
    tbl.add_row([''])
    return tbl

def _is_ul(paragraph):
    """
    Проверяет, является ли абзац частью маркированного списка.

    Аргументы:
        paragraph (ET.Element): абзац <w:p>

    Возвращает:
        int | bool: уровень списка (0,1,2...) или False если не список
    """
    # Проверяем наличие тега <w:numPr>, который обозначает список
    numPr = paragraph.find('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}numPr')
    if numPr is not None:
        # Возвращаем уровень списка (ilvl)
        return numPr.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}ilvl').attrib('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
    else:
        return False


def parse_footnote(run_el):
    """
    Проверяет, есть ли сноска в элементе <w:r>.

    Аргументы:
        run_el (ET.Element): элемент <w:r> абзаца

    Возвращает:
        ET.Element | None: элемент сноски <footnoteReference> или None
    """
    footnote = run_el.find('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}footnoteReference')
    if footnote is not None:
        footnote_id = footnote.attrib['{http://schemas.openxmlformats.org/wordprocessingml/2006/main}id']
        return footnote
    else:
        return None


def parse_cell(cell):
    """
    Преобразует ячейку Word в элемент <entry> DITA с поддержкой сносок и списков.

    Аргументы:
        cell (ET.Element): ячейка <w:tc>

    Возвращает:
        ET.Element: элемент <entry> с содержимым ячейки
    """
    entry = ET.Element('entry') # Создаём контейнер entry для DITA
    elements_stack = []   # Стек для вложенных списков <ul>
    last_li_element = None # Последний <li>, чтобы вложенные списки корректно добавлялись

    # Проходим по каждому абзацу в ячейке
    for paragraph in cell.findall('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
        ul_level = _is_ul(paragraph) # Проверяем, маркирован ли абзац
        
        # Создаём элемент <li> для списка или <div> для обычного текста
        if ul_level:
            el = ET.Element('li')
        else:
            el = ET.Element('div')
        text_buffer = "" # Буфер для текста абзаца
        has_footnote = False

        # Обрабатываем каждый элемент <w:r> (run)
        for run in paragraph.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}r'):

            footnote = parse_footnote(run)
            if footnote is not None:
                has_footnote = True
                el.text = text_buffer
                text_buffer = ""
                el.append(footnote)  # Добавляем сноску внутрь элемента
            else:
                # Собираем текст из <w:t>
                for t_el in run.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
                    text_buffer = f"""{text_buffer}{t_el.text}"""
                
                # Присваиваем текст элементу
                if ul_level:
                    el.text = text_buffer
                
                    if len(elements_stack) == 0:
                        ul_el = ET.SubElement(entry, 'ul')  # Создаём новый список <ul>
                        ul_el.append(el)
                        elements_stack.append(ul_el)
                    elif len(elements_stack) <= int(ul_level) + 1:
                        ul = ET.SubElement(last_li_element, 'ul')
                        ul.append(el)
                        elements_stack.append(ul_el)
                    elif len(elements_stack) <= int(ul_level) + 1:
                        elements_stack.pop()
                        ul = elements_stack[int(ul_level)]
                        ul.append(el)
                    else:
                        ul = elements_stack[int(ul_level)]
                        ul.append(el)
                  
                    last_li_element = el

                else:
                    if has_footnote:
                        footnote.tail = text_buffer
                    else:
                        el.text = text_buffer
                        entry.append(el)

                    elements_stack = []
                    last_li_element = None
    return entry

def parse_table(table_element):
    """
    Преобразует элемент Word <w:tbl> в объект Table DITA.

    Аргументы:
        table_element (ET.Element): элемент таблицы <w:tbl>
    
    Возвращает:
        Table: объект таблицы с заполненными строками и колонками
    """
    table_obj = Table() # Создаём пустой объект таблицы
    col_count = _column_number(table_element) # Определяем количество колонок
    table_obj.set_colnum(col_count)

    # Проходим по каждой строке <w:tr>
    for row_el in table_element.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tr"):
        row_list = []      # Список для gridspan/vmerged
        if config.process_text_in_tables:
            row_entries = []  # Список для элементов <entry> внутри строк
         for idx, cell_el in enumerate(row_el.findall("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tc")):
            span = gridspan(cell_el)  # Проверяем, сколько колонок занимает ячейка
            if config.process_text_in_tables:
                entry_el = parse_cell(cell_el)  # Преобразуем ячейку в <entry>
            
            # Проверяем объединённые ячейки
            if vmerged(cell_el):
                row_list.append("vmerged")
                if config.process_text_in_tables:
                    row_entries.append(None)
            elif span:
                row_list.append(span)
                if config.process_text_in_tables:
                    row_entries.append(entry_el)
            else:
                row_list.append('')
                if config.process_text_in_tables:
                    row_entries.append(entry_el)

        table_obj.add_row(row_list)  # Добавляем строку с информацией о colspan/rowspan
        if config.process_text_in_tables:
            table_obj.add_entries(row_entries)  # Добавляем текстовое содержимое ячеек

    return table_obj


def create_reference_table(table_obj: Table):
    """
    Создаёт DITA reference-топик для таблицы и сохраняет его в файл.

    Аргументы:
        table_obj (Table): объект таблицы, который нужно экспортировать
    
    Возвращает:
        str: ID таблицы в формате "table_<id>"
    """
    # Директория для сохранения таблиц
    table_dir = f"{config.output_dir}/{config.document_type}/table"
    
    # Заголовок таблицы
    table_title = table_obj.title.text
    
    # Создаём корректный идентификатор из заголовка
    base_id = get_proper_id(table_title)
    
    # Добавляем префикс "table_" и проверяем уникальность ID
    table_id = "table_" + validate_id(table_dir, base_id)

    # Присваиваем объекту таблицы уникальный ID
    table_obj.set_id(table_id)
    
    # Очищаем объект таблицы перед вставкой в reference-топик (убираем лишние данные)
    table_obj.clear()

    # Создаём XML-элемент <reference> для DITA
    ref_topic = ET.Element('reference')
    ref_topic.set('id', f"table_topic_{table_id}")  # Уникальный ID топика
    
    # Добавляем заголовок таблицы в топик
    ET.SubElement(ref_topic, 'title').text = table_title
    
    # Добавляем тело топика <refbody> и помещаем туда саму таблицу
    ref_body = ET.SubElement(ref_topic, 'refbody')
    ref_body.append(table_obj.table)

    # Заголовок XML файла с DTD
    header = b"""<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE reference PUBLIC "-//OASIS//DTD DITA Reference//EN" "reference.dtd">\n"""
    
    # Красиво форматируем XML с отступами
    ET.indent(ref_topic)
    
    # Преобразуем XML-дерево в байты
    topic_txt = ET.tostring(ref_topic, encoding='utf-8')

    # Сохраняем файл DITA
    with open(f"{table_dir}/{table_id}.dita", 'xb') as f:
        f.write(header) # Записываем XML заголовок
        f.write(topic_txt) # Записываем сам контент

    # Возвращаем ID таблицы для ключевых ссылок
    return table_id


def process_tables_docx():
    """
    Основная функция обработки всех таблиц из DOCX файла.
    Создаёт reference-топики для каждой таблицы и обновляет ключевой словарь.
    """
    # Проверяем, что DOCX файл загружен
    if config.docx is None:
        exit("Could not read the docx file.")
    else:
        root = config.docx.document  # Корень XML документа Word
        
        table_map = TableKeyReference()  # Объект для хранения ключевых ссылок (keydef)
        previous_label = None            # Хранит заголовок таблицы, если он найден перед таблицей


        # Проходим по всем элементам тела документа
        for el in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}body/*'):
            # Если элемент — абзац, пытаемся извлечь заголовок таблицы
            if el.tag == "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p*":
                label = table_label(el)
                if label is not None:
                    previous_label = label  # Сохраняем заголовок для следующей таблицы

            # Если элемент — таблица и перед ней был заголовок        
            elif (el.tag == "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tbl") and (previous_label is not None):
                table_title = previous_label
                logger.debug(f"Found a table {table_title}")
                previous_label = None  # Сбрасываем, чтобы не привязывалось к следующей таблице
                
                try:
                    # Парсим таблицу из XML Word в объект Table
                    table = parse_table(el)
                    table.set_title(table_title)  # Присваиваем заголовок
                except Exception as e:
                    # Если парсинг не удался — создаём пустую таблицу
                    logger.error(f'Failed to parse table {table_title} because of the following error: {e}')
                    table = _empty_table(table_title)

                # Создаём DITA reference-топик и получаем ID таблицы
                t_id = create_reference_table(table)

                # Добавляем запись в keydef (связываем заголовок и ID)
                table_map.add_keydef(table_title, t_id)
            else:
                # Все остальные элементы пропускаем
                pass
        
        # Сохраняем ключевой словарь таблиц
        table_map.save()