## Implement the real video query and updating system.
## Chen Wang, Feb. 12, 2015
## chenw@cmu.edu
# Package: cache.video_agent
import os
import ntpath
from cache.cache import *

#==========================================================================================
# Get the real videos cached on current apache web server
# And return the html page showing the list of real cached videos 
#==========================================================================================
def queryVideos(handler):
    cached_videos = update_cached_videos()
	handler.send_response(200)
	handler.send_header('Content-type', 'text/html')
	handler.send_header('Params', str(cached_videos))
	handler.end_headers()
	cached_video_page = "<h2>Locally cached videos: </h2><ul>"

	for video in cached_videos:
		cached_video_page = cached_video_page + "<li>" + video + "</li>"

	cached_video_page = cached_video_page + "</ul>"
	handler.wfile.write(cached_video_page)

#==========================================================================================
# Download videos specified by cmdStr to local video folder
# And return the html page showing the list of real cached videos 
#==========================================================================================
def cacheVideos(handler, cmdStr, cached_videos):
	params = cmdStr.split('&')
	to_cache = []
	for video in params:
		if 'cache' not in video:
			if video not in cached_videos:
				to_cache.append(video)
				cache(video)
				cached_videos.append(video)
			else:
				print video + " is cached locally!"

	if to_cache:	
		video_cache_page = "<h2>Starts caching videos: </h2><ul>"
		for v in to_cache:
			video_cache_page = video_cache_page + "<li>" + video + "</li>"
		video_cache_page = video_cache_page + "</ul>"
	else:
		video_cache_page = "<h2>Videos already cached!</h2>"
	handler.send_response(200)
	handler.send_header('Content-type', 'text/html')
	handler.end_headers()
	handler.wfile.write(video_cache_page)

#==========================================================================================
# Delete videos specified by cmdStr from local video folder
# And return the html page showing the deleted videos and the
# list of real cached videos available on current server
#==========================================================================================
def deleteVideos(handler, cmdStr, cached_videos):
	params = cmdStr.split('&')
	for video in params:
		if "delete" not in video:
			print "delete locally cached video ", video
			if video in cached_videos:
				try:
					subprocess.Popen(["rm", "-r", "-f", "../videos/"+ video])
				except:
					failPage = "<h2>Fail to delete video " + video + "<h2>"
					handler.send_response(200)
					handler.send_header('Content-type', 'text/html')
					handler.end_headers()
					handler.wfile.write(failPage)
		
				successPage = "<h2>Successfully delete video: " + video + "<h2>"
				handler.send_response(200)
				handler.send_header('Content-type', 'text/html')
				handler.end_headers()
				handler.wfile.write(successPage)
				cached_videos.remove(video)
			else:
				errPage = "<h2>Wrong Video to delete: " + video + "<h2>"
				handler.send_response(200)
				handler.send_header('Content-type', 'text/html')
				handler.end_headers()
				handler.wfile.write(errPage)


# ================================================================================
# Show locally cached videos for current cache agent. 
# ================================================================================
def update_cached_videos():
    cached_videos = []
    abspath = os.path.abspath("../videos/") # ; print abspath
    dirs = filter(os.path.isdir, [os.path.join(abspath, f) for f in os.listdir(abspath)]) # ; print flist
    print "Locally cached videos are: ", dirs
    for video in dirs:
		cached_videos.append(ntpath.basename(video))
	return cached_videos