## Testing the client agent in AGENS system
# Chen Wang, Feb. 18, 2015
# chenw@andrew.cmu.edu
import random
from client_agent import *
from test_utils import *

### Get client name and attache to the closest cache agent
client_name = getMyName()
cache_agent = attach_cache_agent()
print "Client ", client_name, " is connecting to cache agent : ", cache_agent['name']
cache_agent_ip = cache_agent['ip']

### Get the server to start streaming
for i in range(1):
	# Randomly select a video to stream
	vidNum = 1000
	video_id = random.randrange(1, vidNum, 1)

	## Testing QoE based server selection
	method = 'qoe'
	waitRandom(1, 100)
	server_based_client(cache_agent_ip, video_id, method)

	## Testing load based server selection
	method = 'load'
	waitRandom(1, 100)
	server_based_client(cache_agent_ip, video_id, method)

	## Testing rtt based server selection
	method = 'rtt'
	waitRandom(1, 100)
	server_based_client(cache_agent_ip, video_id, method)

