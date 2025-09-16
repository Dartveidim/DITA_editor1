import logging
import re
import xml.etree.ElementTree as ET
import config
from table import Table, TableKeyReference
from translit import get_proper_id
from topic import validate_id

logger = logging.getLogger(__name__)


def table_label(p):
    labels = p.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t')
    label = ""
    for l in labels:
        label = f"{label}{l.text}"

    tab_pattern = re.compile("""^Таблица[\s]*[А-Я]?[\d\.]+[\s]*[\—\-\–\—][\s]*""")
    correct = tab_pattern.match(label)
    if correct is None:
        label = "ПЕРЕИМЕНУЙ МЕНЯ"
    else:
        label = tab_pattern.sub('', label).strip()
    return label


def _column_number(table):
    cols = table.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}gridCol')
    return len(cols)


def _row_number(table):
    rows = table.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tr')
    return len(rows)


def vmerged(cell):
    vMerge = cell.find('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}vMerge')
    if vMerge is not None:
        if '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val' in vMerge.attrib.keys():
            if vMerge.attrib['{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val'] == "restart":
                return False
            else:
                return True
        else:
            return True
    else:
        return False


def gridspan(cell):
    span = cell.find('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}gridSpan')
    if span is not None:
        return span.attrib['{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val']
    else:
        return None

def _empty_table(title):
    tbl = Table(title)
    tbl.add_row([''])
    return ybl

def _is_ul(p):
    numPr = p.find('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}numPr')
    if numPr is not None:
        return numPr.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}ilvl').attrib('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
    else:
        return False


def parse_footnote(r_el):
    footnote =r_el.find('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}footnoteReference')
    if footnote is not None:
        footnote_id = footnote.attrib['{http://schemas.openxmlformats.org/wordprocessingml/2006/main}id']
        return footnote
    else:
        return None


def parse_cell(cell):
    entry = ET.Element('entry')
    list = []
    last_li_el = None

    for p in cell.findall('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
        ul_lvl = _is_ul(p)
        if ul_lvl:
            el = ET.Element('li')
        else:
            ET.Element('div')
        text = ""
        tail = False

        for r_el in p.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}r'):

            footnote = parse_footnote(r_el)
            if footnote is not None:
                tail = True
                el.text = text
                text = ""
                el.append(footnote)
            else:
                for t_el in r_el.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
                text = f"""{text}{t_el.text}"""

                if ul_lvl:
                    el.text = text
                
                    if len(list) == 0:
                        ul_el = ET.SubElement(entry, 'ul')
                        ul_el.append(el)
                        list.append(ul_el)
                    elif len(list) < int(ul_lvl) + 1:
                        ul = ET.SubElement(last_li_el, 'ul')
                        ul.append(el)
                        list.append(ul)
                    elif len(list) > int(ul_lvl) + 1:
                        list.pop()
                        ul = list[int(ul_lvl)]
                        ul.append(el)
                    else:
                        ul = list[int(ul_lvl)]
                        ul.append(el)
                  
                    last_li_el = el

                else:
                    if tail:
                        footnote.tail = text
                    else:
                        el.text = text
                        entry.append(el)

                    list = []
                    last_li_el = None
    return entry

def parse_table(table):
    tbl = Table()
    cols = _column_number(table)
    tbl.set_colnum(cols)

    for row in table.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tr"):
        row_list = []
        if config.process_text_in_tables: 
            row_entries = []
        for idx, cell in enumerate(row.findall("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tc")):
            span = gridspan(cell)
            if config.process_text_in_tables:
                entry_el = parse_cell(cell) 
            if vmerged(cell):
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

        tbl.add_row(row_list)
        if config.process_text_in_tables:
            tbl.add_entries(row_entries)

    return tbl


def create_reference_table(table_obj: Table):
    dir = f"{config.output_dir}/{config.document_type}/table"
    table_title = table_obj.title.text
    id = get_proper_id(table_title)
    id = validate_id(dir, id)

    table_obj.set_id(id)
    table_obj.clear()

    ref_topic = ET.Element('reference')
    ref_topic.set('id', f"table_topic_{id}")
    ET.SubElement(ref_topic, 'title').text = table_title
    ref_body = ET.SubElement(ref_topic, 'refbody')
    ref_body.append(table_obj.table)

    header = b"""<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE reference PUBLIC "-//OASIS//DTD DITA Reference//EN" "reference.dtd">\n"""
    ET.indent(ref_topic)
    topic_txt = ET.tostring(ref_topic, encoding='utf-8')

    with open(f"{dir}/{id}.dita", 'xb') as f:
        f.write(header)
        f.write(topic_txt)

    return id


def process_tables_docx():
    if config.docx is None:
        exit("Could not read the docx file.")
    else:
        root = config.docx.document
        
        table_map = TableKeyReference()
        previous_label = None

        for el in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}body/*'):
            if el.tag == "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p*":
                label = _table_label(el)
                if label is not None:
                    previous_label = label
            elif (el.tag == "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tbl") and (previous_label is not None):
                table_title = previous_label
                logger.debug(f"Found a table {table_title}")
                previous_label = None
                try:
                    table = parse_table(el)
                    table.set_title(table_title)
                except Exception as e:
                    logger.error(f'Failed to parse table {table_title} because of the following error: {e}')
                    table = _empty_table(table_title)

                id = create_reference_table(table)
                table_map.add_keydef(table_title, id)
            else:
                pass
        table_map.save()