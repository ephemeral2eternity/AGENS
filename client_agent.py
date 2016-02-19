from server_selection import *
from test_utils import *
from dash import *
from adaptive_dash import *
from qoe_dash import *
import config

def client_agent(given_id=None):
    ## Get the video id.
    if given_id == None:
        video_id = random_select_video(config.video_num, config.zipf_param)
    else:
        video_id = given_id

    ## Get the cache agent ip
    if config.cache_agent == None:
        cache_agent_name, cache_agent_ip = attach_cache_agent(config.mngt_srv, probeNum=config.rtt_probe_num)
    else:
        cache_agent_name = config.cache_agent
        cache_agent_ip = config.cache_agent_ip

    print "QoE models used: ", config.qoe_model, "; Server Selection Method: ", config.selection_method

    if config.isAdaptive:
        ## Periodical Server-side server selection for other methods.
        ## For QoE method
        if (config.selection_method == "qoe") and (config.qoe_adaptive_params['isClientControl']):
            qoe_dash(video_id, cache_agent_ip)
        else:
            adaptive_dash(video_id, cache_agent_ip)
    else:
        ## Get the server ip
        server, server_name, cache_agent_ip = ft_server_side_selection(config.mngt_srv, cache_agent_ip, video_id,
                                                                       config.selection_method, config.isAdaptive)
        ## Do video streaming for the whole video and sticks with the same server.
        video_name = config.video_name
        dash(video_name, server, cache_agent_ip)
    return

if __name__ == "__main__":
    ## QoE Comparison Experiments
    if len(sys.argv) > 1:
        # config.qoe_model = sys.argv[1]
        if sys.argv[1] == "client":
            config.qoe_adaptive_params['isClientControl'] = True
        elif sys.argv[1] == "server":
            config.qoe_adaptive_params['isClientControl'] = False
        elif sys.argv[1] == "dash":
            config.isAdaptive = False
            config.selection_method = "rtt"
        elif sys.argv[1] in ["rtt", "hop", "random", "load"]:
            config.selection_method = sys.argv[1]
    # test_video_id = 34
    # client_agent(test_video_id)
    client_agent()