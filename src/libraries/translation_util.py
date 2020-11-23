from googletrans import Translator

translator = Translator()

def translate_text_to(text_to_translate: str, language_to: str, language_from: str = None):
    if language_from:
        translation = translator.translate(text_to_translate, dest=language_to, src=language_from)
    else:
        translation = translator.translate(text_to_translate, dest=language_to)
    return translation


def pretty_translate(text_to_translate: str, language_to: str, language_from: str = None):
    translation = translate_text_to(text_to_translate, language_to, language_from)
    text = translation.text
    language_src = language_from if language_from is not None else translation.src
    message = "From <b>" + language_src + "</b>:\n" + text
    return message


if __name__ == '__main__':
    language = "en"
    text_to_translate = "J'espère que ça va marcher !"
    translation = pretty_translate(text_to_translate, language)
    print(translation)

