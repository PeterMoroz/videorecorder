import logging

import time
from threading import Thread
from queue import Queue, Full

import cv2

class Camera:
    def __init__(self, fps=20.0, queues=[]):
        self.frames = []
        self.framerate = fps
        for i in range(1, 4):
            frame = cv2.imread(str(i) + '.jpg')
            self.frames.append(frame)
        self.queues = queues
        self.read_thread = Thread(target=self._read_routine)
        self.stopped = True

    def start(self):
        self.stopped = False
        self.read_thread.start()

    def stop(self):
        self.stopped = True
        if not self.read_thread is None:
            self.read_thread.join()

    def _read_routine(self):
        while True:
            frame = self._read_frame()
            for q in self.queues:
                try:
                    q.put(frame, block=False)
                except Full as e:
                    logging.error("could not put a from into queue: {}".format(str(e)))
            time.sleep(1.0 / self.framerate)
            if self.stopped:
                return
        
    def _read_frame(self):
        frame = self.frames[int(time.time()) % 3]
        return frame