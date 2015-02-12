# Define a function to update a file to a google cloud storage bucket
#from gcs_authenticate import *
import subprocess

def gcs_upload(bucketName, uploadFile):
	# Execute gsutil command to upload the file "uploadFile"
	# authFile = "./info/auth.json"
	# gcs_authenticate(authFile)
	subprocess.call(["gsutil", "cp", uploadFile, "gs://" + bucketName])
