# Сначала импортируем необходимые классы и библиотеки
from pathlib import Path
from PyPDF2 import PdfFileMerger

# Создаем объект Path, который содержит путь до нужного файла.
# На вашем компьютере он может быть другим
# BASE_PATH = (
    # Path.home()
    # / "creating-and-modifying-pdfs"
    # / "practice_files"
# )

# pdf_paths = [BASE_PATH / "merge1.pdf", BASE_PATH / "merge2.pdf"]
pdf_paths = ["1086.pdf", "1086.pdf"]
pdf_merger = PdfFileMerger()

for path in pdf_paths:
    pdf_merger.append(str(path)) 
    for path in pdf_paths: pdf_merger.append(str(path))

    output_path = Path.home() / "concatenated.pdf"
with output_path.open(mode="wb") as output_file:
    pdf_merger.write(output_file)