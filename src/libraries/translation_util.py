import translators as ts
from TextToOwO.owo import text_to_owo


def translate_text_to(text_to_translate: str, language_to: str, language_from: str = None):
    correct_language_to = language_to
    if language_to == "cn":
        correct_language_to = "zh-CN"

    if language_from:
        translation = ts.google(query_text=text_to_translate, from_language=language_from, to_language=correct_language_to, is_detail_result=True)
    else:
        translation = ts.google(query_text=text_to_translate, to_language=correct_language_to, is_detail_result=True)
    return translation


def text_to_clap(text_to: str):
    return '👏'.join(text_to.split(' '))

def pretty_translate(text_to_translate: str, language_to: str, language_from: str = None):
    if language_to.lower() == "owo" or language_to.lower() == "uwu":
        return text_to_owo(text_to_translate)
    elif language_to.lower() == "clap":
        return text_to_clap(text_to_translate)
    elif language_to.lower() == "yell" or language_to.lower() == "yelling":
        return text_to_translate.upper()
    translation = translate_text_to(text_to_translate, language_to, language_from)
    txt = translation[0][0][0]
    language_src = language_from if language_from is not None else translation[2]
    message = "From <b>" + language_src + "</b>:\n" + txt
    return message


if __name__ == '__main__':
    language = "uwu"
    text_to_translate = "Oh darling isn't it wonderful?"
    translation = pretty_translate(text_to_translate, language)
    # translation = pretty_translate(text_to_translate, language)
    # translation = pretty_translate(text_to_translate, language)
    # translation = pretty_translate(text_to_translate, language)
    # translation = pretty_translate(text_to_translate, language)
    # translation = pretty_translate(text_to_translate, language)
    # translation = pretty_translate(text_to_translate, language)
    # translation = pretty_translate(text_to_translate, language)
    # translation = pretty_translate(text_to_translate, language)
    # translation = pretty_translate(text_to_translate, language)
    # translation = pretty_translate(text_to_translate, language)
    # translation = pretty_translate(text_to_translate, language)
    print(translation)

