import os
import math
import string
import sys
from files import porter
import time


def pre_stopword():
    # ------------------ Read stopwords ------------------#
    stopwords = set()
    # f = open(r'files\stopwords.txt')
    # line = f.readline()
    # while line:
    #     stopwords.add(line.rstrip())
    #     line = f.readline()
    # f.close()
    with open("files/stopwords.txt", 'r') as f:
        for line in f:
            stopwords.add(line.rstrip())
    return stopwords


def prepare():

    pre_start_time = int(time.time() * 1000)

    # Prepare stopwords
    stopwords = pre_stopword()

    # ------------------------ Read document ------------------------#
    # Read folder path
    path = "documents"
    # Get all the file names in the folder
    file_dirs = os.listdir(path)
    # Used to get the root of a word
    stemmer = porter.PorterStemmer()
    # doc_terms stores all documents and their terms dictionary
    # Key is the document ID and value is terms in the document
    doc_terms = {}
    # Count is used to record the total length of all document contents
    count = 0
    # doc_len is used to record the length of each document
    doc_len = {}
    # The total number of terms (here all terms in the collection are counted)
    all_words = {}
    documents = {}

    # Traversal (get all the required data in this traversal)
    for file in file_dirs:
        if not os.path.isdir(file):
            # Iterate through the file contents in turn and save
            # Create a temporary terms for a single document and transfer to doc_terms after traversal
            f = open("documents/"+file, encoding='UTF-8')
            listwords = []
            # Traverse the file, traverse line by line, read text
            for line in f:
                listwords += line.lower().split()
            documents[file] = listwords
            # Record the length of a single document
            doc_len[file] = len(listwords)
            count += len(listwords)

    # ------------------ Reorganize the document content ------------------#
    # The doc_terms is reorganized to obtain a data structure suitable for BM25
    # Here you need to get the data as follows:
    #       "Total number of documents" : all_num
    #       "Number of documents containing query term" : document_num_contain_term dictionary
    #       "The number of times term appears in a document"
    #       "The document length" : doc_len dictionary
    #       "Average Document Length" : avg_num
    all_num = len(documents)
    # Calculate the average length of all documents
    AvaLength = count / all_num

    # Stores terms we have stemmed before
    cache = {}

    # Process every word in the document
    for key, value in documents.items():
        # All words in a single document
        docwords = {}
        for term in value:
            # Delete the punctuation at the beginning or end (multiple punctuation can be deleted)
            termTemp = term.strip(string.punctuation)
            # The full punctuation string is empty after filtering, remove it
            if termTemp != '':
                # Then judge stopwords to prevent punctuation at the end of some words, which cannot be judged before
                if termTemp not in stopwords:
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
                        if termTemp in all_words:
                            all_words[termTemp] += 1
                        else:
                            all_words[termTemp] = 1 
        doc_terms[key] = docwords
        # The length ratio of the document
        doc_len[key] = doc_len[key] / AvaLength


    # ----------------------------- Write doc_terms to TXT -----------------------------#
    with open('index.txt', 'w', encoding='UTF-8') as f:
        f.write(str(all_num) + "\n")
        for key, value in doc_terms.items():
            f.writelines("{} {} {}\n".format(key, doc_len[key], value))
        for key, value in all_words.items():
            f.writelines("{} {}\n".format(key, value))
    f.close()

    pre_end_time = int(time.time() * 1000)
    pre_time = (pre_end_time - pre_start_time) / 1000

    print("The document index was set up in {} s".format(pre_time))


if __name__ == '__main__':

    model = sys.argv[2]

    try:
        f = open("index.txt", encoding='UTF-8')
    # No file found, record the data again
    except FileNotFoundError:
        print("Creating BM25 index to file, please wait and run the program again.")
        prepare()
    # Index already exists and can be retrieved
    else:
        print("Loading BM25 index from file, please wait.")

        load_start_time = int(time.time() * 1000)

        #------------------------ Re-read the data and calculate ------------------------#
        doc_terms = {}
        doc_len = {}
        all_words = {}
        # Only the first line in TXT is read and recorded as the total number of documents
        # Used for circular calculation
        num = f.readline().rstrip()
        total_num = int(num)

        #----------------------- Index file structure description ---------------------#
        #           Each item in index.txt contains data for a document                #
        #                    The first str is the document ID                          #
        #                  The second float is the document length                     #
        #              The third part is about each term and frequency                 #
        #------------------------------------------------------------------------------#

        # Read the whole line (specify starting position 1)
        lines = f.readlines()[0:]

        # Sets the number of cycles in the first part (doc_id & doc_term & frequency)
        for line in lines[0:total_num]:
            terms = {}
            term = line.rstrip().split()
            # Get the document length
            doc_len[term[0]] = float(term[1])
            # Gets the document terms and frequency
            num = 3
            while num < len(term):
                # Record term and frequency
                terms[term[num-1].strip(string.punctuation)] = int(term[num][:-1])
                num = num + 2
            doc_terms[term[0]] = terms
        # documentsNum
        for line in lines[total_num:]:
            wordsFreq = line.rstrip().split()
            all_words[wordsFreq[0]] = int(wordsFreq[1])

        f.close()

        # Read stopwords
        stopwords = pre_stopword()

        # Load the porter stemmer
        stemmer = porter.PorterStemmer()

        # Set BM25 parameter constant
        k = 1
        b = 0.75

        load_end_time = int(time.time() * 1000)
        load_time = (load_end_time - load_start_time) / 1000
        print("\nLoading BM25 index finish in {} seconds".format(load_time))

        # When the user selects Query
        if model == 'manual':
            while True:
                # Gets the user input value
                query = input("\nPlease enter your query: ")

                # Exit
                if query == 'QUIT':
                    break
                # The query is empty
                if query == '':
                    print("\nQuery content not detected, please reenter!")
                # Normal input
                else:
                    query_start_time = int(time.time() * 1000)

                    print("\nResults for query [{}]".format(query))

                    # Give input a lowercase + remove carriage return + split
                    query = query.rstrip()
                    query = query.lower()
                    queryword = query.split()
                    querywords = []
                    for word in queryword:
                        # Use punctuation to remove punctuation marks such as () of input content
                        term = word.strip(string.punctuation)
                        # Delete list contents as ''
                        if term != '':
                            if term not in stopwords:
                                term = stemmer.stem(term)
                                querywords.append(term)

                    # ------------------------ Calculate ------------------------#
                    # Use a dictionary to record the results of each doc
                    results = {}
                    for key, value in doc_terms.items():
                        sim = 0
                        for word in querywords:
                            if word in value:
                                term_frequency = value[word]
                            else:
                                term_frequency = 0
                            # If it is not in the word frequency of all documents, it means fij=0
                            if word in all_words:
                                document_num_contain_term = all_words[word]
                                # If the word frequency of this word is more than half of the number of documents, it will be set to stopwords and will not participate in the calculation
                                if document_num_contain_term <= total_num/2:
                                    sim += (term_frequency * (1+k) / (term_frequency+k*((1-b) + b*doc_len[key]))) * math.log((total_num-document_num_contain_term+0.5) / (document_num_contain_term + 0.5), 2)
                        results[key] = sim

                    # Sort results according to sim from high to low
                    resultlist = sorted(results.items(), key=lambda item: item[1], reverse=True)

                    query_end_time = int(time.time() * 1000)
                    query_time = (query_end_time - query_start_time) / 1000

                    # ----------------------- Output Part -----------------------#
                    index = 1
                    if resultlist[0][1] == 0:
                        # The bm25 of the search result documents are all 0
                        print("No relevant documents, please change the query term")
                    else:
                        for item in resultlist[0:15]:
                            print("{} {} {}".format(index, item[0], item[1]))
                            index += 1
                    print("\nFinish query, took {} seconds".format(query_time))
                    print()

        if model == 'evaluation':
            # No test results
            if os.path.exists('output.txt') is False:

                evaluation_start_time = int(time.time() * 1000)

                queries = {}
                # Reads the query content, but does not process it
                with open("files/queries.txt", 'r') as f:
                    for line in f:
                        doc_id = line.rstrip().split()[0]
                        queries[doc_id] = line.rstrip().lower().split()[1:]
                f.close()

                #------------------- Processing qrels.txt -------------------#
                # relative_doc: Record the standard results for each query
                #       Key is the query statement ID
                #       Value is all related documents corresponding to the query and their relevance
                # Value is also stored as dic
                relative_doc = {}
                # Record unrelated documents
                no_relative_doc = {}
                with open(r'files/qrels.txt') as f:
                    # Record the ID of Query
                    query_id = 0
                    # Create relevant documents and correlations for Query
                    query_relative = {}
                    query_no_relative = {}
                    
                    # Traveled through
                    # Each line is a DOC ID corresponding to a query ID
                    for line in f:
                        line = line.rstrip().split()
                        # Use new_query_id to get the query for each row
                        # And compare it with query_id to judge the change of query, and replace query_relative with it
                        new_query_id = line[0]
                        # The structure is the same as query_relative, and is used to handle replacements of related document collections
                        query_relative_list = {}
                        query_no_relative_list = {}

                        # First, write query id
                        if query_id == 0:
                            query_id = line[0]

                        # Query ID changes, writes the previous data, and recreates query_relative
                        if new_query_id != query_id:
                            query_relative.clear()
                            query_no_relative.clear()
                            query_id = new_query_id

                        #-------------------- Consolidate the document of the Query tag --------------------#
                        # relevant document
                        if line[3] != '0':
                            query_relative[line[2]] = line[3]
                        # non-relevant document
                        else:
                            query_no_relative[line[2]] = line[3]

                        # Consolidate the list of related documents with the same Query ID into query_relative_list
                        query_relative_list = query_relative.copy()
                        # Store it in relative_doc and identify it with query ID
                        relative_doc[query_id] = query_relative_list
                        query_no_relative_list = query_no_relative.copy()
                        no_relative_doc[query_id] = query_no_relative_list
                f.close()

                # Stores terms we have stemmed before
                cache = {}

                # Initialize the final calculation
                Precision_System = 0
                Recall_System = 0
                Precision10_System = 0
                RPrecision_System = 0
                MAP_System = 0
                bpref_System = 0

                for query_key, query_value in queries.items():
                    # Normalize Query and store it in List
                    query_words = list()
                    for word in query_value:
                        term = word.strip(string.punctuation)
                        if term != '':
                            if term not in stopwords:
                                if term not in cache:
                                    cache[term] = stemmer.stem(term)
                                term = cache[term]
                                query_words.append(term)

                    results = {}

                    # BM25 calculation, to get the project calculation results, so as to conduct performance analysis
                    for key, value in doc_terms.items():
                        sim = 0
                        for word in query_words:
                            # Determine the number of times the query term is in the Document
                            if word in value:
                                term_frequency = value[word]
                            else:
                                term_frequency = 0

                            if word in all_words:
                                document_num_contain_term = all_words[word]
                                # If the word frequency of this word is more than half of the number of documents, it will be set to stopwords and will not participate in the calculation
                                if document_num_contain_term <= total_num/2:
                                    sim += (term_frequency * (1+k) / (term_frequency+k*((1-b) + b*doc_len[key]))) * math.log((total_num-document_num_contain_term+0.5) / (document_num_contain_term + 0.5), 2)
                        results[key] = sim

                    # Sort results according to sim from high to low
                    query_ans_sort = sorted(results.items(), key=lambda item: item[1], reverse=True)

                    with open("output.txt", 'a') as f:
                        # Record the rank position
                        index = 1
                        RelRet = 0
                        RelRet_10 = 0
                        R_RelRet = 0
                        MAP = 0
                        bpref = 0
                        nonRel = 0

                        for query_ans in query_ans_sort[0: 50]:
                            f.writelines("{} Q0 {} {} {} 18206372\n".format(query_key, query_ans[0], index, query_ans[1]))

                            # The result of the BM25 calculation is traversed to get the standards-related documents in the query result by comparing it to relative_doc
                            if query_ans[0] in relative_doc[query_key]:
                                # Count the number of relevant documents returned
                                RelRet = RelRet + 1
                                # Calculate the MAP according to the position of each Relative document and the previous relative quantity
                                MAP = MAP + RelRet / index
                                # Precalculation bpref
                                # Out of range are all 0, will not be calculated
                                if nonRel <= len(relative_doc[query_key]):
                                    bpref = bpref + 1 - nonRel/len(relative_doc[query_key])
                                # Pre@10: Just have to count the first 10
                                if index <= 10:
                                    RelRet_10 = RelRet_10 + 1
                                # Pre-R: Total number of related documents required
                                # Then count the number of relevant documents before R query results
                                if index <= len(relative_doc[query_key]):
                                    R_RelRet = R_RelRet + 1
                            # when non-relative document
                            else:
                                if no_relative_doc is None:
                                    nonRel = nonRel + 1
                                else:
                                    if query_key in no_relative_doc:
                                        if query_ans[0] in no_relative_doc[query_key]:
                                            nonRel = nonRel + 1
                            index = index + 1

                    #---------------- Calculate the results of each query ID and add them up ----------------#
                    # 50 documents returned in output
                    Ret = 50
                    # The number of standard documents for each Query ID
                    # There's a case of 0
                    Rel = len(relative_doc[query_key])
                    if Rel == 0:
                        Precision_System = Precision_System

                        Recall_System = Recall_System

                        Precision10_System = Precision10_System

                        RPrecision_System = RPrecision_System

                        MAP_System = MAP_System

                        bpref_System = bpref_System
                    else:
                        Precision = RelRet / Ret
                        Precision_System = Precision_System + Precision

                        Recall = RelRet / Rel
                        Recall_System = Recall_System + Recall

                        Precision10 = RelRet_10 / 10
                        Precision10_System = Precision10_System + Precision10

                        R_Precision = R_RelRet / Rel
                        RPrecision_System = RPrecision_System + R_Precision

                        MAP = MAP / Rel
                        MAP_System = MAP_System + MAP

                        bpref = bpref / Rel
                        bpref_System = bpref_System + bpref

                # Number of query statements
                queriesSize = len(queries)
                # Calculate the average of each indicator
                Precision_System = Precision_System / queriesSize
                Recall_System = Recall_System / queriesSize
                Precision10_System = Precision10_System / queriesSize
                RPrecision_System = RPrecision_System / queriesSize
                MAP_System = MAP_System / queriesSize
                bpref_System = bpref_System / queriesSize

                # Output result
                print("\nEvaluation results:")
                print("Precision: {}".format(Precision_System))
                print("Recall: {}".format(Recall_System))
                print("P@10: {}".format(Precision10_System))
                print("R-precision: {}".format(RPrecision_System))
                print("MAP: {}".format(MAP_System))
                print("bpref: {}".format(bpref_System))

                evaluation_end_time = int(time.time() * 1000)
                evaluation_time = (evaluation_end_time - evaluation_start_time) / 1000
                print("\nFinish evaluation, cost time: {} seconds".format(evaluation_time))

            else:
                print("Found output file, system will use it to evaluation...\n")
                similarity_score = {}

                # Read output
                original_score = []
                with open('output.txt', 'r') as f:
                    for line in f:
                        similarity_result = line.split(" ")
                        # get the similarity score from output file
                        original_score.append({'query': str(similarity_result[0]), 'doc_id': str(similarity_result[2]), 'score': str(similarity_result[3])})
                rank = 1
                for score in original_score:
                    if score['query'] in similarity_score.keys():
                        rank = rank + 1
                        query_id = score['query']
                        similarity_score[query_id].append(
                            {'doc_id': str(score['doc_id']), 'rank': rank, 'score': str(score['score'])})
                    else:
                        query_id = score['query']
                        similarity_score[query_id] = []
                        rank = 1
                        similarity_score[query_id].append(
                            {'doc_id': str(score['doc_id']), 'rank': rank, 'score': str(score['score'])})

                #------------------- Processing qrels.txt -------------------#
                judgement = {}
                with open('files/qrels.txt', 'r') as f:
                    for line in f:
                        line = line.rstrip("\n")
                        line = line.split(" ")
                        if line[0] in judgement.keys():
                            judgement[line[0]].append({'doc_id': line[2], 'relevance': line[3]})
                        else:
                            judgement[line[0]] = []
                            judgement[line[0]].append({'doc_id': line[2], 'relevance': line[3]})

                # Calculate
                evaluation_start_time = int(time.time() * 1000)

                # calculate precision
                precision = 0
                query_number = 0
                for key, value in similarity_score.items():
                    ret = len(value)
                    relret = 0
                    query_judgment = judgement[key]
                    for retrived_item in value:
                        doc_id = retrived_item['doc_id']
                        for query_judgment_item in query_judgment:
                            if query_judgment_item['doc_id'] == doc_id and round(float(query_judgment_item['relevance'])) != 0:
                                relret = relret + 1
                    precision = precision + relret / ret
                    query_number = query_number + 1
                precision = precision / query_number

                # calculate recall
                recall = 0
                query_number = 0
                for key, value in similarity_score.items():
                    rel = 0
                    for judgment_item in judgement[key]:
                        if int(judgment_item['relevance']) != 0:
                            rel = rel + 1
                    relret = 0
                    query_judgment = judgement[key]
                    for retrived_item in value:
                        doc_id = retrived_item['doc_id']
                        for query_judgment_item in query_judgment:
                            if query_judgment_item['doc_id'] == doc_id and int(query_judgment_item['relevance']) != 0:
                                relret = relret + 1
                    if rel != 0:
                        recall = recall + relret / rel
                    else:
                        recall = recall
                    query_number = query_number + 1
                recall = recall / query_number

                # calculate p@10
                precision_at_10 = 0
                query_number = 0
                for key, value in similarity_score.items():
                    index = 0
                    relret = 0
                    while index < 10:
                        retrived_item = value[index]
                        doc_id = retrived_item['doc_id']
                        for judgment_item in judgement[key]:
                            if judgment_item['doc_id'] == doc_id and round(float(judgment_item['relevance'])) != 0:
                                relret = relret + 1
                        index = index + 1
                    precision_at_10 = precision_at_10 + relret / 10
                    query_number = query_number + 1
                precision_at_10 = precision_at_10 / query_number

                # calculate R-precision
                R_precision = 0
                query_number = 0
                for key, value in similarity_score.items():
                    rel = 0
                    for judgment_item in judgement[key]:
                        if int(judgment_item['relevance']) != 0:
                            rel = rel + 1
                    index = 0
                    relret = 0
                    while index < rel and index < 50:
                        retrived_item = value[index]
                        doc_id = retrived_item['doc_id']
                        for judgment_item in judgement[key]:
                            if judgment_item['doc_id'] == doc_id and round(float(judgment_item['relevance'])) != 0:
                                relret = relret + 1
                        index = index + 1
                    if rel != 0:
                        R_precision = R_precision + relret / rel
                    else:
                        R_precision = R_precision
                    query_number = query_number + 1
                R_precision = R_precision / query_number

                # calculate MAP
                MAP = 0
                query_number = 0
                for key, value in similarity_score.items():
                    query_number = query_number + 1

                    rel = 0
                    for judgement_item in judgement[key]:
                        if int(judgement_item['relevance']) != 0:
                            rel = rel + 1

                    rel_doc = []
                    for judgement_item in judgement[key]:
                        if int(judgement_item['relevance']) != 0:
                            rel_doc.append(judgement_item['doc_id'])

                    index = 0
                    relret = 0
                    sum_pre = 0

                    while index < len(value):
                        result_item = value[index]
                        doc_id = result_item['doc_id']
                        if doc_id in rel_doc:
                            relret = relret + 1
                            sum_pre = sum_pre + relret / (index + 1)
                        index = index + 1
                    if rel != 0:
                        MAP = MAP + sum_pre / rel
                    else:
                        MAP = MAP
                MAP = MAP / query_number

                bPref = 0
                query_number = 0
                for key, value in similarity_score.items():
                    query_number = query_number + 1
                    rel = 0
                    non_rel = 0
                    total_weight = 0

                    for judgement_item in judgement[key]:
                        if int(judgement_item['relevance']) != 0:
                            rel = rel + 1

                    for result_item in value:
                        doc_id = result_item['doc_id']
                        for judgement_item in judgement[key]:
                            if judgement_item['doc_id'] == doc_id:
                                weight = 0
                                if int(judgement_item['relevance']) == 0:
                                    non_rel = non_rel + 1
                                else:
                                    if non_rel < rel:
                                        weight = 1 - (non_rel / rel)
                                    else:
                                        weight = 0
                                total_weight = total_weight + weight
                    if rel != 0:
                        bPref = bPref + total_weight / rel
                    else:
                        bPref = bPref
                bPref = bPref / query_number

                print('Evaluation results:')
                print('precision: {}'.format(precision))
                print('recall: {}'.format(recall))
                print('P@10: {}'.format(precision_at_10))
                print('R-precision: {}'.format(R_precision))
                print('MAP: {}'.format(MAP))
                print('bpref: {}'.format(bPref))

                evaluation_end_time = int(time.time() * 1000)
                evaluation_time = (evaluation_end_time - evaluation_start_time) / 1000

                print('\nEvaluation finish, cost time: {} seconds'.format(evaluation_time))
