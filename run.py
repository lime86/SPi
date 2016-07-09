import os
import signal
import shutil
import psutil
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

#if os.path.exists(tmptokenpath):
	#os.chmod(tmptokenpath, 0666)

pid = 0

def start_surveillance():
	print datetime.datetime.now(), "Starting surveillance..."
	surveillance = subprocess.Popen(["/home/pi/.virtualenvs/cv/bin/python", "/home/pi/SPi/pi_surveillance.py", "--conf", "/home/pi/SPi/conf.json"])
	return surveillance.pid

if os.path.exists("/dev/video0"):
	print "Camera connected."
else:
	print "No camera found!"
	quit()

if __name__ == "__main__":
	if conf["use_dropbox"]:
		if os.path.isfile(tokenpath):
			if not os.path.exists(tmptokenpath):
				shutil.copy(tokenpath, tmptokenpath)
				os.chmod(tmptokenpath, 0666)
		else:
			print "No token."
			quit()
	pid = start_surveillance()
	time.sleep(conf["camera_warmup_time"])
#	print "Process PID: ", pid

while True:
	if os.path.isfile(tmptimepath):
		with open(tmptimepath, "r") as timefile:
			line = timefile.readline()
			if not line:
				pass
			else:
				lasttime = datetime.datetime.strptime(line, '%Y-%m-%d %H:%M:%S.%f')
				thistime = datetime.datetime.now()
		
				## check if the script has been writing regularly to a file
				
				if (thistime - lasttime).seconds > conf["read_seconds"]:
					print "Idle > ", conf["read_seconds"], "PID: ", pid
					p = psutil.Process(pid)
					try:
						p.terminate()
						p.wait(timeout=1)
						#os.kill(pid, signal.SIGTERM)
						#os.kill(pid, signal.SIGKILL)
					except OSError:
						raise
				
					if pid not in psutil.pids():
						pid = start_surveillance()
					else:
						p.kill()
						p.wait(timeout=1)
						continue
						
				#elif (thistime - lasttime).seconds < conf["read_seconds"]:
					#print "< ", conf["read_seconds"]
					#pass
				#else:
					#print "Time difference: ", (thistime - lasttime).seconds
					#pass				
		time.sleep(conf["read_seconds"])
		
	else:
		time.sleep(conf["read_seconds"])
		print "No time file. Restart surveillance."
		psutil.Process(pid).terminate()
		psutil.Process(pid).wait(timeout=1)
		if not pid in psutil.pids():
			pid = start_surveillance()

		continue
				
		



