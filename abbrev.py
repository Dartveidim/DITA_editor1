import re

def appendix(txt):
    txt = re.sub('Приложение\s[А-Я]', 'appendix', txt)
    txt = re.sub('\s\(справочное\)\s', ' ', txt)
    return txt

def clean(txt):
    slovar = {
        ' и ': '',
        ' в ': '',
        ' при ': '',
        ' на ': '',
        ' с ': '',
        ' по ': '',
    }

    txt = txt.lower()
    for key in slovar:
        txt = txt.replace(key, slovar[key])
    return txt.strip('_')

def abbreviate(txt):
    glasnye = ['у','е','ы','а','о','э','я','и','ю']
    gl_limit = 3

    finish = False
    abbreviated = ""
    gl_count = 0
    for bukva in txt:
        abbreviated = abbreviated + bukva
        if finish: break
        if bukva in glasnye:
            gl_count = gl_count + 1
            if gl_count == gl_limit:
                finish = True
    return abbreviated

def sokr(txt):
    word_limit_pre = 3
    word_limit_post = 2
    txt = appendix(txt)
    txt = clean(txt)
    words = txt.split()

    if len(words) <= word_limit_pre + word_limit_post:
        words = words[0:word_limit_pre + word_limit_post]
    else:
        words = words[0:word_limit_pre] + words[-word_limit_post:]

    abbreved = [abbreviate(word) for word in words]
    title = " ".join(abbreved)
    return title