## Testing the long client agent in AGENS system
# Chen Wang, Feb. 18, 2015
# chenw@andrew.cmu.edu
import random
import sys
from long_client_agent import *
from test_utils import *
import logging
import shutil
import sys, getopt

def test_long_client(method, duration):
	### Get client name and attache to the closest cache agent
	client_name = getMyName()
	cache_agent = attach_cache_agent()

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


def main(argv):
	method = ''
	duration = 1
	try:
		opts, args = getopt.getopt(argv,"hm:d:",["method=","duration="])
	except getopt.GetoptError:
		print 'test.py -m <method> -d <number of 10 minutes>'
		sys.exit(2)

	for opt, arg in opts:
		if opt == '-h':
			print 'test_long_client.py -m <method> -d <number of 10 minutes>'
			sys.exit()
		elif opt in ("-m", "--method"):
			method = arg
		elif opt in ("-d", "--duration"):
			duration = int(arg)
	
	print 'Testing method is', method
	print 'The duration is around', str(duration * 10), ' minutes!'

	test_long_client(method, duration)

if __name__ == "__main__":
   main(sys.argv[1:])
