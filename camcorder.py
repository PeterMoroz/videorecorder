from picamera.array import PiRGBArray
from picamera import PiCamera

import logging
import datetime

import time
from threading import Thread

import cv2

import numpy as np

import glob
import os
import re


class Camcorder:
    def __init__(self, resolution, framerate, base_path, max_fragment_duration=3600, codec='MJPG'):
        self.camera = PiCamera()
        self.camera.resolution = resolution
        self.camera.framerate = framerate
        self.rawCapture = PiRGBArray(self.camera, size=resolution)
        self.stream = self.camera.capture_continuous(self.rawCapture, format="bgr", use_video_port=True)
        
        self.frame_count = 0
        self.fragment_count = -1
        self.fragment_duration = 0
        self.max_fragment_duration = max_fragment_duration
        self.frame_dimension = resolution
        self.framerate = framerate
        self.base_path = base_path
        
        # logging.debug(f"max fragment duration {self.max_fragment_duration}")
        # logging.debug(f"framerate {self.framerate}")
        
        self.fourcc = cv2.VideoWriter_fourcc(*codec)
        self.worker_thread = Thread(target=self._worker_routine)
        self.stopped = True
        
    def start(self):
        self.stopped = False
        self.fragment_count = self._get_last_fragment_count()
        logging.debug(f"starting from {self.fragment_count}")
        self._start_fragment()
        self.worker_thread.start()

    def stop(self):
        self.stopped = True
        if not self.worker_thread is None:
            self.worker_thread.join()

    def _get_last_fragment_count(self):
        base_dir = os.path.dirname(self.base_path)
        files = list(filter(os.path.isfile, glob.glob(base_dir + "/*.avi")))
        if not files:
            return -1

        files.sort(key=os.path.getctime)
        latest_file = files[len(files)-1]
        filename = os.path.basename(latest_file)
        result = re.search('\d+', filename)
        idx = int(result.group())
        return idx
    
    def _start_fragment(self):
        self.frame_count = 0
        self.fragment_duration = 0
        self.fragment_count += 1
        filename = "{}-{}.avi".format(self.base_path, self.fragment_count)
        self.writer = cv2.VideoWriter(filename, self.fourcc, self.framerate, self.frame_dimension, True)
        
    def _write_frame(self, frame):
        (w, h) = frame.shape[:2]
        
        frame_width = self.frame_dimension[0]
        frame_height = self.frame_dimension[1]
        
        if w != frame_width or h != frame_height:
            # default interpolation is bilinear, experiment with different ones
            frame = cv2.resize(frame, self.frame_dimension)
        timestamp = datetime.datetime.now()
        cv2.putText(frame, timestamp.strftime("%A %d %B %Y %I:%M:%S%p"), (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

        output = np.zeros((frame_height, frame_width, 3), dtype="uint8")
        output[0:frame_height, 0:frame_width] = frame
        self.writer.write(output)
        self.frame_count += 1
        # logging.debug(f"frame count {self.frame_count}")
        if self.frame_count % self.framerate == 0:
            self.fragment_duration += 1
            # logging.debug(f"fragment duration {self.fragment_duration}")
            if self.fragment_duration == self.max_fragment_duration:
                self.writer.release()
                self._start_fragment()
            
    def _worker_routine(self):
        for frame in self.stream:
            self._write_frame(frame.array)
            self.rawCapture.truncate(0)
            # time.sleep(1.0 / self.framerate)

            if self.stopped:
                self.stream.close()
                self.rawCapture.close()
                self.camera.close()
                self.writer.release()
                return