# Script to request cache agent to get the streaming server
import json
import urllib2

# ================================================================================
# Query the closest cache agent to get the selected server according to the method
# @input : cache_agent_ip ---- The ip address of the closest cache agent
#		   video_id ---- the requested video id
#          method ---- the method to select the server including "load", "rtt" and "qoe"
# ================================================================================
def get_srv(cache_agent_ip, video_id, method):
	url = 'http://%s:8615/video/getSrv?vidID=%d&method=%s'%(cache_agent_ip, video_id, method)
	print url
	try:
		rsp = urllib2.urlopen(url)
		rsp_headers = rsp.info()
		srv_info = json.loads(rsp_headers['Params'])
		return srv_info
	except:
		print "get_srv failed"
		return {}

