from pathlib import Path
from typing import List, Union
import sys

from rapidocr_pdf import PDFExtracter
from ..splitter.text_splitter import ChineseTextSplitter


class PDFLoader:
    def __init__(
        self,
    ):
        self.extracter = PDFExtracter()
        self.splitter = ChineseTextSplitter(pdf=True)

    def __call__(self, pdf_path: Union[str, Path]) -> List[str]:
        contents = self.extracter(pdf_path)
        split_contents = [self.splitter.split_text(v[1]) for v in contents]
        return sum(split_contents, [])
        
if __name__ == "__main__":
    loader = PDFLoader()
    print(sys.argv)
    sum = loader(pdf_path=sys.argv[1])
    # sum = loader(pdf_path="./test_0915.pdf")
    print(len(sum))