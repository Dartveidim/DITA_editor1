import os
from translit import get_proper_id
import re
import config
import logging

logger = logging.getLogger(__name__)

def save_topic(dir_: str, _id: str, topic_txt: str):
    try:
        path = f"{dir}/{id}.dita"
        f = open(path, "x", encoding='utf-8')
    except Exception as e:
        print(e)
    else:
        f.write(topic_txt)
        f.close()

def validate_id(dir_: str, _id: str) -> str:
    
    try:
        os.makedirs(dir)
    except FileExistsError:
        pass

    while os.path.exists(f"{dir_}/{_id}.dita"):
        logger.debug(f"A file with the name {_id} already exists. Appending '_N'...")
        m = re.search(r'\_(\d+)$', id)
        if m is not None:
            inc = int(m.group(1))
            full_inc = m.group(0)
            inc = inc+1
            id_base = id.rstrip(full_inc)
            id = f"{id_base}_{inc}"
        else:
            id = f"{id}_1"
    return id

def create_topic(title: str):
    id = get_proper_id(title)
    dir = f"{config.output_dir}/{config.document_type}/topic"
    
    id = validate_id(dir, id)

    topic_txt = F"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE concept PUBLIC "-//OASIS//DTD DITA Concept//EN" "concept.dtd">
<concept id="{id}" xml:lang="ru">
  <title>{title}</title>
  <conbody>
    <p></p>
  </conbody>
</concept>"""
    save_topic(dir, id, topic_txt)

    return id