# SPi
Surveillance RaspPi - SPi

using Python, OpenCV, Dropbox and a normal USB webcam

Original instructions: http://www.pyimagesearch.com/2015/06/01/home-surveillance-and-motion-detection-with-the-raspberry-pi-python-and-opencv/

Executed at system start: in /etc/rc.local add
```bash
/usr/bin/nohup /usr/bin/python /home/pi/SPi/run.py --conf /home/pi/SPi/conf.json >/home/pi/SPi/log 2>&1 &
```
