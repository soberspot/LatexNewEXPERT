from PyPDF2 import PdfReader, PdfFileWriter, PdfFileReader

input_pdf = PdfFileReader(open('1086.pdf', 'rb'))
for i in range(input_pdf.getNumPages()):
    output = PdfFileWriter()
    output.addPage(input_pdf.getPage(i))
    with open(f'output_{i}.pdf', 'wb') as output_pdf:
        output.write(output_pdf)




