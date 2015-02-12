## This agent is used to maintain the cache agent overlay for the VoD system
## Chen Wang, Feb. 12, 2015
## chenw@cmu.edu
# Package: cache.overlay_agent

from get_cache_agents import *
from ping import *

def addOverlayPeer(handler, cmdStr):
	global agentID, peerAgents
	params = cmdStr.split('&')
	for param in params:
		if '=' in param:
			items = param.split('=', 2)
			peerAgents.append(items[1])
	answerOverlayQuery(handler)

def deleteOverlayPeer(handler, cmdStr):
	global agentID, peerAgents
	params = cmdStr.split('&')
	for param in params:
		if '=' in param:
			items = param.split('=', 2)
			peerAgents.remove(items[1])
	answerOverlayQuery(handler)

def answerOverlayQuery(handler):
	global agentID, peerAgents
	handler.send_response(200)
	handler.send_header('Content-type', 'text/html')
	handler.send_header('Params', '\n'.join(peerAgents))
	handler.end_headers()
	outHtml = "<h2>The peers of agent " + agentID + "</h2><ul>"
	for peer in peerAgents:
		outHtml = outHtml + "<li>" + peer + "</li>"
	outHtml = outHtml + "</ul>"
	handler.wfile.write(outHtml)

# ================================================================================
# Get Current Agent ID from its external IP address
# ================================================================================
def getAgentID():
    cache_agents = get_cache_agents()
    cur_ip = getIPAddr()
    agent_id = ""

    for agent in cache_agents:
	if cur_ip in agent.public_ips:
		agent_id = agent.name
		break

    return agent_id

# ================================================================================
# Try to add current node as a peer to an existing available node
# Inputs:
# 	name: existing node's name (agentID)
# 	ip: existing node's ip address
# Return:
#	True: successfull. False: failed.
# ================================================================================
def add_peer(ip, PORT, agentID):
	try:
		r = requests.get("http://" + ip + ":" + str(PORT) + "/overlay?add&peer=" + agentID)
		return True
	except requests.ConnectionError, e:
		return False

# ================================================================================
# Add closest available agents as the peer agent
# ================================================================================
def add_peer_agents(agentID, PORT):
	added_peer = ''
	agent_ips = get_cache_agent_ips()

	## Ping all other agents
	peer_rtts = {}
	for agent in agent_ips.keys():
		if agent != agentID:
			rtt = getRTT(agent_ips[agent], 5)
			mnRtt = sum(rtt) / float(len(rtt))
			peer_rtts[agent] = mnRtt

	## Sort all peers by rtts to them
	sorted_peers = sorted(peer_rtts.items(), key=operator.itemgetter(1))
	print sorted_peers

	## Try to add a peer from the closest one
	for peer in sorted_peers:
		if add_peer(agent_ips[peer[0]], PORT, agentID):
			added_peer = peer[0]
			break

	return added_peer

#==========================================================================================
# Notify all other peers to delete itself from peer agent list.
#==========================================================================================
def deletePeers():
	global agentID, PORT, peerAgents
	agent_ips = get_cache_agent_ips()
	while len(peerAgents) > 0:
		peer = peerAgents.pop()
		peer_ip = agent_ips[peer]
		try:
			r = requests.get("http://" + peer_ip + ":" + str(PORT) + "/overlay?delete&peer=" + agentID)
		except requests.ConnectionError, e:
			peerAgents.append(peer)
