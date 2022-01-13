import os
import zipfile
import shutil


import io

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from pdfminer.high_level import extract_text


def convert_pdf_to_txt(path):
    rsrcmgr = PDFResourceManager()
    retstr = io.StringIO()
    codec = 'utf-8'
    laparams = LAParams()
    device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
    fp = open(path, 'rb')
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    password = ""
    maxpages = 0
    caching = True
    pagenos = set()

    for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages,
                                  password=password,
                                  caching=caching,
                                  check_extractable=True):
        interpreter.process_page(page)

    fp.close()
    device.close()
    text = retstr.getvalue()
    retstr.close()
    return text


source_dir = os.path.dirname(os.path.realpath(__file__))
dir_name = os.path.join(source_dir, 'unzipped')
print('unzippiing into {}'.format(dir_name))
extension = ".zip"

shutil.rmtree(dir_name)
if not os.path.exists(dir_name):
    os.mkdir(dir_name)
# os.chdir(dir_name) # change directory from working dir to dir with files
for item in os.listdir(source_dir):  # loop through items in dir
    print("processing ", item)
    if item.endswith(extension):  # check for ".zip" extension
        print("processing ", item)
        file_name = os.path.abspath(item)  # get full path of files
        zip_ref = zipfile.ZipFile(file_name)  # create zipfile object
        zip_ref.extractall(dir_name)  # extract file to dir
        zip_ref.close()  # close file

for pdfFile in os.listdir(dir_name):
    print('-------')
    print(extract_text(os.path.join(dir_name, pdfFile)))
    print('-------')