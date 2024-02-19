import re
import emoji


def remove_emojis(text):
    clean_text = ''.join([c for c in text if c not in emoji.EMOJI_DATA])
    return clean_text


def remove_multiple_dots(text):
    result_str = re.sub(r'\.{2,}', '.', text)
    return result_str


def remove_code_blocks(text):
    pattern = r'```.*?```'
    return re.sub(pattern, '', text, flags=re.DOTALL)


def find_code_blocks(text):
    code_blocks = []
    pattern = r'```.*?```'
    for match in re.finditer(pattern, text, flags=re.DOTALL):
        code_blocks.append([match.start(), match.end() - 1])
    return code_blocks
