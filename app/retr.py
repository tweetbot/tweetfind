import lucene

from java.io import File
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.document import Document, Field
from org.apache.lucene.search import IndexSearcher
from org.apache.lucene.index import IndexReader
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.store import SimpleFSDirectory
from org.apache.lucene.util import Version

INDEXPATH="/Users/hundal/tweetfind/index/"

def search(query,max):
    lucene.initVM()
    analyzer = StandardAnalyzer(Version.LUCENE_4_10_1)
    reader = IndexReader.open(SimpleFSDirectory(File(INDEXPATH)))
    searcher = IndexSearcher(reader)

    query = QueryParser(Version.LUCENE_4_10_1, "text", analyzer).parse(query)
    hits = searcher.search(query, max)

    #print "Found %d document(s) that matched query '%s':" % (hits.totalHits, query)
    results=[]
    for hit in hits.scoreDocs:
        doc = searcher.doc(hit.doc)
        cur={}
        cur['text']=doc.get("text")
        cur['name']=doc.get("name")
        cur['time']=doc.get("time")
        cur['place']=doc.get("place")
        cur['lat']=doc.get("lat")
        cur['lng']=doc.get("lng")
        results.append(cur)
    
    return results
       
if __name__=="__main__":
    print search("Black Friday", 10)