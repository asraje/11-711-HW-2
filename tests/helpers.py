import tempfile
import unittest
from pathlib import Path

from cmu_rag.io import write_json


class TempCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def json(self, name, data):
        path = self.root / name
        write_json(path, data)
        return path


def chunk(identifier="1", text="Pittsburgh is named after William Pitt.", **kwargs):
    return {"id": identifier, "text": text, "title": "", "url": "https://example.org/" + identifier, **kwargs}
