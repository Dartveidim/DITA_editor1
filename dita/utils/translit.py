from dita.utils.abbrev import appendix, clean, abbreviate, transliterate, repl

# Финальная генерация очищенных и сокращенных идентификаторов
# использует фунции appendix, clean, abbreviate
def sokr(txt):
    word_limit_pre = 3
    word_limit_post = 2
    sokr_id = appendix(txt)
    sokr_id = clean(sokr_id)
    words = sokr_id.split()
    
    # оставляем только первое и последнее сокращенное слово из текста
    if len(words) <= word_limit_pre + word_limit_post:
        words = words[0:word_limit_pre + word_limit_post]
    else:
        words = words[0:word_limit_pre] + words[-word_limit_post:]

    abbreved = [abbreviate(word) for word in words]
    title = " ".join(abbreved)
    return title

# Преобразует текст в корректный идентификатор
def get_proper_id(title: str) -> str:
    proper_id = sokr(title)
    proper_id = repl(proper_id)
    proper_id = transliterate(proper_id)
    return proper_id




