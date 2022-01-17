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
import datetime

import re

regex = r"INVOICE #[\s]+DATE[\s]+DUE DATE[\s]+TOTAL AMOUNT[\s]+TOTAL DUE[\s]+(\b[A-Z][\d]+)[\s]+\w{3}\s\d{1,2},\s\d{4}[\s]+(\w{3}\s\d{1,2},\s\d{4})[\s]+\$\d+\.\d{2}[\s]+\$(\d+\.\d{2})"
regex_one = r"Bill to:([\s\w\W\d]+)I N V O I C E[\s]+" + regex
regex_two = r"Service Fee[\w\d\s\W]+Amount: \$([\d]+.[\d]+) USD x[\w\d\s\W]+Notes: Invoice from Upwork for ([A-Z][\d]+)[\w\d\s\W]+" + regex


def process_first_invoice(invoice_text):
    '''
    returns (customer_info, invoice_id, date string, amount) on sucess,
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
    returns (total_amount, first_invoice, related_invoice_id, date string, fee_amount) on sucess,
    None otherwise 
    '''
    matches = re.finditer(regex_two, invoice_text, re.MULTILINE)
    count = 0
    result = []
    for match in matches:
        count += 1
        result.append(match.group(1,2,3,4,5))
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

def convert_to_date_obj(date_string):
    return datetime.datetime.strptime(date_string, '%b %d, %Y')

def date_obj_to_string(date_obj):
    return date_obj.strftime('%d.%m.%Y')

def convert_date_string(date_string):
    date_obj = datetime.datetime.strptime(date_string, '%b %d, %Y')
    return date_obj.strftime('%d.%m.%Y')

def get_usd_rate_on_data(date_string):
    date_obj = datetime.datetime.strptime(date_string, '%b %d, %Y')
    iso_date_str = date_obj.date().isoformat()
    # print("date for rate: ", iso_date_str)
    r = requests.get(
        "https://www.nbrb.by/api/exrates/rates/usd?parammode=2&ondate={}".format(iso_date_str))
    if r.status_code == requests.codes.ok:
        return float(r.json()["Cur_OfficialRate"])
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

first_records = []
second_records = []

for pdfFile in os.listdir(dir_name):
    invoice_text = extract_text(os.path.join(dir_name, pdfFile))
    res_sec = process_second_invoice(invoice_text)
    if res_sec:
        # print("processed second ", res_sec)
        date_str = res_sec[3]
        rate = get_usd_rate_on_data(date_str)
        # print("rate second: ", rate)
        second_records.append((
            res_sec[0],
            res_sec[1], res_sec[2], 
            convert_to_date_obj(res_sec[3]),  res_sec[4], rate))
        # print('-------')
        # print(invoice_text)
        # print('-------')
    else:
        res_first = process_first_invoice(invoice_text)
        # print("processed first ", res_first)
        rate = get_usd_rate_on_data(res_first[2])
        # print("rate first", rate)
        customer_info = re.sub(r"\s+", ' ', res_first[0])
        customer_info = re.sub(r",", '', customer_info)
        first_records.append((
            customer_info,
            res_first[1],
            convert_to_date_obj(res_first[2]), res_first[3], rate))

if len(first_records) > len(second_records):
    print("got more of 1st invoices ")
elif len(first_records) < len(second_records):
    print("got more of 2nd invoices")
else:
    print("all invoices are matched")
# print(first_records[-1])
# print(second_records[-1])

first_records = sorted(first_records, key=lambda rec: rec[2] )

# print('first')

second_records = sorted(second_records, key=lambda rec: rec[3] )
# print('second ')

# print required strings 
for rec in first_records:
    byn = float(rec[3])*float(rec[4])
    print(
        date_obj_to_string(rec[2]), ";",
        rec[1] + " " + rec[0], ";",
        round(byn, 2), ";",
        "USD", ";",
        rec[4])