# Script to connect a client to the closest cache agent
import time
import random
import sys
import json
import logging
import sys
import operator
import urllib2, socket
from monitor.ping import *
from utils import *

# ================================================================================
## Get Client Agent Name
# ================================================================================
def getMyName():
	hostname = socket.gethostname()
	return hostname

# ================================================================================
# Query the list of all cache agents via the centralized monitor server cmu-agens.
# ================================================================================
def get_cache_agents(mngt_srv):
	url = "http://%s:8000/overlay/node/"%mngt_srv
	req = urllib2.Request(url)
	cache_agents = {}
	try:
		res = urllib2.urlopen(req, timeout=1)
		res_headers = res.info()
		cache_agents = json.loads(res_headers['Params'])
	except:
		print "[Error-AGENP-Client] Failed to obtain availalble cache agent list!"
		pass
	return cache_agents

# ================================================================================
# Ping all servers saved in the dict candidates
# @input : candidates ---- server dict with key as server name and value as server ip
# ================================================================================
def pingSrvs(candidates, probeNum=3):
	srvRtts = {}
	for srv in candidates.keys():
		srvRtts[srv] = getMnRTT(candidates[srv], probeNum)
		# print "Ping ", srv, " : ", str(srvRtts[srv]), " ms"
	return srvRtts

# ================================================================================
# Check if cache agent is alive
# @input : cache_agent_ip ---- the ip address of cache agent to test
# @return : True --- alive
#			False --- dead
# ================================================================================
def is_alive(cache_agent_ip):
	url = 'http://%s:8615/video/getSrv?vidID=1&method=rtt'%cache_agent_ip
	print 'Testing if cache agent is alive:', url
	try:
		rsp = urllib2.urlopen(url)
		rsp_headers = rsp.info()
		srv_info = json.loads(rsp_headers['Params'])
		if srv_info:
			return True
		else:
			return False
	except:
		return False


# ================================================================================
# Attach the closest cache agent to the client.
# @return : cache_agent_obj is the dict that saves the cache agent name and ip
#			cache_agent_obj['name'] --- the name of cache agent srv
#			cache_agent_obj['ip'] --- the ip of the attached cache agent
# ================================================================================
def attach_cache_agent(mngt_srv, probeNum=3):
	cache_agent_obj = {}

	## Try several times before exit
	all_cache_agents = get_cache_agents(mngt_srv)
	trial_num = 0
	while not all_cache_agents and trial_num < 10:
		all_cache_agents = get_cache_agents(mngt_srv)
		trial_num = trial_num + 1

	if all_cache_agents:
		srvRtts = pingSrvs(all_cache_agents, probeNum=3)
		sorted_srv_rtts = sorted(srvRtts.items(), key=operator.itemgetter(1))
		cache_agent = sorted_srv_rtts[0][0]
		cache_agent_obj['name'] = cache_agent
		cache_agent_obj['ip'] = all_cache_agents[cache_agent]
		if not is_alive(cache_agent_obj['ip']):
			print "Cannot connect to the cache agent: ", cache_agent
			exit()
	else:
		logging.info("Agens client can not connect to any cache agent 20 times. The client might lose connection!!!")

	return str(cache_agent_obj['name']), str(cache_agent_obj['ip'])