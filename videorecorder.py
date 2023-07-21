import argparse
import logging

from flask import Flask
from flask import render_template
from flask import Response

from queue import Queue

import cv2

from camera import Camera
from file_writer import FileWriter
from multifile_writer import MultiFileWriter

app = Flask(__name__)

camera = None
queue = None


def read_frame():
    if not queue is None:
        frame = queue.get()
        queue.task_done()
    ok, jpeg = cv2.imencode('.jpg', frame)
    if not ok:
        logging.error('read_frame() - could not encode (jpg) frame')
        return None
    return jpeg.tobytes()
    # return bytearray(jpeg)

def generate_frame():
    while True:
        frame = read_frame()
        if frame is None:
            continue
        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    """Home page"""
    return render_template("index.html")
    
@app.route('/video')
def video():
    """Video streaming route. Put it in the src attribute of an img tag"""
    return Response(generate_frame(), mimetype="multipart/x-mixed-replace; boundary=frame")

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.DEBUG)
    
    ap = argparse.ArgumentParser()
    ap.add_argument("-p", "--port", type=int, default=9000, help="port, the server listen to (1024 to 65535)")
    args = vars(ap.parse_args())
    
    resolution = (640, 480)
    framerate = 25
    
    queue = Queue()
    
    file_writer = MultiFileWriter('output', 60, dimension=resolution, fps=framerate)
    
    camera = Camera(queues=[queue, file_writer.queue], resolution=resolution, framerate=framerate)
    # camera = Camera(queues=[queue])
    camera.start()
    
    file_writer.start()
       
    logging.info("start application")
    # here is an explanation of arguments
    # https://www.twilio.com/blog/how-run-flask-application
    app.run(host='0.0.0.0', port=args["port"], debug=True, threaded=True, use_reloader=False)
    
    logging.info("application stopped")
    camera.stop()
    logging.debug("camera stopped")
    # flush queue
    while not queue.empty():
        frame = queue.get()
        queue.task_done()
    queue.join()
    logging.debug("queue finished")
    
    file_writer.stop()
    logging.debug("filewriter stopped")
