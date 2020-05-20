##################################################
##Define any packages that need installing.
#pip install word2number

##################################################

#Import packages
import csv
import time
from word2number import w2n
import random
import re

##################################################
##Start the program timer.
startTime=time.time()

##################################################
sourceFile="inputAbstracts_knownSize.csv"
askForSourceFile=False
#trainingProp=[0.05,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,0.95]
trainingProp=[0.5]
influenceRange=[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20]
#influenceRange=[1,2,3,4,5]
randomSeedRange=[1,2,3,4,5,6,7,8,9,10]
#randomSeedRange=[1,2,3,4,5]
#trainTestWith=["contentSplit","contentSplit_noPunct","contentSplit_noUpper","contentSplit_noPunct_noUpper","contentSplit_justPunct"]
trainTestWith=["contentSplit_justPunct"]

##################################################

## Define a class for the articles.
class Article():
        ID=""
        content=""
        contentSplit=[]
        contentSplit_noUpper=[]
        contentSplit_noPunct=[]
        contentSplit_noPunct_noUpper=[]
        contentSplit_justPunct=[]
        scoresVector_studySize=[]
        trueStudySize=""
        trueStudySize_position="UNKNOWN"
        estimatedStudySize=""
        estimatedStudySize_numeric=""
        trainingExemplar=False
        def __init__(self,ID,content,trueSize):
            self.ID=ID
            self.content=content
            self.trueStudySize=int(trueSize)
            self.contentSplit=self.content.split()
            ##Create a version of contentSplit without punctuation.
            tempList=[]
            for pos in self.contentSplit:
                temp=""
                for char in pos:
                    if char.isalnum():
                        temp=temp+char
                #print(temp)
                tempList.append(temp)
            self.contentSplit_noPunct=tempList
            ##Create a version of the contentSplit without uppercase.
            tempList=[]
            for pos in self.contentSplit:
                temp=pos.lower()
                #print(temp)
                tempList.append(temp)
            self.contentSplit_noUpper=tempList
            ##Create a version of contentSplit without punctuation or uppercase.
            tempList=[]
            for pos in self.contentSplit:
                temp=""
                for char in pos:
                    if char.isalnum():
                        temp=temp+char
                #print(temp)
                temp=temp.lower()
                tempList.append(temp)
            self.contentSplit_noPunct_noUpper=tempList
            ##Create a version of contentSplit with JUST punctuation.
            tempList=[]
            for pos in self.contentSplit:
                temp=""
                for char in pos:
                    if char.isalnum()==False:
                        temp=temp+char
                #print(temp)
                tempList.append(temp)
            self.contentSplit_justPunct=tempList
            ##Create a scores Vector for later testing.
            self.scoresVector_studySize=[0]*len(self.contentSplit)
##################################################
##Define functions.

## Create an object containing all articles + create the word codons.
def createArticles(askForSourceFile):
    ## Ask user to input the file to import and which columns within it are which.
    fileName = ""
    inputColID = ""
    inputColTrueSize = ""
    inputColAbstract = ""
    if askForSourceFile==True:
        fileName=input('Please enter the csv filename (including ".csv"), then press ENTER: ')
        inputColID=input('Please enter the column letter containing the abstract IDs, then press ENTER: ')
        inputColAbstract=input('Please enter the column letter containing the abstracts text, then press ENTER: ')
        inputColTrueSize=input('Please enter the column letter containing the true study size, then press ENTER: ')
    if fileName is "":
        fileName = sourceFile
    if inputColID is "":
        inputColID = "A"
    if inputColTrueSize is "":
        inputColTrueSize = "L"
    if inputColAbstract is "":
        inputColAbstract = "C"
    inputColID=ord(inputColID.lower())-97
    inputColAbstract=ord(inputColAbstract.lower())-97
    inputColTrueSize=ord(inputColTrueSize.lower())-97
    #print(inputColTrueSize)
    ## Read file and create a list each for IDs, abstracts, and goldTags
    print("Now reading file...")
    try:
        with open(sourceFile,'r',encoding="UTF-8") as csvfile:
            readCSV=csv.reader(csvfile,delimiter=',')
            ##create empty lists for abstracts and screening codes
            IDlist=[]
            contentList=[]
            trueSizeList=[]
            ##populate the empty lists with column data by row
            for row in readCSV:
                IDlist.append(row[inputColID])
                contentList.append(row[inputColAbstract])
                trueSizeList.append(row[inputColTrueSize])
    except:
        print("Unable to open file. Please check filename and type.")
        input('Press ENTER to exit')
        quit()
    ##remove the first item from the list for abstracts and screening codes
    ##as this is just the column names
    contentList=contentList[1:]
    IDlist=IDlist[1:]
    trueSizeList=trueSizeList[1:]
    ## Create an Article object for each article and store them in an object.
    allArticles=[Article(IDlist[i],contentList[i],trueSizeList[i]) for i in range(0,len(IDlist))]
    print("Number of articles: ",len(allArticles))
    return(allArticles)

##Split the input data into training and testing sets.
def SplitTrainTest(Articles,trainingProp):
    print("Splitting articles into training and testing sets.")
    print("Total articles: ",len(Articles))
    print("Training proportion: ",trainingProp)
    trainingNum=round(len(Articles)*trainingProp)
    print("Number of articles selected for training: ",trainingNum)
    ##create a list of article IDS.
    ids=list()
    for article in Articles:
        ids.append(article.ID)
    ##Shuffle it.
    random.shuffle(ids)
    ##assign the shuffled ids to a training list
    trainingIDs=ids[:trainingNum]
    ##Now assign those IDs as training exemplars in Articles.
    for id in trainingIDs:
        for article in Articles:
            if id == article.ID:
                article.trainingExemplar=True

##create vectors indicating where the numbers are.
def FindNumbers(Articles):
    print("Finding numbers...")
    ##First give a score of 1 to any word in the contentSplit list that contains
    ##at least one numeric character.
    for article in Articles:
        for i in range(0,len(article.scoresVector_studySize)):
            for letter in article.contentSplit[i]:
                if letter.isdigit():
                    article.scoresVector_studySize[i]=1
            ##Also give a score of 1 to any word that word2number detects as a number.
            try:
                numAsWords=w2n.word_to_num(article.contentSplit[i])
                #print(article.contentSplit[i])
                #print(numAsWords)
                article.scoresVector_studySize[i]=1
            except:
                continue

## Create dictionaries of baseline word probabilities.
def CalculateWordBaseline(Articles,trainTestWith):
    print("Creating vocabulary...")
    ##Create a count for total word positions.
    totalWords=0
    ##Create a vocabulary of words with how many times they appear. Only use articles
    ##that are in the training set.
    vocab={}
    for article in Articles:
        #print("article.ID: ",article.ID)
        if article.trainingExemplar==True:
            #print("trainginExemplar==True.")
            #for word in article.contentSplit:
            for word in getattr(article,trainTestWith):
                totalWords+=1
                vocab[word]=vocab.get(word,0)+1
    ##Finally divide the count in the vocab by the total words count.
    for word in vocab:
        vocab[word]=vocab[word]/totalWords
    return(vocab)

## use the true values to find the position of that value in all of the articles.
def FindTrueValues(Articles):

    ##Then for each article, try and find the true value in the text.
    ##If it isn't found, or if more than one result is found, skip that article.
    for article in Articles:
        sofar=0
        for i in range(0,len(article.contentSplit)):
            numbs=""
            for char in article.contentSplit[i]:
                if char.isnumeric():
                    numbs=numbs+char
            try:
                numbs=int(numbs)
            except:
                continue
            #print("numbs: ",numbs)
            #print("article.trueStudySize: ",article.trueStudySize)
            if numbs == article.trueStudySize:
                #print("match")
                sofar+=1
                article.trueStudySize_position=i
        if sofar>1:
            article.trueStudySize_position="UNKNOWN"

##Train the extractor using the known values from the training set.
def TrainExtractor(Articles,influenceRange,vocab,trainTestWith):
    print("Training extractor. Only articles where data can be found will be used for training.")
    print("InfluenceRange: ",influenceRange)
    print("trainTestWith", trainTestWith)
    ##First create a dictionary of dictionaries to hold the position word information.
    ##Also make a list of the numeric values. Don't include 0.
    ##Also make a dictionary to keep track of the total number of words at each position.
    wordCounts=dict()
    indices=list()
    totalCounts=dict()
    pos=0-influenceRange
    while pos <=influenceRange:
        if pos!=0:
            wordCounts[pos]={}
            indices.append(pos)
            totalCounts[pos]=0
        pos+=1
    #print(wordCounts)
    #print(indices)
    #print(totalCounts)

    ##For each article that is a training article, and has an index for trueStudySize_position.
    articlesUsed=0
    for article in Articles:
        if article.trainingExemplar==True:
            if article.trueStudySize_position!="UNKNOWN":
                ##For each of the defined offsets
                for offset in indices:
                    #print(offset)
                    ##find the word offset that much from the size value.
                    pos=offset+article.trueStudySize_position
                    ##Skip if this lies outside the index range.
                    if pos>=0 and pos<=len(article.contentSplit)-1:

                        #word = article.contentSplit[offset+article.trueStudySize_position]
                        word = getattr(article,trainTestWith)[offset+article.trueStudySize_position]
                        #print(word)
                        ###add 1 to the total count for that position.
                        totalCounts[offset]+=1
                        ##add 1 to the total count for that position for that word.
                        wordCounts[offset][word]=wordCounts[offset].get(word,0)+1
                        #print("\n",wordCounts)
                        #print("\n",wordCounts)
                articlesUsed+=1
    ##now divide the total count for each word at each position by the total number
    ##of words examined at that position to get the occurance frequency of each word
    ##at each position.
    for position in wordCounts:
        for word in wordCounts[position]:
            wordCounts[position][word]=wordCounts[position][word]/totalCounts[position]
    #print("\n",wordCounts)
    ##Now divide the occurance frequency values by the occurance frequency of that
    ##word across all training exemplars.
    for position in wordCounts:
        for word in wordCounts[position]:
            wordCounts[position][word]=wordCounts[position][word]/vocab[word]
    #print("\n",wordCounts)
    print("Articles where data could be found: ",articlesUsed)
    return(wordCounts)

def TestExtractor(Articles,extractor,trainTestWith):
    print("Testing extractor...")
    print("trainTestWith: ",trainTestWith)
    ##construct a vector of postion values.
    positions=list()
    for key in extractor:
        positions.append(key)
    #print("positions: ",positions)
    ##For each article
    for article in Articles:
        ##for each position in the scoresVector_studySize.
        for pos in range(0,len(article.scoresVector_studySize)-1):
            ##if the current score is not 0.
            if article.scoresVector_studySize[pos]!=0:
                ##For each of the relative index positions.
                for relIndexPos in positions:
                    ##find the word at that position.
                    currentIndexPos=pos+relIndexPos
                    ##But only if that position is within bounds.
                    if currentIndexPos>=0 and currentIndexPos<len(article.scoresVector_studySize):
                        #word=article.contentSplit[currentIndexPos]
                        word=getattr(article,trainTestWith)[currentIndexPos]
                        ##look up that word multiplier in the extractor dictionary for that index.
                        ##If it isn't there use 1.
                        try:
                            multiplier=extractor[relIndexPos][word]
                        except:
                            multiplier=1
                    ##multiply the score at the value position by the current multiplier.
                    article.scoresVector_studySize[pos]*=multiplier

##Choose the number in the abstract with the highest score and assign this as
##studySize. If multiple values have the same score it takes the first one.
def Assign_StudySize(Articles):
    for article in Articles:
        #print("article.ID: ",article.ID)
        highScore= max(article.scoresVector_studySize)
        #print("highScore: ",highScore)
        highScore_index=article.scoresVector_studySize.index(highScore)
        #print("highScore_index: ",highScore_index)
        article.estimatedStudySize=article.contentSplit[highScore_index]
        #print("article.estimatedStudySize: ",article.estimatedStudySize)
        ##Now if that value can be converted to a number
        ##Now put that value as an integer (e.g. if "n=45", change to 45.)
        try:
            article.estimatedStudySize_numeric=int(w2n.word_to_num(article.estimatedStudySize))
        except:
            try:
                article.estimatedStudySize_numeric=int(re.sub("\D","",article.estimatedStudySize))
            except:
                article.estimatedStudySize_numeric=""

##Calculate the accuracy of the estimated study size values.
def CalculateAccuracy(Articles):
    match=0
    total=0
    match_train=0
    total_train=0
    match_test=0
    total_test=0
    for article in Articles:
        total+=1
        #print(article.trueStudySize)
        #print(article.estimatedStudySize_numeric)
        ##If the estimated and actual match,
        if article.estimatedStudySize_numeric == article.trueStudySize:
            match+=1
            ##If it was a training example,
            if article.trainingExemplar==True:
                total_train+=1
                match_train+=1
            ##If it wasn't a training example,
            else:
                total_test+=1
                match_test+=1
        ##If they estimated and actual don't match,
        else:
            if article.trainingExemplar==True:
                total_train+=1
            else:
                total_test+=1
            #print("mismatch")
    print("match: ",match)
    print("total: ", total)
    print("match_train: ",match_train)
    print("total_train: ", total_train)
    print("match_test: ",match_test)
    print("total_test: ", total_test)
    score = match/total
    score_train= match_train/total_train
    score_test= match_test/total_test
    outDict={"total":{"score": score,"match":match,"total":total},
        "train":{"score": score_train,"match":match_train,"total":total_train},
        "test":{"score": score_test,"match":match_test,"total":total_test}}
    return(outDict)

##Export the results as .csv.
def ExportResults(Articles):
    print("Exporting results...")
    ##Create lists for Export.
    IDlist=["ID"]
    abstractList=["Abstract"]
    trueSizeList=["trueSize"]
    estimatedSizeList=["estimatedSize"]
    estimatedSizeList_numeric=["estimatedSize_numeric"]
    ##Populate lists
    for article in Articles:
        IDlist.append(article.ID)
        abstractList.append(article.content)
        trueSizeList.append(article.trueStudySize)
        estimatedSizeList.append(article.estimatedStudySize)
        estimatedSizeList_numeric.append(article.estimatedStudySize_numeric)
    ##Create data columns.
    rowList=[IDlist,
        abstractList,
        trueSizeList,
        estimatedSizeList,
        estimatedSizeList_numeric]
    zipRowList=zip(*rowList)

    ##Save the file.
    with open(str(int(startTime))+"output.csv",'w',newline='',encoding="UTF-8") as file:
        writer=csv.writer(file)
        writer.writerows(zipRowList)

##Create a table to store results of paramter opimisation.
def CreateParamsOptTable():
    table=[["influenceRange_val"],["randomSeed_val"],["trainingProp"],["splitOffPunctuation"],["train_score"],["test_score"]]
    return(table)

##add the current parameters and the results they produce to a table.
def UpdateParamsOptTable(paramsOptTable,performance):
    paramsOptTable[0].append(influenceRange_val)
    paramsOptTable[1].append(randomSeed_val)
    paramsOptTable[2].append(trainingProp_val)
    paramsOptTable[3].append(trainTestWith_val)
    paramsOptTable[4].append(performance["train"]["score"])
    paramsOptTable[5].append(performance["test"]["score"])
    return(paramsOptTable)

##Export the scores results from the paramsOptTable
def ExportParamsOptTable(paramsOptTable):
    print("Exporting parameter optimisation results...")
    zipList=zip(*paramsOptTable)
    #print("zipList: ",zipList)
    ##save the file.
    with open(str(int(startTime))+"paramsOptOutput.csv",'w',encoding="UTF-8",newline='') as fle:
        writer=csv.writer(fle)
        writer.writerows(zipList)
##################################################
#Run program.

paramsOptTable=CreateParamsOptTable()
for trainingProp_val in trainingProp:
    for influenceRange_val in influenceRange:
        for randomSeed_val in randomSeedRange:
            for trainTestWith_val in trainTestWith:
                random.seed(randomSeed_val)
                Articles=createArticles(askForSourceFile)
                FindTrueValues(Articles)
                SplitTrainTest(Articles,trainingProp_val)
                FindNumbers(Articles)
                vocab= CalculateWordBaseline(Articles,trainTestWith_val)
                extractor=TrainExtractor(Articles,influenceRange_val,vocab,trainTestWith_val)
                TestExtractor(Articles,extractor,trainTestWith_val)
                Assign_StudySize(Articles)
                performance=CalculateAccuracy(Articles)
                #print("total: ",performance["total"]["match"]," / ",performance["total"]["total"]," = ",performance["total"]["score"])
                #print("train: ",performance["train"]["match"]," / ",performance["train"]["total"]," = ",performance["train"]["score"])
                #print("test: ",performance["test"]["match"]," / ",performance["test"]["total"]," = ",performance["test"]["score"])
                paramsOptTable=UpdateParamsOptTable(paramsOptTable,performance)
                #print(paramsOptTable)
                ExportResults(Articles)
ExportParamsOptTable(paramsOptTable)


#for article in Articles:
#    print("\n")
#    print (article.content)
#    print("\n",article.contentSplit)
#    print("\n",article.scoresVector_studySize)
#    print("trueSize",article.trueStudySize)
#    print("trueStudySize_position: ",article.trueStudySize_position)
#    print("estimatedStudySize",article.estimatedStudySize)
#    print("estimatedStudySize_numeric",article.estimatedStudySize_numeric)
#    print("trainingExemplar",article.trainingExemplar)
