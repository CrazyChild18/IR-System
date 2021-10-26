import os
import string
import math
import sys
from files import porter
from os import path   

#
# Read all documents and preprocess to generate index
#
def readDocuments():
    # Read all documents
    files= os.listdir("documents") # Get all file names in this folder
    documents = {}
    documentsLength = {}
    AllLength = 0
    for file in files: # Traverse folder
        if not os.path.isdir(file): # Determine whether it is a folder, and open it if it is not a folder
            f = open("documents/"+file, encoding='UTF-8'); # Folder directory, open file
            listwords = []
            for line in f: # Traverse the file, traverse line by line, read text
                listwords += line.lower().split()
            documents[file] = listwords
            documentsLength[file] = len(listwords) # Record the length of a single document
            AllLength += len(listwords)

    # Read stopwords
    stopwords = set()
    with open("files/stopwords.txt", 'r' ) as f:
        for line in f:
            stopwords.add(line.rstrip())

    # Load the porter stemmer
    stemmer = porter.PorterStemmer()

    # Calculation of relevant parameters
    N = len(documents)
    AvaLength = AllLength / N # Calculate the average length of all documents
    allwords = {} # All words in all documents
    documentsWords = {}

    # Stores terms we have stemmed before
    cache = {}

    # Process every word in the document
    for key,value in documents.items():
        docwords = {} # All words in a single document
        for term in value:
            termTemp = term.strip(string.punctuation) # Delete the punctuation at the beginning or end (multiple punctuation can be deleted)
            if termTemp is not '': # The full punctuation string is empty after filtering, remove it
                if termTemp not in stopwords: # Then judge stopwords to prevent punctuation at the end of some words, which cannot be judged before
                    # If the word has not been stemmed
                    if termTemp not in cache:
                        cache[termTemp] = stemmer.stem(termTemp)
                    termTemp = cache[termTemp]
                    # Count the number of occurrences of the word in the document
                    if termTemp in docwords:
                        docwords[termTemp] += 1
                    else:
                        docwords[termTemp] = 1
                        # Count the number of occurrences of the word in all documents
                        if termTemp in allwords:
                            allwords[termTemp] += 1
                        else:
                            allwords[termTemp] = 1 
        documentsWords[key] = docwords
        documentsLength[key] = documentsLength[key] / AvaLength # The length ratio of the document

    # Output index document
    with open("index.txt","w", encoding='UTF-8') as f:
            f.write(str(N)+"\n") # Number of documents
            for key,value in documentsWords.items():
                f.writelines("{} {} {}\n".format(key,documentsLength[key],value)) # Length ratio and word frequency of a single document
            for key,value in allwords.items():
                f.writelines("{} {}\n".format(key,value)) # Word frequency of all words


if __name__=='__main__':

    manual = sys.argv[1]
    # Record user input selection manual or evaluation
    choice = sys.argv[2]

    #
    # Determine if index file exists
    #
    try:
        f = open("index.txt", encoding='UTF-8')
    # The first run, need to generate index
    except FileNotFoundError:
        print("Creating BM25 index to file, please wait and run the program again.")
        readDocuments()
    # Address is a folder
    except IsADirectoryError:
        print("It is a directory")
    # Permission not allowed
    except PermissionError:
        print("Permission denied")
    # Index already exists and can be retrieved
    else:
        print("Loading BM25 index from file, please wait.")

        documents = {}
        documentsLength = {}
        words = {}
        documentsNum = int( f.readline().rstrip() ) # Read the total number of documents
        lines = f.readlines()[0:] # Read the remaining lines
        # Read information about each document
        for line in lines[0:documentsNum]:
            documentwords = {} 
            document = line.rstrip().split()
            documentsLength[document[0]] = float(document[1]) # Read the length ratio of each document
            index = 3
            while index < len(document):
                documentwords[document[index-1].strip(string.punctuation)] = int(document[index][:-1]) # Read contained words and word frequency
                index += 2
            documents[document[0]] = documentwords
        # Read the word frequency of all words
        for line in lines[documentsNum:]:
            wordsFreq = line.rstrip().split()
            words[wordsFreq[0]] = int(wordsFreq[1])

        f.close()

        # Read stopwords
        stopwords = set()
        with open( "files/stopwords.txt", 'r' ) as f:
            for line in f:
                stopwords.add(line.rstrip())
        f.close()

        # Load the porter stemmer
        stemmer = porter.PorterStemmer()

        # Set BM25 parameter constant
        k = 1
        b = 0.75

        #
        # User selects manual
        #
        if choice == 'manual':

            while True:
                # Prompt the user to enter a sentence
                query = input("Enter query: ")

                # Quit the program when entering QUIT
                if query == 'QUIT':
                    break

                print("\nResults for query [{}]".format(query))

                # Handle user input
                queryword = query.rstrip().lower().split()
                querywords = []
                for word in queryword:
                    termTemp = word.strip(string.punctuation) # Delete the punctuation at the beginning or end (multiple punctuation can be deleted)
                    if termTemp is not '': # The full punctuation string is empty after filtering, remove it
                        if termTemp not in stopwords:
                            termTemp = stemmer.stem(termTemp)
                            querywords.append(termTemp)

                # Calculate the results of the input and document parameters
                results = {}
                for key,value in documents.items():
                    sim = 0
                    for word in querywords:
                        if word in value:
                            fij = value[word]
                        else:
                            fij = 0
                        # If it is not in the word frequency of all documents, it means fij=0, this word will not affect the calculation of the following sim, so don’t need to consider
                        if word in words:
                            ni = words[word]
                            # View as stopwords:
                            # If the word frequency of this word is more than half of the number of documents, it will be set to stopwords and will not participate in the calculation
                            if ni <= documentsNum/2:
                                sim += fij * (1+k) * math.log( (documentsNum-ni+0.5) / (ni+0.5), 2 ) / ( fij+k*( (1-b)+b*documentsLength[key] ) )      
                    results[key] = sim

                # Sort results according to sim from high to low
                resultlist = sorted(results.items(), key=lambda item:item[1], reverse = True)

                # Output top 15 results
                index = 1
                if resultlist[0][1] == 0:
                    print("Sorry, no results") # The bm25 of the search result documents are all 0
                else:
                    for item in resultlist[0:15]:
                        print("{} {} {}".format(index,item[0],item[1]))
                        index += 1
                print("")
                
        #
        # User selects evaluation
        #
        if choice == 'evaluation':
            
            # Determine whether there is an output file
            try:
                f = open("output.txt")
            except FileNotFoundError:
                # Read all the queries
                queries = {}
                with open( "files/queries.txt", 'r' ) as f:
                    for line in f:
                        queries[line.rstrip().split()[0]] = line.rstrip().lower().split()[1:]
                f.close()

                # Read the relevance of the document corresponding to the query
                qrels = {}
                qrelsNonRel = {} # Non-relevant document
                with open( "files/qrels.txt", 'r' ) as f:
                    qrelsIndex = 0
                    qrelsDic = {}
                    qrelsNonRelDic = {}
                    for line in f:
                        qrelsDicRecent = {}
                        qrelsNonRelDicRecent = {}

                        linelist = line.rstrip().split()
                        qrelsIndexRecent = linelist[0]

                        if qrelsIndex == 0:  # The first qrel, initialization
                            qrelsIndex = linelist[0]

                        if qrelsIndexRecent != qrelsIndex: # Encounter new qrel, clear the original dic, change the index
                            qrelsDic.clear()
                            qrelsNonRelDic.clear()
                            qrelsIndex = qrelsIndexRecent
                        if linelist[3] is not '0': # Determine whether it is a relevant document
                            qrelsDic[ linelist[2] ] = linelist[3]  # Record non-relevant documents
                        else:
                            qrelsNonRelDic[ linelist[2] ] = linelist[3]  # Record relevant documents
                        qrelsDicRecent = qrelsDic.copy() # Deep copy, not quote
                        qrels[qrelsIndex] = qrelsDicRecent
                        qrelsNonRelDicRecent = qrelsNonRelDic.copy() # Deep copy, not quote
                        qrelsNonRel[qrelsIndex] = qrelsNonRelDicRecent
                f.close()

                # Stores terms we have stemmed before
                cache = {}

                # Initialize the indicators
                PrecisionSys = 0
                RecallSys = 0
                Precision10Sys = 0
                R_PrecisionSys = 0
                MAPSys = 0
                bprefSys = 0

                # Process the words in each query
                for querykey,queryvalue in  queries.items():
                    querysWords = []
                    for word in queryvalue:
                        termTemp = word.strip(string.punctuation) # Delete the punctuation at the beginning or end (multiple punctuation can be deleted)
                        if termTemp is not '': # The full punctuation string is empty after filtering, remove it
                            if termTemp not in stopwords: # Then judge stopwords to prevent punctuation at the end of some words, which cannot be judged before
                                if termTemp not in cache:
                                    cache[termTemp] = stemmer.stem(termTemp)
                                termTemp = cache[termTemp]
                                querysWords.append(termTemp)
                    results = {}

                    # Calculate bm25
                    for key,value in documents.items():
                        sim = 0
                        for word in querysWords:
                            if word in value:
                                fij = value[word]
                            else:
                                fij = 0
                            # If it is not in the word frequency of all documents, it means fij=0, this word will not affect the calculation of the following sim, so don’t need to consider
                            if word in words:
                                ni = words[word]
                                # View as stopwords:
                                # If the word frequency of this word is more than half of the number of documents, it will be set to stopwords and will not participate in the calculation
                                if ni <= documentsNum/2:
                                    sim += fij * (1+k) * math.log( (documentsNum-ni+0.5) / (ni+0.5), 2 ) / ( fij+k*( (1-b)+b*documentsLength[key] ) )         
                        results[key] = sim
                    resultlist = sorted(results.items(), key=lambda item:item[1], reverse = True)
                    
                    # Calculate various indicators and output 'output' documents
                    with open("output.txt","a") as f:
                        index = 1
                        RelRet = 0
                        RelRet10 = 0
                        R_RelRet = 0
                        MAP = 0
                        bpref = 0
                        nonRel = 0
                        for item in resultlist[0:50]:
                            f.writelines("{} Q0 {} {} {} 17206032\n".format(querykey,item[0],index,item[1]))

                            # This document is relevant
                            if item[0] in qrels[querykey]:
                                # Count the number of relevant documents returned
                                RelRet += 1
                                # Precalculation MAP
                                MAP += RelRet / index
                                # Precalculation bpref
                                if nonRel <= len(qrels[querykey]): # Out of range are all 0, will not be calculated
                                    bpref += 1 - nonRel/len(qrels[querykey])
                                # Precalculation P10
                                if index <= 10:
                                    RelRet10 += 1
                                # Precalculation R pre
                                if index <= len(qrels[querykey]):
                                    R_RelRet += 1

                            # This document is a non-relevant document 
                            else:
                                # qrelsNonRel is empty, it is currently a small corpus, if not, it is a large corpus
                                if qrelsNonRel is None: # A small corpus: all of which are non-relevant documents except relevant
                                    nonRel += 1
                                else: # A large corpus: In addition to relevant documents, non-relevant documents, there are unjudged documents
                                    if querykey in qrelsNonRel: # If there is a non-relevant document
                                        if item[0] in qrelsNonRel[querykey]:
                                            nonRel += 1
                            index += 1

                    # Calculate the indicators of a single query and accumulate the indicators
                    Ret = 50 # 50 documents returned in output
                    Rel = len(qrels[querykey])

                    if Rel == 0:
                        PrecisionSys = PrecisionSys

                        RecallSys = RecallSys

                        Precision10Sys = Precision10Sys

                        R_PrecisionSys = R_PrecisionSys

                        MAPSys = MAPSys

                        bprefSys = bprefSys
                    else:
                        Precision = RelRet/Ret
                        PrecisionSys = PrecisionSys + Precision

                        Recall = RelRet/Rel
                        RecallSys = RecallSys + Recall

                        Precision10 = RelRet10 / 10
                        Precision10Sys = Precision10Sys + Precision10

                        R_Precision = R_RelRet / Rel
                        R_PrecisionSys = R_PrecisionSys + R_Precision

                        MAP = MAP / Rel
                        MAPSys = MAPSys + MAP

                        bpref = bpref / Rel
                        bprefSys = bprefSys + bpref


                queriesSize = len(queries) # Number of query statements
                # Calculate the average of each indicator
                PrecisionSys = PrecisionSys / queriesSize
                RecallSys = RecallSys / queriesSize
                Precision10Sys = Precision10Sys / queriesSize
                R_PrecisionSys = R_PrecisionSys / queriesSize
                MAPSys = MAPSys / queriesSize
                bprefSys = bprefSys / queriesSize

                # Output result
                print("\nEvaluation results:")
                print("Precision: {}".format(PrecisionSys))
                print("Recall: {}".format(RecallSys))
                print("P@10: {}".format(Precision10Sys))
                print("R-precision: {}".format(R_PrecisionSys))
                print("MAP: {}".format(MAPSys))
                print("bpref: {}".format(bprefSys))

            except IsADirectoryError:
                print("It is a directory")
            except PermissionError:
                print("Permission denied")
            # Output document already exists
            else:
                print("There has been an output file.")
