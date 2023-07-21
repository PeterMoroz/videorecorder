import logging
import datetime

from threading import Thread
from queue import Queue, Empty

import cv2

import numpy as np


class MultiFileWriter:
    def __init__(self, filename_base, max_fragment_duration=3600, codec='MJPG', fps=20, dimension=(640, 480)):
        self.filename_base = filename_base
        self.frame_count = 0
        self.fragment_count = -1
        self.fragment_duration = 0
        self.max_fragment_duration = max_fragment_duration
        self.dimension = dimension
        self.fps = fps
        self.fourcc = cv2.VideoWriter_fourcc(*codec)
        self.queue = Queue()
        self.write_thread = Thread(target=self._write_routine)
        self.stopped = True

    def start(self):
        self.stopped = False
        self._start_fragment()
        self.write_thread.start()
    
    def stop(self):
        self.stopped = True
        if not self.write_thread is None:
            self.write_thread.join()
        self.writer.release()
        
    def _start_fragment(self):
        self.frame_count = 0
        self.fragment_duration = 0
        self.fragment_count += 1
        filename = "{}-{}.avi".format(self.filename_base, self.fragment_count)
        self.writer = cv2.VideoWriter(filename, self.fourcc, self.fps, self.dimension, True)

    def _write_routine(self):
        while True:
            if self.stopped == True:
                break
            try:
                frame = self.queue.get(block=True, timeout=1)
            except Empty as e:
                continue
            self.queue.task_done()
            self._write_frame(frame)
        while not self.queue.empty():
            frame = self.queue.get()
            self.queue.task_done()
            self._write_frame(frame)

    def _write_frame(self, frame):
        (w, h) = frame.shape[:2]
        
        frame_width = self.dimension[0]
        frame_height = self.dimension[1]
        
        if w != frame_width or h != frame_height:
            # default interpolation is bilinear, experiment with different ones
            frame = cv2.resize(frame, self.dimension)
        timestamp = datetime.datetime.now()
        cv2.putText(frame, timestamp.strftime("%A %d %B %Y %I:%M:%S%p"), (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

        output = np.zeros((frame_height, frame_width, 3), dtype="uint8")
        output[0:frame_height, 0:frame_width] = frame
        self.writer.write(output)
        self.frame_count += 1
        if self.frame_count % self.fps == 0:
            self.fragment_duration += 1
            if self.fragment_duration == self.max_fragment_duration:
                self.writer.release()
                self._start_fragment()