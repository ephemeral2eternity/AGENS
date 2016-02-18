import os
#import requests     PlanetLab nodes do not have package requests
import urllib2
import re
import copy
import operator
import sys
import xml.etree.ElementTree as ET

def num(s):
	try:
		return int(s)
	except ValueError:
		return float(s)

def mpd_parser(server_address, videoName):

	# server_address = 'ec2-54-76-42-64.eu-west-1.compute.amazonaws.com'
	# videoName = 'st'
	mpdFile = 'stream.mpd'

	url = 'http://' + server_address + '/' + videoName + '/' + mpdFile
	print "MPD URL: ", url
	#r = requests.get(url)

	try:
		r = urllib2.Request(url)
		f = urllib2.urlopen(r)
		mpdString = f.read()
		# mpdString = str(r.content)
		# print mpdString
	except:
		print "Failed to get the url :", url
		return {}

	representations = {}

	root = ET.fromstring(mpdString)
	mediaLengthStr = root.get('mediaPresentationDuration')[2:]
	mlA = re.findall(r'\d+', mediaLengthStr)
	if len(mlA) == 3:
		mediaLength = num(mlA[0])*3600 + num(mlA[1])*60 + num(mlA[2])
	elif len(mlA) == 2:
		mediaLength = num(mlA[0])*60 + num(mlA[1])
	elif len(mlA) == 1:
		mediaLength = num(mlA[0])
	else:
		print 'Parsing mpd file error, unrecognized mediaPresentationDuration!'
		sys.exit(1)

	minBufferTime = num(root.get('minBufferTime')[2:-1])
	for period in root:
		for adaptSet in period: 
			for rep in adaptSet:
				repType = rep.get('mimeType')
				repID = rep.get('id')
				repBW = rep.get('bandwidth')
				for seg in rep:
					initSeg = seg.get('initialization')
					segName = seg.get('media')
					segStart = seg.get('startNumber')
					segLength = seg.get('duration')
					timescale = seg.get('timescale')
				representations[repID] = dict(mtype=repType, name=segName, bw=repBW, initialization=initSeg, start=segStart, length=segLength, timescale=timescale)

	# for item in representations:
	#	print item
	f.close()

	return {'representations' : representations, 'mediaDuration':mediaLength, 'minBufferTime': minBufferTime}


### ===========================================================================================================
## mpd_parser failure handler
### ===========================================================================================================
def ft_mpd_parser(retry_srv, retry_num, video_name):
	error_num = 0
	rsts = ''
	while (not rsts) and (error_num < retry_num):
		rsts = mpd_parser(retry_srv, video_name)
		error_num += 1

	return rsts


def parse_video_obj(server, video_name, retry=3):
	video_obj = dict()
	## ==================================================================================================
	## Parse the mpd file for the streaming video
	## ==================================================================================================
	rsts = ft_mpd_parser(server, retry, video_name)

	### ===========================================================================================================
	## Add mpd_parser failure handler
	### ===========================================================================================================
	trial_time = 0
	while (not rsts) and (trial_time < retry):
		rsts = ft_mpd_parser(server, retry, video_name)
		trial_time = trial_time + 1

	if not rsts:
		return {}

	video_obj['vidLength'] = int(rsts['mediaDuration'])
	video_obj['minBuffer'] = num(rsts['minBufferTime'])
	video_obj['reps'] = rsts['representations']

	# Get video bitrates in each representations
	vidBWs = {}
	for rep in video_obj['reps']:
		if not 'audio' in rep:
			vidBWs[rep] = int(video_obj['reps'][rep]['bw'])
	video_obj['vidBWs'] = copy.deepcopy(vidBWs)

	video_obj['sortedVids'] = sorted(vidBWs.items(), key=operator.itemgetter(1))

	# Start streaming from the minimum bitrate
	minID = video_obj['sortedVids'][0][0]
	video_obj['initChunk'] = video_obj['reps'][minID]['initialization']
	video_obj['maxBW'] = video_obj['sortedVids'][-1][1]

	# Read common parameters for all chunks
	video_obj['timescale'] = int(video_obj['reps'][minID]['timescale'])
	video_obj['chunkLen'] = int(video_obj['reps'][minID]['length']) / video_obj['timescale']
	video_obj['nextChunk'] = int(video_obj['reps'][minID]['start'])

	return video_obj

