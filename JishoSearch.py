# libraries
from bs4 import BeautifulSoup

import lxml
import os
import requests
import string
import xlwt
import re

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

def getUrl(options, pageNum):
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
        sheet.write(0, 0, "Kanji")
        sheet.write(0, 1, "Furigana")
        sheet.write(0, 2, "KANA TAG")
        sheet.write(0, 3, "Options")
    if isValidKanji(options):
        sheet.write(0, 0, "Kanji")
        sheet.write(0, 1, "Readings")
        sheet.write(0, 2, "Options")

    return (filename, book, sheet)


# iterates through all entries until empty
def scrapeAndWrite(soup, options, pageNum):
    if isValidWord(options):
        scrapeAndWriteWords(soup, options, pageNum)
    elif isValidKanji(options):
        scrapeAndWriteKanji(soup, options, pageNum)

# iterates through all entries until empty
def scrapeAndWriteWords(soup, options, pageNum):

    # initialize spreadsheet in scrape() for access
    file, book, sheet = initXls(options)

    # keeps track of row in spreadsheet
    rowIndex = 0
    
    while(not soup.find('div', {'id' : 'no-matches'})):
        for entry in soup.find_all('div', {'class' : 'concept_light clearfix'}):
            
            kanji = entry.find('span', {'class' : 'text'}).text.strip()

            furiganaSet = []
            for furiganaElement in entry.find_all('span', {'class' : 'furigana'}):
                for furigana in furiganaElement.find_all('span'):
                    if furigana.text.strip():
                        furiganaSet.append(furigana.find('rt').text.strip() if furigana.find('rt') else furigana.text.strip())

            furigana = ''.join([furiganaSet[i] if i < len(furiganaSet) else c for i, c in enumerate(kanji)])
            furigana = ''.join(c for c in furigana if c <= 'ヿ')


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
        pageNum += 1
        soup = BeautifulSoup(requests.get(getUrl(options, pageNum), "html.parser").text, "lxml")
    return


# iterates through all entries until empty
def scrapeAndWriteKanji(soup, options, pageNum):

    # initialize spreadsheet in scrape() for access
    file, book, sheet = initXls(options)

    # keeps track of row in spreadsheet
    rowIndex = 0
    
    while(not soup.find('div', {'id' : 'no-matches'})):
        for entry in soup.find_all('div', {'class' : 'kanji_light_content'}):
            
            kanji = entry.find('div', {'class' : 'literal_block'}).text.strip()

            kunReadings = ""
            kunR = entry.find('div', {'class' : 'kun readings'})
            if (kunR != None):
                kunWrappers = kunR.find_all('span', {'class' : 'japanese_gothic'})
                for wrapper in kunWrappers:
                    reading = wrapper.text.strip()
                    kunReadings += (reading)
                kunReadings = kunReadings

            onReadings = ""
            onR = entry.find('div', {'class' : 'on readings'})
            if (onR != None):
                onWrappers = onR.find_all('span', {'class' : 'japanese_gothic'})
                for wrapper in onWrappers:
                    reading = wrapper.text.strip()
                    onReadings += (reading)
                onReadings = onReadings

            readings = onReadings + "；" + kunReadings

            # update row index for spreadsheet
            rowIndex += 1

            # write to spreadsheet, check for commonWordsOnly
            sheet.write(rowIndex, 0, kanji)
            sheet.write(rowIndex, 1, readings)
            sheet.write(rowIndex, 2, options)

            # save spreadsheet, in innermost loop for safety in case of error, crash, etc.
            book.save(file)

        # output simple feedback of progress
        print("RESULTS OF PAGE: " + "%03d" % (pageNum) + "\n\n" + "--------------------" + "\n")
        
        # reset soup object with updated url (new page numbers), call scrape() again
        pageNum += 1
        soup = BeautifulSoup(requests.get(getUrl(options, pageNum), "html.parser").text, "lxml")
    return


def main():
    options = getJlptoptions()
    pageNum = 0
    scrapeAndWrite(BeautifulSoup(requests.get(getUrl(options, pageNum), "html.parser").text, "lxml"), options, pageNum)

if __name__ == "__main__":
    main()
