"""
Adds YAML frontmatter tags to all .md files based on their folder structure.
Tags are derived from the subfolder path between the category root and the file.

Example:
  enemies/Chaoswesen/Boss/Chaosritter.md  →  tags: Chaoswesen, Boss
  dm_notes/Geschichte - Söldner/...       →  tags: Geschichte - Söldner, ...

Existing frontmatter is preserved; only the 'tags' field is updated.
Files without subfolder depth (directly in category root) are skipped.

Usage:
  python scripts/add_frontmatter_tags.py [--dry-run]
"""

import glob
import io
import os
import sys

# Force UTF-8 output on Windows consoles
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
CATEGORIES = [
    "enemies", "dm_notes", "npcs", "items",
    "locations", "organizations", "gods", "backstories", "dm_tools",
]


def get_tags(filepath: str, cat_root: str) -> list:
    """Returns folder-based tags for a file."""
    parent = os.path.dirname(filepath)
    rel = os.path.relpath(parent, cat_root)
    if rel == ".":
        return []
    parts = rel.replace("\\", "/").split("/")
    return [p.strip() for p in parts if p and not p.startswith(".")]


def update_tags_in_content(content: str, tags_str: str) -> str:
    """Inserts or replaces the 'tags' field in YAML frontmatter."""
    if content.startswith("---"):
        end = content.find("\n---", 3)
        if end != -1:
            fm_lines = [
                line for line in content[3:end].splitlines()
                if not line.lower().startswith("tags:")
            ]
            fm_lines.append(f"tags: {tags_str}")
            body = content[end + 4:].lstrip("\n")
            return "---\n" + "\n".join(fm_lines) + "\n---\n\n" + body
    # No frontmatter yet — prepend a new block
    return f"---\ntags: {tags_str}\n---\n\n{content}"


def already_has_tags(content: str, tags_str: str) -> bool:
    """Returns True if the file already has the exact tags we'd write."""
    if not content.startswith("---"):
        return False
    end = content.find("\n---", 3)
    if end == -1:
        return False
    fm_block = content[3:end]
    for line in fm_block.splitlines():
        if line.lower().startswith("tags:"):
            existing = line.split(":", 1)[1].strip()
            return existing == tags_str
    return False


def main(dry_run: bool = False):
    changed = skipped = errors = 0

    for cat in CATEGORIES:
        cat_root = os.path.normpath(os.path.join(DATA_DIR, cat))
        if not os.path.exists(cat_root):
            continue

        for filepath in sorted(glob.glob(os.path.join(cat_root, "**", "*.md"), recursive=True)):
            tags = get_tags(filepath, cat_root)
            if not tags:
                skipped += 1
                continue

            tags_str = ", ".join(tags)

            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                print(f"  ERROR reading {filepath}: {e}")
                errors += 1
                continue

            if already_has_tags(content, tags_str):
                skipped += 1
                continue

            rel = filepath.replace(os.path.normpath(DATA_DIR), "").lstrip("/\\")
            print(f"  [{tags_str}]  {rel}")

            if not dry_run:
                new_content = update_tags_in_content(content, tags_str)
                try:
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    changed += 1
                except Exception as e:
                    print(f"  ERROR writing {filepath}: {e}")
                    errors += 1
            else:
                changed += 1  # count as "would change"

    label = "Would update" if dry_run else "Updated"
    print(f"\n{'[DRY RUN] ' if dry_run else ''}{label}: {changed}, skipped: {skipped}, errors: {errors}")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    main(dry_run=dry_run)
