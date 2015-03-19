import urllib2
import socket
import time
import datetime
import json
import shutil
import os
import math
import logging
from dash_utils import *
from dash_qoe import *
from attach_cache_agent import *
from get_srv import *
from mpd_parser import *
from download_chunk import *
from client_utils import *

## ==================================================================================================
# define client_agent method that streams a video using server-side controlled server selection
# @input : cache_agent_obj --- the dict denoting cache agent ip and name
#		   video_id --- the video id the client is requesting
#		   method --- selecting server according to which method
#					  Available methods are: load, rtt, hop, random, qoe
## ==================================================================================================
def long_client_agent(cache_agent_obj, video_id, method, vidNum=5, expID=None):
	## Read info from cache_agent_obj
	cache_agent_ip = cache_agent_obj['ip']
	cache_agent = cache_agent_obj['name']

	## ==================================================================================================
	## Client name and info
	## ==================================================================================================
	client = str(socket.gethostname())
	if expID:
		client_ID = client + "_" + expID + "_" + method
	else:
		cur_ts = time.strftime("%m%d%H%M")
		client_ID = client + "_" + cur_ts + "_" + method
	videoName = 'BBB'

	## ==================================================================================================
	## Get the initial streaming server
	## ==================================================================================================
	srv_info = get_srv(cache_agent_ip, video_id, method)

	if not srv_info:
		logging.info("[" + client_ID + "]Agens client can not get srv_info for video " + str(video_id) + " with method " + method + \
			" on cache agent " + cache_agent_ip + ". Try again to get the srv_info!!!")
		srv_info = get_srv(cache_agent_ip, video_id, method)
		if not srv_info:
			logging.info("[" + client_ID + "]Agens client can not get srv_info for video " + str(video_id) + " with method " + method + \
			" on cache agent " + cache_agent_ip + " twice. Stop the streaming!!!")

			if method == "qoe":
				trial_time = 0
				while not srv_info and trial_time < 10:
					cache_agent_obj = attach_cache_agent()
					cache_agent_ip = cache_agent_obj['ip']
					cache_agent = cache_agent_obj['name']
					srv_info = get_srv(cache_agent_ip, video_id, method)
					trial_time = trial_time + 1
				if not srv_info:
					reportErrorQoE(client_ID, cache_agent_obj['name'])
					return
			else:
				## Write out 0 QoE traces for clients.
				reportErrorQoE(client_ID, cache_agent_obj['name'])
				return

	## ==================================================================================================
	## Parse the mpd file for the streaming video
	## ==================================================================================================
	rsts = mpd_parser(srv_info['ip'], videoName)

	## Add mpd_parser failure handler
	if not rsts:
		logging.info("[" + client_ID + "]Agens client can not download mpd file for video " + videoName + " from server " + srv_info['srv'] + \
					"Stop and exit the streaming for methods other than QoE. For qoe methods, get new srv_info!!!")

		if method == "qoe":
			update_qoe(cache_agent_ip, srv_info['srv'], 0, 0.9)
			srv_info = get_srv(cache_agent_ip, video_id, method)
			if not srv_info:
				rsts = mpd_parser(srv_info['ip'], videoName)
			else:
				rsts = ''
			trial_time = 0
			while not rsts and trial_time < 10:
				cache_agent_obj = attach_cache_agent()
				cache_agent_ip = cache_agent_obj['ip']
				cache_agent = cache_agent_obj['name']
				srv_info = get_srv(cache_agent_ip, video_id, method)
				rsts = mpd_parser(srv_info['ip'], videoName)
				trial_time = trial_time + 1
			if not rsts:
				reportErrorQoE(client_ID, srv_info['srv'])
				return
		else:
			update_qoe(cache_agent_ip, srv_info['srv'], 0, 0.9)
			reportErrorQoE(client_ID, srv_info['srv'])
			return



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
	print "[" + client_ID + "] Selected server for next 12 chunks is :" + srv_info['srv']
	vchunk_sz = download_chunk(srv_info['ip'], videoName, vidInit)
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
	alpha = 0.1
	error_num = 0

	## Define how long the video is
	vid_len_in_chunks = int(vidLength / chunkLen + 1)
	vid_len = vid_len_in_chunks * vidNum

	## ==================================================================================================
	# Start streaming the video
	## ==================================================================================================
	while (chunkNext < vid_len) :
		nextRep = findRep(sortedVids, est_bw, curBuffer, minBuffer)

		chunkID = chunkNext % vid_len_in_chunks
		print chunkNext, chunkID, vid_len_in_chunks
		vidChunk = reps[nextRep]['name'].replace('$Number$', str(chunkID))

		loadTS = time.time();
		vchunk_sz = download_chunk(srv_info['ip'], videoName, vidChunk)
		
		## Try 10 times to download the chunk
		while vchunk_sz == 0 and error_num < 3:
			# Try to download again the chunk
			vchunk_sz = download_chunk(srv_info['ip'], videoName, vidChunk)
			error_num = error_num + 1

		if vchunk_sz == 0:
			logging.info("[" + client_ID + "]Agens client can not download chunks video " + videoName + " from server " + srv_info['srv'] + \
			" 3 times. Stop and exit the streaming!!!")

			## Write out 0 QoE traces for clients.
			if method == "qoe":
				update_qoe(cache_agent_ip, srv_info['srv'], 0, 0.9)
				srv_info = get_srv(cache_agent_ip, video_id, method)
				trial_time = 0
				while not srv_info and trial_time < 10:
					cache_agent_obj = attach_cache_agent()
					cache_agent_ip = cache_agent_obj['ip']
					cache_agent = cache_agent_obj['name']
					srv_info = get_srv(cache_agent_ip, video_id, method)
					trial_time = trial_time + 1
				if not srv_info:
					reportErrorQoE(client_ID, srv_info['srv'], trace=client_tr)
					return
				vchunk_sz = download_chunk(srv_info['ip'], videoName, vidChunk)
			else:
				update_qoe(cache_agent_ip, srv_info['srv'], 0, 0.9)
				reportErrorQoE(client_ID, srv_info['srv'], trace=client_tr)
				return
		else:
			error_num = 0

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

		print "|---", str(int(curTS)), "---|---", str(chunkNext), "---|---", str(chunkID), "---|---", nextRep, "---|---", str(chunk_QoE), "---|---", \
						str(curBuffer), "---|---", str(freezingTime), "---|---", srv_info['srv'], "---|---", str(rsp_time), "---|"
		
		client_tr[chunkNext] = dict(TS=int(curTS), Representation=nextRep, QoE=chunk_QoE, Buffer=curBuffer, \
			Freezing=freezingTime, Server=srv_info['srv'], Response=rsp_time)
		srv_qoe_tr[chunkNext] = chunk_QoE

		# Select server for next 12 chunks
		if chunkNext%12 == 0 and chunkNext > 4:
			mnQoE = averageQoE(srv_qoe_tr)
			update_qoe(cache_agent_ip, srv_info['srv'], mnQoE, alpha)
			if method == "qoe":
				srv_info = get_srv(cache_agent_ip, video_id, method)
				if srv_info:
					print "[" + client_ID + "] Selected server for next 12 chunks is :" + srv_info['srv']

		# Update iteration information
		curBuffer = curBuffer + chunkLen
		if curBuffer > 30:
			time.sleep(chunkLen)
		preTS = curTS
		chunk_download += 1
		chunkNext += 1

	## Write out traces after finishing the streaming
	writeTrace(client_ID, client_tr)

	## If tmp path exists, deletes it.
	if os.path.exists('./tmp'):
		shutil.rmtree('./tmp')

	return