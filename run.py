import os.path
import shutil
import subprocess
import datetime
import time
import argparse
import json

ap = argparse.ArgumentParser()
ap.add_argument("-c", "--conf", required=True, help="path to the JSON configuration file")
args = vars(ap.parse_args())

conf = json.load(open(args["conf"]))
tokenpath = conf["tokenpath"]
tmptokenpath = conf["tmptokenpath"]
tmptimepath = conf["tmptimepath"]

if os.path.exists("/dev/video0"):
	print "Camera connected."
else:
	print "No camera found!"
	quit()

if __name__ == "__main__":
	if conf["use_dropbox"]:
		if os.path.isfile(tokenpath):
			shutil.copy(tokenpath, "/tmp/")
		else:
			print "No token."
			quit()
	print "Starting surveillance..."		
	subprocess.Popen(["/home/pi/.virtualenvs/cv/bin/python", "/home/pi/SPi/pi_surveillance.py", "--conf", "/home/pi/SPi/conf.json"])

while True:
	if os.path.isfile(tmptimepath):
		with open(tmptimepath, "r") as timefile:
			line = timefile.readline()
			if not line:
				pass
			else:
				lasttime = datetime.datetime.strptime(line, '%Y-%m-%d %H:%M:%S.%f')
				thistime = datetime.datetime.now()
				print lasttime
				print thistime
				if (thistime - lasttime).seconds > conf["check_seconds"]:
					print "> 10"
				elif (thistime - lasttime).seconds < conf["check_seconds"]:
					print "< 10"
				else:
					print "haha"
		time.sleep(conf["check_seconds"])
	else:
		print "No time file. Restart surveillance."
		#implement the restarting thing
		quit()
				
		



