## Testing the long client agent in AGENS system
# Chen Wang, Feb. 18, 2015
# chenw@andrew.cmu.edu
import random
import sys
from long_client_agent import *
from test_utils import *
import logging
import shutil
import random
import sys, getopt

### Get client name and attache to the closest cache agent
client_name = getMyName()
cache_agent = attach_cache_agent()

### Available methods to choose from
methods = ['load', 'rtt', 'hop', 'random', 'qoe']
method = random.choice(methods)

## Set the duration to be 1 hour
duration = 6

if not cache_agent:
	reportErrorQoE(client_name)
	sys.exit()

## Config logging level
logging.basicConfig(filename='agens_' + client_name + '.log', level=logging.INFO)

print "Client ", client_name, " is connecting to cache agent : ", cache_agent['name']
cache_agent_ip = cache_agent['ip']

### Report cache agent to the centralized controller cmu-agens
update_cache_agent(client_name, cache_agent['name'])

## Get the CDF of Zipf distribution
N = 1000
p = 0.1
zipf_cdf = getZipfCDF(N, p)

# Randomly select a video to stream
vidNum = 1000
video_id = weighted_choice(zipf_cdf)

### Get the server to start streaming
long_client_agent(cache_agent, video_id, method, vidNum=duration)
