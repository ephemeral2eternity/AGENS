# AGENS
The client agent for AGENS system that can be run in Planetlab nodes.

## Main components in AGENS system
- Server-side controled server selection
  * Connect to the closest cache agent
    * Via PINGs
    * Via DNS
  * The QoE updating to the closest cache agent
  * Periodically Query the streaming server from the closest cache agent (Period: 1 minute)
    * Get the server with the content and with the least server load
    * Get the server with the content and with the least RTT
    * Get the server with the content and with the best QoE
  * Basic DASH Streaming Client (Streaming from the server got every 1 minute)
- Client side controled Server Selection
  * Connect to the closest cache agent (Similar with Server-side controlled server selection)
  * The QoE update to the cache agent
    * Only report srv's QoE if client sticks with the server for more than 12 chunks (1 minute)
  * Only query 2 candidate serves before the streaming starts
  * DASH streaming with 2 candidate servers
  
## Usage

