import os
import glob
import re
from typing import Dict, List, Optional, Tuple
from src.utils.logger import setup_logging
from src.config import DATA_DIR

logger = setup_logging()

class LibraryDataManager:
    """
    Verwaltet den Zugriff auf die Markdown-Bibliothek (Regeln, Items, etc.).
    Scannt Verzeichnisse und ermöglicht die Suche nach Dateien.
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
        """Gibt alle Markdown-Dateien in einer Kategorie zurück."""
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
        """Leert den Cache, damit beim nächsten Zugriff neu gescannt wird."""
        self._file_cache.clear()

    def search_file(self, name: str) -> Optional[Tuple[str, str]]:
        """
        Sucht nach einer Datei in allen Kategorien.
        Gibt (Kategorie, Dateipfad) zurück oder None.
        """
        # Falls der Name einen Pfad enthält (z.B. "Ordner/Datei"), nur den Dateinamen nehmen
        if "/" in name:
            name = name.split("/")[-1]
        if "\\" in name:
            name = name.split("\\")[-1]

        # 1. Versuch: Exakte Suche
        result = self._perform_search(name)
        if result: return result

        # 2. Versuch: Ohne Suffix in Klammern (z.B. "Bandit (Boss)" -> "Bandit")
        clean_name = re.sub(r'\s*\([^)]+\)\s*$', '', name).strip()
        if clean_name and clean_name != name:
            result = self._perform_search(clean_name)
            if result: return result

        # 3. Versuch: Teilstring-Suche (Fallback)
        if clean_name and clean_name != name:
             result = self._perform_search_partial(clean_name)
             if result: return result

        # 4. Versuch: Teilstring-Suche mit Originalnamen
        result = self._perform_search_partial(name)
        if result: return result

        return None

    def _perform_search(self, name: str) -> Optional[Tuple[str, str]]:
        """Sucht nach exaktem Dateinamen (ohne Extension)."""
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
        """Sucht nach Teilstring im Dateinamen."""
        name_lower = name.lower()
        for category, root_dir in self.dirs.items():
            files = self.get_files_in_category(category)
            for filepath in files:
                filename = os.path.basename(filepath)
                display_name = os.path.splitext(filename)[0]
                if name_lower in display_name.lower():
                    return category, filepath
        return None

