from models import Language, Translation, DictionaryEntry
import requests
# import secret
import sys
import json
import os
# from secret import GOOGLE_LANGUAGE_KEY, WORDS_API_KEY

# GOOGLE_LANGUAGE_KEY = os.environ.get('GOOGLE_LANGUAGE_KEY')
# WORDS_API_KEY = os.environ.get('WORDS_API_KEY')


def query_translation_api(source_word, source_code, translate_code):
    API_BASE_ULR = 'https://translation.googleapis.com/language/translate/v2'
    API_KEY = os.environ.get('GOOGLE_LANGUAGE_KEY')
    # API_KEY = GOOGLE_LANGUAGE_KEY

    url = f"{API_BASE_ULR}?key={API_KEY}"
    headers = {'Content-Type': 'application/json'}
    params = {
        "q": source_word,
        "source": source_code,
        "target": translate_code
    }

    response = requests.post(url, params=params, headers=headers)
    data = response.json()['data']
    translations = data['translations']
    return translations[0]['translatedText']


def query_dictionary_api(word):
    API_BASE_ULR = 'https://wordsapiv1.p.rapidapi.com/words'
    API_KEY = os.environ.get('WORDS_API_KEY')
    # API_KEY = WORDS_API_KEY

    url = f"{API_BASE_ULR}/{word}"
    headers = {
        'x-rapidapi-host': 'wordsapiv1.p.rapidapi.com',
        'x-rapidapi-key': API_KEY
    }

    response = requests.get(url, headers=headers)
    data = response.json()
    return data


class TranslationWord:
    """Model to handle user interactions with a particular word to be translated."""

    def __init__(self, source_word, source_code, translate_code='en'):
        """Create a word instance."""

        self.source_code = source_code
        self.translate_code = translate_code
        self.source_word = source_word
        self.translated_word = self.get_translation()

    def get_translation(self):
        """Get translations from API or database."""

        existing_translation = Translation.get_by_source_word(
            self.source_code, self.translate_code, self.source_word)

        if existing_translation == None:

            api_translation = query_translation_api(
                self.source_word, self.source_code, self.translate_code)

            new_translation = Translation.add_translation(
                self.source_code, self.translate_code, self.source_word, api_translation)
            print(f"NEW: {new_translation}", file=sys.stderr)

            return new_translation.translated_word

        else:
            print(f"EXISTING: {existing_translation}", file=sys.stderr)
            return existing_translation.translated_word


class DictionaryWord:
    """Model to handle user interactions with a particular word to be dictionary searched."""

    def __init__(self, word, language_code='en'):
        """Create a word instance."""

        self.word = word
        self.language_code = language_code
        self.definitions = self.get_dictionary_entry()

    def get_dictionary_entry(self):
        """Get dictionary entries from API or database."""

        existing_entry = DictionaryEntry.get_by_word(
            self.language_code, self.word)

        if existing_entry == None:

            api_dictionary = query_dictionary_api(self.word)
            # print(f"NEW API: {api_dictionary}", file=sys.stderr)

            new_dictionary = DictionaryEntry.add_dictionary_entry(
                self.language_code, self.word, json.dumps(api_dictionary))
            print(f"NEW DB: {new_dictionary}", file=sys.stderr)

            return new_dictionary.definitions

        else:
            print(f"EXISTING: {existing_entry}", file=sys.stderr)
            return existing_entry.definitions
