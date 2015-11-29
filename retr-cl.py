import sys
import lucene
import os
import argparse

# Arguments Parsing
parser = argparse.ArgumentParser(
    description="TweetFind 1.0 Co-Developed by Amr El Sisy and Anmol Singh Hundal")

parser.add_argument('-ip', '--indexpath', action="store", dest='indexpath', type=str, default='./index', metavar='Output_Path', help='path to index directory.')

# Parse the arguments
parsed_args = parser.parse_args()

# Handle errors related to path
INDEXPATH = os.path.expanduser(parsed_args.indexpath)

# Normalize the path, so that it works on both Unix Based Systems and Windows
INDEXPATH = os.path.normpath(INDEXPATH) + os.sep

if not os.path.isdir(INDEXPATH):
    print "Index Directory does not exist. Shutting Down."
    exit()

from java.io import File
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.document import Document, Field
from org.apache.lucene.search import IndexSearcher
from org.apache.lucene.index import IndexReader
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.store import SimpleFSDirectory
from org.apache.lucene.util import Version

lucene.initVM()
analyzer = StandardAnalyzer(Version.LUCENE_4_10_1)
reader = IndexReader.open(SimpleFSDirectory(File(INDEXPATH)))
searcher = IndexSearcher(reader)

query = QueryParser(Version.LUCENE_4_10_1, "text", analyzer).parse("Black friday")
MAX = 10
hits = searcher.search(query, MAX)

print "Found %d document(s) that matched query '%s':" % (hits.totalHits, query)
for hit in hits.scoreDocs:
    print hit.score, hit.doc, hit.toString()
    doc = searcher.doc(hit.doc)
    print doc.get("text").encode("utf-8")
