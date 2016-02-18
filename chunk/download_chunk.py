import os
import time
import urllib2, socket, urlparse, httplib

def download_chunk(server_addr, vidName, chunk_name):
	url = 'http://' + server_addr + '/' + vidName + '/' + chunk_name
	file_size = 0
	srv_ip_addr = ''

	try:
		u = urllib2.urlopen(url)
		srv_ip_addr = socket.gethostbyname(urlparse.urlparse(u.geturl()).hostname)
		localCache = os.getcwd() + '/tmp/'

		# Create a cache folder locally
		try:
			os.stat(localCache)
		except:
			os.mkdir(localCache)

		localFile = localCache + chunk_name.replace('/', '-')

		f = open(localFile, 'wb')
		meta = u.info()
		file_size = int(meta.getheaders("Content-Length")[0])
		# print "Downloading: %s Bytes: %s" % (localFile, file_size)

		file_size_dl = 0
		block_sz = 8192
		while True:
			buffer = u.read(block_sz)
			if not buffer:
				break

		file_size_dl += len(buffer)
		f.write(buffer)
		status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
		status = status + chr(8)*(len(status)+1)
		# print status,
		# print "Downloaded server address: ", srv_ip_addr

		rsp_code = str(u.getcode())

		f.close()
		u.close()
	except urllib2.HTTPError, err:
		rsp_code = str(err.code)
	except urllib2.URLError, e:
		rsp_code = str(e.code)
	except:
		rsp_code = 'Unknown'

	return (file_size, srv_ip_addr, rsp_code)


### ===========================================================================================================
## Chunk request failure handler
### ===========================================================================================================
def ft_download_chunk(retry_srv, retry_num, video_name, chunk_id):
	vchunk_sz = 0
	error_num = 0
	rsp_code = 'Unknown'
	error_codes = {}
	chunk_srv_ip= retry_srv
	while (vchunk_sz == 0) and (error_num < retry_num):
		# Try to download again the chunk
		(vchunk_sz, chunk_srv_ip, rsp_code) = download_chunk(retry_srv, video_name, chunk_id)
		if not rsp_code.startswith('2'):
			error_codes[time.time()] = rsp_code
			print rsp_code

		error_num = error_num + 1

	return (vchunk_sz, chunk_srv_ip, error_codes)