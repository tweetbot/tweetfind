import os
import sys
import lucene
import argparse
import shutil
import json

# Arguments Parsing
parser = argparse.ArgumentParser(
    description="TweetFind 1.0 Co-Developed by Amr El Sisy and Anmol Singh Hundal")

parser.add_argument('-ip', '--indexpath', action="store", dest='indexpath', type=str,
                    default='./index', metavar='Output_Path', help='path to index directory.')
parser.add_argument('-tp', '--tweetspath', action="store", dest='tweetspath', type=str,
                    default='./tweets', metavar='Output_Path', help='path to tweets directory.')

# Parse the arguments
parsed_args = parser.parse_args()

# Handle errors related to path
INDEXPATH = os.path.expanduser(parsed_args.indexpath)
TWEETSPATH = os.path.expanduser(parsed_args.tweetspath)

# Normalize the path, so that it works on both Unix Based Systems and Windows
INDEXPATH = os.path.normpath(INDEXPATH) + os.sep
TWEETSPATH = os.path.normpath(TWEETSPATH) + os.sep


from java.io import File
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.document import Document, Field, IntField, DateTools
from org.apache.lucene.index import IndexWriter, IndexWriterConfig
from org.apache.lucene.store import SimpleFSDirectory
from org.apache.lucene.util import Version

if not os.path.isdir(TWEETSPATH):
    print "Tweets Directory does not exist"
    exit()

# Remove the folder if it exists
if os.path.isdir(INDEXPATH):
    print INDEXPATH,"already exists."
    cmd=raw_input("Should I delete existing index directory(Y/n): ")
    if cmd=='Y' or cmd=='y':
        pass
    else:
        print "Then please specify another index directory using -ip flag. See -h for more details"
        exit()
    try:
        shutil.rmtree(INDEXPATH)
        print "Deleted", INDEXPATH
    except shutil.ERROR, (error, message):
        print "Error deleting old directory. Exiting"
        exit()

print "Attempting to create a directory"
try:
    os.makedirs(INDEXPATH)
    print "Directory successfully created."
except OSError, (error, message):
    print "Error creating a directory at the specified path"
    exit()

print "Index path",INDEXPATH
print "Tweets path",TWEETSPATH

lucene.initVM()
indexDir = SimpleFSDirectory(File(INDEXPATH))
writerConfig = IndexWriterConfig(Version.LUCENE_4_10_1, StandardAnalyzer())
writer = IndexWriter(indexDir, writerConfig)

fileno=0
filepath=TWEETSPATH+"twitter_store"+str(fileno)+".txt"
numlines=0
while(os.path.exists(filepath)):
    print "Indexing file",fileno
    with open(filepath, 'r') as input:
        for line in input:
            jsontweet=json.loads(line)
            try:
                doc = Document()
                doc.add(Field("text", jsontweet['text'], Field.Store.YES, Field.Index.ANALYZED))
                doc.add(Field("time", str(jsontweet['timestamp_ms']), Field.Store.YES, Field.Index.NO))
                doc.add(Field("name", jsontweet['user']['screen_name'], Field.Store.YES, Field.Index.ANALYZED))
                if (u'place' in jsontweet.keys()):
                    if jsontweet[u'place']!=None:
                        if(u'full_name' in jsontweet[u'place'].keys()):
                            if jsontweet[u'place'][u'full_name']!=None:
                                doc.add(Field("place", jsontweet[u'place'][u'full_name'], Field.Store.YES, Field.Index.ANALYZED))
                                doc.add(Field("lat", str(jsontweet[u'place'][u'bounding_box'][u'coordinates'][0][0][1]),Field.Store.YES,Field.Index.NO))
                                doc.add(Field("lng", str(jsontweet[u'place'][u'bounding_box'][u'coordinates'][0][0][0]),Field.Store.YES,Field.Index.NO))
                                numlines+=1
                                writer.addDocument(doc)
            except AttributeError:
                print line
            except TypeError:
                print line

    fileno+=1
    filepath=TWEETSPATH+"twitter_store"+str(fileno)+".txt"

writer.close()
print "Indexed", numlines, "tweets"
