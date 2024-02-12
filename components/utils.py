import re
import emoji


def remove_emojis(text):
    allchars = [str for str in text]
    emoji_list = [c for c in allchars if c in emoji.EMOJI_DATA]
    clean_text = ' '.join([str for str in text.split() if not any(i in str for i in emoji_list)])
    return clean_text


def remove_multiple_dots(text):
    result_str = re.sub(r'\.{2,}', '.', text)
    return result_str


def remove_code_blocks(text):
    pattern = r'```.*?```'
    return re.sub(pattern, '', text, flags=re.DOTALL)
