from picamera.array import PiRGBArray
from picamera import PiCamera

import logging

import time
from threading import Thread
from queue import Queue, Full

class Camera:
    def __init__(self, resolution=(640, 480), framerate=20, queues=[]):
        self.camera = PiCamera()
        self.camera.resolution = resolution
        self.camera.framerate = framerate
        self.framerate = framerate
        self.rawCapture = PiRGBArray(self.camera, size=resolution)
        self.stream = self.camera.capture_continuous(self.rawCapture, format="bgr", use_video_port=True)
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
        frame_count = 0
        for f in self.stream:
            frame = f.array
            for q in self.queues:
                try:
                    q.put(frame, block=False)
                except Full as e:
                    logging.error("could not put a from into queue: {}".format(str(e)))
            self.rawCapture.truncate(0)
            time.sleep(1.0 / self.framerate)

            if self.stopped:
                self.stream.close()
                self.rawCapture.close()
                self.camera.close()
                return