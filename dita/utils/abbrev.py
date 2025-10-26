# Модуль для генерации сокращенных идентификаторов из заголовков или текстовых фрагметов.
# Используется для формирования ID элементы документации, названия файлов, ссылок и текстовых идентификаторов
import re
from translit_map import abbrev_clean_words, glasnye_letters, repl_map, translit_dict

# Заменяет текст 'Приложение Х' на 'appendix', а слово '(справочное)' удаляет
def appendix(txt):
    txt = re.sub('Приложение\s[А-Я]', 'appendix', txt)
    txt = re.sub('\s\(справочное\)\s', ' ', txt)
    return txt

# Удаляет из текста служебные слова по шаблону abbrev_clean_words из файла translit_map
def clean(txt):
    txt = txt.lower()
    for key in abbrev_clean_words:
        txt = txt.replace(key, abbrev_clean_words[key])
    return txt.strip('_')

# Сокращает слова в тексте до лимита содержания гласных букв по шаблону гласных glasnye_letters из файла translit_map
def abbreviate(txt):
    gl_limit = 3 # задается лимит гласных для слова
    finish = False
    abbreviated = ""
    gl_count = 0
    for bukva in txt:
        abbreviated = abbreviated + bukva
        if finish: break
        if bukva in glasnye_letters:
            gl_count = gl_count + 1
            if gl_count == gl_limit:
                finish = True
    return abbreviated

# очищает текст от нежелательных символов или заменяет их на '_' по словарю translit_clean_map из файла translit_map
def repl(txt: str) -> str:
    txt = txt.lower()
    for key, value in repl_map.items():
        txt = txt.replace(key, value)
        txt = re.sub(r'_+', '_', txt)
    return txt.strip('_')

# Выполняет транслитерацию русского текста в латиницу по словарю translit_map из файла translit_map
def transliterate(name: str) -> str:
    name = name.lower()
    for key in translit_dict:
        name = name.replace(key, translit_dict[key])
    return name.strip('_')