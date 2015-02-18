## Some utilities for testing script
# Chen Wang, Feb. 18, 2014
# chenw@andrew.cmu.edu
## test_utils.py

import random
import time

## Wait for a random interval of time
def waitRandom(minPeriod, maxPeriod):
	## Sleeping a random interval before starting the client agent
	waitingTime = random.randint(minPeriod, maxPeriod)
	print "Before running DASH on the client agent, sleep %d seconds!" % waitingTime
	time.sleep(waitingTime)