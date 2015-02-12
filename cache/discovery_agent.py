## Emulate the videos cached in the agent and emulate the content discovery
# Chen Wang, Feb. 12, 2015
# chenw@cmu.edu
# cache.discovery_agent.py

# ================================================================================
# Initialize the cached video id list by ./vidlists/agentID file.
# Above cache list is computed based on 1000 videos with Zipf distribution.
# @ agentID : the cache list file for current agent named as agentID.
# ================================================================================
def read_vidlist(agentID):
	vid_list = []
	vid_list_file = "./vidlists/" + agentID
	with open(vid_list_file) as f:
		vid_list_str = f.readlines()
	vid_list = [int(i) for i in vid_list_str]

	return vid_list

# ================================================================================
# This method is to send out available cached video ids to peers.
# The method will be called every hour to let other new joined nodes known about 
# videos it has cached (This is just emulation).
# @ agentID : the cache list file for current agent named as agentID.
# ================================================================================
def vid_discovery():
