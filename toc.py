import re
from translit import get_proper_id
import config
import os

def write_csv(csv, number, title):
    id = get_proper_id(title)
    indent = number.count('.')
    indents = {f'r{i}': '' for i in range(7)}
    indents[f'r{indent}'] = number
    csv.write(f"""{indents['r0']};{indents['r1']};{indents['r2']};{indents['r3']};{indents['r4']};{indents['r5']};{indents['r6']};{title};{id}\n""")

def toc():
    try:
        os.makedirs(config.output_dir)
    except FileExistsError:
        pass
    
    csv = open(f"{config.output_dir}/Трансформация_названий_разделов.csv", "w")
    t = open('doc_structure.txt', 'w', encoding='utf-8')
    with open('word.txt', "r", encoding='utf-8') as f:
        for line in f.readlines():
            m = re.search(r"^[A-Я]?[\d\.]+\s", line)
            if m is not None:
                indent = m[0].count('.')
                line = re.sub(r"^[A-Я]?[\d\.]+\s", "    " * indent, line)
                t.write(line)
                write_csv(csv, m[0].strip(), line.strip())
            else:
                t.write(line)
                write_csv(csv, "", line.strip())
    t.close()
    csv.close()