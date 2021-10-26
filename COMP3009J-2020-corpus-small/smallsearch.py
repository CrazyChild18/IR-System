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
feedback_length = 15  # GLOBAL VARIABLE:  the limitation for returned feedback
evaluation_feedback_length = 50  # GLOBAL VARIABLE:  the number limitation for returned feedback in evaluation part
index = {}


# read all files and split sentences into words
def initialization():
    """
    :return: after execution, it will return the words contained in one file in the format of 'dictionary'
    """
    dict = {}
    files=os.listdir(path)
    for file in files:
        global doc_number
        doc_number = doc_number + 1
        # read all documents in the specific folder
        with open(path+os.sep+file, 'r') as f:
            for line in f:
                # the strategy here is to only get the useful words
                dict[str(file)] = re.compile(r"[A-Za-z-]+").findall(line)
    return dict


# read stopword files and remove the from "original text"
def stopword_removal(dict):
    """
    :param dict: the dict passed from function initialization, it will remove stopwords it have
    :return: the term-dictionary after stopword remove
    """
    stopwords = []
    with open('files/stopwords.txt', 'r') as f:
        for line in f:
            line = line.rstrip()
            stopwords.append(line)
    stopwords = set(stopwords)
    # if the word is not in the stopwords then we put it into the wordlist
    for key,value in dict.items():
        word_list = value
        word_list = [x for x in word_list if x not in stopwords]
        dict[key] = word_list
    return dict


# stem words into 'word-root'
def stemming(dict):
    """
    :param dict: the dict passed from function stopword_removal, it will stem all words
    :return: the term-dictionary after stemming
    """
    p = porter.PorterStemmer()
    stemmed_term = {}

    # stemming the word by using the API provided in PorterStemmer
    for key, value in dict.items():
        # word_list = value
        # word_list = [p.stem(x) for x in word_list]
        word_list = []
        for word in value:
            if word in stemmed_term.keys():
                word_list.append(stemmed_term[word])
            else:
                stemmed_term[word] = p.stem(word)
                word_list.append(stemmed_term[word])

        dict[key] = word_list
    return dict


# calculate the average length of documents
def avg_length(dict):
    doc_number = len(dict)
    word_number = 0
    for value in dict.values():
        word_number=word_number+len(value)
    return int(word_number/doc_number)


# calculate the length for each document
def length_doc(dict):
    length={}
    for key,value in dict.items():
        doc_length=len(value)
        length["len_doc"+key]=doc_length
    return length


# generate the index file
def index_generation(dict):
    """
     :param dict: the dictionary after stemming
     :return: the content wrote in the json file
     """
    index = {}
    word_reference = {}
    index['len_avg'] = avg_length(dict)
    index['doc_number'] = doc_number

    docs_length = length_doc(dict)
    index.update(docs_length)

    for key,value in dict.items():
        word_list = value
        for word in word_list:
            if word in word_reference.keys():
                existed_word = word_reference[word]
                existed_word['appearance'] = existed_word['appearance']+1

                existed_occurrences = existed_word['occurrences']
                if key in existed_occurrences.keys():
                    existed_occurrences[key]=existed_occurrences[key]+1
                else:
                    existed_occurrences[key] =1
                existed_word['occurrences'] = existed_occurrences
                word_reference[word] = existed_word

            else:
                word_reference[word]={'appearance':1 , 'occurrences':{key:1}}
    index.update(word_reference)
    index.update(dict)

    json_data = json.dumps(index,indent=4)
    with open("record.json", "w") as f:
        f.write(json_data)
    return index


# calculate the similarity between one query and one document
def calculate_similarity(i, len_avg,query_index,doc_number,load_dict):
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
    for key,values in query_index.items():
        if key in load_dict.keys():
            term = load_dict[key]
            term_occurrences = term['occurrences']
            if str(i) in term_occurrences.keys():
                n_i = len(term_occurrences)
                f_ij =term_occurrences[str(i)]
                len_doc = load_dict['len_doc'+str(i)]

                idf = (f_ij*(1+k))/(f_ij + k*((1-b)+(b*len_doc/len_avg)))
                tf = log(doc_number+0.5-n_i, 2) - log(n_i+0.5, 2)

                similarity = similarity + values*tf*idf
    return similarity


# execute the query for input by calling function "calculate_similarity"
def query_execution(query_index, load_dict):
    """
     :param query_index: the query content
     :param load_dict:  the content from json file
     :return: document within its similarity score
     """
    total_similarity = {}
    len_avg = load_dict['len_avg']
    doc_number = load_dict['doc_number']
    i = 1
    while i <= doc_number:
        total_similarity[i] = calculate_similarity(i, len_avg,query_index,doc_number, load_dict)
        i = i+1
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


# rank the feedback and return the top 15
def rank(sim):
    ranked_feedback = {}
    sort = sorted(sim.items(), key = lambda x:x[1], reverse = True)
    i =0
    global feedback_length
    while i < feedback_length:
        ranked_feedback[i] = sort[i]
        # print(sort[i])
        i=i+1
    return ranked_feedback


# rank the feedback and return the top 50 (evaluation part)
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
    index_time = 0
    query = input('Enter Query\n')
    if query == 'QUIT':
        print('Thanks For Query')
    else:
        # determine the file exists
        if not os.path.isfile('record.json'):
            start = int(time.time() * 1000)
            dict = initialization()
            dict = stopword_removal(dict)
            dict = stemming(dict)
            index_generation(dict)
            end = int(time.time() * 1000)
            index_time = end - start

        start = int(time.time() * 1000)
        query_index = query_handler(query)
        load_dict = load_json()
        sim = query_execution(query_index, load_dict)
        sim = rank(sim)
        end = int(time.time() * 1000)
        query_time = end -start

        for key,value in sim.items():
            rank_id = key+1
            doc_id = value[0]
            sim_score = value[1]
            print(str(rank_id)+'  '+str(doc_id)+'  '+str(sim_score))

        print('TIME SPENT:')
        print('FOR GENERATING INDEX FILE: ' + str(index_time / 1000) + 'seconds')
        print('FOR LOAD INDEX FILE AND QUERYING: ' + str(query_time / 1000) + " seconds")


# automatically execute query documents by queries.txt
def automatic(query):
    """
    :param query: the query content read from the qrels.txt
    """
    query_index = query_handler(query)
    if not index:
        load_json()
    load_dict = load_json()
    sim = query_execution(query_index, load_dict)
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
            capture = p.split(line,maxsplit=1)
            query[capture[0]] = capture[1].rstrip("\n")
    return query


# load judgement from qrels.txt
def judge():
    """
    :return: judgement from qrels.txt
    """
    judgement = {}
    with open('files/qrels.txt', 'r') as f:
        for line in f:
            line = line.rstrip("\n")
            line = re.compile(r"[0-9]+").findall(line)
            if line[0] in judgement.keys():
                judgement[line[0]].append({'doc_id': line[2], 'relevance': line[3]})
            else:
                judgement[line[0]] = []
                judgement[line[0]].append({'doc_id':line[2], 'relevance':line[3]})
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
        index_time = index_end-index_start
        print('TIME FOR GENERATING INDEX FILE: ' + str(index_time / 1000) + 'seconds')

    # find the index file
    print('INDEX FOUND')
    similarity_score = {}
    # judge whether there exist output file
    if not os.path.isfile('files/output.txt'):
        # if there is not any output file, then generate a new one
        output_start = int(time.time() * 1000)
        with open('files/output.txt', 'a') as f:
            for key, value in query.items():
                print('START QUERY: ' + str(key))
                similarity_score[key] = []
                feedback = automatic(value)
                rank = 1
                for feedback_value in feedback.items():
                    score = feedback_value[1]
                    f.writelines([key,' Q0 ',str(score[0]),' ', str(rank), ' ', str(score[1]),' ','17205995','\n'])
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
                original_score.append({'query':str(similarity_result[0]),'doc_id': str(similarity_result[2]), 'score': str(similarity_result[3])})
        rank = 1
        for score in original_score:
            if score['query'] in similarity_score.keys():
                rank = rank + 1
                query_id = score['query']
                similarity_score[query_id].append({'doc_id': str(score['doc_id']), 'rank': rank, 'score': str(score['score'])})
            else:
                query_id = score['query']
                similarity_score[query_id] = []
                rank = 1
                similarity_score[query_id].append({'doc_id': str(score['doc_id']), 'rank': rank, 'score': str(score['score'])})
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
    for key,value in similarity_score.items():
        ret = len(value)
        relret = 0
        query_judgment = judgment[key]
        for retrived_item in value:
            doc_id = retrived_item['doc_id']
            for query_judgment_item in query_judgment:
                if query_judgment_item['doc_id'] == doc_id and round(float(query_judgment_item['relevance'])) !=0:
                    relret = relret + 1
        pre =pre + relret/ret
        query_number = query_number +1
    return pre/query_number


# recall evaluation
def recall(similarity_score,judgment):
    """
    :param similarity_score: the similarity score for each query and each document
    :param judgment: the judgement made by experts
    :return: the feedback of recall evaluation
    """
    rec = 0
    query_number = 0
    for key,value in similarity_score.items():
        rel =0
        for judgment_item in judgment[key]:
            if int(judgment_item['relevance']) != 0:
                rel = rel + 1
        relret = 0
        query_judgment = judgment[key]
        for retrived_item in value:
            doc_id = retrived_item['doc_id']
            for query_judgment_item in query_judgment:
                if query_judgment_item['doc_id'] == doc_id and round(float(query_judgment_item['relevance']))!=0:
                    relret = relret + 1
        rec =rec + relret/rel
        query_number = query_number +1
    return rec/query_number


# p@10 evaluation
def p_at_n(similarity_score,judgment,n):
    """
    :param similarity_score: the similarity score for each query and each document
    :param judgment: the judgement made by experts
    :param n: the configuration for p@n
    :return: the feedback of p@n evaluation
    """
    p_at_10 = 0
    query_number = 0
    for key,value in similarity_score.items():
        index =0
        relret=0
        while index<n:
            retrived_item = value[index]
            doc_id = retrived_item['doc_id']
            for judgment_item in judgment[key]:
                if judgment_item['doc_id'] == doc_id and round(float(judgment_item['relevance'])) != 0:
                    relret = relret + 1
            index = index+1
            p_at_10 = p_at_10 + relret/n
            query_number = query_number + 1
    return p_at_10/query_number


# RPrecision evaluation
def r_precision(similarity_score, judgment):
    """
    :param similarity_score: the similarity score for each query and each document
    :param judgment: the judgement made by experts
    :return: the feedback of RPrecision evaluation
    """
    r_pr = 0
    query_number = 0
    for key,value in similarity_score.items():
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
        r_pr = r_pr + relret / rel
        query_number=query_number+1
    return r_pr/query_number


# MAP evaluation
def map(similarity_score,judgment):
    """
    :param similarity_score: the similarity score for each query and each document
    :param judgment: the judgement made by experts
    :return: the feedback of MAP evaluation
    """
    map_result = 0
    query_number = 0
    for key,value in similarity_score.items():
        query_number = query_number + 1

        rel = 0
        for judgement_item in judgment[key]:
            if int(judgement_item['relevance']) != 0:
                rel = rel + 1
        # print(value)

        rel_doc = []
        for judgement_item in judgment[key]:
            rel_doc.append(judgement_item['doc_id'])

        index = 0
        relret = 0
        sum_pre = 0
        while index < len(value):
            result_item = value[index]
            doc_id = result_item['doc_id']
            if doc_id in rel_doc:
                relret = relret + 1
                sum_pre = sum_pre + relret/(index +1)
            index = index + 1
        map_result = map_result + sum_pre/rel
    return map_result/query_number


# bpref evaluation
def bpref(similarity_score,judgment):
    """
    :param similarity_score: the similarity score for each query and each document
    :param judgment: the judgement made by experts
    :return: the feedback of bpref evaluation
    """
    bpref_result = 0
    query_number = 0

    for key,value in similarity_score.items():
        query_number = query_number + 1
        rel = 0
        total_weight = 0

        for judgement_item in judgment[key]:
            if int(judgement_item['relevance']) != 0:
                rel = rel + 1
        rel_doc = []
        for judgement_item in judgment[key]:
            rel_doc.append(judgement_item['doc_id'])
        non_rel = 0
        for result_item in value:
            doc_id = result_item['doc_id']

            if doc_id in rel_doc:
                if non_rel < rel:
                    weight = 1 - (non_rel / rel)
                else:
                    weight = 0
                total_weight = total_weight + weight
            else:
                non_rel = non_rel +1
        bpref_result = bpref_result + total_weight/rel
    return bpref_result/query_number


def evaluation():
    """
    :return: print the evaluation feedback to the command line
    """
    query = load_query()
    similarity_score = evaluation_handler(query)
    judgment = judge()

    start = int(time.time() * 1000)
    pre = precision(similarity_score=similarity_score,judgment=judgment)
    rec = recall(similarity_score=similarity_score,judgment=judgment)
    p_at_10 = p_at_n(similarity_score=similarity_score, judgment=judgment, n=10)
    r_pr = r_precision(similarity_score=similarity_score,judgment=judgment)
    map_result = map(similarity_score=similarity_score,judgment=judgment)
    bpref_result = bpref(similarity_score=similarity_score,judgment=judgment)

    print('Evaluation results:')
    print('precision: '+str(pre))
    print('recall: '+str(rec))
    print('P@10: '+str(p_at_10))
    print('R-precision: '+str(r_pr))
    print('MAP: '+ str(map_result))
    print('bpref: '+str(bpref_result))
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
