# Define a function to download a video file folder from google cloud storage
import httplib2
import os
import time
import json
import subprocess

def cache(contentName):
	## Execute gsutil command to cache content
	# The VM should be configured without gsutil authentication
	# authFile = "./info/auth.json"
	# bucketName = "agens-videos"
	# gcs_authenticate(authFile)
	subprocess.Popen(["gsutil", "cp", "-r", "gs://agens-videos/" + contentName, "../videos/"])
