## Testing the client agent in AGENS system using rtt method
# Chen Wang, Feb. 18, 2015
# chenw@andrew.cmu.edu
# test_qoe_client.py
import random
import sys
from client_agent import *
from test_utils import *
import logging
import shutil

### Get client name and attache to the closest cache agent
client_name = getMyName()
cache_agent = attach_cache_agent()

## Config logging level
logging.basicConfig(filename='agens_' + client_name + '.log', level=logging.INFO)

## Try several times to confirm the lose connection of client agent
# cache_agent = attach_cache_agent()

print "Client ", client_name, " is connecting to cache agent : ", cache_agent['name']
cache_agent_ip = cache_agent['ip']

### Report cache agent to the centralized controller cmu-agens
update_cache_agent(client_name, cache_agent['name'])

## Get the CDF of Zipf distribution
N = 1000
p = 0.1
zipf_cdf = getZipfCDF(N, p)

### Get the server to start streaming
for i in range(5):
	# Randomly select a video to stream
	vidNum = 1000
	video_id = weighted_choice(zipf_cdf)

	## Testing load based server selection
	method = 'qoe'
	waitRandom(1, 100)
	server_based_client(cache_agent, video_id, method)

