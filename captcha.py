#!/usr/bin/python
import glob
import subprocess
import re
import csv
import os
import sys
import time
import json
from bs4 import BeautifulSoup
from pytesseract import *
import PIL
import selenium
import scipy as sp
from PIL import Image
from PIL import ImageFilter
from PIL import ImageEnhance
from scipy.misc import imread
from selenium import webdriver
from pyvirtualdisplay import Display
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

url = 'http://ceodelhi.gov.in/OnlineErms/electorsearchidcard.aspx'


def get_epic_from_txtFile(txtFile):

    epicNo = []

    pattern = '\s{0,1}[A-Z]{3}\d{7}|DL\/\d\d\/\d{3}\/\d{6}'

    with open(txtFile, 'r') as f:
        allData = f.readlines()

        for data in allData:
            if re.search(pattern, data):

                if (' ' in data):

                    try:
                        data = data.split(' ')[1]

                    except IndexError:
                        continue
                epicNo.append(data.strip('\n'))

    return epicNo


def get_img(img):

    data = imread(img)
    #Formula for Brightness index is dot product with RGB value divide by 1000
    data = sp.inner(data, [299, 587, 114]) / 1000.0
    return (data - data.mean()) / data.std()


def crop(infile, height, width):

    im = Image.open(infile)
    imgwidth, imgheight = im.size
    first_black = 28

    k = 0
    flag = 1
    for col in range(2, imgwidth - 2):
        rgb = ''
        for row in range(2, imgheight - 2):

            r, g, b = im.getpixel((col, row))

            if (r, g, b) == (128, 128, 128):
                rgb = rgb + "0"

            else:
                rgb = rgb + "1"
                first_black = col
                flag = 0
                break

        if flag == 0:
            break

    for i in range(imgheight // height):
        for j in range(first_black, imgwidth, width):
            if k > 3:
                break
            box = (j, i * height, j + width, (i + 1) * height)
            k = k + 1
            yield im.crop(box)


def get_details_from_epic(epic, txtfile):

    tmp_path = os.getcwd()
    # display = Display(visible=0, size=(800, 600))
    # display.start()
    txtFile = txtfile

    chromedriver = "../chromedriver"
    os.environ["webdriver.chrome.driver"] = chromedriver
    driver = webdriver.Chrome(chromedriver)

    driver.get(url)

    input_epic = driver.find_element_by_name(
        'ctl00$ContentPlaceHolder1$TextBoxIDCardNo')
    input_epic.send_keys(epic)

    capcha_textBox = driver.find_element_by_id(
        'ctl00_ContentPlaceHolder1_TextBoxcaptacha')

    # ----------- code to save screenshot and get capcha ----------------
    capcha_img = driver.find_element_by_id('ctl00_ContentPlaceHolder1_myImage')

    driver.save_screenshot(os.path.join(tmp_path, 'screenshot.png'))

    loc = capcha_img.location

    left = loc['x']
    right = loc['y']
    top = loc['x'] + 139
    bottom = loc['y'] + 30

    box = (left, right, top, bottom)
    img = Image.open(os.path.join(tmp_path, 'screenshot.png'))
    img = img.crop(box)

    img.save(os.path.join(tmp_path, "img_crop.png"))
    capchaText = read_from_cropped_capcha(os.path.join(
        tmp_path, 'img_crop.png'), epic, driver, txtFile)
    #--------------------------------------------------------------------

    capcha_textBox.send_keys(capchaText)

    xpath = ".//input[@type='submit' and @value='Search']"
    driver.find_element_by_xpath(xpath).click()

    try:
        WebDriverWait(driver, 3).until(EC.alert_is_present(),
                                       'Timed out waiting for PA creation ' +
                                       'confirmation popup to appear.')
        alert = driver.switch_to_alert()
        alert.accept()
        print "alert accepted"
        driver.quit()
        get_details_from_epic(epic, txtFile)

    except TimeoutException:
        print "no alert"

    soup = BeautifulSoup(driver.page_source, 'lxml')
    tr = soup.find(
        'table', attrs={
            'id': 'ctl00_ContentPlaceHolder1_GridViewSearchResult'}).findAll('tr')[1]
    all_data_td = tr.findAll('td')

    partNo = all_data_td[2].text
    section = all_data_td[4].text
    houseNo = all_data_td[5].text.strip('\n')
    houseNo = ' '.join(houseNo.split())
    name = all_data_td[6].text
    fatherOrhusband = all_data_td[8].text
    age = all_data_td[9].text
    sex = all_data_td[10].text
    EPICno = all_data_td[11].text

    with open(txtFile.strip('.txt') + '.csv', 'a') as f:
        writer = csv.writer(f)

        writer.writerow([EPICno, name, fatherOrhusband,
                         age, sex, houseNo, partNo, section])
    driver.quit()


def read_from_cropped_capcha(img, epic, driver, txtFile):

    img = Image.open(img)

    img.thumbnail((100, 100))
    img = img.convert('L')
    img = img.filter(ImageFilter.SHARPEN)

    sharpener = PIL.ImageEnhance.Sharpness(img)
    img = sharpener.enhance(0.8)

    contrast = PIL.ImageEnhance.Contrast(img)
    img = contrast.enhance(0.8)

    bright = PIL.ImageEnhance.Brightness(img)
    img = bright.enhance(0.8)

    img.show()

    text = image_to_string(img)
    print text
    try:
        text = int(text)
    except ValueError:
        print 'error getting capcha'

        driver.quit()
        get_details_from_epic(epic, txtFile)

    if len(str(text)) == 5:
        capcha_to_put = text
    else:
        print 'Capcha read wrong'
        driver.quit()
        get_details_from_epic(epic, txtFile)

    return text

# get_details_from_epic('ZIP1689123')
#---------------------------------MAIN-----------------------------

cwd = os.getcwd()

for directory in os.listdir(cwd):
    district = directory

    if os.path.isdir(os.path.join(cwd, directory)):

        if os.getcwd() != cwd:
            os.chdir(cwd + '/')

        os.chdir(directory + '/')
        for txtFile in glob.glob('*.txt'):

            list_of_epic = get_epic_from_txtFile(txtFile)
            print txtFile

            with open(txtFile.strip('.txt') + '.csv', 'wb') as f:

                writer = csv.writer(f)
                headers = [
                    'EPICno',
                    'name',
                    'father/husband name',
                    'age',
                    'sex',
                    'houseNo',
                    'partNo',
                    'section']
                writer.writerow(headers)

            for epic in list_of_epic:
                get_details_from_epic(epic, txtFile)
