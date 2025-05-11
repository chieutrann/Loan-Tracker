from googletrans import Translator




def auto_translate(text, target_lang, translation_dict):
    translator = Translator()
    if target_lang == "en":
        return text
    if text in translation_dict:
        return translation_dict[text]
    try:
        translated = translator.translate(text, dest=target_lang).text
        translation_dict[text] = translated
        return translated
    except Exception as e:
        print(f"Translation error for '{text}': {e}")
        return text