import os
import glob
import re
from typing import Dict, List, Optional, Tuple
from src.utils.logger import setup_logging
from src.config import DATA_DIR

logger = setup_logging()

class LibraryDataManager:
    """
    Manages access to the Markdown library (rules, items, etc.).
    Scans directories and allows searching for files.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LibraryDataManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # Ensure default directories exist
        default_folders = ["rules", "items", "enemies"]
        for folder in default_folders:
            path = os.path.join(DATA_DIR, folder)
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)

        # Dynamic scanning of directories in DATA_DIR
        self.dirs = {}
        if os.path.exists(DATA_DIR):
            for entry in os.scandir(DATA_DIR):
                if entry.is_dir():
                    self.dirs[entry.name] = entry.path

        self._file_cache: Dict[str, List[str]] = {}

        self._initialized = True

    def get_category_dir(self, category: str) -> Optional[str]:
        return self.dirs.get(category)

    def get_files_in_category(self, category: str) -> List[str]:
        """Returns all Markdown files in a category."""
        if category in self._file_cache:
            return self._file_cache[category]

        root_dir = self.dirs.get(category)
        if not root_dir or not os.path.exists(root_dir):
            return []

        files = glob.glob(os.path.join(root_dir, "**/*.md"), recursive=True)
        files.sort()
        self._file_cache[category] = files
        return files

    def refresh_cache(self):
        """Clears the cache, so the next access will re-scan."""
        self._file_cache.clear()

    def search_file(self, name: str) -> Optional[Tuple[str, str]]:
        """
        Searches for a file in all categories.
        Returns (category, filepath) or None.
        """
        # If the name contains a path (e.g., "Folder/File"), only take the filename
        if "/" in name:
            name = name.split("/")[-1]
        if "\\" in name:
            name = name.split("\\")[-1]

        # 1. Attempt: Exact search
        result = self._perform_search(name)
        if result: return result

        # 2. Attempt: Without suffix in parentheses (e.g., "Bandit (Boss)" -> "Bandit")
        clean_name = re.sub(r'\s*\([^)]+\)\s*$', '', name).strip()
        if clean_name and clean_name != name:
            result = self._perform_search(clean_name)
            if result: return result

        # 3. Attempt: Substring search (fallback)
        if clean_name and clean_name != name:
             result = self._perform_search_partial(clean_name)
             if result: return result

        # 4. Attempt: Substring search with original name
        result = self._perform_search_partial(name)
        if result: return result

        # 5. Attempt: Content search (if the name appears in a file)
        result = self._perform_content_search(name)
        if result: return result

        # 6. Attempt: Content search with cleaned name (without suffix)
        if clean_name and clean_name != name:
            result = self._perform_content_search(clean_name)
            if result: return result

        return None

    def _perform_search(self, name: str) -> Optional[Tuple[str, str]]:
        """Searches for exact filename (without extension)."""
        name_lower = name.lower()
        for category, root_dir in self.dirs.items():
            files = self.get_files_in_category(category)
            for filepath in files:
                filename = os.path.basename(filepath)
                display_name = os.path.splitext(filename)[0]
                if display_name.lower() == name_lower:
                    return category, filepath
        return None

    def _perform_search_partial(self, name: str) -> Optional[Tuple[str, str]]:
        """Searches for substring in filename."""
        name_lower = name.lower()
        for category, root_dir in self.dirs.items():
            files = self.get_files_in_category(category)
            for filepath in files:
                filename = os.path.basename(filepath)
                display_name = os.path.splitext(filename)[0]
                if name_lower in display_name.lower():
                    return category, filepath
        return None

    def _perform_content_search(self, name: str) -> Optional[Tuple[str, str]]:
        """
        Searches for the occurrence of a name in the contents of the files.
        Returns the first file found that contains the name in its content.
        """
        name_lower = name.lower()
        for category, root_dir in self.dirs.items():
            files = self.get_files_in_category(category)
            for filepath in files:
                try:
                    with open(filepath, 'r', encoding='utf-8') as file:
                        content = file.read()
                        if name_lower in content.lower():
                            return category, filepath
                except Exception as e:
                    logger.warning(f"Error reading file {filepath}: {e}")
        return None
