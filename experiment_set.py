import cv2
import numpy as np
import time
import win32gui
from mss import mss
from os import listdir
from keyboard import press_and_release


class Card:
    collection = []
    
    def __init__(self,color,pattern,shape,count,index = None):
        self.color = color
        self.pattern = pattern
        self.shape = shape
        
        self.colorCode = ord(color[0])
        self.patternCode = ord(pattern[0])
        self.shapeCode = ord(shape[0])
        self.count = count
        
        self.index = index
    
    def __str__(self):
        return f'Color: {self.color}\nShape: {self.shape}\nPattern: {self.pattern}\nCount: {self.count}\nIndex: {self.index}'


def getScreenShotFromWindow(windowName):
    def enum_cb(hwnd, results):
        winlist.append((hwnd, win32gui.GetWindowText(hwnd)))
        
    sct = mss()
    toplist, winlist = [], []

    win32gui.EnumWindows(enum_cb, toplist)

    window = [(hwnd, title) for hwnd, title in winlist if windowName in title.lower()]
    window = window[0]
    hwnd = window[0]

    win32gui.SetForegroundWindow(hwnd)

    time.sleep(250/1000)
    
    bboxCoordinates = win32gui.GetWindowRect(hwnd)
    bboxForSct = {'left': bboxCoordinates[0], 'top': bboxCoordinates[1], 'width': bboxCoordinates[2], 'height': bboxCoordinates[3]}

    return np.array(sct.grab(bboxForSct))

    

def isLocationTooClose(loc1,loc2, distance):
    return abs(loc1[0] - loc2[0]) < distance and abs(loc1[1] - loc2[1]) < distance

def removeCloseNeighbours(locations, neighbourDistance):
    uniqueLocations = []
    
    for location in locations:
        isInUniqueLocations = any(isLocationTooClose(uLoc,location,neighbourDistance) for uLoc in uniqueLocations)
        
        if not isInUniqueLocations:
            uniqueLocations.append(location)
            
    return uniqueLocations
                            
def getLocationsOfMatches(baseImg, templateImg, matchingThreshold, mask = None):
    res = None
    if mask is None:
        res = cv2.matchTemplate(baseImg,templateImg,cv2.TM_CCORR_NORMED)
    else:
        res = cv2.matchTemplate(baseImg,templateImg,cv2.TM_CCORR_NORMED,None, mask=mask)
    
    loc = np.where( res >= matchingThreshold)
    locationsPassingThreshold=[locations for locations in zip(*loc[::-1])]
    uniqueLocations = removeCloseNeighbours(locationsPassingThreshold, 30)
    return uniqueLocations

def readFigureTemplates():
    figureTemplates = []
    figureTemplateNames = listdir("./cards")

    for figureTemplateName in figureTemplateNames:
        figureBGR = cv2.imread(f'./cards/{figureTemplateName}',1)
        figureRGB = cv2.cvtColor(figureBGR, cv2.COLOR_BGR2RGB)
        figureTemplates.append(figureRGB)
    return figureTemplates, figureTemplateNames

def identifyCardsOnScreen():
    
    for cardIndex, rawCard in enumerate(rawCards):
        rawCardRGB = cv2.cvtColor(rawCard, cv2.COLOR_BGR2RGB)
        for index, figureBGR in enumerate(figureTemplates):
            uniqueLocations = getLocationsOfMatches(rawCardRGB, figureBGR, 0.95)
            if uniqueLocations:
                for pt in uniqueLocations:
                    cv2.rectangle(rawCard, pt, (pt[0] + figureBGR.shape[1], pt[1] + figureBGR.shape[0]), (0,0,255), 2)
                cv2.imshow(f'{figureTemplateNames[index]}', rawCard)
            
                name = figureTemplateNames[index].split(".")[0]
                color = name.split("_")[0]
                pattern = name.split("_")[1]
                shape = name.split("_")[2]
                count = len(uniqueLocations)

                card = Card(color,pattern,shape,count,cardIndex)

                Card.collection.append(card)
                break
            
def findSets():
    totalCards = len(Card.collection)
    sets =[]
    
    for i in range(totalCards):
        for j in range(i+1,totalCards):
            for k in range(j+1,totalCards):
                firstCard = Card.collection[i]
                secondCard = Card.collection[j]
                thirdCard = Card.collection[k]

                colorSetLength = len({firstCard.colorCode, secondCard.colorCode, thirdCard.colorCode})
                patternSetLength = len({firstCard.patternCode, secondCard.patternCode, thirdCard.patternCode})
                shapeSetLength = len({firstCard.shapeCode, secondCard.shapeCode, thirdCard.shapeCode})
                countSetLength = len({firstCard.count, secondCard.count, thirdCard.count})
                
                if colorSetLength != 2 and patternSetLength != 2 and shapeSetLength != 2 and countSetLength != 2:
                    sets.append((firstCard,secondCard,thirdCard))
    return sets
                    

                    

cardFrame = cv2.imread('empty_card_enlarged.png',0)
cardFrameWidth, cardFrameHeight = cardFrame.shape[::-1]

mask = np.zeros((cardFrameHeight, cardFrameWidth), dtype="uint8")
maskPositionTopLeft = (int(cardFrameWidth * 0.1), int(cardFrameHeight * 0.1))
maskSize = (int(cardFrameWidth * 0.9), int(cardFrameHeight * 0.9))

cv2.rectangle(mask, maskPositionTopLeft, maskSize, 255, -1)
mask = cv2.bitwise_not(mask, mask)

maskedFrame = cv2.bitwise_and(cardFrame, cardFrame, mask=mask)
cv2.imshow('screen', maskedFrame)

w, h = cardFrame.shape[::-1]

figureTemplates, figureTemplateNames = readFigureTemplates()

while True:
  
    imgBaseRgb = getScreenShotFromWindow("chrome")
    imgBaseGray = cv2.cvtColor(imgBaseRgb, cv2.COLOR_BGR2GRAY)
    imgOriginal = imgBaseRgb.copy()

    cardLocations = getLocationsOfMatches(imgBaseGray,cardFrame, 0.9, mask)

    rawCards = []
    for uLoc in cardLocations:
        card = np.zeros((cardFrameHeight, cardFrameWidth),dtype="uint8")
        cardPosX, cardPosY = uLoc
        card = imgOriginal[cardPosY:cardPosY+cardFrameHeight, cardPosX:cardPosX+cardFrameWidth]
        rawCards.append(card)

    Card.collection = []
    identifyCardsOnScreen()

    sets = findSets()

    if sets:
        for card in sets[0]:
            if card.index == 0:
                press_and_release('1')
                print("Key pressed: 1")
            elif card.index == 1:
                press_and_release('2')
                print("Key pressed: 2")
            elif card.index == 2:
                press_and_release('3')
                print("Key pressed: 3")
            elif card.index == 3:
                press_and_release('q')
                print("Key pressed: q")
            elif card.index == 4:
                press_and_release('w')
                print("Key pressed: w")
            elif card.index == 5:
                press_and_release('e')
                print("Key pressed: e")
            elif card.index == 6:
                press_and_release('a')
                print("Key pressed: a")
            elif card.index == 7:
                press_and_release('s')
                print("Key pressed: s")
            elif card.index == 8:
                press_and_release('d')
                print("Key pressed: d")
            elif card.index == 9:
                press_and_release('z')
                print("Key pressed: z")
            elif card.index == 10:
                press_and_release('x')
                print("Key pressed: x")
            elif card.index == 11:
                press_and_release('c')
                print("Key pressed: c")
            elif card.index == 12:
                press_and_release('r')
                print("Key pressed: r")
            elif card.index == 13:
                press_and_release('t')
                print("Key pressed: t")
            elif card.index == 14:
                press_and_release('y')
                print("Key pressed: y")

    
    for set in sets:
        print("------- set start -------")
        print(set[0])
        print("")
        print(set[1])
        print("")
        print(set[2])
    
    time.sleep(1000/1000)
    if cv2.waitKey(1) == ord('q'):
        break


cv2.imshow("overall res", imgBaseRgb)


cv2.waitKey(0)
cv2.destroyAllWindows()



# encountered problems:
# - either one by one matching or finding cards and deciding for each
# - very sensitive to size changes
# - template matching finds the same card multiple times or does not find all depending on threshold
