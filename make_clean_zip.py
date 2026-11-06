"""Makes a zip that is safe to share:   python make_clean_zip.py

Leaves out .env, .venv, .git and caches. Refuses to run if a key is found inside a code file."""
import sys
import zipfile
from datetime import date
from pathlib import Path

import check_before_sharing as guard

ROOT = Path(__file__).resolve().parent
EXCLUDED_DIRS = {".venv", "venv", ".git", "__pycache__", ".pytest_cache", "node_modules", "shareable"}


def should_include(path, root):
    parts = path.relative_to(root).parts
    if any(part in EXCLUDED_DIRS for part in parts[:-1]):
        return False
    return not guard.is_secret_env_file(path) and path.suffix != ".pyc"


def build_zip(root=ROOT, out_path=None):
    """Returns the path of the zip. Raises RuntimeError if anything unsafe would be included."""
    root = Path(root)
    keys = guard.find_keys_in_code(root)
    if keys:
        raise RuntimeError("Not creating the zip: a key was found in " + ", ".join(name for name, _ in keys))
    out_path = Path(out_path) if out_path else root / "shareable" / f"{root.name}_{date.today():%Y%m%d}.zip"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(root.rglob("*")):
            if path.is_file() and path != out_path and should_include(path, root):
                archive.write(path, (Path(root.name) / path.relative_to(root)).as_posix())
    with zipfile.ZipFile(out_path) as archive:          # double-check what we just made
        bad = [n for n in archive.namelist() if guard.is_secret_env_file(Path(n)) or "/.venv/" in n]
    if bad:
        out_path.unlink()
        raise RuntimeError("The zip would have contained: " + ", ".join(bad))
    return out_path


def main():
    try:
        out = build_zip()
    except RuntimeError as problem:
        print("PROBLEM  " + str(problem))
        return 1
    print("Created: " + str(out))
    print("It does not contain your .env file or your .venv folder.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
