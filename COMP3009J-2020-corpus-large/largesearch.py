# encoding:utf-8

# Main Idea For BM25:
#   1. At the beginning, it will receive the query from user input and divide the query into words
#   2.And then it will check whether index file exist or not.
#       2.1 If not, it will scan all document and generate new one.
#       2.2 If so, it will use it directly.
#   3. After using the content of index file, it will order the document in the index file
#   4. The IR system will execute the query and return all the feedback
#   5. rank function will rank them and return the TOP15

# Main Idea For Evaluation
#   1.At the beginning, it will get the queries.txt and read content of it as the query
#   2.Then it will check whether index file exist or not.
#       2.1 If not, it will scan all document and generate new one.
#       2.2 If so, it will use it directly.
#   3.After ensuring the exists of index file, it will check whether output files
#       3.1 If not, it will generate a new one by querying all sentences in the queries.txt
#       3.2 If so, it will use the content of it directly
#   4.It will compare the output file and qrels.txt to get the evaluation score.

# Main Idea For Project Design
#   1. It will read the order from user
#       1.1 If is '-m manual', then it will execute the BM25 Searching
#       1.2 If is '-m evaluation', then it will execute the evaluating process


import os  # "import os" to find the document in the right place
import re  # "import re" to cut sentences into words
import json  # 'import json' to write and read one json file (index file)
import sys  # 'import sys' to receive the command from user
from optparse import OptionParser  # 'from optparse import OptionParser' to receive the command from user
import time  # 'import time' as one timer

from math import log  # 'from math import log' to calculate the similarity score
from files import porter  # 'from files import porter' to stem words

path = 'documents'  # path for documents
doc_number = 0  # GLOBAL VARIABLE: how many documents are there in the document folder
feedback_length = 15  # GLOBAL VARIABLE:  the number limitation for returned feedback in manual part
evaluation_feedback_length = 50  # GLOBAL VARIABLE:  the number limitation for returned feedback in evaluation part

passage = []  # GLOBAL VARIABLE:  the array for storing the passage dictionaries
passage_name = []  # GLOBAL VARIABLE:  the array for storing the passage dictionaries
passage_length = {}  # GLOBAL VARIABLE: pair of passage order and passage name
all_word = 0  # GLOBAL VARIABLE:  the number of all words in all passages
stopwords = []  # GLOBAL VARIABLE:  array for storing stopwords
index = {}

# read all files and split sentences into words
def initialization():
    """
    :return: after execution, it will return the words contained in one file in the format of 'dictionary'
    """
    dict = {}
    files = os.listdir(path)
    for file in files:
        global doc_number
        doc_number = doc_number + 1
        words = []
        # read all documents in the specific folder
        with open(path + os.sep + file, 'r', encoding='gb18030', errors='ignore') as f:
            for line in f:
                line.rstrip(" \n")
                # the strategy here is to get off the useless punctuation marks and split off the whole sentences
                line = re.sub(r'[!@#$%^&*()_\-+=<>,./?;:''\"\"\'{}[]/\|`~]', "", line)
                words.extend(line.split())
        dict[str(file)] = words
    return dict


# read stopword files and remove the from "original text"
def stopword_removal(dict):
    """
    :param dict: the dict passed from function initialization, it will remove stopwords it have
    :return: the term-dictionary after stopword remove
    """
    global stopwords
    # read the stopword in the stopwords.txt
    with open('files/stopwords.txt', 'r') as f:
        for line in f:
            line = line.rstrip()
            stopwords.append(line)
    stopwords = set(stopwords)

    for key, value in dict.items():
        word_list = value
        # if the word is not in the stopwords then we put it into the word list
        word_list = [str(x).lower() for x in word_list if x not in stopwords]
        dict[key] = word_list
    return dict


# stem words into 'word-root'
def stemming(dict):
    """
    :param dict: the dict passed from function stopword_removal, it will stem all words
    :return: the term-dictionary after stemming
    """
    global all_word
    global passage_length
    stemmed_term = {} # the dictionary for storing the words which have been stemmed

    p = porter.PorterStemmer()
    for key, value in dict.items():
        word_dict = {}
        word_list = []

        for word in value:
            if word in stemmed_term.keys():
                word_list.append(stemmed_term[word])
            else:
                stemmed_term[word] = p.stem(word)
                word_list.append(stemmed_term[word])
        all_word = all_word + len(word_list)
        passage_length["len_doc" + key] = len(word_list)

        for word in word_list:
            if word in word_dict.keys():
                word_dict[word] = word_dict[word] + 1
            else:
                word_dict[word] = 1
        dict[key] = word_dict
    return dict


# generate the index file
def index_generation(dict):
    """
    :param dict: the dictionary after stemming
    :return: the content wrote in the json file
    """
    # index = {}
    global index
    word_reference = {}
    # calculate the average length of documents
    index['len_avg'] = int(all_word / doc_number)
    # calculate the number of the documents
    index['doc_number'] = doc_number

    docs_length = passage_length
    index.update(docs_length)

    # create the invert index
    for key, value in dict.items():
        word_list = value
        for word in word_list:
            if word in word_reference.keys():
                existed_word = word_reference[word]
                if key in existed_word.keys():
                    # the word is already in the keys
                    existed_word[key] = existed_word[key] + 1
                else:
                    # the word is not in the keys
                    existed_word[key] = 1
                word_reference[word] = existed_word
            else:
                word_reference[word] = {key: 1}

    index["passage"] = dict
    index['word'] = word_reference

    # write data into json file
    json_data = json.dumps(index, indent=4)
    with open("record.json", "w") as f:
        f.write(json_data)
    return index


# calculate the similarity between one query and one document
def calculate_similarity(i, len_avg, query_index, doc_number, load_dict):
    """
    :param i: the document id
    :param len_avg: the average length of documents
    :param query_index: the query index
    :param doc_number: the number of documents
    :param load_dict: the content from json file
    :return:
    """
    k = 1
    b = 0.75
    similarity = 0
    global passage

    word = load_dict['word']

    documents = load_dict['passage']

    for key, value in query_index.items():
        if key in word.keys():
            term = word[key]
            if passage_name[i] in term.keys():
                n_i = len(term)
                doc_info = documents[str(passage_name[i])]
                f_ij = doc_info[key]

                doc_name = 'len_doc' + str(passage_name[i])
                len_doc = load_dict[doc_name]

                idf = (f_ij * (1 + k)) / (f_ij + k * ((1 - b) + (b * len_doc / len_avg)))
                tf = log(doc_number + 0.5 - n_i, 2) - log(n_i + 0.5, 2)
                similarity = similarity + value * tf * idf
    return similarity


# find the relationship between the documents id and documents name
def passage_indexing(load_dict):
    """
    :param load_dict: the content of the json file
    """
    global passage
    global passage_name
    # global passage_document
    passage = load_dict['passage']

    for passage_item in passage.keys():
        passage_name.append(passage_item)


# execute the query for input by calling function "calculate_similarity"
def query_execution(query_index, load_dict):
    """
    :param query_index: the query content
    :param load_dict:  the content from json file
    :return: document within its similarity score
    """
    global passage
    total_similarity = {}

    len_avg = load_dict['len_avg']
    doc_number = load_dict['doc_number']
    i = 0
    while i < doc_number:
        total_similarity[passage_name[i]] = calculate_similarity(i, len_avg, query_index, doc_number, load_dict)
        i = i + 1
    return total_similarity


# read the index json file and read the content of it
def load_json():
    global index
    with open("record.json", 'r') as load_f:
        index = json.load(load_f)
    return index


# handle the query and split it into several words
def query_handler(query):
    """
    :param query: the content of query the user input
    :return: query content after stemming
    """
    words = re.compile(r"[A-Za-z]+").findall(query)
    p = porter.PorterStemmer()
    stemming_word = [p.stem(x) for x in words]
    query_dict = {}
    for words in stemming_word:
        if words in query_dict.keys():
            query_dict[words] = query_dict[words] + 1
        else:
            query_dict[words] = 1
    return query_dict


# rank the feedback and return the top 15 (manual part)
def rank(sim):
    ranked_feedback = {}
    sort = sorted(sim.items(), key=lambda x: x[1], reverse=True)
    i = 0
    global feedback_length
    while i < feedback_length:
        ranked_feedback[i] = sort[i]
        i = i + 1
    return ranked_feedback


def evaluation_rank(sim):
    """
    :param sim: rank thw similarity score
    :return: rank the feedback and return the top 50 (evaluation part)
    """
    ranked_feedback = {}
    sort = sorted(sim.items(), key=lambda x: x[1], reverse=True)
    i = 0
    global evaluation_feedback_length
    while i < evaluation_feedback_length:
        ranked_feedback[i] = sort[i]
        i = i + 1
    return ranked_feedback


def manual():
    generate_seconds = 0
    reading_seconds = 0
    stemming_seconds = 0
    total_time_start=int(time.time() * 1000)
    query = input('Enter Query\n')
    if query == 'QUIT':
        print('Thanks For Query')
    else:
        # determine the file exists
        if not os.path.isfile('record.json'):
            print('Generating Index File Now, Please Waiting....')
            print('Read Files From Folder')
            reading_file_start = int(time.time() * 1000)
            dict = initialization()
            reading_file_end = int(time.time() * 1000)

            generate_start = int(time.time() * 1000)
            stemming_start = int(time.time() * 1000)
            print('Remove stopwords')
            dict = stopword_removal(dict)
            stemming_end = int(time.time() * 1000)
            print('Stemming')
            dict = stemming(dict)

            print('INDEX GENERATION......')
            generate_end = int(time.time() * 1000)
            index_generation(dict)
            print('INDEX GENERATION FINISHED')

            reading_seconds = reading_file_end - reading_file_start
            generate_seconds = generate_end - generate_start
            stemming_seconds = stemming_end - stemming_start
        print('FIND INDEX FILE!')
        query_index = query_handler(query)

        start_time = int(time.time() * 1000)
        print('LOAD INDEX FILE......')
        load_dict = load_json()
        passage_indexing(load_dict)
        end_time = int(time.time() * 1000)
        load_seconds = end_time - start_time

        print('QUERYING......')
        start_time = int(time.time() * 1000)
        sim = query_execution(query_index, load_dict)
        print('RANKING FEEDBACK......')
        sim = rank(sim)
        end_time = int(time.time() * 1000)
        query_seconds = end_time - start_time

        print('Results for query [' + query + ']')
        for key, value in sim.items():
            print(str(key + 1) + '  ' + str(value[0]) + '  ' + str(value[1]))

        total_time_end = int(time.time() * 1000)
        total_time = total_time_end-total_time_start
        print('TIME SPENT:'+ str(total_time/ 1000) + 'seconds')
        print('FOR READING DOCUMENTS: ' + str(reading_seconds / 1000) + 'seconds')
        print('FOR REMOVE & STEMMING DOCUMENTS: ' + str(stemming_seconds / 1000) + 'seconds')
        print('FOR GENERATING INDEX FILE: ' + str(generate_seconds / 1000) + 'seconds')
        print('FOR LOAD INDEX FILE: ' + str(load_seconds / 1000) + " seconds")
        print('FOR QUERYING: ' + str(query_seconds / 1000) + " seconds")


# automatically execute query documents by queries.txt
def automatic(query):
    """
    :param query: the query content read from the qrels.txt
    """
    query_index = query_handler(query)
    if not index:
        load_json()
    passage_indexing(index)
    sim = query_execution(query_index, index)
    return evaluation_rank(sim)


# load queries from queries.txt
def load_query():
    """
    :return: the query content read from the qrels.txt
    """
    query = {}
    p = re.compile(" ")
    with open('files/queries.txt', 'r') as f:
        for line in f:
            capture = p.split(line, maxsplit=1)
            query[capture[0]] = capture[1].rstrip("\n")
    return query


def judge():
    """
    :return: judgement from qrels.txt
    """
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
    return judgement


def evaluation_handler(query):
    # judge whether there exist index file
    if not os.path.isfile('record.json'):
        # if there is not any index file, then generate a new one
        index_start = int(time.time() * 1000)
        print('Generating Index File Now, Please Waiting')
        dict = initialization()
        dict = stopword_removal(dict)
        print('INDEX GENERATION......')
        dict = stemming(dict)

        index_generation(dict)

        index_end = int(time.time() * 1000)
        print('INDEX GENERATION FINISHED')
        index_time = index_end - index_start
        print('TIME FOR GENERATING INDEX FILE: ' + str(index_time / 1000) + 'seconds')

    # find the index file
    print('INDEX FOUND')
    similarity_score = {}
    # judge whether there exist output file
    if not os.path.isfile('files/output.txt'):
        # if there is not any output file, then generate a new one
        print('NOT FOUND OUTPUT FILE!')
        output_start = int(time.time() * 1000)
        with open('files/output.txt', 'a') as f:
            for key, value in query.items():
                print('START QUERY: ' + str(key))
                similarity_score[key] = []
                feedback = automatic(value)
                rank = 1
                for feedback_value in feedback.items():
                    score = feedback_value[1]
                    f.writelines(
                        [key, ' Q0 ', str(score[0]), ' ', str(rank), ' ', str(score[1]), ' ', '17205995', '\n'])
                    # write lines according to the format
                    similarity_score[key].append({'doc_id': str(score[0]), 'rank': rank, 'score': str(score[1])})
                    rank = rank + 1
        output_end = int(time.time() * 1000)
        output_time = output_end - output_start
        print('TIME FOR GENERATING OUTPUT FILE: ' + str(output_time / 1000) + 'seconds')
    else:
        # find the output file
        print('FOUND OUTPUT FILE!')
        original_score = []
        with open('files/output.txt', 'r') as f:
            for line in f:
                similarity_result = line.split(" ")
                # get the similarity score from output file
                original_score.append({'query': str(similarity_result[0]), 'doc_id': str(similarity_result[2]),
                                       'score': str(similarity_result[3])})
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
    print('GOT ALL SIMILARITY SCORE!')
    return similarity_score


# precision evaluation
def precision(similarity_score, judgment):
    """
     :param similarity_score: the similarity score for each query and each document
     :param judgment: the judgement made by experts
     :return: the feedback of precision evaluation
     """
    pre = 0
    query_number = 0
    for key, value in similarity_score.items():
        ret = len(value)
        relret = 0
        query_judgment = judgment[key]
        for retrived_item in value:
            doc_id = retrived_item['doc_id']
            for query_judgment_item in query_judgment:
                if query_judgment_item['doc_id'] == doc_id and round(float(query_judgment_item['relevance'])) != 0:
                    relret = relret + 1
        pre = pre + relret / ret
        query_number = query_number + 1
    return pre / query_number


def recall(similarity_score, judgment):
    """
    :param similarity_score: the similarity score for each query and each document
    :param judgment: the judgement made by experts
    :return: the feedback of recall evaluation
    """
    rec = 0
    query_number = 0
    for key, value in similarity_score.items():
        rel = 0
        for judgment_item in judgment[key]:
            if int(judgment_item['relevance']) != 0:
                rel = rel + 1
        relret = 0
        query_judgment = judgment[key]
        for retrived_item in value:
            doc_id = retrived_item['doc_id']
            for query_judgment_item in query_judgment:
                if query_judgment_item['doc_id'] == doc_id and int(query_judgment_item['relevance']) != 0:
                    relret = relret + 1
        if rel != 0:
            rec = rec + relret / rel
        else:
            rec = rec
        query_number = query_number + 1
    return rec / query_number


def p_at_n(similarity_score, judgment, n):
    """
    :param similarity_score: the similarity score for each query and each document
    :param judgment: the judgement made by experts
    :param n: the configuration for p@n
    :return: the feedback of p@n evaluation
    """
    p_at_10 = 0
    query_number = 0
    for key, value in similarity_score.items():
        index = 0
        relret = 0
        while index < n:
            retrived_item = value[index]
            doc_id = retrived_item['doc_id']
            for judgment_item in judgment[key]:
                if judgment_item['doc_id'] == doc_id and round(float(judgment_item['relevance'])) != 0:
                    relret = relret + 1
            index = index + 1
        p_at_10 = p_at_10 + relret / n
        query_number = query_number + 1
    return p_at_10 / query_number


def r_precision(similarity_score, judgment):
    """
    :param similarity_score: the similarity score for each query and each document
    :param judgment: the judgement made by experts
    :return: the feedback of RPrecision evaluation
    """
    r_pr = 0
    query_number = 0
    for key, value in similarity_score.items():
        rel = 0
        for judgment_item in judgment[key]:
            if int(judgment_item['relevance']) != 0:
                rel = rel + 1
        index = 0
        relret = 0
        global evaluation_feedback_length
        while index < rel and index < evaluation_feedback_length:
            retrived_item = value[index]
            doc_id = retrived_item['doc_id']
            for judgment_item in judgment[key]:
                if judgment_item['doc_id'] == doc_id and round(float(judgment_item['relevance'])) != 0:
                    relret = relret + 1
            index = index + 1
        if rel != 0:
            r_pr = r_pr + relret / rel
        else:
            r_pr = r_pr
        query_number = query_number + 1
    return r_pr / query_number


def map(similarity_score, judgment):
    """
    :param similarity_score: the similarity score for each query and each document
    :param judgment: the judgement made by experts
    :return: the feedback of MAP evaluation
    """
    map_result = 0
    query_number = 0
    for key, value in similarity_score.items():
        query_number = query_number + 1

        rel = 0
        for judgement_item in judgment[key]:
            if int(judgement_item['relevance']) != 0:
                rel = rel + 1

        rel_doc = []
        for judgement_item in judgment[key]:
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
            map_result = map_result + sum_pre / rel
        else:
            map_result = map_result
    return map_result / query_number


def bpref(similarity_score, judgment):
    """
    :param similarity_score: the similarity score for each query and each document
    :param judgment: the judgement made by experts
    :return: the feedback of bpref evaluation
    """
    bpref_result = 0
    query_number = 0

    for key, value in similarity_score.items():
        query_number = query_number + 1
        rel = 0
        non_rel = 0
        total_weight = 0

        for judgement_item in judgment[key]:
            if int(judgement_item['relevance']) != 0:
                rel = rel + 1

        for result_item in value:
            doc_id = result_item['doc_id']
            for judgement_item in judgment[key]:
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
            bpref_result = bpref_result + total_weight / rel
        else:
            bpref_result = bpref_result
    return bpref_result / query_number


def evaluation():
    """
    :return: print the evaluation feedback to the command line
    """
    print('READY FOR EVALUATION: ')
    query = load_query()
    print('ALL QUERIES ARE LOADED!')
    similarity_score = evaluation_handler(query)
    judgment = judge()

    start = int(time.time() * 1000)
    pre = precision(similarity_score=similarity_score, judgment=judgment)
    rec = recall(similarity_score=similarity_score, judgment=judgment)
    p_at_10 = p_at_n(similarity_score=similarity_score, judgment=judgment, n=10)
    r_pr = r_precision(similarity_score=similarity_score, judgment=judgment)
    map_result = map(similarity_score=similarity_score, judgment=judgment)
    bpref_result = bpref(similarity_score=similarity_score, judgment=judgment)

    print('Evaluation results:')
    print('precision: ' + str(pre))
    print('recall: ' + str(rec))
    print('P@10: ' + str(p_at_10))
    print('R-precision: ' + str(r_pr))
    print('MAP: ' + str(map_result))
    print('bpref: ' + str(bpref_result))
    end = int(time.time() * 1000)
    evaluation_time = end - start
    print('TIME FOR EVALUATING OUTPUT FILE: ' + str(evaluation_time / 1000) + 'seconds')


if __name__ == '__main__':
    # get the instruction from  command line
    parser = OptionParser()
    parser.add_option('-m', action="store", type="string")
    options, args = parser.parse_args(sys.argv[1:])

    # if the command line is '-m manual'
    if options.m == 'manual':
        manual()
    # if the command line is '-m evaluation'
    elif options.m == 'evaluation':
        evaluation()
    else:
        print('UN-RECOGNIZABLE ORDER-CHAR')
