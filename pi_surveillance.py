
# import the necessary packages
from pyimagesearch.tempimage import TempImage
from dropbox.client import DropboxOAuth2FlowNoRedirect
from dropbox.client import DropboxClient
import argparse
import warnings
import datetime
import imutils
import json
import time
import cv2
import threading
import Queue
import os

def upload(q, t, path, client, save):
	q.put(client.put_file(path, open(t.path, "rb")))
	if not save:
		q.put(t.cleanup())

def writeTime(timefile, time):
	with open(timefile, "w") as file:
		#print "Timefile: ", time
		file.write(str(time))
	
	
# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-c", "--conf", required=True, help="path to the JSON configuration file")
args = vars(ap.parse_args())

# filter warnings, load the configuration and initialize the Dropbox
# client
warnings.filterwarnings("ignore")
conf = json.load(open(args["conf"]))
client = None
joblist = []
q = Queue.Queue()
lasttime = -1
thistime = -1

if conf["use_dropbox"]:
	path = conf["tmptokenpath"]
	if os.path.isfile(path):
		tokenfile = open(path, 'r')
		for line in tokenfile.readlines():
			token = line.split(conf["tokenstart"])[1].split(conf["tokenend"])[0]
			#print token
			client = DropboxClient(token)
			print "[SUCCESS] dropbox account linked"
	else:
		pass
	# connect to dropbox and start the session authorization process
	#flow = DropboxOAuth2FlowNoRedirect(conf["dropbox_key"], conf["dropbox_secret"])
	#print "[INFO] Authorize this application: {}".format(flow.start())
	#authCode = raw_input("Enter auth code here: ").strip()
	# finish the authorization and grab the Dropbox client
	#(accessToken, userID) = flow.finish(authCode)
	

camera = cv2.VideoCapture(0)
#camera.set(5, conf["fps"]) ##doesnt work
#print camera.get(5)

# allow the camera to warmup, then initialize the average frame, last
# uploaded timestamp, and frame motion counter
print "[INFO] warming up..."
time.sleep(conf["camera_warmup_time"])
avg = None
lastUploaded = datetime.datetime.now()
motionCounter = 0

timefile = conf["tmptimepath"]

while True:
	timestamp = datetime.datetime.now()
	
	if not os.path.exists(timefile):
		print "Creating tmp timefile..."
		file = open(timefile, "w")
		file.write(str(timestamp))
		file.close()
		os.chmod(timefile, 0666)

	if lasttime == -1:
		lasttime = timestamp

	if (timestamp - lasttime).seconds > conf["write_seconds"]:
		threadOfTime = threading.Thread(target=writeTime, args=(timefile,timestamp))
		threadOfTime.daemon = True
		threadOfTime.start()		
		lasttime = timestamp
	
	# grab current frame and initialise occupied/unoccupied
	(grabbed, frame) = camera.read()
	text = "Unoccupied"

	# if not grabbed then end of video
	if not grabbed:
		break
	
	frame = imutils.resize(frame, conf["width"])
	gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
	gray = cv2.GaussianBlur(gray, (21,21), 0) # apply Gaussian smoothing to average pixel intensities across an 11 x 11 region

	# if the average frame is None, initialize it
	if avg is None:
		print "[INFO] starting background model..."
		avg = gray.copy().astype("float")
		continue
 
	# accumulate the weighted average between the current frame and
	# previous frames, then compute the difference between the current
	# frame and running average
	cv2.accumulateWeighted(gray, avg, 0.5)
	frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))

	# setting threshold for frameDelta, thr at 25, all pixel above set to 255, last argument is method
	thres = cv2.threshold(frameDelta, conf["delta_thres"], 255, cv2.THRESH_BINARY)[1]
	
	# dilate the thresholded image to fill in holes, then find contours on thresholded image
	thres = cv2.dilate(thres, None, iterations=2)
	(_, cnts, _) = cv2.findContours(thres.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

	# loop over contours
	for c in cnts:
		# if the contour is too small, ignore
		if cv2.contourArea(c) < conf["min_area"]:
			continue
			
		# compute the bounding box for the contour, draw it on the frame and update the text
		(x, y, w, h) = cv2.boundingRect(c)
		cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 1)
		text = "Occupied"
		
	ts = timestamp.strftime("%A %d %B %Y %H:%M:%S")
	cv2.putText(frame, "Room Status: {}".format(text), (5,15), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1)
	cv2.putText(frame, ts, (5, frame.shape[0] - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
	
	# check to see if the room is occupied
	if text == "Occupied":
		#print "if ", text
		# check to see if enough time has passed between uploads
		if (timestamp - lastUploaded).seconds >= conf["min_upload_seconds"]:
			# increment the motion counter
			motionCounter += 1
			#print "motion counter ", motionCounter
 
			# check to see if the number of frames with consistent motion is
			# high enough
			if motionCounter >= conf["min_motion_frames"]:
				#print motionCounter, " >= ", conf["min_motion_frames"]
				ts = timestamp.strftime("%Y%m%d%H%M%S%f")
				# write the image to temporary file
				t = TempImage(timestamp=ts)
				cv2.imwrite(t.path, frame)
				
				# check to see if dropbox sohuld be used
				if conf["use_dropbox"]:
					# upload the image to Dropbox and cleanup the tempory image
					print "[UPLOAD] {}".format(ts)
					path = "{base_path}/{timestamp}.jpg".format(base_path=conf["dropbox_base_path"], timestamp=ts)
					print path
					joblist.append(t)
					#print "No. of jobs: ", len(joblist), joblist
					#print q
					for job in joblist:
						thread = threading.Thread(target=upload, args = (q,job,path,client,conf["save_img"]))
						thread.daemon = True
						thread.start()
						joblist.pop(joblist.index(job))
					#s = q.get()
					#print s

				# update the last uploaded timestamp and reset the motion
				# counter
				lastUploaded = timestamp
				motionCounter = 0
	# otherwise, the room is not occupied
	else:
		motionCounter = 0

	# check to see if the frames should be displayed to screen
	if conf["show_video"]:
		# display the security feed
		cv2.imshow("Security Feed", frame)
		key = cv2.waitKey(1) & 0xFF
 
		# if the `q` key is pressed, break from the lop
		if key == ord("q"):
			break
			

		
