# Introduction About The Search

>Name: **Yunkai Li**
>
>UCD Number: **18206372**
>
>BJUT Number: **18372312**
>
>Email: **yunkai.li@ucdconnect.ie**
>
>Applicable Corpus: **search-small.py for small corpus and search-large.py for large corpus**

## 1. Project Introduction

### 1.1 Submission Content

- **README.md**: descriptive document
- **search-small.py**: which can be used in small corpuses
- **search-large.py**: which can be used in large corpuses

### 1.2 Project Structure

- <u>documents</u>: file set for documents which will be used in searching 
- files:
  - <u>porter.py:</u>  package which support stemming
  - <u>qrels.txt</u>: files that store the judgements
  - <u>queries.txt</u>: files that store the queries
  - <u>stopwords.txt</u>: file that store the stopwords
- <u>search-small.py</u>: python file which is used to execute the BM25 search and evaluation
- <u>search-large.py</u>: python file which is used to execute the BM25 search and evaluation
- <u>index.txt</u> **(generated)**: index file that store related information for searching
- <u>output.txt</u> **(generated)**:  files generated during the evaluation process which contains the result of the query

## 2. What The Program Can Do

The project consists of two major functions, namely: **"search based on BM25 algorithm"** and **"evaluation of BM25 search results"**.  

### 2.1 **Search Based On BM25:**

- **Function Introduction**  
   This function allows users to enter query statements of any length, and the system will automatically process the input text and compare it with its own corpus, and return the user a list of "sorting + document label + similarity" containing 15 documents. (Sort according to the degree of relevance between the document and the user's input information) When the user enters null value or information irrelevant to the corpus, the system will prompt no result and wait for the user's next input.
- **Function usage method**  
   Under the project directory, use the command line or a non-IDE tool to enter the command:  

   ```DOS
   python search-large.py -m manual
   ```

   At this time, the system will pre-process the corpus and convert it into a "index.txt" file containing a fixed format and save it locally. Content as follow:

   ```DOS
   6377
   GX000-01-10544170 0.1235364077939689 {'link': 7, ...}
   GX000-09-2703409 0.7500556264569737 {'depart': 3, ...}
   link 2335
   nation 4214
   ...
   ```

   The first time you log into the system, a copy of "index.txt" is created, so it takes about a minute. After the creation is complete, the system will prompt the creation is complete and output a prompt asking the user to re-enter.  

   ```DOS
   Creating BM25 index to file, please wait and run the program again.
   The document index was set up in 27.132 s
   ```

   The user re-enters the above operation instructions, and the system begins to read the index and waits for user input:  

   ```DOS
   Please enter your query:
   ```

   At this point, the user can continue typing the query and end with Enter, after which the system will return a list of results as follow:

   ```DOS
   Results for query [describe history oil industry]
   1 GX232-43-0102505 9.178508892069537
   2 GX229-87-1373283 8.76453179681041
   3 GX255-56-12408598 8.75908106551843
   4 GX253-41-3663663 8.719037671375233
   5 GX268-35-11839875 8.59576844900468
   6 GX064-43-9736582 8.515499514703484
   7 GX231-53-10990040 8.490227877435718
   8 GX253-57-7230055 8.463240479961671
   9 GX063-18-3591274 8.4509240321487
   10 GX263-63-13628209 8.37689604538001
   11 GX262-28-10252024 8.3658778211185
   12 GX261-99-14766455 8.31114804639688
   13 GX006-76-15945590 8.294422012844263
   14 GX262-86-10646381 8.264288527583593
   15 GX015-20-10573408 8.25155779987773
   ```

### 2.2 **Evaluation of BM25 Search Results:**

- **Function Introduction**  
    The purpose of this feature is to evaluate the results of the previous BM25 algorithm using the results for each query that have been marked by the expert team or users, and to obtain a score for the system's retrieval capability.  
    The results were based on five common system evaluation criteria: **"Precision"**, **"Recall"**, **"Precision@10"**, **"R-Precision"**, **"MAP"** and **"bPref"**. The specific evaluation formula is as follows:  
   1. Precision  
      $\large Precision = \frac{|RelRet|}{|Ret|}$
   2. Recall  
      $\large Recall = \frac{|RelRet|}{|Rel|}$
   3. Precision@10  
      $\large Precision@10 = \frac{|Rel\ in\ first\ 10\ result|}{10}$
   4. R-precision  
      $\large R-precision = \frac{|Rel\ in\ first\ R\ result|}{|R|}$
   5. MAP  
      $\large AP = \frac{\sum_{j=1}^{n_{i}}P(j)*y_{i,j}}{\sum_{j=1}^{n_{i}}y_{i,j}}$  
      </br>
      $\large P(j) = \frac{\sum_{k:\pi_{i}(k)\leq\pi_{i}(j)}y_(i,k)}{\pi_{i}(j)}$  
       MAP is the average of AP.
   6. bpref  
      $\large bPref =\frac{1}{R}\sum_{r \in R}1-\frac{|n\ ranked\ higher\ than\ r|}{R}$
- **Function usage method**  
   Under the project directory, use the command line or a non-IDE tool to enter the command:  

   ```DOS
   python search-large.py -m evaluation
   ```

   Similarly, at this time, the system will first retrieve whether the "output.txt" file has been retrieved. If it exists, the results are directly used as the basis for evaluation; If it does not exist, re-read the query list and perform query operation. When the system is ready, the results of each evaluation criteria are printed and communicated to the user.

## 3. Working Conditions

- The running equipment shall have the running environment of Python 3;

- The project is complete, including the "search-large.py" code or "search-small.py", the "file" folder, and the Corpus "documents";

- Runtime needs to run under the project directory;

- Cannot run directly from the IDE, need to use **"search.py -m run type"** on the command line to use;

## 4. Introduction To Key Parts

This project consists of three key parts: BM25 calculation, result evaluation, and data consolidation and optimization. In my opinion, the most core part of IR system is data consolidation and optimization.This process has a direct impact on the user's waiting time. Next, I will select the key parts to introduce. See the comments section of the code for details on the process.

### 4.1 Data Processing

Data processing is located at the beginning of the program to help the system pre-process the contents such as corpus and stopwords and transform them into a data structure that can be directly read and used by the program. In this project, I set the collation structure into three parts according to the calculation requirements of BM25: 

- Document Total Number  
  As a part of the calculation formula, this value can also facilitate the system to limit the number of times when traversing the following contents, thus reducing the traversal process of all documents in the system during calculation. The total quantity is obtained based on the system's reading of the specified document collection. The specific code is as follows:

   ```python
   for file in os.listdir("documents"):
      f = open("documents/"+file, encoding='UTF-8')
      listwords = []
      for line in f:
         ...
      documents[file] = listwords
   all_num = len(documents)
   ```

- Document and Term Processing (ID, the ratio of the document to the average length, the number of occurrentions of each term in the document)  
  Since BM25 operates on a per-document basis, saving terms relative to the document is particularly important for optimization.  
  After the total number of files is obtained, the document content is read line by line, and the obtained content is divided according to Spaces. After abandoning meaningless marks through *"string.punctuation"*, each word is stored in doc_terms dictionary according to document ID. Store word and total occurrences in the *"all_words"* dictionary. This gives you information about the relationship between documents and words.

   ```python
   for key, value in documents.items():
      docwords = {}
      for term in value:
         termTemp = term.strip(string.punctuation)
         if termTemp != '':
               if termTemp not in stopwords:
                  if termTemp in docwords:
                     docwords[termTemp] = docwords[termTemp] + 1
                  else:
                     docwords[termTemp] = 1
                     if termTemp in all_words:
                           all_words[termTemp] += 1
                     else:
                           all_words[termTemp] = 1 
      doc_terms[key] = docwords
   ```

### 4.2 Data Access And Reading

After obtaining the collated data, in order to provide users with a faster use experience, the system should not extract and process the data once every time it runs. Therefore, this project adopts to write the collated data into the local TXT file in a certain standard format, so that it can be read and used directly in the next running time of the system, which can save a lot of computing and processing time.  
First, on the data write, the system will create the *"index.txt"* file and save all the contents obtained in the previous step. The specific code is as follows:

```python
with open('index.txt', 'w', encoding='UTF-8') as f:
   f.write(all_num + "\n")
   for key, value in doc_terms.items():
      f.writelines("{} {} {}\n".format(key, doc_len[key], value))
   for key, value in all_words.items():
      f.writelines("{} {}\n".format(key, value))
f.close()
```

After the creation of the file, every time the system runs, the local *"index.txt"* file is retrieved and read first, and if it does not exist, the initialization operation is re-carried out. If it exists, use it directly. The whole reading process is based on the strictly stored index data structure and is transferred to system memory by the threshold of the total number of documents. The main code is as follows:

```python
lines = f.readlines()[0:]

for line in lines[0:total_num]:
   terms = {}
   term = line.rstrip().split()
   doc_len[term[0]] = float(term[1])
   num = 3
   while num < len(term):
         terms[term[num-1].strip(string.punctuation)] = int(term[num][:-1])
         num = num + 2
   doc_terms[term[0]] = terms

for line in lines[total_num:]:
   wordsFreq = line.rstrip().split()
   all_words[wordsFreq[0]] = int(wordsFreq[1])

f.close()
```

### 4.3 BM25 Calculate

- Computing Formula  
   $\Large sim_{BM25}(d_{j},q)=\sum_{k_{i}\in d{j}\bigcap k_{i}\in q}\frac{f_{i,j}\ *\ (1\ +\ k)}{f_{i,j}\ +\ k((1\ -\ b)+\frac{b\ *\ len(d_{j})}{avg_doclen})}\ *\  log(\frac{N\ -\ n_{i}\ +\ 0.5}{n_{i}\ +\ 0.5})$

- Operation Code

   ```python
   results = {}
   for key, value in doc_terms.items():
      sim = 0
      for word in querywords:
            if word in value:
               term_frequency = value[word]
            else:
               term_frequency = 0
            if word in all_words:
               document_num_contain_term = all_words[word]
               if document_num_contain_term <= total_num/2:
                  sim += (term_frequency * (1+k) / (term_frequency+k*((1-b) + b*doc_len[key]))) * math.log((total_num-document_num_contain_term+0.5) / (document_num_contain_term + 0.5), 2)
      results[key] = sim

   # Sort results according to sim from high to low
   resultlist = sorted(results.items(), key=lambda item: item[1], reverse=True)
   ```

### 4.4 Evaluation

- Evaluation Criteria  
   The specific performance Evaluation of the system is based on the introduction of **"Evaluation of BM25 Search Results"** above, and will not be elaborated here.

- Evaluation Process  
   The evaluation is based on the contents of the *"qrel.txt"* file in the *"files"* folder as the standard evaluation result for the sample query. By reading the contents of the file and creating a ranking list of the relevant documents relative to each Query ID, and giving different weights to the documents in different orders. At the same time, it is compared with the returned results of the system to obtain the accuracy of the system.

## 5. Performance Statistics

> All following statistics are based on my laptop performance. The configuration of my laptop (HUAWEI MATEBOOK 13) is shown as below:
>
> - RAM: 16GB
> - CPU: AMD Ryzen 5 4600H
> - Frequency: 3.00 GHz

### 5.1 Performance In Small Corpus

- Time for loading index file and searching *one word*: about **0.062** seconds
- Time for generating index file: about **0.672** seconds
- Time for generating output file: about **3.064** seconds
- Time for finish the evaluation (without generating output file): about **0.01** seconds

### 5.2 Performance In Large Corpus

- Time for searching (without loading index file): about **0.031** seconds
- Time for loading index file: about **4.332** seconds
- Time for generating index file: about **26.831** seconds
- Time for generating output file: about **3.563** seconds
- Time for finish the evaluation (without generating output file):  about **0.047** seconds
