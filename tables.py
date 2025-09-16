import config
from translit import get_proper_id
import re
from topic import validate_id, save_topic
from docx_tables import process_tables_docx
from table import TableKeyReference

def create_reference(table_title: str) -> str:
    id = get_proper_id(table_title)
    dir = f"{config.output_dir}/{config.document_type}/table"
    id = validate_id(dir, id)

    reference_txt = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE reference PUBLIC "-//OASIS//DTD DITA Reference//EN" "reference.dtd">
<reference id="table_topic_{id}">
  <title>{table_title}</title>
  <refbody>
    <table id="{id}">
      <title>{table_title}</title>
      <tgroup cols="1">
        <tbody>
          <row>
            <entry>ЗАМЕНИ МЕНЯ!!!</entry>
          </row>
        </tbody>
      </tgroup>
    </table>
  </refbody>
</reference>"""
    
    save_topic(dir, id, reference_txt)
    return id

def process_tables():
    table_map = TableKeyReference()
    with open("tables.txt", "r", encoding="utf-8") as f:
        for line in f.readlines():
            title = re.sub('^Таблица\s\d+\s\-\s', '', line).strip()
            id = create_reference(title)
            table_map.add_keydef(title, id)
    table_map.save()