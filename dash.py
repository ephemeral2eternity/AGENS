from chunk.utils import *
from qoe.dash_chunk_qoe import *
from attach_cache_agent import *
from chunk.mpd_parser import *
from chunk.download_chunk import *

def dash(video_name, server, cache_agent):
	## Read from global parameters
	method = config.selection_method
	video_folder = config.video_folder
	heart_beat_period = config.adaptive_selection_period
	retry = config.retry
	cache_folder = config.cache_path

	## Client name and info
	client = str(socket.gethostname())
	cur_ts = time.strftime("%m%d%H%M")
	client_ID = client + "_" + cur_ts + "_dash_" + method

	## Server URL for the video
	server_url = server + video_folder

	video_obj = parse_video_obj(server_url, video_name, retry=3)
	if not video_obj:
		update_qoe(cache_agent, server, 0, 0.9)
		return

	## ==================================================================================================
	# Start downloading the initial video chunk
	## ==================================================================================================
	curBuffer = 0
	chunk_download = 0
	loadTS = time.time()
	print "["+client_ID+"] Start downloading video " + video_name + " at " + datetime.datetime.fromtimestamp(int(loadTS)).strftime("%Y-%m-%d %H:%M:%S")
	print "["+client_ID+"] Server to download the video is :" + server
	vchunk_sz, _, error_codes = ft_download_chunk(server_url, retry, video_name, video_obj['initChunk'])
	startTS = time.time()
	print "["+client_ID+"] Start playing video at " + datetime.datetime.fromtimestamp(int(startTS)).strftime("%Y-%m-%d %H:%M:%S")

	est_bw = vchunk_sz * 8 / (startTS - loadTS)
	print "|-- TS --|-- Chunk # --|- Representation -|-- Linear QoE --|-- Cascading QoE --|-- Buffer --|-- Freezing --|-- Selected Server --|-- Chunk Response Time --|"
	preTS = startTS
	chunk_download += 1
	curBuffer += video_obj['chunkLen']

	## Traces to write out
	client_tr = {}
	qoe_tr = {}

	## ==================================================================================================
	# Start streaming the video
	## ==================================================================================================
	while (video_obj['nextChunk'] * video_obj['chunkLen'] < video_obj['vidLength']) :
		nextRep = findRep(video_obj['sortedVids'], est_bw, curBuffer, video_obj['minBuffer'])
		vidChunk = video_obj['reps'][nextRep]['name'].replace('$Number$', str(video_obj['nextChunk']))
		loadTS = time.time()
		vchunk_sz, _, error_codes = ft_download_chunk(server_url, retry, video_name, vidChunk)

		### ===========================================================================================================
		## Failover control for the timeout of chunk request
		### ===========================================================================================================
		if vchunk_sz == 0:
			logging.info("["+client_ID+"]Client can not download chunks video " + video_name + " from server " +server + \
						 str(retry) + " times. Stop and exit the streaming!!!")

			## Write error traces for failed chunk downloading.
			reportErrorQoE(client_ID, server, trace=client_tr)
			update_qoe(cache_agent, server, 0, 0.9)
			return

		curTS = time.time()
		rsp_time = curTS - loadTS
		est_bw = vchunk_sz * 8 / rsp_time
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
		curBW = num(video_obj['reps'][nextRep]['bw'])
		chunk_linear_QoE = computeLinQoE(freezingTime, curBW, video_obj['maxBW'])
		chunk_cascading_QoE = computeCasQoE(freezingTime, curBW, video_obj['maxBW'])

		print "|---", str(curTS), "---|---", str(video_obj['nextChunk']), "---|---", nextRep, "---|---", str(chunk_linear_QoE), "---|---", \
			str(chunk_cascading_QoE), "---|---", str(curBuffer), "---|---", str(freezingTime), "---|---", server, "---|---", str(rsp_time), "---|"

		client_tr[video_obj['nextChunk']] = dict(TS=curTS, Representation=nextRep, QoE1=chunk_linear_QoE, QoE2=chunk_cascading_QoE, Buffer=curBuffer, \
							Freezing=freezingTime, Server=server, Response=rsp_time)

		qoe_tr[video_obj['nextChunk']] = chunk_cascading_QoE

		# Update the average heart_beat_period to the cache agent
		if video_obj['nextChunk']%heart_beat_period == 0 and video_obj['nextChunk'] > heart_beat_period - 1:
			mnQoE = averageQoE(qoe_tr, heart_beat_period)
			update_qoe(cache_agent, server, mnQoE)

		# Update iteration information
		curBuffer = curBuffer + video_obj['chunkLen']
		if curBuffer > config.buf_size:
			time.sleep(video_obj['chunkLen'])
		preTS = curTS
		chunk_download += 1
		video_obj['nextChunk'] += 1

	## Write out traces after finishing the streaming
	writeTrace(client_ID, client_tr)

	## If tmp path exists, deletes it.
	if os.path.exists(cache_folder):
		shutil.rmtree(cache_folder)

	return client_tr