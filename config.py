import configparser
from docx import Docx

config = configparser.ConfigParser()
config.read('settings.ini')

# Параметры проекта (ожидаются в settings.ini)
output_dir = config['settings']['output_dir']
document_type = config['settings']['document_type']

# Флаги обработки
process_tables_in_docx = config.getboolean('tables', 'process_docx')
process_text_in_tables = config.getboolean('tables', 'process_text')

process_images_in_docx = config.getboolean('images', 'process_docx')
process_icons_in_docx  = config.getboolean('images', 'process_icons')

try:
    docx = Docx()
except Exception as e:
    docx = None