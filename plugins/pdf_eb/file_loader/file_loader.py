from .pdf_loader import PDFLoader
import os

class FileLoader:
    def __init__(self):
        self.pdf_loader = PDFLoader()

    def __call__(self, path):
        all_content = {}
        filename = os.path.basename(path)
        all_content[filename] = self.pdf_loader(path)
        return all_content