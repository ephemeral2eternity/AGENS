#!/usr/bin/python
# Cache Agent in Agent based management and control system
# Chen Wang, chenw@cmu.edu
import subprocess 
import argparse
import string,cgi,time
import json
import ntpath
import sys
import urllib2
import sqlite3 as lite
import shutil
import operator
import requests
from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver
from apscheduler.schedulers.background import BackgroundScheduler
from os import curdir, sep
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import os

## Import self-written libraries
from gcs_upload import *
from ping import *
from provision import *
from cache.get_cache_agents import *
from cache.monitor_agent import *
from cache.web_agent import *
from cache.qoe_agent import *
from cache.discovery_agent import *
from cache.overlay_agent import *
from cache.video_agent import *
from cache.cache_content import *

 
## Current Path
CWD = os.path.abspath('.')

## Global Varibles
PORT = 8615     
QoE = {}
agentID = ""
peerAgents = []
delta = 0.5
previousBytes = -1
client_addrs = []
cached_videos = []
bwTrace = {}

# -----------------------------------------------------------------------
class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
    	global cached_videos
        try:
        	## Return nothing for the icon request.
		    if "ico" in self.command:
				return

            elif self.path == '/' :
                page = welcome_page()
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(page)
                return

            ## ---------------------------------------------------------------------------- ##
			## Processing requests related to locally cached videos (Real System)
			## REST API: http://cache_agent_ip:port/videos
			##			 http://cache_agent_ip:port/videos?query
			##			 http://cache_agent_ip:port/videos?cache&vidToCache1&vidToCache2
			##			 http://cache_agent_ip:port/videos?delete&vidToDel1&vidToDel1
			## ----------------------------------------------------------------------------- ##
            elif self.path.startswith('/videos'):
            	if '?' in self.path:
            		cmdStr = self.path.split('?', 2)[1]
            		if 'query' in cmdStr:
            			print "Query local cached videos"
            			queryVideos(self)
            		elif 'cache' in cmdStr:
            			print "cache a new video"
            			cacheVideos(self, cmdStr, cached_videos)
            		elif 'delete' in cmdStr:
            			deleteVideos(self, cmdStr, cached_videos)
            		else:
            			print "[AGENP]Wrong videos command"
            			print "Please try videos?query, delete, cache!"
        		else:
        			page = make_index( self.path.replace('/videos', '../videos') )
        			self.send_response(200)
        			self.send_header('Content-type', 'text/html')
        			self.end_headers()
        			self.wfile.write(page)
        		return

        	## ---------------------------------------------------------------------------- ##
			## Processing requests related to QoE update, query and evaluation
			## REST API: http://cache_agent_ip:port/QoE?query
			##			 http://cache_agent_ip:port/QoE?update&s=srv&q=qoe
			## ----------------------------------------------------------------------------- ##
            elif self.path.startswith("/QoE?"):
            	contents = self.path.split('?', 2)[1]
            	params = contents.split('&')
            	if 'query' in contents:
            		print "[AGENP] Receive QoE query message!"
                	answerQoE(self)
                elif 'update' in contents:
                	rint "[AGENP] Receive QoE update message!"
                	updateQoE(self, params)
                	return

	    ## Processing requests related to Ring Overlay
	    elif self.path.startswith('/overlay?'):
		cmdStr = self.path.split('?', 2)[1]
		if 'query' in cmdStr:
			answerOverlayQuery(self)
		#if 'update' in cmdStr:
		#	answerOverlayUpdate(self, cmdStr)
		if 'add' in cmdStr:
			addOverlayPeer(self, cmdStr)
		if 'delete' in cmdStr:
			deleteOverlayPeer(self, cmdStr)
		return

            elif self.path.endswith(".html"):
                ## print curdir + sep + self.path
                f = open(curdir + sep + self.path)
                #note that this potentially makes every file on your computer readable by the internet
                self.send_response(200)
                self.send_header('Content-type',    'text/html')
                self.end_headers()
                self.wfile.write(f.read())
                f.close()
                return
                
            elif self.path.endswith(".esp"):   #our dynamic content
                self.send_response(200)
                self.send_header('Content-type',    'text/html')
                self.end_headers()
                self.wfile.write("hey, today is the " + str(time.localtime()[7]))
                self.wfile.write(" day in the year " + str(time.localtime()[0]))
                return

            else :
		# Get client addresses
		client_addr = self.client_address[0]
		if client_addr not in client_addrs:
			client_addrs.append(client_addr)
 
		# default: just send the file     
                # filepath = self.path[1:] + '/videos/' # remove leading '/'
                filepath = '../videos' + self.path
                fileSz = os.path.getsize(filepath)
                f = open( os.path.join(CWD, filepath), 'rb' )
                #note that this potentially makes every file on your computer readable by the internet
                self.send_response(200)
                self.send_header('Content-type',    'application/octet-stream')
                self.send_header('Content-Length', str(fileSz))
                self.end_headers()
                self.wfile.write(f.read())
                f.close()
                return
            return # be sure not to fall into "except:" clause ?       

        except IOError as e :  
             # debug     
             print e
             self.send_error(404,'File Not Found: %s' % self.path)

    def do_POST(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write("<HTML><HEAD></HEAD><BODY>POST OK.<BR><BR>");
            self.wfile.write( "File uploaded under name: " + os.path.split(fullname)[1] );
            self.wfile.write(  '<BR><A HREF=%s>back</A>' % ( UPLOAD_PAGE, )  )
            self.wfile.write("</BODY></HTML>");
	
# ================================================================================
# Initialize the global variables by detecting names on the server
# ================================================================================
def initialize():
    global agentID, PORT, peerAgents, delta, QoE, cached_videos

    ## Get current agent name
    agentID = getAgentID()

    ## Initialize QoE vector for all servers
    QoE = initializeQoE(agentID)

    ## Connect current agent to the closest agent add current agent as its peer
    added_peer = add_peer_agents(agentID, PORT)
    if not added_peer:
    	peerAgents.append(added_peer)

    ## Print initialization information in command line
    print "Agent ID: ", agentID
    print "Listening Port: ", str(PORT)
    print "Peer Agents: ", peerAgents
    print "Forgetting Coefficient: ", str(delta)
    print "Initialized QoE Evaluation Vector: ", str(QoE)

    ## Update what have been cached locally in a real system
    # update_cached_videos()

    ## Read the emulated video library list
    cached_video_ids = read_vidlist(agentID)
    print "The emulated cached video ids: ", cached_video_ids


#==========================================================================================
# Main Function of Cache Agent
#==========================================================================================
def main(argv):
    initialize()
    try:
		sched = BackgroundScheduler()
		sched.add_job(bw_monitor, 'interval', minutes=1, args=[agentID, previousBytes, bwTrace])
		sched.add_job(load_monitor, 'interval', minutes=5)
		sched.add_job(demand_monitor, 'interval', minutes=5)
		sched.add_job(vid_discovery, 'interval', minutes=60)
		sched.start()

        server = HTTPServer(('', PORT), MyHandler)
        print 'started httpserver...'
        server.serve_forever()
 
    except KeyboardInterrupt:
        print '^C received, shutting down server'
		# Delete edges
		deletePeers()
        server.socket.close()
		sched.shutdown()

if __name__ == '__main__':
    main(sys.argv)
 
