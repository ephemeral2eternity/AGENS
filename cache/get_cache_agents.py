import json
from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver
from gce_authenticate import *

def get_cache_agents():
	driver = gce_authenticate("./info/auth.json")

	# List all instances
	cache_agents = []
	nodes = driver.list_nodes()
	for node in nodes:
		if "cache" in node.name:
			cache_agents.append(node)

	return cache_agents

def get_cache_agent_names():
	nodes = get_cache_agents()
	agent_names = []
	for node in nodes:
		agent_names.append(node.name)
	return agent_names

def get_cache_agent_ips():
	nodes = get_cache_agents()
	# List all instances
	agent_ips = {}
	for node in nodes:
		if "cache" in node.name:
			agent_ips[node.name] = node.public_ips[0]

	return agent_ips
