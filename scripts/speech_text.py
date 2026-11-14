# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 BT-7274 Voice Companion contributors

"""TTS-only pronunciation and streamed sentence boundaries; never edits chat text."""
import json
import re
import unicodedata
from pathlib import Path
import cn2an

ROOT = Path(__file__).resolve().parents[1]
LETTERS = dict(zip('abcdefghijklmnopqrstuvwxyz', [
    '诶', '比', '西', '迪', '伊', '艾弗', '吉', '艾尺', '爱', '杰', '开', '艾尔', '艾姆',
    '恩', '欧', '批', '丘', '阿尔', '艾斯', '提', '优', '维', '达布溜', '艾克斯', '外', '贼德']))
DIGITS = str.maketrans('0123456789', '零一二三四五六七八九')


def number_words(value):
    sign = '负' if value.startswith('-') else ''
    return sign + cn2an.an2cn(value.lstrip('+-'))


def normalize_for_speech(text):
    text = unicodedata.normalize('NFKC', text).replace(',', '，')
    # Level is a term, not five spelled-out letters. Match before generic Latin.
    text = re.sub(r'(?<![A-Za-z0-9_])level\s*([0-9]+|[零一二三四五六七八九十]+)(?![A-Za-z0-9_])',
                  lambda m: (number_words(m[1]) if m[1].isdigit() else m[1]) + '级', text, flags=re.I)
    text = re.sub(r'(?<![A-Za-z0-9_])L([123])(?![A-Za-z0-9_])',
                  lambda m: number_words(m[1]) + '级', text, flags=re.I)
    text = re.sub(r'(?<![A-Za-z])v(?=\d+\.)', '版本', text, flags=re.I)
    text = re.sub(r'(?<![\d.])\d+(?:\.\d+){2,}(?![\d.])',
                  lambda m: '点'.join(x.translate(DIGITS) for x in m[0].split('.')), text)
    text = re.sub(r'(-?\d+(?:\.\d+)?)\s*%',
                  lambda m: '百分之' + number_words(m[1]), text)
    text = re.sub(r'(?<![A-Za-z0-9_])(-\d+(?:\.\d+)?)', lambda m: number_words(m[1]), text)
    terms = json.loads((ROOT / 'config/pronunciations.json').read_text(encoding='utf-8'))
    for word in sorted(terms, key=len, reverse=True):
        text = re.sub(r'(?<![A-Za-z0-9_])' + re.escape(word) + r'(?![A-Za-z0-9_])',
                      lambda m, replacement=terms[word]: replacement, text, flags=re.I)
    # The original Chinese model cannot pronounce arbitrary English words.
    # Keep an honest spelling fallback and record it for later dictionary additions.
    unknown = re.findall(r'[A-Za-z]+', text)
    text = re.sub(r'[A-Za-z]', lambda m: LETTERS[m[0].lower()], text)
    text = re.sub(r'[*_`#<>]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text, sorted(set(unknown), key=str.casefold)


def spoken_text(text):
    return normalize_for_speech(text)[0]


def segment_complete_sentences(text):
    """Wait for full Chinese sentences; do not break streamed decimals/version IDs.

    A trailing ASCII period waits for the next token (or the upstream final flush),
    because a later token might turn '0.' into '0.8'. Quotes stay with the sentence.
    """
    sentences = []
    start = 0
    i = 0
    while i < len(text):
        char = text[i]
        ending = char in '。！？!?'
        if char == '.' and i + 1 < len(text):
            # Treat numeric/version dots and abbreviations as part of the sentence.
            prev = text[i - 1] if i else ''
            nxt = text[i + 1]
            ending = not (prev.isdigit() and nxt.isdigit()) and not (prev.isalpha() and nxt.isalpha())
        if ending:
            end = i + 1
            while end < len(text) and text[end] in '。！？!?….”’」』）)]':
                end += 1
            piece = text[start:end].strip()
            if piece:
                sentences.append(piece)
            start = end
            i = end
        else:
            i += 1
    return sentences, text[start:].strip()
