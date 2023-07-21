import logging
import datetime

from threading import Thread
from queue import Queue, Empty

import cv2

import numpy as np


class FileWriter:
    def __init__(self, filepath, codec='MJPG', fps=20, dimension=(640, 480)):
        fourcc = cv2.VideoWriter_fourcc(*codec)
        self.frame_width = dimension[0]
        self.frame_height = dimension[1]
        self.writer = cv2.VideoWriter(filepath, fourcc, fps, dimension, True)
        self.queue = Queue()
        self.write_thread = Thread(target=self._write_routine)
        self.stopped = True

    def start(self):
        self.stopped = False
        self.write_thread.start()
    
    def stop(self):
        self.stopped = True
        if not self.write_thread is None:
            self.write_thread.join()
        self.writer.release()

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
        if w != self.frame_width or h != self.frame_height:
            # default interpolation is bilinear, experiment with different ones
            frame = cv2.resize(frame, (self.frame_width, self.frame_height))
        timestamp = datetime.datetime.now()
        cv2.putText(frame, timestamp.strftime("%A %d %B %Y %I:%M:%S%p"), (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

        output = np.zeros((self.frame_height, self.frame_width, 3), dtype="uint8")
        output[0:self.frame_height, 0:self.frame_width] = frame
        self.writer.write(output)