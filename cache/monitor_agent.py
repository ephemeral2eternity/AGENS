## This agent is used to monitor the load, outbound bw and user demand on current cache agent
# Chen Wang, Feb. 12, 2015
# chenw@cmu.edu
# cache.monitor_agent.py
import json
import string,cgi,time
import sys
sys.path.append('../')
from AGENS.gcs_upload import *

# ================================================================================
# Probe outbound traffic every 1 minutes. 
# ================================================================================
def bw_monitor():
	global agentID, previousBytes, bwTrace
	if previousBytes < 0:
		previousBytes = get_tx_bytes()
	else:
		curBytes = get_tx_bytes()
		out_bw = (curBytes - previousBytes) * 8 / (60.0 * 1024 * 1024)
		previousBytes = curBytes
		print "[AGENP-Monitoring]Outbound bandwidth is " + str(out_bw) + " Mbps!"

		## Record the bw in bwTraces and dump it per hour 60 * 60 / 5 = 720
		curTS = time.time()	

		# Save TS to google cloud
		bwTrace[curTS] = out_bw
		if len(bwTrace) >= 720:
			bwTraceFile = "./data/" + agentID + "-bw-" + str(int(curTS)) + ".json"
			with open(bwTraceFile, 'w') as outfile:
				json.dump(bwTrace, outfile, sort_keys = True, indent = 4, ensure_ascii = False)

		# Upload the bwTrace file to google cloud
		bucketName = "agens-data"
		gcs_upload(bucketName, bwTraceFile)

		# Client bwTrace buffer
		bwTrace = {}

		# Delete local bwTrace file
		shutil.rmtree(bwTraceFile)

# ================================================================================
# Monitor user demand on a cache agent. 
# User demand is measured by the number of unique flows connecting to the same 
# cache agent in 1 minutes.
# ================================================================================
def demand_monitor():
	global client_addrs, con
	demand = len(client_addrs)
	print "[AGENP-Monitoring] There are " + str(len(client_addrs)) + \
		" clients connecting to this server in last 1 minutes."
	
	## Record the user demand per 1 minute
	curTS = time.time()

	# Save TS to the database
	try:
	connection = lite.connect('agens.db')
	cur = connection.cursor()
	cur.execute('''INSERT INTO DEMAND(TS, USERNUM) VALUES(?, ?)''', (int(curTS), demand))
	connection.commit()
	connection.close()
	except lite.Error, e:
	if connection:
		connection.rollback()
	print "SQLITE DB Error %s" % e.args[0]
		
	print "==================================================="
	for client in client_addrs:
		print client
	print "==================================================="
	# Clear client agents to empty
	client_addrs[:] = []
	

# ================================================================================
# Read outbound bytes in 5 seconds. 
# ================================================================================
def get_tx_bytes():
	file_txbytes = open('/sys/class/net/eth0/statistics/tx_bytes')
	lines = file_txbytes.readlines()
	tx_bytes = int(lines[0])
	return tx_bytes
