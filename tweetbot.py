# *********
#   TweetBot
#   Effort by Amr El Sisy and Anmol Singh Hundal
#   CS 172 - Information Retrieval Systems
# *********

from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from threading import Thread
from threading import current_thread
from Queue import Queue
from reppy.cache import RobotsCache
import reppy
from bs4 import BeautifulSoup
import threading
import itertools
import os
import json
import sys
import argparse
import time
import signal
import urllib2
import re

#VARIABLES THAT CONTAIN THE USER CREDENTIALS TO ACCESS TWITTER API
access_token = "269391427-milwXV0oyqRCIqCwGxIjzQkFb1ACABQztqJbUbK0"
access_token_secret = "pGpnbtxvOWt6yRAQwwFidJDnO67A9Jmv0gOc6NlgvkVsA"
consumer_key = "KHaVQSfjXZhOPvguDpwxOKwXO"
consumer_secret = "zoQDy3Cxoo0hEbjBdkMu3vywrVZL424JFX8i06xERj7tBabm7T"

#Arguments Parsing
parser=argparse.ArgumentParser(description="TweetBot 1.0 Co-Developed by Amr El Sisy and Anmol Singh Hundal")

parser.add_argument('-p','--path', action="store", dest='path', type=str, default='.', metavar='Output_Path', help='path to store files of streamed tweets. By default the path will be current folder.')
parser.add_argument('-s','--size', action="store", dest='size', type=int, default=10, metavar='Filesize', help='specify size of a single file in MegaBytes.')
parser.add_argument('-n','--number', action="store", dest='number', type=int, default=500, metavar='Number_of_Files', help='Specify the number of files we want to save.')
parser.add_argument('-t','--threads', action="store", dest='threadcount', type=int, default=1, choices=xrange(2,5), metavar='Number of parser threads', help='Specify the number of parser threads you want to run. By default there will be only one parser thread. Because of the limitation of the API, there is only one streamer thread.')
parser.add_argument('-d','--debug', action="store_true", dest='debug', default=False, help='Print additional debugging information.')

parsed_args=parser.parse_args()
NUMBEROFFILES=parsed_args.number
FILESIZE=parsed_args.size
DEBUG=parsed_args.debug
PWORKERS=parsed_args.threadcount

# Handle errors related to path
PATH=os.path.expanduser(parsed_args.path)

# Normalize the path, so that it works on both Unix Based Systems and Windows
PATH=os.path.normpath(PATH)+os.sep

# Check if path exits, if not try to create a directory over there
if not os.path.isdir(PATH):
    print "Path does not exist. Attempting to create a directory"
    try:
        os.makedirs(PATH)
        print "Directory successfully created."
    except OSError, (error, message):
        print "Error creating a directory at the specified path"
        exit()

if DEBUG:
    print "path is", PATH

#File Size in bytes
FILESIZEBYTES=FILESIZE*1024*1024

#Listener that catches tweets and puts them on raw tweets list
class listener(StreamListener):
    def on_data(self, data):
        if terminator:
            streamobj.disconnect()

        raw_tweets.put(data,True)
        if DEBUG:
            print "Put on Rawqueue. RawSize", raw_tweets.qsize()

    def on_error(self, status):
        print 'Error on status', status

    def on_limit(self, status):
        print 'Limit threshold exceeded', status

    def on_timeout(self, status):
        print 'Stream disconnected; continuing...'

#Thread class that runs listener
class StreamingWorker(Thread):
    def __init__(self, auth, listener):
        Thread.__init__(self)
        self.auth=auth
        self.listener=listener

    def run(self):
        global streamobj
        streamobj = Stream(self.auth, self.listener)

        #LOCATION OF USA = [-124.85, 24.39, -66.88, 49.38,] filter tweets from the USA, and are written in English
        streamobj.filter(locations = [-124.85, 24.39, -66.88, 49.38,], languages=['en'])
        return

#Thread class that runs parser
class ParsingWorker(Thread):
    def __init__(self):
        Thread.__init__(self)

    def run(self):
        global terminator
        pattern='(http://)(\w*\.)+\w+(/\w*)*'
        #Initialize RobotsCache object
        robots=RobotsCache()
        while 1:
            if terminator:
                break
            cur_raw_tweet=raw_tweets.get(True)
            curtweet=json.loads(cur_raw_tweet)
            if DEBUG:
                print "Got an item from raw_tweets", current_thread().getName()

            # Check if twitter has tate limited you by sending a blank tweet
            if u'text' in curtweet.keys():
                text=curtweet[u'text']
            else:
                print "Rate limited by twitter. Continuing"
                continue

            #Get text and check if it has links using regex.
            link=re.search(pattern,text)
            if link:
                if DEBUG:
                    print "match"
                flink=link.group()

                #Check if crawling is allowed
                try:
                    if robots.allowed(flink,'tweetbot'):
                        soup=BeautifulSoup(urllib2.urlopen(flink),"lxml")

                        #Check if page has title
                        if soup.title:
                            curtweet[u'linkTitle']=soup.title.string
                except reppy.ReppyException:
                    print "Error fetching robots.txt. Continuing"
                    continue
                except urllib2.URLError:
                    print "Bad Url. Report to the developer. Continuing"
                    continue
                except urllib2.HTTPError:
                    print "Error Fetching Web Page. Continuing"
                    continue

            else:
                if DEBUG:
                    print "not match"

            processed_tweets.put(json.dumps(curtweet),True)
            if DEBUG:
                print "Put on processed queue. ProcessedSize", processed_tweets.qsize()

#Thread class that saves tweets from processed queue into a file
class SavingWorker(Thread):
    def __init__(self):
        Thread.__init__(self)

    def run(self):
        #FIXME
        #do path and file verification here.
        global filecounter
        global terminator
        #print "Started saving thead", current_thread().getName()

        while 1:
            if terminator:
                break
            curtweet=processed_tweets.get(True)
            if DEBUG:
                print "Get from processed queue. ProcessedSize", processed_tweets.qsize()

            if(os.path.exists(PATH+"twitter_store"+str(filecounter)+".txt")):
                #This if statement checks if file size is less than the specified file size, if it is, we keep outputting to the file
                if(os.path.getsize(PATH+"twitter_store"+str(filecounter)+".txt") >= FILESIZEBYTES):
                    filecounter+=1
            if filecounter>NUMBEROFFILES:
                terminator=True

            with open(PATH+"twitter_store"+str(filecounter)+".txt", 'a') as output:
                output.write(curtweet+"\n")


#For Streaming
l = listener()
auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

#Global File Counter
filecounter=0

#Global Tweets Lists
raw_tweets=Queue(10)
processed_tweets=Queue(10)

#global terminate status
terminator=False

#Signal Handler for SIGINT (Ctrl-C)
def signal_handler(signal, frame):
    if current_thread().getName()=='MainThread':
        print "\nCleaning up.."
    if current_thread().getName()=='MainThread':
        print "Exiting."
    sys.exit()

signal.signal(signal.SIGINT,signal_handler)

#Error handling for booting threads
try:

    #Start the streamer thread
    streamer=StreamingWorker(auth,l)
    streamer.setDaemon(True)
    streamer.start()

    #start processor threads
    for y in range(PWORKERS):
        pworker=ParsingWorker()
        pworker.setDaemon(True)
        pworker.start()

    #start filesaver thread
    filesaver=SavingWorker()
    filesaver.setDaemon(True)
    filesaver.start()

except threading.ThreadError:
    print "Error booting up threads"


while threading.active_count() > 1:
        time.sleep(0.1)
