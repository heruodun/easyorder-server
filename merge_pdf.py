import fitz  # PyMuPDF


def merge_pdfs(paths, output):
    pdf_writer = fitz.open()
    for path in paths:
        pdf_reader = fitz.open(path)
        pdf_writer.insert_pdf(pdf_reader)
        pdf_reader.close()
    pdf_writer.save(output)
    pdf_writer.close()


if __name__ == '__main__':
    paths = ['C:\\Users\\Administrator\\Desktop\\33030123-4934395285.pdf', 'C:\\Users\\Administrator\\Desktop\\1.pdf', 'C:\\Users\\Administrator\\Desktop\\2.pdf']
    output = 'merged.pdf'  # 输出的PDF文件名
    merge_pdfs(paths, output)

