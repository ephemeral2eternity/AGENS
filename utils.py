import time
import shutil
import urllib2
from ipinfo.ipinfo import *
import config

# ================================================================================
## Get Client Agent External IP Address
# ================================================================================
def get_ext_ip():
	try:
		response = urllib2.urlopen("http://curlmyip.com")
	except:
		try:
			response = urllib2.urlopen("http://myexternalip.com/raw")
		except:
			return ""

	ext_ip_line = response.read()
	ext_ip = ext_ip_line.rstrip()
	return ext_ip

# ================================================================================
## Get Client Agent Hostname
# ================================================================================
def getMyName():
	hostname = socket.gethostname()
	not_found_names = {
		"221.199.217.144" : "planetlab1.research.nicta.com.au",
		"221.199.217.145" : "planetlab2.research.nicta.com.au"
	}

	if '.' not in hostname:
		ext_ip = get_ext_ip()
		myInfo = ipinfo(ext_ip)
		if "hostname" in myInfo.keys():
			if '.' in myInfo["hostname"]:
				hostname = myInfo["hostname"]
		elif ext_ip in not_found_names.keys():
			hostname = not_found_names[ext_ip]

		if '.' not in hostname:
			hostname = ext_ip
	return hostname

## ==================================================================================================
# Finished steaming videos, write out traces
# @input : client_ID --- the client ID to write traces
# 		   client_tr --- the client trace dictionary
## ==================================================================================================
def writeTrace(client_ID, client_tr):
	trFileName = config.data_path + client_ID + ".json"
	with open(trFileName, 'w') as outfile:
		json.dump(client_tr, outfile, sort_keys = True, indent = 4, ensure_ascii=False)

## ==================================================================================================
# Write out Error Client Traces
# @input : client_ID --- the client ID to write traces
## ==================================================================================================
def reportErrorQoE(client_ID, srv=None, trace=None):
	client_tr = {}
	curTS = time.time()
	if trace:
		client_error_ID = "crash_" + client_ID
		writeTrace(client_error_ID, trace)

	client_tr["0"] = dict(TS=int(curTS), QoE=0, Server=srv, Representation=-1, Freezing=-1, Response=1000, Buffer=0)
	writeTrace(client_ID, client_tr)