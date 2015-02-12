## Utilities of cache agent
## Chen Wang, Feb. 12, 2015
# chenw@cmu.edu
from get_cache_agents import *

# ================================================================================
# Return the integer or float value of a number string
# @input : s --- the string of the number
# ================================================================================
def num(s):
	try:
		return int(s)
	except ValueError:
		return float(s)

# ================================================================================
# Get external IP address of current agent
# ================================================================================
def getIPAddr():
	data = json.loads(urllib2.urlopen("http://ip.jsontest.com/").read())
	return data["ip"]

# ================================================================================
# Get Current Agent ID from its external IP address
# ================================================================================
def getAgentID():
    cache_agent_ips = get_cache_agent_ips()
    cur_ip = getIPAddr()
    agent_id = ""

	for key, value in cache_agent_ips:
    	if cur_ip in value:
    		agent_id = key
    		break

    return agent_id