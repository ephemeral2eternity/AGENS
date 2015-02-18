# Script to connect a client to the closest cache agent
import time
import random
import sys
import json
import operator
import urllib2, socket
from ping import *

# ================================================================================
## Get Client Agent Name
# ================================================================================
def getMyName():
	hostname = socket.gethostname()
	return hostname

# ================================================================================
# Query the list of all cache agents via the centralized monitor server cmu-agens.
# ================================================================================
def get_cache_agents():
	plsrv = '146.148.66.148'
	url = "http://%s:8000/overlay/node/"%plsrv
	req = urllib2.Request(url)
	cache_agents = {}
	try:
		res = urllib2.urlopen(req)
		res_headers = res.info()
		cache_agents = json.loads(res_headers['Params'])
	except urllib2.HTTPError, e:
		print "[Error-AGENP-Client] Failed to obtain avaialble cache agent list!"
	return cache_agents

# ================================================================================
# Ping all servers saved in the dict candidates
# @input : candidates ---- server dict with key as server name and value as server ip
# ================================================================================
def pingSrvs(candidates):
	srvRtts = {}
	for srv in candidates.keys():
		srvRtts[srv] = getMnRTT(candidates[srv], 5)
		print "Ping ", srv, " : ", str(srvRtts[srv]), " ms"
	return srvRtts


# ================================================================================
# Attach the closest cache agent to the client.
# @return : cache_agent_obj is the dict that saves the cache agent name and ip
#			cache_agent_obj['name'] --- the name of cache agent srv
#			cache_agent_obj['ip'] --- the ip of the attached cache agent
# ================================================================================
def attach_cache_agent():
	cache_agent_obj = {}
	all_cache_agents = get_cache_agents()
	srvRtts = pingSrvs(all_cache_agents)
	sorted_srv_rtts = sorted(srvRtts.items(), key=operator.itemgetter(1))
	cache_agent = sorted_srv_rtts[0][0]
	cache_agent_obj['name'] = cache_agent
	cache_agent_obj['ip'] = all_cache_agents[cache_agent]
	return cache_agent_obj