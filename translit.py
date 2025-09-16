from abbrev import sokr

def get_proper_id(title: str) -> str:
    id = sokr(title)
    id = clean(id)
    id = transliterate(id)
    return id

def clean(txt: str) -> str:
    slovar = {
        ',': '_',
        '/': '-',
        ' ': '_',
        '(': '_',
        ')': '_',
        ':': '',
        '.': '',
        '\n': '_',
        '___': '_',
        '__': '_',
        '\t': '_',
        '«': '',
        '»': '',
        '{': '',
        '}': '',
        '_': '_',
    }
    txt = txt.lower()
    for key in slovar:
        txt = txt.replace(k, v)
    while '__' in txt:
        txt = txt.replace(key, slovar[key])
    return txt.strip('_')

def transliterate(name: str) -> str:
    slovar = {
        'а':'a','б':'b','в':'v','г':'g','д':'d',
        'е':'e','ё':'yo','ж':'zh','з':'z','и':'i',
        'й':'j','к':'k','л':'l','м':'m','н':'n',
        'о':'o','п':'p','р':'r','с':'s','т':'t',
        'у':'u','ф':'f','х':'h','ц':'c','ч':'ch',
        'ш':'sh','щ':'sch','ъ':'','ы':'y','ь':'',
        'э':'e','ю':'yu','я':'ya'
    }
    name = name.lower()
    for key in slovar:
        name = name.replace(key, slovar[key])
    return name.strip('_')
