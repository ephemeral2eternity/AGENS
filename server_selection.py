# Script to request cache agent to get the streaming server
import json
import urllib2
import random
from attach_cache_agent import *


def server_side_server_selection(cache_agent, video_id, method, isAdaptive, qoeParams, retry):
    ## Handling epsilon method
    if not isAdaptive:
        url = 'http://%s:8615/video/getSrv?vidID=%d&method=%s'%(cache_agent, video_id, method)
    else:
        url = 'http://%s:8615/video/getSrv?vidID=%d&method=%s&sqs=%s&action=%s&epsilon=%.2f' % \
              (cache_agent, video_id, method, qoeParams['sqs_learning_method'], qoeParams['action'], qoeParams['epsilon'])

    # print url
    srv_info = {}
    tries = 0
    while not srv_info and (tries < retry):
        try:
            rsp = urllib2.urlopen(url)
            rsp_headers = rsp.info()
            srv_info = json.loads(rsp_headers['Params'])
        except:
            print "get_srv failed"
            pass
        tries += 1

    if not srv_info:
        return None, None, None

    return srv_info['ip'], srv_info['srv'], srv_info['vidName']


def ft_server_side_selection(mngt_server, cache_agent, video_id, method, isAdaptive, qoeParams=None, retry=3):
    ## Select the server to download the initial chunk
    server, server_name, _ = server_side_server_selection(cache_agent, video_id, method, isAdaptive, qoeParams, retry)

    trials = 0
    while (not server) and (trials < retry):
        cache_agent_name, cache_agent = attach_cache_agent(mngt_server)
        server, server_name, _ = server_side_server_selection(cache_agent, video_id, method, isAdaptive, qoeParams, retry)
        trials += 1

    return server, server_name, cache_agent

def get_candidates(cache_agent, video_id):
    ## Get all candidate servers
    url = 'http://%s:8615/video/getCandidates?vidID=%d'%(cache_agent, video_id)

    # print url
    candidates = {}
    tries = 0
    while not candidates and (tries < config.retry):
        try:
            rsp = urllib2.urlopen(url)
            rsp_headers = rsp.info()
            candidates = json.loads(rsp_headers['Params'])
        except:
            print "getCandidates failed"
            pass
        tries += 1

    return candidates

def ft_get_candidates(mngt_server, cache_agent, video_id, retry=3):
    ## Select the server to download the initial chunk
    candidates = get_candidates(cache_agent, video_id)

    trials = 0
    while (not candidates) and (trials < retry):
        cache_agent_name, cache_agent = attach_cache_agent(mngt_server)
        candidates = get_candidates(cache_agent, video_id)
        trials += 1

    return candidates, cache_agent