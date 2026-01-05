import json
import os
from functools import reduce
from src.config.defaults import DEFAULT_LANGUAGE
from src.models.enums import Language

class Localization:
    def __init__(self, language_code=None):
        self.translations = {}
        if language_code is None:
            language_code = DEFAULT_LANGUAGE
        self.language_code = language_code
        self.load_translations()

    def load_translations(self):
        # Correctly construct the path to the i18n directory
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        i18n_dir = os.path.join(base_dir, '..', 'data', 'i18n')
        file_path = os.path.join(i18n_dir, f'{self.language_code}.json')
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
        except FileNotFoundError:
            print(f"Warning: Language file not found for {self.language_code}, falling back to default.")
            # If the requested language is not found, try falling back to English
            if self.language_code != Language.ENGLISH.value:
                self.set_language(Language.ENGLISH.value)
            else:
                self.translations = {}
        except json.JSONDecodeError:
            print(f"Warning: Could not decode language file for {self.language_code}.")
            self.translations = {}

    def set_language(self, language_code: str):
        """Sets a new language and reloads the translations."""
        self.language_code = language_code
        self.load_translations()

    def get(self, key, **kwargs):
        """
        Retrieves a translation string by a nested key (e.g., 'dialog.title.confirm').
        Formats the string with any provided keyword arguments.
        """
        try:
            # Use reduce to navigate the nested dictionary
            template = reduce(lambda d, k: d[k], key.split('.'), self.translations)
        except (KeyError, TypeError):
            template = key # Fallback to the key itself

        # If there are keyword arguments, format the string
        if kwargs and isinstance(template, str):
            try:
                return template.format(**kwargs)
            except KeyError as e:
                print(f"Warning: Missing placeholder in translation for key '{key}': {e}")
                return template # Return the unformatted template as a fallback
        
        return template

# Global instance
localization_manager = Localization()

def translate(key, **kwargs):
    return localization_manager.get(key, **kwargs)
