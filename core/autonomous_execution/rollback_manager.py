import os
from typing import List, Dict


class RollbackManager:
    """
    Creates file checkpoints and restores them if an execution failure occurs.
    """

    def __init__(self, graph=None):
        self.graph = graph
        self.backups: Dict[str, bytes] = {}

    def create_checkpoint(self, files: List[str]) -> None:
        self.backups.clear()
        for f in files:
            abs_path = os.path.abspath(f)
            if os.path.exists(abs_path):
                try:
                    with open(abs_path, "rb") as fh:
                        self.backups[abs_path] = fh.read()
                except Exception:
                    pass

    def rollback(self) -> None:
        for path, content in self.backups.items():
            try:
                with open(path, "wb") as fh:
                    fh.write(content)
            except Exception:
                pass
