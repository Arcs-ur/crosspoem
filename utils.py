import opencc
import random

def convert_to_simplified(text):
    """将文本转换为简体中文"""
    converter = opencc.OpenCC('t2s')
    return converter.convert(text)

def convert_to_traditional(text):
    """将文本转换为繁体中文"""
    converter = opencc.OpenCC('s2t')
    return converter.convert(text)

def get_random_poem(poems):
    """从诗句列表中随机选择一首"""
    return random.choice(poems) if poems else None