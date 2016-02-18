import os

## Parameters to connect to a cache agent or find candidate servers.
mngt_srv = "130.211.191.160"
rtt_probe_num = 3
retry = 5

## Parameters to get video id.
video_num = 1000
zipf_param = 0.1

## Video Player Params
buf_size = 30

## Adaptive Server Selection Parameters
isAdaptive = True

selection_method = "qoe"                    # Options: RTT, HOP, LOAD, RANDOM and QoE according to description in the paper.
qoe_model = "linear"                        # Option: linear, cascading
adaptive_selection_period = 6
qoe_adaptive_params = dict(
    isClientControl = True,                 # True or False determines if it is the client-side control
    sqs_learning_method = "exp",            # Options: exp, ave
    alpha = 0.1,                            # alpha is used in exp_ave
    win = 6,                                # window_size is effective for window average method
    action = "greedy",                      # Options: greedy, epsilon,
    epsilon = 0.1                           # Will only be effective if selection_method is epsilon and isClientControl is true.
)

## Configure the real video name to download
video_name = "BBB"
video_folder = "/videos/"

## File paths
config_file_path = os.path.dirname(__file__)
cache_path = config_file_path + '/tmp/'
try:
    os.stat(cache_path)
except:
    os.mkdir(cache_path)

data_path = config_file_path + '/data/'
try:
    os.stat(data_path)
except:
    os.mkdir(data_path)

