import re


def normalize_xml_token(token):
    return re.sub(r'[^\S]', ' ', token).replace('  ', ' ').strip()
