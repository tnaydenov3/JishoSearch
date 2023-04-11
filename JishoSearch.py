from bs4 import BeautifulSoup

import requests
import xlwt

def getOptions():
    options = input("Please enter options (kanji or words): ")
    while(not isValidInput(options)):
        print(f"ERROR: \"{options}\" is an invalid input\n")
        options = input("Please enter options: ")
    return(options)

VALID_OPTIONS = {'kanji', 'words'}
VALID_SEARCH = {'common', 'joyo','jinmeyo'}

def isValidInput(options):
    return options in VALID_OPTIONS

def isValidSearch(search):
    return search in VALID_SEARCH


URL_PREFIXES = {
    'common': '/search/%23common%20%23words?page=',
    'joyo': '/search/%23kanji%20%23joyo?page=',
    'jinmeyo': '/search/%23kanji%20%23jinmei?page=',
}

def getUrl(search, pageNum):
    prefix = URL_PREFIXES[search]
    url = f'https://jisho.org{prefix}{pageNum}'
    return url

def initXls(options):    
    filename = f"Jisho-{options}.xls"
    name = options
    book = xlwt.Workbook()
    sheet = book.add_sheet(name, True)
    if options == 'kanji':    
        sheet.write(0, 0, "Kanji")
        sheet.write(0, 1, "Readings")
        sheet.write(0, 2, "Study tag")
    if options == 'words':
        sheet.write(0, 0, "Entry")
        sheet.write(0, 1, "Kanji")
        sheet.write(0, 2, "Kana")
        sheet.write(0, 3, "Study entry")     
        sheet.write(0, 4, "Study group")            
    return (filename, book, sheet)

SEARCHES = {
    'kanji' : ['joyo', 'jinmeyo'],
    'words' : ['common']
}

def getSoup(search, pageNum):
    return BeautifulSoup(requests.get(getUrl(search, pageNum), "html.parser").text, "lxml")


def scrapeAndWrite(options):
    file, book, sheet = initXls(options)
    rowIndex = 0
    for search in SEARCHES[options]:
        pageNum = 1
        mining = True
        soup = getSoup(search, pageNum)
        while (mining):
            mining = False          
            if options == 'kanji':   
                mining, rowIndex = scrapeAndWriteKanji(soup, sheet, rowIndex)
            if options == 'words':
                mining, rowIndex = scrapeAndWriteWords(soup, sheet, rowIndex)
            book.save(file)
            print("RESULTS OF PAGE: " + "%02d" % (pageNum) + "--------------------" + "\n")  
            pageNum += 1
            soup = getSoup(search, pageNum)
    return

def scrapeAndWriteWords(soup, sheet, rowIndex):
    mining = not soup.find('div', {'id' : 'no-matches'})

    for entry in soup.find_all('div', {'class' : 'concept_light clearfix'}):
        
        kanji = entry.find('span', {'class' : 'text'}).text.strip()
        wordEntry = kanji

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

        studyEntry = kanji
        studyGroup = "kanji"

        if ("Usually written using kana alone" in primaryMeaning):
            wordEntry += "、" + furigana
            studyEntry = furigana
            studyGroup = "kanji - kana"


        if (kanji == furigana):
            wordEntry = kanji
            studyGroup = "kana"

        rowIndex += 1

        sheet.write(rowIndex, 0, wordEntry)
        sheet.write(rowIndex, 1, kanji)
        sheet.write(rowIndex, 2, furigana)
        sheet.write(rowIndex, 3, studyEntry)
        sheet.write(rowIndex, 4, studyGroup)
        print(kanji)
       
    return mining, rowIndex


def scrapeAndWriteKanji(soup, sheet, rowIndex):
    mining = soup.find('div', {'class' : 'kanji_light_block'})

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

        tag = "J3-jinmei"
        info = entry.find('div', {'class' : 'info clearfix'}).text.strip()
        if ("taught in grade" in info):
            tag = "J1-kyoiku"
        elif ("junior high" in info):
            tag = "J2-koko"

        rowIndex += 1

        sheet.write(rowIndex, 0, kanji)
        sheet.write(rowIndex, 1, readings)
        sheet.write(rowIndex, 2, tag)
        print(kanji)

    return mining, rowIndex


def main():
    options = getOptions()
    scrapeAndWrite(options)

if __name__ == "__main__":
    main()
