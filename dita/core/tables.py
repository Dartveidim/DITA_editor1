import dita.config.config as config
from dita.utils.translit import get_proper_id
import re
from dita.core.topic import validate_id, save_topic
from dita.services.docx_tables import process_tables_docx
from dita.models.table import TableKeyReference
from dita.utils.id_generators import gen_tab_id

def create_reference(table_title: str) -> str:
    """
    Создаёт DITA reference для таблицы.
    
    Аргументы:
    table_title -- заголовок таблицы
    
    Возвращает:
    table_id -- уникальный идентификатор таблицы
    """
    table_id = gen_tab_id(table_title) # см. dita.utils.id_generators

    # Формируем XML-текст reference
    reference_txt = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE reference PUBLIC "-//OASIS//DTD DITA Reference//EN" "reference.dtd">
<reference id="{table_id}">
  <title>{table_title}</title>
  <refbody>
    <table id="{table_id}">
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
    
    # Сохраняем DITA-топик таблицы
    save_topic(table_dir, table_id, reference_txt)
    
    return table_id

def process_tables():
    """
    Читает файл tables.txt, создаёт reference для каждой таблицы и сохраняет ключи.
    """
    table_key_map = TableKeyReference() # объект для хранения ключей таблиц
    
    with open("tables.txt", "r", encoding="utf-8") as f:
        for line in f.readlines():
            # Убираем префикс "Таблица N - " из заголовка
            cleaned_title = re.sub('^Таблица\s\d+\s\-\s', '', line).strip()
            
            # Создаём reference и получаем уникальный id
            table_id = create_reference(cleaned_title)
            
            # Добавляем ключ в карту
            table_key_map.add_keydef(cleaned_title, table_id)
    
    # Сохраняем ключи таблиц
    table_key_map.save()