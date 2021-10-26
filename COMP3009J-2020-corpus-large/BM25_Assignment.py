import os
import math
import string
import sys
from files import porter
import time


def pre_stopword():
    # ------------------ 读取stopwords ------------------#
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

    # 读取stopwords
    stopwords = pre_stopword()

    # ------------------------ 读取document内容 ------------------------#
    # 读取文件夹路径
    path = "documents"
    # 得到文件夹下所有文件名
    file_dirs = os.listdir(path)
    # 这一算法可以用于得到单词的词根
    stemmer = porter.PorterStemmer()
    # doc_terms储存所有文档和文档对应的terms字典
    # key是文档id，value是文档中的terms
    doc_terms = {}
    # count用来记录所有文档内容总长度
    count = 0
    # doc_len用来记录每一个文档的长度-------important
    doc_len = {}
    # term的总数（在这里将collection中所有的term都进行统计）-------important
    all_words = {}
    documents = {}

    # 遍历(在这次遍历中得到所有需要的数据)
    for file in file_dirs:
        if not os.path.isdir(file):
            # 依次遍历文件内容并储存
            # 创建单独document的临时terms，遍历完成转入doc_terms
            f = open("documents/"+file, encoding='UTF-8')
            listwords = []
            # Traverse the file, traverse line by line, read text
            for line in f:
                listwords += line.lower().split()
            documents[file] = listwords
            # Record the length of a single document
            doc_len[file] = len(listwords)
            count += len(listwords)

    # ------------------ 重新整理document内容 ------------------#
    # 重新对doc_terms进行整理，获得适合BM25的数据结构
    # 在这里需要得到数据如下：
    #       “文档总数” : all_num
    #       “包含查询term的文档数” : document_num_contain_term字典（预处理）
    #       “term在某个文档中出现的次数”
    #       “该文档长度” : doc_len字典
    #       “平均文档长度” : avg_num
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


    # ----------------------------- 将doc_terms写入txt -----------------------------#
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
    # 未发现文件，重新对数据进行记录
    except FileNotFoundError:
        print("Creating BM25 index to file, please wait and run the program again.")
        prepare()
    # Index already exists and can be retrieved
    else:
        print("Loading BM25 index from file, please wait.")

        load_start_time = int(time.time() * 1000)

        #------------------------ 重新读取数据并计算 ------------------------#
        doc_terms = {}
        doc_len = {}
        all_words = {}
        # 只读取txt中第一行，记录为文档总数
        # 用作循环计算使用
        num = f.readline().rstrip()
        total_num = int(num)

        #------------------------- index文件结构说明 --------------------------#
        #                  index.txt中每一行为一个文档的数据                    #
        #                  第一个str为文档id                                   #
        #                  第二个float为文档长度                               #
        #                  第三部分为每个term和frequency                       #
        #---------------------------------------------------------------------#

        # 整行读取(规定起始位置1)
        lines = f.readlines()[0:]

        # 设置第一部分（doc_id & doc_term & frequency）循环次数
        for line in lines[0:total_num]:
            terms = {}
            term = line.rstrip().split()
            # 获取文档长度
            doc_len[term[0]] = float(term[1])
            # 获取文档terms和frequency
            num = 3
            while num < len(term):
                # 记录term和frequency
                terms[term[num-1].strip(string.punctuation)] = int(term[num][:-1])
                num = num + 2
            doc_terms[term[0]] = terms
        # documentsNum
        for line in lines[total_num:]:
            wordsFreq = line.rstrip().split()
            all_words[wordsFreq[0]] = int(wordsFreq[1])

        f.close()

        # ------------------ 读取stopwords ------------------#
        stopwords = pre_stopword()
        # with open(r"files\stopwords.txt") as f:
        #     for line in f:
        #         stopwords.add(line.rstrip())
        # f.close()

        # Load the porter stemmer
        stemmer = porter.PorterStemmer()

        # Set BM25 parameter constant
        k = 1
        b = 0.75

        load_end_time = int(time.time() * 1000)
        load_time = (load_end_time - load_start_time) / 1000
        print("\nLoading BM25 index finish in {} seconds".format(load_time))

        # 当用户选择query
        if model == 'manual':
            while True:
                # 获取用户输入值
                query = input("\nPlease enter your query: ")

                # 退出
                if query == 'QUIT':
                    break
                # 查询为空
                if query == '':
                    print("\nQuery content not detected, please reenter!")
                # 正常输入
                else:
                    query_start_time = int(time.time() * 1000)

                    print("\nResults for query [{}]".format(query))

                    # 将input进行小写+去除回车+分割
                    query = query.rstrip()
                    query = query.lower()
                    queryword = query.split()
                    querywords = []
                    for word in queryword:
                        # 利用punctuation对输入内容的()等标点符号去除 -------- important
                        term = word.strip(string.punctuation)
                        # 删除为''的list内容
                        if term != '':
                            if term not in stopwords:
                                term = stemmer.stem(term)
                                querywords.append(term)

                    # ------------------------ Calculate ------------------------#
                    # 利用字典记录每个doc的结果
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
                        print("无相关文档，请更换查询词")
                    else:
                        for item in resultlist[0:15]:
                            print("{} {} {}".format(index, item[0], item[1]))
                            index += 1
                    print("\nFinish query, took {} seconds".format(query_time))
                    print()

        if model == 'evaluation':
            # 无测试结果
            if os.path.exists('output.txt') is False:

                evaluation_start_time = int(time.time() * 1000)

                queries = {}
                # 读取query内容，但不进行处理
                with open("files/queries.txt", 'r') as f:
                    for line in f:
                        doc_id = line.rstrip().split()[0]
                        queries[doc_id] = line.rstrip().lower().split()[1:]
                f.close()

                #------------------- 处理qrels.txt -------------------#
                # relative_doc: 记录对于每一个查询的标准结果
                #       key为query语句id
                #       value为query所对应的所有相关文档和其相关度
                # value同样储存为dic
                relative_doc = {}
                # 记录不相关文档
                no_relative_doc = {}
                with open(r'files/qrels.txt') as f:
                    # 记录query的id
                    query_id = 0
                    # 为query创建相关文档和相关度
                    query_relative = {}
                    query_no_relative = {}
                    
                    # 行遍历
                    # 每一行都是一个query id对应的一个doc id
                    for line in f:
                        line = line.rstrip().split()
                        # 用new_query_id来获取每一行所对应的query
                        # 并以此与query_id对比来判断query的更换，并以此更换query_relative
                        new_query_id = line[0]
                        # 结构同query_relative，用来处理相关文档集合更换
                        query_relative_list = {}
                        query_no_relative_list = {}

                        # 首先写入query id
                        if query_id == 0:
                            query_id = line[0]

                        # 此时query id变更，写入之前数据，并重新创建query_relative
                        if new_query_id != query_id:
                            query_relative.clear()
                            query_no_relative.clear()
                            query_id = new_query_id

                        #-------------------- 对query标记的文档进行整理 --------------------#
                        # relevant document
                        if line[3] != '0':
                            query_relative[line[2]] = line[3]
                        # non-relevant document
                        else:
                            query_no_relative[line[2]] = line[3]

                        # 将相同query id的相关文档列表整合至query_relative_list
                        query_relative_list = query_relative.copy()
                        # 存入relative_doc，并以query id进行标识
                        relative_doc[query_id] = query_relative_list
                        query_no_relative_list = query_no_relative.copy()
                        no_relative_doc[query_id] = query_no_relative_list
                f.close()

                # Stores terms we have stemmed before
                cache = {}

                # 初始化最终计算结果
                Precision_System = 0
                Recall_System = 0
                Precision10_System = 0
                RPrecision_System = 0
                MAP_System = 0
                bpref_System = 0

                for query_key, query_value in queries.items():
                    # 对query进行标准化处理，存入list
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

                    # BM25运算，得到项目运算结果，以此进行性能分析
                    for key, value in doc_terms.items():
                        sim = 0
                        for word in query_words:
                            # 判断查询term在document中的次数
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
                        # 记录排名位置
                        index = 1
                        RelRet = 0
                        RelRet_10 = 0
                        R_RelRet = 0
                        MAP = 0
                        bpref = 0
                        nonRel = 0

                        for query_ans in query_ans_sort[0: 50]:
                            f.writelines("{} Q0 {} {} {} 18206372\n".format(query_key, query_ans[0], index, query_ans[1]))

                            # 遍历BM25计算结果，通过与relative_doc进行比较来获取查询结果中的标准相关文档
                            if query_ans[0] in relative_doc[query_key]:
                                # Count the number of relevant documents returned
                                RelRet = RelRet + 1
                                # 依据每一个relative文档的位置和之前的相关数量来计算MAP
                                MAP = MAP + RelRet / index
                                # Precalculation bpref
                                # Out of range are all 0, will not be calculated
                                if nonRel <= len(relative_doc[query_key]):
                                    bpref = bpref + 1 - nonRel/len(relative_doc[query_key])
                                # Pre@10：只需要计算前10个
                                if index <= 10:
                                    RelRet_10 = RelRet_10 + 1
                                # Pre-R: 需要获得总相关文档数
                                # 并以此计算在R个查询结果前的相关文档数量
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

                    #---------------- 计算每一个query id的结果并累加 ----------------#
                    # 50 documents returned in output
                    Ret = 50
                    # 对于每一个query id的标准相关文档数
                    # 存在0的情况
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

                # 读取output文件
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

                #------------------- 处理qrels.txt -------------------#
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

                # 计算
                evaluation_start_time = int(time.time() * 1000)

                pre = 0
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
                    pre = pre + relret / ret
                    query_number = query_number + 1
                pre = pre / query_number

                rec = 0
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
                        rec = rec + relret / rel
                    else:
                        rec = rec
                    query_number = query_number + 1
                rec = rec / query_number

                p_at_10 = 0
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
                    p_at_10 = p_at_10 + relret / 10
                    query_number = query_number + 1
                p_at_10 = p_at_10 / query_number

                r_pr = 0
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
                        r_pr = r_pr + relret / rel
                    else:
                        r_pr = r_pr
                    query_number = query_number + 1
                r_pr = r_pr / query_number

                map_result = 0
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
                        map_result = map_result + sum_pre / rel
                    else:
                        map_result = map_result
                map_result = map_result / query_number

                bpref_result = 0
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
                        bpref_result = bpref_result + total_weight / rel
                    else:
                        bpref_result = bpref_result
                bpref_result = bpref_result / query_number

                print('Evaluation results:')
                print('precision: {}'.format(pre))
                print('recall: {}'.format(rec))
                print('P@10: {}'.format(p_at_10))
                print('R-precision: {}'.format(r_pr))
                print('MAP: {}'.format(map_result))
                print('bpref: {}'.format(bpref_result))
                evaluation_end_time = int(time.time() * 1000)
                evaluation_time = (evaluation_end_time - evaluation_start_time) / 1000

                print('\nEvaluation finish, cost time: {} seconds'.format(evaluation_time))
