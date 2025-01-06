def load_file_as_bin(path:str):
    text = ''
    with open(path, "rt", encoding='utf-8') as rt:
        text = rt.read()
    return bytes(text, encoding='utf-8')

def load_text(path:str):
    text = ''
    with open(path, "rt", encoding='utf-8') as rt:
        text = rt.read()
    return text
