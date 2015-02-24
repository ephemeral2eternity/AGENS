import urllib2
import socket
import time
import datetime
import json
import shutil
from dash_utils import *
from dash_qoe import *
from attach_cache_agent import *
from get_srv import *
from mpd_parser import *
from download_chunk import *

### define client_agent method that streams a video using server-side controlled server selection
def server_based_client(cache_agent_ip, video_id, method):
	## ==================================================================================================
	## Get the initial streaming server
	## ==================================================================================================
	srv_info = get_srv(cache_agent_ip, video_id, method)

	if srv_info:
		selected_srv = srv_info['srv']
		selected_srv_ip = srv_info['ip']
		videoName = srv_info['vidName']
	else:
		print "Client streaming failed due to failure in get_srv!!!"
		return

	
	## ==================================================================================================
	## Client name and info
	## ==================================================================================================
	client = str(socket.gethostname())
	cur_ts = time.strftime("%m%d%H%M")
	client_ID = client + "_" + cur_ts + "_" + method


	## ==================================================================================================
	## Parse the mpd file for the streaming video
	## ==================================================================================================
	rsts = mpd_parser(selected_srv_ip, videoName)
	vidLength = int(rsts['mediaDuration'])
	minBuffer = num(rsts['minBufferTime'])
	reps = rsts['representations']

	# Get video bitrates in each representations
	vidBWs = {}
	for rep in reps:
		if not 'audio' in rep:
			vidBWs[rep] = int(reps[rep]['bw'])		

	sortedVids = sorted(vidBWs.items(), key=itemgetter(1))

	# Start streaming from the minimum bitrate
	minID = sortedVids[0][0]
	vidInit = reps[minID]['initialization']
	maxBW = sortedVids[-1][1]

	# Read common parameters for all chunks
	timescale = int(reps[minID]['timescale'])
	chunkLen = int(reps[minID]['length']) / timescale
	chunkNext = int(reps[minID]['start'])

	## ==================================================================================================
	# Start downloading the initial video chunk
	## ==================================================================================================
	curBuffer = 0
	chunk_download = 0
	loadTS = time.time()
	print "[" + client_ID + "] Start downloading video " + videoName + " at " + datetime.datetime.fromtimestamp(int(loadTS)).strftime("%Y-%m-%d %H:%M:%S")
	print "[" + client_ID + "] Selected server for next 12 chunks is :" + selected_srv
	vchunk_sz = download_chunk(selected_srv_ip, videoName, vidInit)
	startTS = time.time()
	print "[" + client_ID + "] Start playing video at " + datetime.datetime.fromtimestamp(int(startTS)).strftime("%Y-%m-%d %H:%M:%S")
	est_bw = vchunk_sz * 8 / (startTS - loadTS)
	print "|-- TS --|-- Chunk # --|- Representation -|-- QoE --|-- Buffer --|-- Freezing --|-- Selected Server --|-- Chunk Response Time --|"
	preTS = startTS
	chunk_download += 1
	curBuffer += chunkLen

	## Traces to write out
	client_tr = {}
	srv_qoe_tr = {}
	alpha = 0.5

	## ==================================================================================================
	# Start streaming the video
	## ==================================================================================================
	while (chunkNext * chunkLen < vidLength) :
		nextRep = findRep(sortedVids, est_bw, curBuffer, minBuffer)
		vidChunk = reps[nextRep]['name'].replace('$Number$', str(chunkNext))
		loadTS = time.time();
		vchunk_sz = download_chunk(selected_srv_ip, videoName, vidChunk)
		curTS = time.time()
		rsp_time = curTS - loadTS
		est_bw = vchunk_sz * 8 / (curTS - loadTS)
		time_elapsed = curTS - preTS

		# Compute freezing time
		if time_elapsed > curBuffer:
			freezingTime = time_elapsed - curBuffer
			curBuffer = 0
			# print "[AGENP] Client freezes for " + str(freezingTime)
		else:
			freezingTime = 0
			curBuffer = curBuffer - time_elapsed

		# Compute QoE of a chunk here
		curBW = num(reps[nextRep]['bw'])
		chunk_QoE = computeQoE(freezingTime, curBW, maxBW)

		print "|---", str(int(curTS)), "---|---", str(chunkNext), "---|---", nextRep, "---|---", str(chunk_QoE), "---|---", \
						str(curBuffer), "---|---", str(freezingTime), "---|---", selected_srv, "---|---", str(rsp_time), "---|"
		
		client_tr[chunkNext] = dict(TS=int(curTS), Representation=nextRep, QoE=chunk_QoE, Buffer=curBuffer, \
			Freezing=freezingTime, Server=selected_srv, Response=rsp_time)
		srv_qoe_tr[chunkNext] = chunk_QoE

		# Select server for next 12 chunks
		if chunkNext%12 == 0 and chunkNext > 4:
			mnQoE = averageQoE(srv_qoe_tr)
			update_qoe(cache_agent_ip, selected_srv, mnQoE, alpha)
			srv_info = get_srv(cache_agent_ip, video_id, method)
			if srv_info:
				selected_srv = srv_info['srv']
				selected_srv_ip = srv_info['ip']
				print "[" + client_ID + "] Selected server for next 12 chunks is :" + selected_srv

		# Update iteration information
		curBuffer = curBuffer + chunkLen
		if curBuffer > 30:
			time.sleep(chunkLen)
		preTS = curTS
		chunk_download += 1
		chunkNext += 1

	## ==================================================================================================
	# Finished steaming videos, write out traces
	## ==================================================================================================
	# trFileName = "./data/" + clientID + "_" + videoName + "_" + str(time.time()) + ".json"
	## Writer out traces files and upload to google cloud
	trFileName = "./dataQoE/" + client_ID + ".json"
	with open(trFileName, 'w') as outfile:
		json.dump(client_tr, outfile, sort_keys = True, indent = 4, ensure_ascii=False)
	# qoe_tr_filename = "./data/" + client_ID + "_QoE.json"
	# with open(qoe_tr_filename, 'w') as outfile:
	#	json.dump(srv_qoe_tr, outfile, sort_keys = True, indent = 4, ensure_ascii = False)
	
	shutil.rmtree('./tmp')




