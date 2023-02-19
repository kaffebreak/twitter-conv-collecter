import re
from xml.sax.saxutils import unescape


def sentence(sentence):
    if sentence is None:
        return ''

    # 特殊文字デコード
    sentence = unescape(sentence)

    # ユーザー名削除
    sentence = re.sub(r'@[0-9a-zA-Z_:]*', "", sentence)

    # ハッシュタグ削除
    sentence = re.sub(r'#.*', "", sentence)

    # URL削除
    sentence = re.sub(
        r'(https?)(:\/\/[-_.!~*\'()a-zA-Z0-9;\/?:\@&=+\$,%#]+)', "", sentence)

    return sentence
