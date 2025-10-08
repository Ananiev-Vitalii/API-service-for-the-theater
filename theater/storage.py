from __future__ import annotations
from pathlib import Path
from typing import Iterable
from django.core.files.storage import FileSystemStorage
from django.db import transaction


TRASH_FILES: tuple[str, ...] = (
    "Thumbs.db",
    "desktop.ini",
    ".DS_Store",
    ".ds_store",
    ".gitkeep",
)


def _prune_empty_dirs(
    start: Path, root: Path, trash: Iterable[str] = TRASH_FILES
) -> None:

    try:
        cur = start.parent.resolve()
        root = root.resolve()
    except Exception:
        return

    while True:
        if cur == root or not cur.exists() or not cur.is_dir():
            break

        for name in trash:
            tp = cur / name
            if tp.exists():
                try:
                    tp.unlink()
                except Exception:
                    pass

        try:
            cur.rmdir()
        except OSError:
            break

        cur = cur.parent


class PruningFileSystemStorage(FileSystemStorage):

    def delete(self, name):

        try:
            file_path = Path(self.path(name))
            root = Path(self.location)
        except Exception:
            file_path = None
            root = None

        super().delete(name)

        if not file_path or not root:
            return

        def _run():
            _prune_empty_dirs(file_path, root)

        try:
            transaction.on_commit(_run)
        except Exception:
            _run()
