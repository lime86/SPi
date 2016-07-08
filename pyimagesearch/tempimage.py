import uuid
import os
import datetime
 
class TempImage:
	def __init__(self, basePath="img", timestamp = datetime.datetime.now(), ext=".jpg"):
		# construct the file path
		self.path = "{base_path}/{timestamp}{ext}".format(base_path=basePath, timestamp=timestamp , ext=ext)
 
	def cleanup(self):
		# remove the file
		os.remove(self.path)
