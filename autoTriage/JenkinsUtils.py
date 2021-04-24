from jenkinsapi.jenkins import Jenkins
import re
import sys
from re import search
import collections
import itertools
import sys
import gensim 
from gensim.models import Word2Vec 
import nltk
from nltk.corpus import stopwords 
from nltk.tokenize import word_tokenize 
nltk.download('stopwords')

#nltk.download('punkt')

def get_server_instance():
    jenkins_url = 'http://jenkins:8080'
    server = Jenkins(jenkins_url, username = '', password = '')
    return server


# Get details of particular job running on Jenkins server
def get_job_details():
    server = get_server_instance()
    job_name = 'Embrace-api-validation'
    if ( server.has_job(job_name)):
        job_instance = server.get_job(job_name)
        print 'Job Name:%s' %(job_instance.name)
        print 'Job Description:%s' %(job_instance.get_description())
        print 'Is Job running:%s' %(job_instance.is_running())
        print 'Is Job enabled:%s' %(job_instance.is_enabled())
        print 'Last build number :%s' %(job_instance.get_last_buildnumber())

        last_build = job_instance.get_last_buildnumber()
        print last_build
    
        status = job_instance.get_build(last_build).get_status()
        print status

def cleanse_logs():
    infile = "/autoTriage/jenkinsLogs/failed/175.txt"
    outfile = "/autoTriage/jenkinsLogs/new.txt"

    file_stream = open(infile)
    line = file_stream.read()
    regex_str1 = "\[\d+.*\]"
    regex_str2 = "(\>).*"
    regex_str3 = "(\d+.*)(\d)"
    regex_str4 = "[!@#$%^&*+\>{}-]"
    regex_str5 = "( \w )"
    regex_str6 = "(\^\[\[m)"
    #result = any(re.sub(regex_str1, " ", tmp) for regex in []
    result = re.sub("|".join([regex_str1, regex_str2, regex_str3, regex_str4, regex_str5, regex_str6]), "", line)

    sys.stdout = open( outfile, 'w')
    print (result)

def get_stack_trace():
    infile = "/autoTriage/jenkinsLogs/new.txt"
    tracefile = "/autoTriage/jenkinsLogs/trace/175.txt"

    string_to_find_1 = "Exception"
    string_to_find_2 = "java"
    string_to_find_in_next_line = "at"
    trace = open (tracefile, 'w')

    with open(infile) as f:
        before = collections.deque(maxlen=4)
        for line in f:
            if string_to_find_1 in line and string_to_find_2 in line:
                #sys.stdout.writelines(before)
                trace.writelines(before)
                #sys.stdout.write(line)
                trace.write(line)

                next_line = f.next()
                while string_to_find_in_next_line in next_line:
                    #sys.stdout.writelines(next_line)
                    trace.writelines(next_line)
                    next_line = f.next()
        trace.close()
        f.close()

def clean_trace_file():
    tracefile = "/autoTriage/jenkinsLogs/trace/175.txt"
    file_stream = open(tracefile, 'rt')
    lines = file_stream.read()

    regex_str1 = 'at'
    regex_str2 = '(^\s+)'
    regex_str3 = '(\^\[\[m)'
    regex_str4 = '[^a-zA-Z0-9\n\.]'
    regex_str5 = 'm'
    
    result = re.sub("|".join([regex_str1, regex_str2, regex_str3, regex_str4, regex_str5]), "", lines)
    file_stream.close()

    open(tracefile, 'wt').write(result)

def tokenize_data(tracefile):
    lines = tracefile.read()
    
    # Replace escape charater with space
    f = lines.replace("\n", " ")

    data = []
    # iterate through each sentence in the file 
    for i in nltk.sent_tokenize(f): 
        temp = []
        # tokenize the sentence into words 
        for j in nltk.word_tokenize(i): 
            temp.append(j.lower()) 
  
        data.append(temp) 
  
    print data
    return data

def word2vec_similarity():
    # Read the trace file
    tracefile = open ("/autoTriage/jenkinsLogs/trace/175.txt", "r")
    data = tokenize_data(tracefile)

    tracefile2 = open ("/autoTriage/jenkinsLogs/trace/174.txt", "r")
    data2 = tokenize_data(tracefile2)
    
    #tracefile2 = open ("/autoTriage/jenkinsLogs/trace/174.txt", "r")
    str1 = 'org.glassfish.jersey.internal.errors.processerrors.java';
    str2 = 'org.glassfish.jersey.client.internal.httpurlconnector.applyhttpurlconnector.java';
    str3 = 'processerrors'
    str4 = 'applyhttpurlconnector'

    # Create CBOW model 
    model1 = gensim.models.Word2Vec(data, min_count = 1, size = 100, window = 5) 
    print model1
    # Print results 
    print("Cosine similarity  - CBOW : ", model1.similarity(str1, str1)) 
    print("Cosine similarity  - CBOW : ", model1.similarity(str1, str2)) 
    
    # Create Skip Gram model 
    model2 = gensim.models.Word2Vec(data, min_count = 1, size = 100, window = 5, sg = 1) 
    print model2
    # Print results 
    print("Cosine similarity  - Skip Gram : ", model2.similarity(str1, str1))
    print("Cosine similarity  - Skip Gram : ", model2.similarity(str1, str2))

def cosine_similarity():
    list1 = ['connectException', 'parsingException', 'Error', 'Not found', 'Internal error']
    list2 = ['processingexception', 'httpurlconnector', 'connectionrefused', 'Internal error', 'connectException']

    X_list = [x.lower() for x in list1]
    Y_list = [x.lower() for x in list2]
    #print(list(map(lambda x: x.lower(), list1)))
    #print(list(map(lambda x: x.lower(), list2)))
    print X_list
    print Y_list

    # sw contains the list of stopwords 
    sw = stopwords.words('english')  
    l1 =[];l2 =[]

    # remove stop words from the string 
    X_set = {w for w in X_list if not w in sw}  
    Y_set = {w for w in Y_list if not w in sw} 

    rvector = X_set.union(Y_set)  
    for w in rvector: 
        if w in X_set: l1.append(1) # create a vector 
        else: l1.append(0) 
        if w in Y_set: l2.append(1) 
        else: l2.append(0) 
    c = 0
    
    # cosine formula  
    for i in range(len(rvector)): 
            c+= l1[i]*l2[i] 
    cosine = c / float((sum(l1)*sum(l2))**0.5) 
    print("similarity: ", cosine) 



# Get Jenkins version
if __name__ == '__main__':
    #print get_server_instance().version
    #print get_job_details()
    #print cleanse_logs()
    #get_stack_trace()
    #clean_trace_file()
    #word2vec_similarity()
    cosine_similarity()
    

