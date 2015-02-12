## Implement the QoE query, update, and evaluate agent for current cache agent
## Chen Wang, Feb. 12, 2015
## chenw@cmu.edu
# Package: cache.qoe_agent

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import json

## Self written libraries
from get_cache_agents import *

# ================================================================================
# Initialize the QoE vector for all servers on current agent
# ================================================================================
def initializeQoE(cur_agent):
	QoE = {}
	cache_agents = get_cache_agent_names()
    for agent in cache_agents:
		if agent is not cur_agent:
			QoE[agent] = 4.0
	QoE[cur_agent] = 5.0
	return QoE

def getQoE(params):
	qUpdates = {}
	for param in params:
		if '=' in param:
			items = param.split('=', 2)
			qUpdates[items[0]] = items[1]
	return qUpdates

def answerQoE(handler, QoE):
	handler.send_response(200)
	handler.send_header('Content-type', 'text/html')
	handler.send_header('Params', json.dumps(QoE))
	handler.end_headers()
	handler.wfile.write("Updated QoE is: " + json.dumps(QoE))

def updateQoE(handler, params, QoE):
	if len(params) >= 2:
		qupdates = getQoE(params)
		for s in qupdates.keys():
        		QoE[s] = num(qupdates[s]) * delta + QoE[s] * (1 - delta)
			print "[AGENP] Updated QoE is : " + str(QoE[s]) + " for server " + s
	answerQoE(handler)