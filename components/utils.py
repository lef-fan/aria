import re


def remove_emojis(text):
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F700-\U0001F77F"  # alchemical symbols
        u"\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
        u"\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        u"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        u"\U0001FA00-\U0001FA6F"  # Chess Symbols
        u"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        u"\U00002702-\U000027B0"  # Dingbats
        u"\U000024C2-\U0001F251"  # Miscellaneous Symbols and Pictographs
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)


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
