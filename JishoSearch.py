# libraries
from bs4 import BeautifulSoup

import lxml
import os
import requests
import string
import xlwt
import re

# global variable(s)
pageNum = 0
options = ""

# asks user for desired  options, handles input error
def getJlptoptions():
    options = input("Please enter options (JLPT N5-1, joyo, or jinmeyo): ")
    while(not isValidInput(options)):
        print(f"ERROR: \"{options}\" is an invalid input\n")
        options = input("Please enter options: ")
    return(options)

# checking if proper options
VALID_OPTIONS = {'N5', 'N4', 'N3', 'N2', 'N1', 'common', 'joyo', 'jinmeyo'}

def isValidInput(options):
    return options in VALID_OPTIONS

# checking if proper word options
def isValidWord(options):
    if(isValidJLPT(options) or options=="common"):
        return True
    else:
        return False
    
def isValidKanji(options):
    if(options=="joyo" or options=="jinmeyo"):
        return True
    else:
        return False

# checking if proper JLPT options
def isValidJLPT(options):
    if(options == "N5" or options == "N4" or options == "N3" or options == "N2" or options == "N1"):
        return True
    else:
        return False

# function for getting input, called in soup object declaration
URL_PREFIXES = {
    'N5': '/search/jlpt%20N5%20%23words?page=',
    'N4': '/search/jlpt%20N4%20%23words?page=',
    'N3': '/search/jlpt%20N3%20%23words?page=',
    'N2': '/search/jlpt%20N2%20%23words?page=',
    'N1': '/search/jlpt%20N1%20%23words?page=',
    'common': '/search/%23common%20%23words?page=',
    'joyo': '/search/%23kanji%20%23joyo?page=',
    'jinmeyo': '/search/%23kanji%20%23jinmei?page=',
}

def getUrl(options):
    global pageNum
    pageNum += 1
    prefix = URL_PREFIXES[options]
    url = f'https://jisho.org{prefix}{pageNum}'
    return url

# initializes xls spreadsheet with proper formatting and returns book, sheet, meaningFx, and regularFx
def initXls(options):
    
    # creates xls spreadsheet
    filename = f"Jisho-{options}.xls"
    name = options
    book = xlwt.Workbook()
    sheet = book.add_sheet(name, True)

    # create header cells and format accordingly
    if isValidWord(options):    
        sheet.write(0, 0, "KANJI")
        sheet.write(0, 1, "FURIGANA")
        sheet.write(0, 2, "KANA TAG")
        sheet.write(0, 3, "options")
    if isValidKanji(options):
        sheet.write(0, 0, "KANJI")
        sheet.write(0, 1, "KUNYOMI")
        sheet.write(0, 2, "ONYOMI")
        sheet.write(0, 3, "options")

    return (filename, book, sheet)


# iterates through all entries until empty
def scrapeAndWrite(soup, options):
    if isValidWord(options):
        scrapeAndWriteWords(soup, options)
    elif isValidKanji(options):
        scrapeAndWriteKanji(soup, options)

# iterates through all entries until empty
def scrapeAndWriteWords(soup, options):

    # initialize spreadsheet in scrape() for access
    file, book, sheet = initXls(options)

    # keeps track of row in spreadsheet
    rowIndex = 0
    
    while(not soup.find('div', {'id' : 'no-matches'})):
        for entry in soup.find_all('div', {'class' : 'concept_light clearfix'}):
            
            kanji = entry.find('span', {'class' : 'text'}).text.strip()

            furiganaSet = []
            for furiganaElement in entry.find_all('span', {'class' : 'furigana'}):
                if(len(furiganaElement.find_all('rt')) > 0):
                    furiganaSet.append(furiganaElement.find('rt').text.strip())
                    break
                for furigana in furiganaElement.find_all('span'):
                    if(furigana.text.strip() == ""):
                        continue
                    furiganaSet.append(furigana.text.strip())

            furigana = kanji
            furiganaIndex = 0
            furiganaSetIndex = 0
            while(furiganaIndex < len(furigana) and furiganaSetIndex < len(furiganaSet)):
                if(furigana[furiganaIndex] > 'ヿ'):
                    furigana= furigana.replace(furigana[furiganaIndex], furiganaSet[furiganaSetIndex])
                    furiganaSetIndex += 1
                furiganaIndex += 1
            for kana in furigana:
                if(kana > 'ヿ'):
                    furigana = furigana.replace(kana, "")

            meaningWrappers = entry.find_all('div', {'class' : 'meaning-wrapper'})
            primaryMeaning = meaningWrappers[0].text.strip()

            kanaTag = ""
            if ("Usually written using kana alone" in primaryMeaning):
                kanaTag = "Kana" 

            # update row index for spreadsheet
            rowIndex += 1

            # write to spreadsheet, check for commonWordsOnly
            sheet.write(rowIndex, 0, kanji)
            sheet.write(rowIndex, 1, furigana)
            sheet.write(rowIndex, 2, kanaTag)
            sheet.write(rowIndex, 3, options)

            # save spreadsheet, in innermost loop for safety in case of error, crash, etc.
            book.save(file)

        # output simple feedback of progress
        print("RESULTS OF PAGE: " + "%03d" % (pageNum) + "\n\n" + "--------------------" + "\n")
        
        # reset soup object with updated url (new page numbers), call scrape() again
        soup = BeautifulSoup(requests.get(getUrl(options), "html.parser").text, "lxml")
    return


# iterates through all entries until empty
def scrapeAndWriteKanji(soup, options):

    # initialize spreadsheet in scrape() for access
    file, book, sheet = initXls(options)

    # keeps track of row in spreadsheet
    rowIndex = 0
    
    while(not soup.find('div', {'id' : 'no-matches'})):
        for entry in soup.find_all('div', {'class' : 'entry kanji_light clearfix'}):
            
            kanji = entry.find('span', {'class' : 'character literal japanese_gothic'}).text.strip()

            kunReadings = ""
            kunR = entry.find('span', {'class' : 'kun readings'})
            kunWrappers = kunR.find_all('div', {'class' : 'japanese_gothic '})
            for wrapper in kunWrappers:
                reading = wrapper.text.strip()
                kunReadings.append(reading + "、")
            kunReadings = kunReadings[:-1]

            onReadings = ""
            onR = entry.find('span', {'class' : 'on readings'})
            onWrappers = onR.find_all('div', {'class' : 'japanese_gothic '})
            for wrapper in onWrappers:
                reading = wrapper.text.strip()
                onReadings.append(reading + "、")
            onReadings = kunReadings[:-1]

            # update row index for spreadsheet
            rowIndex += 1

            # write to spreadsheet, check for commonWordsOnly
            sheet.write(rowIndex, 0, kanji)
            sheet.write(rowIndex, 1, kunReadings)
            sheet.write(rowIndex, 2, onReadings)
            sheet.write(rowIndex, 3, options)

            # save spreadsheet, in innermost loop for safety in case of error, crash, etc.
            book.save(file)

        # output simple feedback of progress
        print("RESULTS OF PAGE: " + "%03d" % (pageNum) + "\n\n" + "--------------------" + "\n")
        
        # reset soup object with updated url (new page numbers), call scrape() again
        soup = BeautifulSoup(requests.get(getUrl(options), "html.parser").text, "lxml")
    return


def main():
    options = getJlptoptions()
    scrapeAndWrite(BeautifulSoup(requests.get(getUrl(options), "html.parser").text, "lxml"), options)

if __name__ == "__main__":
    main()
