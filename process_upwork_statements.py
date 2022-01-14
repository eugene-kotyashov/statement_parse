import os
import zipfile
import shutil
import requests


import io

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from pdfminer.high_level import extract_text

import re

regex = r"INVOICE #[\s]+DATE[\s]+DUE DATE[\s]+TOTAL AMOUNT[\s]+TOTAL DUE[\s]+(\b[A-Z][\d]+)[\s]+\w{3}\s\d{1,2},\s\d{4}[\s]+(\w{3}\s\d{1,2},\s\d{4})[\s]+\$\d+\.\d{2}[\s]+\$(\d+\.\d{2})"
regex_one = r"Bill to:([\s\w\W\d]+)I N V O I C E[\s]+" + regex
regex_two = r"Service Fee[\w\d\s\W]+Notes: Invoice from Upwork for ([A-Z][\d]+)[\w\d\s\W]+" + regex


def process_first_invoice(invoice_text):
    '''
    returns (invoic_id, date string, amount) on sucess,
    None otherwise 
    '''
    matches = re.finditer(regex_one, invoice_text, re.MULTILINE)
    count = 0
    result = []
    for match in matches:
        count += 1
        result.append(match.group(1,2,3,4))
    if count == 0: 
        return None
    return result[0]

def process_second_invoice(invoice_text):
    '''
    returns (invoic_id, date string, amount) on sucess,
    None otherwise 
    '''
    matches = re.finditer(regex_two, invoice_text, re.MULTILINE)
    count = 0
    result = []
    for match in matches:
        count += 1
        result.append(match.group(1,2,3,4))
    if count == 0: 
        return None
    return result[0]
    


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


def get_usd_rate_on_data(date_string):
    r = requests.get("https://www.nbrb.by/api/exrates/rates/usd?parammode=2&{}".format(date_string))
    if r.status_code == requests.codes.ok:
        return r.json()
    else: 
        return None


source_dir = os.path.dirname(os.path.realpath(__file__))
dir_name = os.path.join(source_dir, 'unzipped')
print('unzippiing into {}'.format(dir_name))
extension = ".zip"

if os.path.exists(dir_name):
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
    invoice_text = extract_text(os.path.join(dir_name, pdfFile))
    # print(invoice_text)
    print('-------')
    res_sec = process_second_invoice(invoice_text)
    if res_sec:
        print("processed second ", res_sec)
    else:
        print("processed first ", process_first_invoice(invoice_text))


#print(get_usd_rate_on_data('2021-11-01'))