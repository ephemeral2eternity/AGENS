import urllib2
import socket
import time
import datetime
import json
import shutil
import os
import logging
import random
from server_selection import *
from chunk.utils import *
from qoe.dash_chunk_qoe import *
from attach_cache_agent import *
from chunk.mpd_parser import *
from chunk.download_chunk import *
import config

def learn_sqs_ave_method(srv_sqs, srv_qoes, window):
    for srv in srv_qoes.keys():
        if len(srv_qoes[srv]) == 0:
            pass
        elif len(srv_qoes[srv]) < window:
            srv_sqs[srv] = sum(srv_qoes[srv])/float(len(srv_qoes[srv]))
        else:
            srv_sqs[srv] = sum(srv_qoes[srv][-window:])/float(window)
    return srv_sqs


def learn_sqs_exp_method(srv_sqs, alpha, qoe, srv):
    srv_sqs[srv] = srv_sqs[srv]*(1 - alpha) + qoe * alpha
    return srv_sqs


def greedy_selection(srv_sqs, candidates):
    # Selecting a server with maximum QoE
    selected_srv = max(srv_sqs.iteritems(), key=itemgetter(1))[0]
    return selected_srv


def epsilon_greedy_selection(srv_sqs, candidates, epsilon):
    rnd = random.random()
    # Selecting a server with maximum QoE
    if rnd < epsilon:
        selected_srv = random.choice(candidates.keys())
    else:
        selected_srv = max(srv_sqs.iteritems(), key=itemgetter(1))[0]
    return selected_srv


def qoe_dash(video_id, cache_agent):
    ## Client name and info
    client = str(socket.gethostname())
    cur_ts = time.strftime("%m%d%H%M")
    client_ID = client + "_" + cur_ts + "_qoedash_" + \
                config.qoe_model + "_" + \
                config.qoe_adaptive_params['sqs_learning_method'] + "_" + \
                config.qoe_adaptive_params['action']

    ## Obtaining the candidate servers
    candidates, cache_agent = ft_get_candidates(config.mngt_srv, cache_agent, video_id, retry=config.retry)

    ## Parameters
    retry = config.retry
    video_name = config.video_name
    video_folder = config.video_folder
    cache_folder = config.cache_path
    adaptive_selection_period = config.adaptive_selection_period
    qoe_params = config.qoe_adaptive_params

    ## Initialize the srv_qoes
    srv_qoes = {}
    srv_sqs = {}
    for srv_name in candidates:
        if candidates[srv_name] == cache_agent:
            srv_qoes[srv_name] = []
            srv_sqs[srv_name] = 5
        else:
            srv_qoes[srv_name] = []
            srv_sqs[srv_name] = 4.5

    ## Select the server to download the video
    if config.qoe_adaptive_params['action'] == "greedy":
        selected_srv = greedy_selection(srv_sqs, candidates)
    elif config.qoe_adaptive_params['action'] == "epsilon":
        selected_srv = epsilon_greedy_selection(srv_sqs, candidates, config.qoe_adaptive_params['epsilon'])
    else:
        print "The input of qoe_adaptive_params.action in config.py is not recognized, using the default greedy action."
        selected_srv = greedy_selection(srv_sqs, candidates)

    server = candidates[selected_srv]
    server_url = server + video_folder

    # Getting the parameters for the video object by readig the mpd file
    video_obj = parse_video_obj(server_url, video_name, retry=retry)

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
        print "The selected server for chunk ", video_obj['nextChunk'], " is ", selected_srv
        server = candidates[selected_srv]
        server_url = server + video_folder
        vchunk_sz, _, error_codes = ft_download_chunk(server_url, retry, video_name, vidChunk)

        ### ===========================================================================================================
        ## Failover control for the timeout of chunk request
        ### ===========================================================================================================
        if vchunk_sz == 0:
            logging.info("["+client_ID+"]Client can not download chunks video " + video_name + " from server " +server + \
                         str(retry) + " times. Stop and exit the streaming!!!")

            ## Write error traces for failed chunk downloading.
            reportErrorQoE(client_ID, server, trace=client_tr)
            update_qoe(cache_agent, server, 0, 0.9, 10)
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

        ## Update the srv_sqs or the srv_qoes according to the sqs_learning method
        if config.qoe_model == "linear":
            current_chunk_qoe = chunk_linear_QoE
        else:
            current_chunk_qoe = chunk_cascading_QoE

        srv_qoes[selected_srv].append(current_chunk_qoe)
        qoe_tr[video_obj['nextChunk']] = current_chunk_qoe

        # print "The selected server and QoE experienced on the server!"
        print srv_sqs, selected_srv
        if config.qoe_adaptive_params['sqs_learning_method'] == "exp":
            srv_sqs = learn_sqs_exp_method(srv_sqs, qoe_params['alpha'], current_chunk_qoe, selected_srv)

        if config.qoe_adaptive_params['sqs_learning_method'] == "ave":
            srv_sqs = learn_sqs_ave_method(srv_sqs, srv_qoes, config.qoe_adaptive_params['win'])

        # Update the average heart_beat_period to the cache agent
        if video_obj['nextChunk'] > adaptive_selection_period - 1:
            print srv_sqs
            ## Select the server to download the video
            if config.qoe_adaptive_params['action'] == "greedy":
                selected_srv = greedy_selection(srv_sqs, candidates)
            elif config.qoe_adaptive_params['action'] == "epsilon":
                selected_srv =  epsilon_greedy_selection(srv_sqs, candidates, config.qoe_adaptive_params['epsilon'])
            else:
                print "The input of qoe_adaptive_params.action in config.py is not recognized, " \
                      "using the default greedy action."
                selected_srv = greedy_selection(srv_sqs, candidates)

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
