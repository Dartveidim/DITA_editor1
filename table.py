import xml.etree.ElementTree as ET
from translit import get_proper_id
import config
import os

class Table:
    def __init__(self, title="Тестовая таблица"):
        self.previous_row = None
        self.table = ET.Element("table")
        self.title = ET.SubElement(self.table, "title")
        self.title.text = title
        self.tgroup = ET.SubElement(self.table, "tgroup")
        self.colnum = None
        self.tbody = ET.SubElement(self.tgroup, "tbody")
        self.previous_row = None

    def add_entries(self, entries):
        parent = self.tbody.findall("row")[-1]
        for idx, entry in enumerate(entries):
            if entry is not None:
                local_entry = parent.findall("entry")[idx]
                attr = local_entry.attrib
                parent.remove(local_entry)
                entry.attrib = attr
                parent.insert(idx, entry)

    def set_title(self, title_txt):
        self.title.text = title_txt

    def set_id(self, id):
        self.table.set("id", id)

    def set_colnum(self, col_number: int):
        self.colnum = col_number
        self.tgroup.set("cols", str(col_number))
        for i in range(self.colnum):
            colspec = ET.Element("colspec")
            colspec.set("colnum", str(i + 1))
            colspec.set("colwidth", "1*")
            colspec.set("colname", f"col{i + 1}")
            self.tgroup.insert(i, colspec)

    def add_row(self, cells_in_row: list[str]):
        row = ET.SubElement(self.tbody, "row")
        for idx, cell in enumerate(cells_in_row):
            if cell == "vmerged":
                self.mark_first_merged_cell(idx)
                cell_el = ET.SubElement(row, 'entry')
                cell_el.set("vmerged", "")
            elif cell != '':
                span = cell
                cell_el = ET.SubElement(row, 'entry')
                cell_el.set('namest', f'col{idx + 1}')
                cell_el.set('nameend', f'col{idx + int(span)}')
            else:
                ET.SubElement(row, "entry")

    def mark_first_merged_cell(self, id):
        rows = self.tbody.findall('row')[:-1 or None]
        for row in reversed(rows):
            cells = row.findall("entry")
            cell_above = cells[id]
            if "vmerged" in cell_above.attrib:
                continue
            else:
                if "morerows" in cell_above.attrib:
                    num_of_merged_cells = cell_above.attrib["morerows"]
                    cell_above.set("morerows", str(int(num_of_merged_cells) + 1))
                else:
                    cell_above.set("morerows", "1")
                break

    def __str__(self):
        ET.indent(self.table)
        self.clear()
        return ET.tostring(self.table, encoding="utf-8").decode("utf-8")

    def clear(self):
        for parent_row in self.table.findall(".//row"):
            for merged_cell in parent_row.findall(".//entry"):
                if "vmerged" in merged_cell.attrib:
                    parent_row.remove(merged_cell)

class TableKeyReference:
    def __init__(self):
        self.map = ET.Element("map")
        self.map.set("id", f"{config.document_type}-KEYLIST-TABLES")
        self.map.set("xml:lang", "ru")
        title = ET.SubElement(self.map, "title")
        title.text = "Список ключей таблиц"
        self.topicgroup = ET.SubElement(self.map, "topicgroup")

    def add_keydef(self, table_title, id):
        comment = ET.Comment(f"{table_title}")
        self.topicgroup.append(comment)
        keydef = ET.SubElement(self.topicgroup, "keydef")
        keydef.set("keys", id)
        keydef.set("href", f"table/{id}.dita")

    def save(self):
        dir = f"{config.output_dir}/{config.document_type}"
        file = f"{config.document_type}-KeyList-Tables.ditamap"
        
        try:
            os.makedirs(dir)
        except FileExistsError:
            pass

        header = b"""<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE bookmap PUBLIC "-//OASIS//DTD DITA BookMap//EN" "bookmap.dtd">\n"""
        ET.indent(self.map)
        map_txt = ET.tostring(self.map, encoding="utf-8")
        with open(f"{dir}/{file}", "wb") as f:
            f.write(header)
            f.write(map_txt)